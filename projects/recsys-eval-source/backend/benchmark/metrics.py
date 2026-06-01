import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Tuple


def _find_span(trace: Dict[str, Any], span_id: str) -> Dict[str, Any]:
    for span in trace["trace"]:
        if span["span_id"] == span_id:
            return span
    raise KeyError(span_id)


def _product_map(trace: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {p["sku_id"]: p for p in trace["reference"].get("products", [])}


def _doc_ids(trace: Dict[str, Any]) -> List[str]:
    return [d["doc_id"] for d in trace["reference"].get("docs", [])]


def _safe_mean(values: List[float]) -> float:
    return round(mean(values), 4) if values else 0.0


def _flatten_constraints(category: str, constraints: Dict[str, Any]) -> set:
    flat = {f"category={category}"}
    for k, v in constraints.items():
        if isinstance(v, list):
            for item in v:
                flat.add(f"{k}={item}")
        else:
            flat.add(f"{k}={v}")
    return flat


def _slot_f1(expected: set, predicted: set) -> float:
    if not expected and not predicted:
        return 1.0
    tp = len(expected & predicted)
    if tp == 0:
        return 0.0
    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / len(expected) if expected else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _hit_at_k(final_items: List[str], gt_items: List[str]) -> float:
    return 1.0 if any(item in gt_items for item in final_items) else 0.0


def _recall_at_k(pred_items: List[str], gt_items: List[str]) -> float:
    if not gt_items:
        return 1.0
    return len(set(pred_items) & set(gt_items)) / len(gt_items)


def _mrr(pred_items: List[str], gt_items: List[str]) -> float:
    for idx, item in enumerate(pred_items, start=1):
        if item in gt_items:
            return 1.0 / idx
    return 0.0


def _ndcg(pred_items: List[str], gt_items: List[str]) -> float:
    if not gt_items:
        return 1.0

    rel_map = {}
    size = len(gt_items)
    for i, item in enumerate(gt_items):
        rel_map[item] = size - i

    dcg = 0.0
    for idx, item in enumerate(pred_items, start=1):
        rel = rel_map.get(item, 0)
        if rel > 0:
            dcg += rel / __import__("math").log2(idx + 1)

    ideal = 0.0
    for idx, item in enumerate(gt_items, start=1):
        rel = rel_map[item]
        ideal += rel / __import__("math").log2(idx + 1)

    return dcg / ideal if ideal > 0 else 0.0


def _pairwise_accuracy(pred_items: List[str], gt_items: List[str]) -> float:
    positions = {item: idx for idx, item in enumerate(pred_items)}
    valid_pairs = 0
    correct_pairs = 0
    for i in range(len(gt_items)):
        for j in range(i + 1, len(gt_items)):
            a = gt_items[i]
            b = gt_items[j]
            if a in positions and b in positions:
                valid_pairs += 1
                if positions[a] < positions[b]:
                    correct_pairs += 1
    if valid_pairs == 0:
        return 0.0
    return correct_pairs / valid_pairs


def _diversity(items: List[str], product_map: Dict[str, Dict[str, Any]]) -> float:
    if len(items) < 2:
        return 0.0
    pairs = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            tags_i = set(product_map.get(items[i], {}).get("tags", []))
            tags_j = set(product_map.get(items[j], {}).get("tags", []))
            if not tags_i and not tags_j:
                score = 0.0
            else:
                union = tags_i | tags_j
                inter = tags_i & tags_j
                score = 1 - (len(inter) / len(union) if union else 0.0)
            pairs.append(score)
    return sum(pairs) / len(pairs) if pairs else 0.0


def _compute_intent_metrics(trace: Dict[str, Any]) -> Tuple[float, float]:
    s1 = _find_span(trace, "s1")
    expected_category = trace["reference"]["category"]
    expected_constraints = trace["reference"]["constraints"]

    if trace["template_type"] == "composite_enhanced":
        predicted_category = s1["output"]["constraints"].get("category", expected_category)
        predicted_constraints = {k: v for k, v in s1["output"]["constraints"].items() if k != "category"}
    else:
        predicted_category = s1["output"].get("category", expected_category)
        predicted_constraints = s1["output"].get("constraints", {})

    expected_set = _flatten_constraints(expected_category, expected_constraints)
    predicted_set = _flatten_constraints(predicted_category, predicted_constraints)
    intent_accuracy = 1.0 if predicted_category == expected_category and expected_set == predicted_set else 0.0
    slot_f1 = _slot_f1(expected_set, predicted_set)
    return intent_accuracy, slot_f1


def _compute_recall_metrics(trace: Dict[str, Any]) -> Tuple[float, float]:
    gt_items = trace["ground_truth"]["expected_top_items"]

    if trace["template_type"] == "classic":
        merged = _find_span(trace, "s3")["output"]["merged_candidates"]
        return _recall_at_k(merged, gt_items), _recall_at_k(_find_span(trace, "s4")["output"]["kept_candidates"], gt_items)

    if trace["template_type"] == "llm_hybrid":
        merged = _find_span(trace, "s3")["output"]["merged_candidates"]
        return _recall_at_k(merged, gt_items), _recall_at_k(_find_span(trace, "s4")["output"]["top_candidates"], gt_items)

    recalled = _find_span(trace, "s4")["output"]["recalled_items"]
    valid = _find_span(trace, "s7")["output"]["valid_candidates"]
    return _recall_at_k(recalled, gt_items), _recall_at_k(valid, gt_items)


def _compute_evidence_coverage(trace: Dict[str, Any]) -> float:
    expected_docs = trace["ground_truth"].get("expected_evidence", [])
    if not expected_docs:
        return 1.0
    if trace["template_type"] != "composite_enhanced":
        return 1.0
    selected = _find_span(trace, "s7")["output"].get("selected_evidence_docs", [])
    return _recall_at_k(selected, expected_docs)


def _compute_ranking_metrics(trace: Dict[str, Any]) -> Tuple[float, float]:
    gt_items = trace["ground_truth"]["expected_top_items"]
    final_items = trace["final_output"]["items"]
    return _ndcg(final_items, gt_items), _pairwise_accuracy(final_items, gt_items)


def _compute_agent_metrics(trace: Dict[str, Any]) -> Tuple[float, float]:
    if trace["template_type"] != "composite_enhanced":
        return 1.0, 1.0
    s5 = _find_span(trace, "s5")
    s6 = _find_span(trace, "s6")
    expected_tools = trace["ground_truth"].get("expected_tool_usage", [])
    observed_tools = [s5["meta"].get("tool_name"), s6["meta"].get("tool_name")]
    tool_call_accuracy = len([x for x in observed_tools if x in expected_tools]) / len(expected_tools) if expected_tools else 1.0
    tool_success_rate = sum(1 for s in [s5, s6] if s["status"] == "success") / 2
    parameter_accuracy = 1.0
    warehouse = trace["reference"]["constraints"].get("warehouse")
    if s5["input"].get("warehouse") != warehouse:
        parameter_accuracy = 0.0
    return (tool_call_accuracy + tool_success_rate) / 2, parameter_accuracy


def _compute_system_metrics(trace: Dict[str, Any]) -> Tuple[float, float, float, float]:
    summary = trace["trace_summary"]
    latency = float(summary["total_latency_ms"])
    error_count = float(summary["error_span_count"])
    tokens = float(summary["llm_token_total"])
    cost = float(summary["llm_estimated_cost"])
    return latency, error_count, tokens, cost


def _predict_fault_module(metric_row: Dict[str, Any]) -> Tuple[str, bool]:
    degraded = []

    if metric_row["intent_accuracy"] < 1.0 or metric_row["slot_f1"] < 0.85:
        degraded.append("intent_understanding")
    if metric_row["candidate_recall"] < 0.99 or metric_row["post_filter_recall"] < 0.99:
        degraded.append("candidate_recall")
    if metric_row["evidence_coverage"] < 0.99:
        degraded.append("knowledge_retrieval")
    if metric_row["ranking_ndcg"] < 0.90 or metric_row["pairwise_accuracy"] < 1.0:
        degraded.append("ranking_decision")
    if metric_row["tool_health"] < 0.95 or metric_row["tool_param_accuracy"] < 1.0:
        degraded.append("agent_execution")
    if metric_row["system_latency_ms"] > 220 or metric_row["system_error_count"] > 0 or metric_row["system_retry_count"] > 0:
        degraded.append("system_engineering")

    if not degraded:
        return "none", False

    priority = [
        "system_engineering",
        "agent_execution",
        "intent_understanding",
        "knowledge_retrieval",
        "candidate_recall",
        "ranking_decision",
    ]
    for item in priority:
        if item in degraded:
            return item, len(degraded) > 1
    return degraded[0], len(degraded) > 1


def compute_all_metrics(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    per_trace = []
    grouped_end_to_end = defaultdict(list)
    grouped_module = defaultdict(list)
    grouped_attr_case = []

    by_pair = defaultdict(dict)

    for trace in traces:
        trace_id = trace["trace_id"]
        meta = trace["experiment_meta"]
        gt_items = trace["ground_truth"]["expected_top_items"]
        final_items = trace["final_output"]["items"]
        product_map = _product_map(trace)

        intent_accuracy, slot_f1 = _compute_intent_metrics(trace)
        candidate_recall, post_filter_recall = _compute_recall_metrics(trace)
        evidence_coverage = _compute_evidence_coverage(trace)
        ranking_ndcg, pairwise_acc = _compute_ranking_metrics(trace)
        tool_health, tool_param_accuracy = _compute_agent_metrics(trace)
        latency, error_count, tokens, cost = _compute_system_metrics(trace)

        row = {
            "trace_id": trace_id,
            "pair_id": meta["pair_id"],
            "scene_id": meta["scene_id"],
            "repeat_idx": meta["repeat_idx"],
            "template_type": meta["template_type"],
            "trace_type": meta["trace_type"],
            "issue_type": meta["issue_type"],
            "fault_module": meta["fault_module"],
            "hit_at_k": round(_hit_at_k(final_items, gt_items), 4),
            "end2end_ndcg": round(_ndcg(final_items, gt_items), 4),
            "mrr": round(_mrr(final_items, gt_items), 4),
            "diversity": round(_diversity(final_items, product_map), 4),
            "intent_accuracy": round(intent_accuracy, 4),
            "slot_f1": round(slot_f1, 4),
            "candidate_recall": round(candidate_recall, 4),
            "post_filter_recall": round(post_filter_recall, 4),
            "evidence_coverage": round(evidence_coverage, 4),
            "ranking_ndcg": round(ranking_ndcg, 4),
            "pairwise_accuracy": round(pairwise_acc, 4),
            "tool_health": round(tool_health, 4),
            "tool_param_accuracy": round(tool_param_accuracy, 4),
            "system_latency_ms": round(latency, 2),
            "system_error_count": int(error_count),
            "system_retry_count": int(trace["trace_summary"]["retry_count_total"]),
            "llm_token_total": int(tokens),
            "llm_estimated_cost": round(cost, 6),
        }

        predicted_module, has_cascade = _predict_fault_module(row)
        row["predicted_fault_module"] = predicted_module
        row["cascade_detected"] = has_cascade

        per_trace.append(row)
        by_pair[row["pair_id"]][row["trace_type"]] = row

        grouped_end_to_end[(row["template_type"], row["issue_type"])].append(row)
        grouped_module[row["issue_type"]].append(row)

    end_to_end_table = []
    for (template_type, issue_type), rows in sorted(grouped_end_to_end.items()):
        end_to_end_table.append({
            "template_type": template_type,
            "issue_type": issue_type,
            "sample_count": len(rows),
            "hit_at_k": _safe_mean([r["hit_at_k"] for r in rows]),
            "ndcg_at_k": _safe_mean([r["end2end_ndcg"] for r in rows]),
            "mrr": _safe_mean([r["mrr"] for r in rows]),
            "diversity": _safe_mean([r["diversity"] for r in rows]),
        })

    module_response_table = []
    for issue_type, rows in sorted(grouped_module.items()):
        if issue_type == "normal":
            continue
        module_response_table.append({
            "issue_type": issue_type,
            "sample_count": len(rows),
            "intent_score": _safe_mean([(r["intent_accuracy"] + r["slot_f1"]) / 2 for r in rows]),
            "recall_score": _safe_mean([(r["candidate_recall"] + r["post_filter_recall"]) / 2 for r in rows]),
            "evidence_score": _safe_mean([r["evidence_coverage"] for r in rows]),
            "ranking_score": _safe_mean([(r["ranking_ndcg"] + r["pairwise_accuracy"]) / 2 for r in rows]),
            "agent_score": _safe_mean([(r["tool_health"] + r["tool_param_accuracy"]) / 2 for r in rows]),
            "system_latency_ms": _safe_mean([r["system_latency_ms"] for r in rows]),
            "system_error_count": _safe_mean([r["system_error_count"] for r in rows]),
            "llm_estimated_cost": _safe_mean([r["llm_estimated_cost"] for r in rows]),
        })

    attribution_case_table = []
    attr_correct = []
    cascade_correct = []
    primary_correct = []

    for pair_id, pair_data in sorted(by_pair.items()):
        normal = pair_data.get("normal")
        faulty = pair_data.get("faulty")
        if not normal or not faulty:
            continue

        actual = faulty["fault_module"]
        predicted = faulty["predicted_fault_module"]
        is_correct = actual == predicted

        expected_cascade = faulty["issue_type"] in {"understanding_bias", "evidence_insufficient", "tool_failure"}
        cascade_ok = expected_cascade == faulty["cascade_detected"]

        attribution_case_table.append({
            "pair_id": pair_id,
            "template_type": faulty["template_type"],
            "issue_type": faulty["issue_type"],
            "actual_fault_module": actual,
            "predicted_fault_module": predicted,
            "is_correct": int(is_correct),
            "cascade_detected": int(faulty["cascade_detected"]),
            "expected_cascade": int(expected_cascade),
            "cascade_correct": int(cascade_ok),
        })

        attr_correct.append(int(is_correct))
        primary_correct.append(int(is_correct))
        cascade_correct.append(int(cascade_ok))

    attribution_summary = [{
        "attribution_accuracy": round(sum(attr_correct) / len(attr_correct), 4) if attr_correct else 0.0,
        "primary_fault_identification_rate": round(sum(primary_correct) / len(primary_correct), 4) if primary_correct else 0.0,
        "cascade_detection_rate": round(sum(cascade_correct) / len(cascade_correct), 4) if cascade_correct else 0.0,
        "faulty_case_count": len(attr_correct),
    }]

    summary = {
        "trace_count": len(per_trace),
        "normal_count": sum(1 for r in per_trace if r["trace_type"] == "normal"),
        "faulty_count": sum(1 for r in per_trace if r["trace_type"] == "faulty"),
        "template_distribution": {
            key: sum(1 for r in per_trace if r["template_type"] == key)
            for key in sorted({r["template_type"] for r in per_trace})
        },
        "issue_distribution": {
            key: sum(1 for r in per_trace if r["issue_type"] == key)
            for key in sorted({r["issue_type"] for r in per_trace})
        },
        "headline_metrics": attribution_summary[0],
    }

    return {
        "per_trace": per_trace,
        "end_to_end_table": end_to_end_table,
        "module_response_table": module_response_table,
        "attribution_case_table": attribution_case_table,
        "attribution_summary": attribution_summary,
        "summary": summary,
    }


def save_metrics(outputs: Dict[str, Any], output_dir: Path) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)

    file_map = {}

    def _write_csv(name: str, rows: List[Dict[str, Any]]):
        path = output_dir / name
        file_map[name] = str(path)
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    _write_csv("per_trace_metrics.csv", outputs["per_trace"])
    _write_csv("table_end_to_end.csv", outputs["end_to_end_table"])
    _write_csv("table_module_response.csv", outputs["module_response_table"])
    _write_csv("table_attribution_case.csv", outputs["attribution_case_table"])
    _write_csv("table_attribution_summary.csv", outputs["attribution_summary"])

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(outputs["summary"], ensure_ascii=False, indent=2), encoding="utf-8")
    file_map["summary.json"] = str(summary_path)

    return file_map
