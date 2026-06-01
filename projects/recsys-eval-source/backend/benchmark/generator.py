import csv
import json
import copy
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

from .templates import (
    generate_classic_gt,
    generate_llm_hybrid_gt,
    generate_composite_gt,
)
from .injectors import (
    inject_classic_recall_missing,
    inject_classic_ranking_abnormal,
    inject_llm_understanding_bias,
    inject_llm_ranking_abnormal,
    inject_llm_system_abnormal,
    inject_composite_understanding_bias,
    inject_composite_evidence_insufficient,
    inject_composite_tool_failure,
    inject_composite_system_abnormal,
)
from .validate import validate_trace
from .scene_pool import (
    CLASSIC_SCENES,
    LLM_HYBRID_SCENES,
    COMPOSITE_ENHANCED_SCENES,
)


def _apply_scene_variation(scene: dict, repeat_idx: int) -> dict:
    new_scene = copy.deepcopy(scene)

    if "user_profile" in new_scene and "user_id" in new_scene["user_profile"]:
        new_scene["user_profile"]["user_id"] = f'{new_scene["user_profile"]["user_id"]}_r{repeat_idx + 1}'

    if "query" in new_scene:
        suffix_pool = [
            "",
            "，尽量实用一些",
            "，希望整体更适合日常使用",
            "，优先考虑性价比和实用性",
        ]
        suffix = suffix_pool[repeat_idx % len(suffix_pool)]
        if suffix and suffix not in new_scene["query"]:
            new_scene["query"] = new_scene["query"] + suffix

    return new_scene


def _compute_trace_summary(trace: dict) -> dict:
    spans = trace.get("trace", [])
    if not spans:
        return {
            "span_count": 0,
            "total_latency_ms": 0,
            "error_span_count": 0,
            "retry_count_total": 0,
            "llm_token_total": 0,
            "llm_estimated_cost": 0.0,
        }

    total_latency_ms = max(span["end_ms"] for span in spans)
    error_span_count = sum(1 for span in spans if span.get("status") != "success")
    retry_count_total = sum(span.get("meta", {}).get("retry_count", 0) or 0 for span in spans)

    llm_token_total = 0
    llm_estimated_cost = 0.0
    for span in spans:
        meta = span.get("meta", {})
        llm_token_total += meta.get("total_tokens", 0) or 0
        llm_estimated_cost += meta.get("estimated_cost", 0.0) or 0.0

    return {
        "span_count": len(spans),
        "total_latency_ms": total_latency_ms,
        "error_span_count": error_span_count,
        "retry_count_total": retry_count_total,
        "llm_token_total": llm_token_total,
        "llm_estimated_cost": round(llm_estimated_cost, 6),
    }


def _infer_eval_layer(issue_type: str) -> str:
    if issue_type in {"understanding_bias", "recall_missing", "evidence_insufficient", "ranking_abnormal"}:
        return "business_process"
    if issue_type in {"tool_failure", "system_abnormal"}:
        return "llm_enhancement"
    return "reference"


def _annotate_trace(trace: dict, pair_id: int, scene_id: str, repeat_idx: int, scene_variant: dict):
    issue_type = trace.get("issue_type", "normal")
    fault_module = trace.get("fault_module", "none")

    trace["experiment_meta"] = {
        "pair_id": pair_id,
        "scene_id": scene_id,
        "repeat_idx": repeat_idx,
        "template_type": trace.get("template_type"),
        "trace_type": trace.get("trace_type"),
        "issue_type": issue_type,
        "fault_module": fault_module,
        "eval_layer": _infer_eval_layer(issue_type),
        "query": scene_variant.get("query", ""),
        "city": scene_variant.get("context", {}).get("city", ""),
        "channel": scene_variant.get("context", {}).get("channel", ""),
    }
    trace["trace_summary"] = _compute_trace_summary(trace)


def _manifest_row(trace: dict) -> dict:
    meta = trace.get("experiment_meta", {})
    summary = trace.get("trace_summary", {})
    return {
        "trace_id": trace.get("trace_id"),
        "pair_id": meta.get("pair_id"),
        "scene_id": meta.get("scene_id"),
        "repeat_idx": meta.get("repeat_idx"),
        "template_type": meta.get("template_type"),
        "trace_type": meta.get("trace_type"),
        "issue_type": meta.get("issue_type"),
        "fault_module": meta.get("fault_module"),
        "eval_layer": meta.get("eval_layer"),
        "total_latency_ms": summary.get("total_latency_ms"),
        "error_span_count": summary.get("error_span_count"),
        "retry_count_total": summary.get("retry_count_total"),
        "llm_token_total": summary.get("llm_token_total"),
        "llm_estimated_cost": summary.get("llm_estimated_cost"),
    }


def build_main_benchmark(repeats_per_scene: int = 4) -> Tuple[List[dict], List[dict]]:
    dataset: List[dict] = []
    manifest: List[dict] = []

    case_id = 1
    pair_id = 1

    template_plan = [
        (
            "classic",
            CLASSIC_SCENES,
            generate_classic_gt,
            [inject_classic_recall_missing, inject_classic_ranking_abnormal],
        ),
        (
            "llm_hybrid",
            LLM_HYBRID_SCENES,
            generate_llm_hybrid_gt,
            [inject_llm_understanding_bias, inject_llm_ranking_abnormal, inject_llm_system_abnormal],
        ),
        (
            "composite_enhanced",
            COMPOSITE_ENHANCED_SCENES,
            generate_composite_gt,
            [
                inject_composite_understanding_bias,
                inject_composite_evidence_insufficient,
                inject_composite_tool_failure,
                inject_composite_system_abnormal,
            ],
        ),
    ]

    for template_name, scenes, gt_fn, injector_list in template_plan:
        for scene_idx, scene in enumerate(scenes, start=1):
            for r in range(repeats_per_scene):
                scene_variant = _apply_scene_variation(scene, r)
                for injector_fn in injector_list:
                    normal_trace = gt_fn(case_id, scene_variant)
                    faulty_trace = injector_fn(normal_trace)

                    scene_id = f"{template_name}_scene{scene_idx:02d}"
                    _annotate_trace(normal_trace, pair_id, scene_id, r + 1, scene_variant)
                    _annotate_trace(faulty_trace, pair_id, scene_id, r + 1, scene_variant)

                    dataset.extend([normal_trace, faulty_trace])
                    manifest.append(_manifest_row(normal_trace))
                    manifest.append(_manifest_row(faulty_trace))

                    case_id += 1
                    pair_id += 1

    return dataset, manifest


def save_benchmark(output_dir: Path, repeats_per_scene: int = 4) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset, manifest = build_main_benchmark(repeats_per_scene=repeats_per_scene)

    all_errors = []
    for idx, trace in enumerate(dataset):
        errs = validate_trace(trace)
        if errs:
            all_errors.append((idx, trace.get("trace_id"), errs))

    output_jsonl = output_dir / "benchmark_main_v1.jsonl"
    output_csv = output_dir / "benchmark_main_v1_manifest.csv"

    with output_jsonl.open("w", encoding="utf-8") as f:
        for trace in dataset:
            f.write(json.dumps(trace, ensure_ascii=False) + "\n")

    with output_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "trace_id", "pair_id", "scene_id", "repeat_idx",
                "template_type", "trace_type", "issue_type", "fault_module", "eval_layer",
                "total_latency_ms", "error_span_count", "retry_count_total",
                "llm_token_total", "llm_estimated_cost",
            ],
        )
        writer.writeheader()
        writer.writerows(manifest)

    meta = {
        "trace_count": len(dataset),
        "pair_count": len(dataset) // 2,
        "validation_errors": all_errors,
        "jsonl_path": str(output_jsonl),
        "manifest_path": str(output_csv),
    }

    counter = Counter((row["template_type"], row["trace_type"], row["issue_type"]) for row in manifest)
    meta["distribution"] = {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in counter.items()}
    return meta


def load_jsonl(path: Path) -> List[dict]:
    data = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data
