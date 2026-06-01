
import io
import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .benchmark.metrics import compute_all_metrics
from .benchmark.validate import validate_trace
from .benchmark.generator import load_jsonl
from .benchmark.experiment_runner import generated_dir

DATA_DIR = Path(__file__).resolve().parent / "data"
TASKS_PATH = DATA_DIR / "tasks.json"
TASK_FILES_DIR = DATA_DIR / "task_files"

CATEGORY_LABELS = {
    "end_to_end": "端到端结果评测",
    "business_process": "业务过程评测",
    "llm_enhancement": "业务过程中的大模型增强评测",
}

MODULE_LABELS = {
    "final_result": "最终结果",
    "intent_understanding": "意图理解",
    "candidate_recall": "候选召回",
    "knowledge_retrieval": "证据检索",
    "ranking_decision": "排序决策",
    "agent_execution": "智能体执行",
    "system_engineering": "系统工程",
}

METRIC_META = {
    "hit_at_k": {
        "name": "命中率@K",
        "meaning": "用于判断最终推荐列表中是否至少包含一个相关项目。",
        "formula": "若前K个结果中存在相关项目，则记为1，否则记为0。",
        "diagnosis": "适合粗粒度判断系统是否仍返回了可接受结果，但对排序位置变化不敏感。",
    },
    "end2end_ndcg": {
        "name": "归一化折损累计增益@K",
        "meaning": "用于衡量相关项目在推荐列表中的排序质量。",
        "formula": "根据相关项目在前K个位置上的排序收益计算DCG，并与理想排序下的IDCG归一化。",
        "diagnosis": "能够反映‘找到了但排错了’的问题，对排序异常较敏感。",
    },
    "mrr": {
        "name": "平均倒数排名",
        "meaning": "用于衡量首个正确项目出现的位置。",
        "formula": "首个正确项目排名的倒数，在样本上取平均。",
        "diagnosis": "适合反映首个正确结果是否被提前展示。",
    },
    "diversity": {
        "name": "推荐多样性",
        "meaning": "用于衡量推荐列表中项目之间的差异程度。",
        "formula": "根据推荐项目标签集合的差异度进行平均计算。",
        "diagnosis": "用于观察推荐结果是否过于同质化。",
    },
    "intent_accuracy": {
        "name": "意图识别准确率",
        "meaning": "用于判断系统是否正确识别用户需求与约束。",
        "formula": "当解析出的类别与约束与参考答案一致时记为1，否则记为0。",
        "diagnosis": "可用于识别意图理解错误或约束解析偏差。",
    },
    "slot_f1": {
        "name": "槽位F1值",
        "meaning": "用于衡量约束槽位抽取的完整性与准确性。",
        "formula": "根据槽位预测结果与参考约束计算精确率、召回率与F1。",
        "diagnosis": "当部分约束遗漏或解析偏差时，该指标会下降。",
    },
    "candidate_recall": {
        "name": "召回率@K",
        "meaning": "用于判断相关项目是否进入候选集合。",
        "formula": "前K个候选中命中的相关项目数除以相关项目总数。",
        "diagnosis": "适合识别漏召问题。",
    },
    "post_filter_recall": {
        "name": "过滤后召回率",
        "meaning": "用于衡量经过业务过滤后的候选覆盖情况。",
        "formula": "过滤后候选中命中的相关项目数除以相关项目总数。",
        "diagnosis": "可用于区分是召回不足还是过滤策略过严。",
    },
    "evidence_coverage": {
        "name": "证据覆盖率",
        "meaning": "用于判断检索到的证据是否覆盖预期支持信息。",
        "formula": "被选中证据与参考证据的重合比例。",
        "diagnosis": "适合发现RAG链路中的证据缺失问题。",
    },
    "ranking_ndcg": {
        "name": "排序nDCG",
        "meaning": "用于衡量排序模块输出与理想排序的一致程度。",
        "formula": "对最终排序结果计算nDCG。",
        "diagnosis": "能够较直接反映排序质量退化。",
    },
    "pairwise_accuracy": {
        "name": "成对一致性",
        "meaning": "用于衡量项目对之间的相对排序是否正确。",
        "formula": "统计在参考顺序中有先后关系的项目对，在预测排序中是否保持相同顺序。",
        "diagnosis": "适合识别局部顺序错误。",
    },
    "tool_health": {
        "name": "工具调用健康度",
        "meaning": "综合反映工具调用是否成功以及调用目标是否正确。",
        "formula": "工具调用准确率与工具成功率的平均值。",
        "diagnosis": "适合识别工具空返回、超时或错误调用。",
    },
    "tool_param_accuracy": {
        "name": "参数正确率",
        "meaning": "用于判断工具调用参数是否与任务要求一致。",
        "formula": "依据关键参数是否与参考约束一致进行计算。",
        "diagnosis": "适合发现仓库、预算等参数传递错误。",
    },
    "system_latency_ms": {
        "name": "时延",
        "meaning": "用于衡量整条链路完成一次请求所需时间。",
        "formula": "取各Span结束时间的最大值作为总时延。",
        "diagnosis": "适合发现系统响应变慢或重试导致的性能退化。",
    },
    "system_error_count": {
        "name": "错误率",
        "meaning": "用于衡量链路中非成功状态节点的数量。",
        "formula": "统计状态不为success的Span数量，并按样本平均。",
        "diagnosis": "适合发现系统稳定性问题。",
    },
    "llm_estimated_cost": {
        "name": "令牌成本",
        "meaning": "用于估计大模型调用带来的推理成本。",
        "formula": "根据请求中累计token数及预设单价估算。",
        "diagnosis": "适合观察系统优化前后的成本变化。",
    },
    "system_retry_count": {
        "name": "重试次数",
        "meaning": "用于反映系统在执行过程中触发重试的频率。",
        "formula": "统计Span中的retry_count总和。",
        "diagnosis": "适合发现外部接口不稳定或限流问题。",
    },
}


def ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TASK_FILES_DIR.mkdir(parents=True, exist_ok=True)
    if not TASKS_PATH.exists():
        TASKS_PATH.write_text("[]", encoding="utf-8")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _read_tasks() -> List[Dict[str, Any]]:
    ensure_storage()
    return json.loads(TASKS_PATH.read_text(encoding="utf-8"))


def _write_tasks(tasks: List[Dict[str, Any]]) -> None:
    ensure_storage()
    TASKS_PATH.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def _task_dir(task_id: str) -> Path:
    path = TASK_FILES_DIR / task_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_tasks() -> List[Dict[str, Any]]:
    tasks = _read_tasks()
    return sorted(tasks, key=lambda x: x.get("updated_at", ""), reverse=True)


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    for task in _read_tasks():
        if task["id"] == task_id:
            return task
    return None


def _update_task(task_id: str, updater) -> Dict[str, Any]:
    tasks = _read_tasks()
    updated = None
    for idx, task in enumerate(tasks):
        if task["id"] == task_id:
            updated = updater(task)
            updated["updated_at"] = _now()
            tasks[idx] = updated
            break
    if updated is None:
        raise KeyError(task_id)
    _write_tasks(tasks)
    return updated


def create_task(name: str) -> Dict[str, Any]:
    tasks = _read_tasks()
    task = {
        "id": uuid.uuid4().hex[:12],
        "name": name,
        "created_at": _now(),
        "updated_at": _now(),
        "status": "draft",
        "mode": "single",
        "uploads": {},
        "validation": None,
        "parsed_chain": None,
        "structure_confirmed": False,
        "config": default_config(),
        "results": None,
    }
    tasks.append(task)
    _write_tasks(tasks)
    return task


def default_config() -> Dict[str, Any]:
    return {
        "auto_eval": {
            "categories": [
                {
                    "key": "end_to_end",
                    "label": CATEGORY_LABELS["end_to_end"],
                    "modules": [
                        {
                            "key": "final_result",
                            "label": MODULE_LABELS["final_result"],
                            "selected_metrics": ["hit_at_k", "end2end_ndcg", "mrr", "diversity"],
                            "recommended_metrics": ["end2end_ndcg", "mrr", "hit_at_k"],
                        }
                    ],
                },
                {
                    "key": "business_process",
                    "label": CATEGORY_LABELS["business_process"],
                    "modules": [
                        {"key": "intent_understanding", "label": MODULE_LABELS["intent_understanding"], "selected_metrics": ["intent_accuracy", "slot_f1"], "recommended_metrics": ["intent_accuracy", "slot_f1"]},
                        {"key": "candidate_recall", "label": MODULE_LABELS["candidate_recall"], "selected_metrics": ["candidate_recall", "post_filter_recall", "evidence_coverage"], "recommended_metrics": ["candidate_recall", "post_filter_recall"]},
                        {"key": "ranking_decision", "label": MODULE_LABELS["ranking_decision"], "selected_metrics": ["ranking_ndcg", "pairwise_accuracy"], "recommended_metrics": ["ranking_ndcg", "pairwise_accuracy"]},
                    ],
                },
                {
                    "key": "llm_enhancement",
                    "label": CATEGORY_LABELS["llm_enhancement"],
                    "modules": [
                        {"key": "agent_execution", "label": MODULE_LABELS["agent_execution"], "selected_metrics": ["tool_health", "tool_param_accuracy"], "recommended_metrics": ["tool_health", "tool_param_accuracy"]},
                        {"key": "system_engineering", "label": MODULE_LABELS["system_engineering"], "selected_metrics": ["system_latency_ms", "system_error_count", "llm_estimated_cost", "system_retry_count"], "recommended_metrics": ["system_latency_ms", "system_error_count"]},
                    ],
                },
            ]
        },
        "llm_judge": {
            "enabled": False,
            "modules": ["ranking_decision", "agent_execution"],
            "prompt_template": "请根据任务目标、链路日志与自动评测结果，对该模块得分进行辅助判断，并给出0到1之间的评分。",
            "scoring": "0-1区间",
        },
        "human_review": {
            "enabled": False,
            "modules": ["intent_understanding", "candidate_recall"],
            "sampling_mode": "抽样评测",
            "sampling_ratio": 0.2,
            "description": "对关键异常样例进行人工复核，用于校正自动评测结果。",
        },
    }


def save_mode(task_id: str, mode: str) -> Dict[str, Any]:
    return _update_task(task_id, lambda task: {**task, "mode": mode, "status": "mode_selected"})


def _parse_uploaded_content(file_bytes: bytes) -> List[Dict[str, Any]]:
    text = file_bytes.decode("utf-8")
    stripped = text.lstrip()
    if stripped.startswith("["):
        data = json.loads(text)
        if isinstance(data, list):
            return data
        raise ValueError("JSON 文件内容不是数组")

    records = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    if not records:
        raise ValueError("文件为空或无法解析为 JSONL")
    return records


def upload_files(task_id: str, files: Dict[str, Tuple[str, bytes]]) -> Dict[str, Any]:
    def updater(task):
        task_dir = _task_dir(task_id)
        uploads = dict(task.get("uploads") or {})
        for key, (filename, file_bytes) in files.items():
            if not file_bytes:
                continue
            safe_name = filename.replace("/", "_")
            path = task_dir / f"{key}_{safe_name}"
            path.write_bytes(file_bytes)
            traces = _parse_uploaded_content(file_bytes)
            uploads[key] = {
                "filename": safe_name,
                "path": str(path),
                "trace_count": len(traces),
            }
        task["uploads"] = uploads
        task["status"] = "uploaded"
        task["validation"] = None
        task["parsed_chain"] = None
        task["structure_confirmed"] = False
        task["results"] = None
        return task
    return _update_task(task_id, updater)


def _load_uploaded_traces(path_str: str) -> List[Dict[str, Any]]:
    path = Path(path_str)
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if stripped.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def validate_task_uploads(task_id: str) -> Dict[str, Any]:
    def validate_one(upload: Dict[str, Any]) -> Dict[str, Any]:
        traces = _load_uploaded_traces(upload["path"])
        errors = []
        warnings = []
        template_distribution: Dict[str, int] = {}
        faulty_count = 0
        normal_count = 0
        missing_fields = 0
        for idx, trace in enumerate(traces):
            errs = validate_trace(trace)
            if errs:
                errors.append({"index": idx, "trace_id": trace.get("trace_id"), "errors": errs})
            template = trace.get("template_type", "未知")
            template_distribution[template] = template_distribution.get(template, 0) + 1
            if trace.get("trace_type") == "faulty":
                faulty_count += 1
            else:
                normal_count += 1
            for field in ["reference", "ground_truth", "trace", "final_output"]:
                if field not in trace:
                    missing_fields += 1
        if missing_fields:
            warnings.append(f"共发现 {missing_fields} 处关键字段缺失，可能影响后续评测。")
        passed = len(errors) == 0
        return {
            "passed": passed,
            "trace_count": len(traces),
            "normal_count": normal_count,
            "faulty_count": faulty_count,
            "template_distribution": template_distribution,
            "errors": errors[:30],
            "error_count": len(errors),
            "warnings": warnings,
        }

    def updater(task):
        uploads = task.get("uploads") or {}
        if not uploads:
            raise ValueError("请先上传 Trace 日志")
        validation = {key: validate_one(value) for key, value in uploads.items()}
        validation["passed"] = all(v["passed"] for v in validation.values() if isinstance(v, dict) and "passed" in v)
        task["validation"] = validation
        task["status"] = "validated" if validation["passed"] else "validation_failed"
        return task
    return _update_task(task_id, updater)


def _extract_chain_structure(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for trace in traces:
        grouped.setdefault(trace.get("template_type", "unknown"), []).append(trace)

    chain_types = []
    structures = []
    for template_type, rows in grouped.items():
        sample = rows[0]
        spans = sample.get("trace", [])
        nodes = []
        edges = []
        span_lookup = {span.get("span_id"): span for span in spans}
        for span in spans:
            label = MODULE_LABELS.get(span.get("module"), span.get("module", "未知模块"))
            nodes.append({
                "id": span.get("span_id"),
                "label": label,
                "subtitle": span.get("node_type", ""),
                "module": span.get("module", ""),
            })
            parent = span.get("parent_span_id")
            if parent and parent in span_lookup:
                edges.append({"from": parent, "to": span.get("span_id")})
        modules = []
        for span in spans:
            m = span.get("module")
            if m and m not in modules:
                modules.append(m)
        chain_types.append({
            "template_type": template_type,
            "label": chain_label(template_type),
            "sample_count": len(rows),
            "modules": [MODULE_LABELS.get(m, m) for m in modules],
        })
        structures.append({
            "template_type": template_type,
            "label": chain_label(template_type),
            "nodes": nodes,
            "edges": edges,
        })
    return {
        "chain_types": chain_types,
        "structures": structures,
        "description": "系统已根据上传日志解析出推荐链路中的关键步骤，并生成链路结构图供确认。",
    }


def chain_label(template_type: str) -> str:
    return {
        "classic": "经典推荐链路",
        "llm_hybrid": "大模型混合推荐链路",
        "composite_enhanced": "检索增强与智能体复合链路",
    }.get(template_type, template_type)


def parse_task_chain(task_id: str) -> Dict[str, Any]:
    def updater(task):
        validation = task.get("validation") or {}
        if not validation or not validation.get("passed"):
            raise ValueError("请先完成日志结构校验")
        uploads = task.get("uploads") or {}
        primary = uploads.get("primary")
        if not primary:
            raise ValueError("未找到主日志文件")
        traces = _load_uploaded_traces(primary["path"])
        task["parsed_chain"] = _extract_chain_structure(traces)
        task["status"] = "parsed"
        return task
    return _update_task(task_id, updater)


def confirm_structure(task_id: str, confirmed: bool) -> Dict[str, Any]:
    def updater(task):
        task["structure_confirmed"] = confirmed
        task["status"] = "structure_confirmed" if confirmed else "parsed"
        return task
    return _update_task(task_id, updater)


def save_config(task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    def updater(task):
        task["config"] = config
        task["status"] = "configured"
        return task
    return _update_task(task_id, updater)


def _safe_mean(nums: List[float]) -> float:
    return round(sum(nums) / len(nums), 4) if nums else 0.0


def _module_source_tag(config: Dict[str, Any], module_key: str) -> str:
    tags = ["自动评测"]
    llm_cfg = config.get("llm_judge", {})
    human_cfg = config.get("human_review", {})
    if llm_cfg.get("enabled") and module_key in (llm_cfg.get("modules") or []):
        tags.append("LLM裁判校正")
    if human_cfg.get("enabled") and module_key in (human_cfg.get("modules") or []):
        tags.append("人工校正")
    return " + ".join(tags)


def _status_by_score(score: float, reverse: bool = False) -> Tuple[str, str]:
    value = score if not reverse else 1 - min(max(score, 0.0), 1.0)
    if value >= 0.85:
        return "良好", "good"
    if value >= 0.6:
        return "关注", "warn"
    return "异常", "bad"


def _status_by_ratio(value: float, baseline: float) -> Tuple[str, str]:
    if baseline <= 0:
        return "良好", "good"
    ratio = value / baseline
    if ratio <= 1.15:
        return "良好", "good"
    if ratio <= 1.6:
        return "关注", "warn"
    return "异常", "bad"


def _baseline_faulty_split(per_trace: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    normal = [row for row in per_trace if row.get("trace_type") == "normal"]
    faulty = [row for row in per_trace if row.get("trace_type") == "faulty"]
    return normal, faulty


def _avg(rows: List[Dict[str, Any]], key: str) -> float:
    values = [float(r.get(key, 0) or 0) for r in rows]
    return _safe_mean(values)


def _layer_distribution(details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for cat in details:
        scores = [m["module_score"] for m in cat["modules"]]
        out.append({
            "name": cat["label"],
            "value": round(sum(scores), 4),
        })
    return out


def _recent_task_trend(current_task_id: str, current_score: float) -> List[Dict[str, Any]]:
    tasks = list_tasks()[:6]
    tasks = list(reversed(tasks))
    trend = []
    for task in tasks:
        result = task.get("results") or {}
        overview = result.get("overview") or {}
        score = overview.get("overall_score")
        if score is None and task["id"] == current_task_id:
            score = current_score
        if score is None:
            continue
        trend.append({"name": task["name"], "score": score})
    if not trend:
        trend.append({"name": "当前任务", "score": current_score})
    return trend


def _metric_card(metric_key: str, current: float, baseline: float, module_key: str, config: Dict[str, Any], value_suffix: str = "") -> Dict[str, Any]:
    meta = METRIC_META[metric_key]
    if metric_key in {"system_latency_ms", "system_error_count", "llm_estimated_cost", "system_retry_count"}:
        status_text, status_class = _status_by_ratio(current, baseline if baseline else 1.0)
    else:
        status_text, status_class = _status_by_score(current)
    return {
        "key": metric_key,
        "name": meta["name"],
        "current_value": current,
        "baseline_value": baseline,
        "display_value": f"{current:.4f}{value_suffix}" if isinstance(current, float) else str(current),
        "baseline_display": f"{baseline:.4f}{value_suffix}" if isinstance(baseline, float) else str(baseline),
        "status": status_text,
        "status_class": status_class,
        "source": _module_source_tag(config, module_key),
        "help": {
            "meaning": meta["meaning"],
            "formula": meta["formula"],
            "diagnosis": meta["diagnosis"],
        },
    }


def _module_score_from_metrics(module_key: str, current: Dict[str, float], baseline: Dict[str, float]) -> float:
    if module_key == "final_result":
        return round((current["end2end_ndcg"] + current["mrr"] + current["hit_at_k"]) / 3, 4)
    if module_key == "intent_understanding":
        return round((current["intent_accuracy"] + current["slot_f1"]) / 2, 4)
    if module_key == "candidate_recall":
        return round((current["candidate_recall"] + current["post_filter_recall"] + current["evidence_coverage"]) / 3, 4)
    if module_key == "ranking_decision":
        return round((current["ranking_ndcg"] + current["pairwise_accuracy"]) / 2, 4)
    if module_key == "agent_execution":
        return round((current["tool_health"] + current["tool_param_accuracy"]) / 2, 4)
    if module_key == "system_engineering":
        latency_score = min(1.0, baseline["system_latency_ms"] / current["system_latency_ms"]) if current["system_latency_ms"] else 1.0
        cost_score = min(1.0, baseline["llm_estimated_cost"] / current["llm_estimated_cost"]) if current["llm_estimated_cost"] else 1.0
        error_score = 1.0 / (1.0 + current["system_error_count"])
        retry_score = 1.0 / (1.0 + current["system_retry_count"])
        return round((latency_score + cost_score + error_score + retry_score) / 4, 4)
    return 1.0


def _major_modules(details: List[Dict[str, Any]]) -> List[str]:
    items = []
    for cat in details:
        for module in cat["modules"]:
            items.append(module)
    items.sort(key=lambda x: x["module_score"])
    return [item["label"] for item in items[:3] if item["module_score"] < 0.85] or ["未发现显著异常模块"]


def _metric_suffix(metric_key: str) -> str:
    if metric_key == "system_latency_ms":
        return " ms"
    return ""


def _core_metric_keys() -> List[str]:
    return [
        "hit_at_k", "end2end_ndcg", "mrr", "diversity", "intent_accuracy", "slot_f1",
        "candidate_recall", "post_filter_recall", "evidence_coverage", "ranking_ndcg", "pairwise_accuracy",
        "tool_health", "tool_param_accuracy", "system_latency_ms", "system_error_count", "llm_estimated_cost", "system_retry_count"
    ]


def _build_categories_from_scores(cur: Dict[str, float], base: Dict[str, float], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    categories = [
        {
            "key": "end_to_end",
            "label": CATEGORY_LABELS["end_to_end"],
            "modules": [
                {
                    "key": "final_result",
                    "label": MODULE_LABELS["final_result"],
                    "metrics": [
                        _metric_card("hit_at_k", cur["hit_at_k"], base["hit_at_k"], "final_result", config),
                        _metric_card("end2end_ndcg", cur["end2end_ndcg"], base["end2end_ndcg"], "final_result", config),
                        _metric_card("mrr", cur["mrr"], base["mrr"], "final_result", config),
                        _metric_card("diversity", cur["diversity"], base["diversity"], "final_result", config),
                    ],
                }
            ],
        },
        {
            "key": "business_process",
            "label": CATEGORY_LABELS["business_process"],
            "modules": [
                {
                    "key": "intent_understanding",
                    "label": MODULE_LABELS["intent_understanding"],
                    "metrics": [
                        _metric_card("intent_accuracy", cur["intent_accuracy"], base["intent_accuracy"], "intent_understanding", config),
                        _metric_card("slot_f1", cur["slot_f1"], base["slot_f1"], "intent_understanding", config),
                    ],
                },
                {
                    "key": "candidate_recall",
                    "label": MODULE_LABELS["candidate_recall"],
                    "metrics": [
                        _metric_card("candidate_recall", cur["candidate_recall"], base["candidate_recall"], "candidate_recall", config),
                        _metric_card("post_filter_recall", cur["post_filter_recall"], base["post_filter_recall"], "candidate_recall", config),
                        _metric_card("evidence_coverage", cur["evidence_coverage"], base["evidence_coverage"], "candidate_recall", config),
                    ],
                },
                {
                    "key": "ranking_decision",
                    "label": MODULE_LABELS["ranking_decision"],
                    "metrics": [
                        _metric_card("ranking_ndcg", cur["ranking_ndcg"], base["ranking_ndcg"], "ranking_decision", config),
                        _metric_card("pairwise_accuracy", cur["pairwise_accuracy"], base["pairwise_accuracy"], "ranking_decision", config),
                    ],
                },
            ],
        },
        {
            "key": "llm_enhancement",
            "label": CATEGORY_LABELS["llm_enhancement"],
            "modules": [
                {
                    "key": "agent_execution",
                    "label": MODULE_LABELS["agent_execution"],
                    "metrics": [
                        _metric_card("tool_health", cur["tool_health"], base["tool_health"], "agent_execution", config),
                        _metric_card("tool_param_accuracy", cur["tool_param_accuracy"], base["tool_param_accuracy"], "agent_execution", config),
                    ],
                },
                {
                    "key": "system_engineering",
                    "label": MODULE_LABELS["system_engineering"],
                    "metrics": [
                        _metric_card("system_latency_ms", cur["system_latency_ms"], base["system_latency_ms"], "system_engineering", config, " ms"),
                        _metric_card("system_error_count", cur["system_error_count"], base["system_error_count"], "system_engineering", config),
                        _metric_card("llm_estimated_cost", cur["llm_estimated_cost"], base["llm_estimated_cost"], "system_engineering", config),
                        _metric_card("system_retry_count", cur["system_retry_count"], base["system_retry_count"], "system_engineering", config),
                    ],
                },
            ],
        },
    ]
    for cat in categories:
        for module in cat["modules"]:
            module["module_score"] = _module_score_from_metrics(module["key"], cur, base)
            status_text, status_class = _status_by_score(module["module_score"])
            module["status"] = status_text
            module["status_class"] = status_class
    return categories


def _headline_metrics(summary_headline: Dict[str, Any], faulty_case_count: int) -> Dict[str, Any]:
    return {
        "归因准确率": round(float(summary_headline["attribution_accuracy"]), 4),
        "主故障识别率": round(float(summary_headline["primary_fault_identification_rate"]), 4),
        "级联故障区分率": round(float(summary_headline["cascade_detection_rate"]), 4),
        "异常样例数": faulty_case_count,
    }


def _evaluate_dataset(task_id: str, traces: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    outputs = compute_all_metrics(traces)
    per_trace = outputs["per_trace"]
    normal_rows, faulty_rows = _baseline_faulty_split(per_trace)
    keys = _core_metric_keys()
    base = {key: _avg(normal_rows, key) for key in keys}
    cur = {key: _avg(faulty_rows or normal_rows, key) for key in keys}
    categories = _build_categories_from_scores(cur, base, config)
    overall_score = round(_safe_mean([m["module_score"] for c in categories for m in c["modules"]]), 4)
    overall_status, overall_status_class = _status_by_score(overall_score)
    major_modules = _major_modules(categories)
    faulty_case_count = outputs["summary"]["faulty_count"]
    headline = outputs["summary"]["headline_metrics"]
    diagnosis = "；".join([
        f"当前任务共检测到 {faulty_case_count} 条异常样例。",
        f"整体评测得分为 {overall_score:.4f}，系统状态为{overall_status}。",
        f"主要异常集中在：{'、'.join(major_modules)}。",
    ])
    reading_suggestion = "建议优先查看评测详情中的低分模块，再结合可视化分析页面判断异常集中在哪一层评测体系。"
    return {
        "overview": {
            "overall_score": overall_score,
            "overall_status": overall_status,
            "overall_status_class": overall_status_class,
            "major_anomaly_modules": major_modules,
            "diagnosis": diagnosis,
            "task_status": "评测完成",
            "reading_suggestion": reading_suggestion,
            "headline_metrics": _headline_metrics(headline, faulty_case_count),
        },
        "details": categories,
        "visualization": {
            "module_scores": [
                {"name": module["label"], "score": module["module_score"], "status": module["status"], "module_key": module["key"]}
                for category in categories for module in category["modules"]
            ],
            "layer_distribution": _layer_distribution(categories),
            "task_trend": _recent_task_trend(task_id, overall_score),
        },
        "raw_tables": {
            "end_to_end": outputs["end_to_end_table"],
            "module_response": outputs["module_response_table"],
            "attribution_case": outputs["attribution_case_table"],
            "attribution_summary": outputs["attribution_summary"],
        },
    }


def _flatten_module_rows(details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for category in details:
        for module in category["modules"]:
            rows.append({
                "category_key": category["key"],
                "category_label": category["label"],
                "module_key": module["key"],
                "module_label": module["label"],
                "module_score": module["module_score"],
                "status": module["status"],
                "status_class": module["status_class"],
            })
    return rows


def _flatten_metric_rows(details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for category in details:
        for module in category["modules"]:
            for metric in module["metrics"]:
                rows.append({
                    "category_key": category["key"],
                    "category_label": category["label"],
                    "module_key": module["key"],
                    "module_label": module["label"],
                    "metric_key": metric["key"],
                    "metric_name": metric["name"],
                    "value": metric["current_value"],
                    "display_value": metric["display_value"],
                    "baseline_value": metric["baseline_value"],
                    "baseline_display": metric["baseline_display"],
                    "help": metric["help"],
                    "source": metric["source"],
                })
    return rows


def _compare_status(delta: float, reverse: bool = False) -> Tuple[str, str]:
    improved = delta < 0 if reverse else delta > 0
    worsened = delta > 0 if reverse else delta < 0
    if abs(delta) < 1e-9:
        return "持平", "status-draft"
    if improved:
        return "提升", "badge-good"
    if worsened:
        return "下降", "badge-bad"
    return "持平", "status-draft"


def _merge_compare_details(primary_details: List[Dict[str, Any]], secondary_details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sec_modules = {(c["key"], m["key"]): m for c in secondary_details for m in c["modules"]}
    sec_metrics = {(c["key"], m["key"], metric["key"]): metric for c in secondary_details for m in c["modules"] for metric in m["metrics"]}
    compare_categories = []
    reverse_metric_keys = {"system_latency_ms", "system_error_count", "llm_estimated_cost", "system_retry_count"}
    for category in primary_details:
        new_cat = {"key": category["key"], "label": category["label"], "modules": []}
        for module in category["modules"]:
            other_module = sec_modules.get((category["key"], module["key"]), {})
            delta_module = round(module["module_score"] - float(other_module.get("module_score", 0) or 0), 4)
            mod_trend, mod_class = _compare_status(delta_module)
            new_module = {
                "key": module["key"],
                "label": module["label"],
                "primary_score": module["module_score"],
                "secondary_score": float(other_module.get("module_score", 0) or 0),
                "delta": delta_module,
                "trend": mod_trend,
                "trend_class": mod_class,
                "metrics": [],
            }
            for metric in module["metrics"]:
                other_metric = sec_metrics.get((category["key"], module["key"], metric["key"]), {})
                p_val = float(metric.get("current_value", 0) or 0)
                s_val = float(other_metric.get("current_value", 0) or 0)
                delta = round(p_val - s_val, 4)
                trend, trend_class = _compare_status(delta, metric["key"] in reverse_metric_keys)
                new_module["metrics"].append({
                    "key": metric["key"],
                    "name": metric["name"],
                    "primary_value": p_val,
                    "secondary_value": s_val,
                    "delta": delta,
                    "primary_display": metric.get("display_value", "-"),
                    "secondary_display": other_metric.get("display_value", f"{s_val:.4f}{_metric_suffix(metric['key'])}"),
                    "baseline_primary": metric.get("baseline_display", "-"),
                    "baseline_secondary": other_metric.get("baseline_display", "-"),
                    "trend": trend,
                    "trend_class": trend_class,
                    "source": metric.get("source", "自动评测"),
                    "help": metric["help"],
                })
            new_cat["modules"].append(new_module)
        compare_categories.append(new_cat)
    return compare_categories


def _comparison_visualization(primary_eval: Dict[str, Any], secondary_eval: Dict[str, Any], compare_details: List[Dict[str, Any]], task_id: str) -> Dict[str, Any]:
    module_rows = []
    for cat in compare_details:
        for module in cat["modules"]:
            module_rows.append({
                "name": module["label"],
                "primary_score": module["primary_score"],
                "secondary_score": module["secondary_score"],
                "delta": module["delta"],
            })
    layer_rows = []
    sec_layer = {row["name"]: row["value"] for row in secondary_eval["visualization"]["layer_distribution"]}
    for row in primary_eval["visualization"]["layer_distribution"]:
        s_val = sec_layer.get(row["name"], 0)
        layer_rows.append({
            "name": row["name"],
            "primary_value": row["value"],
            "secondary_value": s_val,
            "delta": round(row["value"] - s_val, 4),
        })
    metric_rows = []
    for cat in compare_details:
        for module in cat["modules"]:
            for metric in module["metrics"]:
                metric_rows.append({
                    "category_label": cat["label"],
                    "module_label": module["label"],
                    "metric_name": metric["name"],
                    "primary_value": metric["primary_value"],
                    "secondary_value": metric["secondary_value"],
                    "delta": metric["delta"],
                    "primary_display": metric["primary_display"],
                    "secondary_display": metric["secondary_display"],
                    "help": metric["help"],
                })
    return {
        "module_scores_compare": module_rows,
        "layer_distribution_compare": layer_rows,
        "metric_compare_rows": metric_rows,
        "task_trend": _recent_task_trend(task_id, primary_eval["overview"]["overall_score"]),
        "overall_compare": [
            {"name": "主日志", "score": primary_eval["overview"]["overall_score"]},
            {"name": "对比日志", "score": secondary_eval["overview"]["overall_score"]},
        ],
    }


def _build_results(task_id: str, traces_primary: List[Dict[str, Any]], traces_secondary: Optional[List[Dict[str, Any]]], config: Dict[str, Any]) -> Dict[str, Any]:
    primary_eval = _evaluate_dataset(task_id, traces_primary, config)
    if not traces_secondary:
        return {
            "mode": "single",
            **primary_eval,
        }

    secondary_eval = _evaluate_dataset(task_id, traces_secondary, config)
    compare_details = _merge_compare_details(primary_eval["details"], secondary_eval["details"])
    p_score = primary_eval["overview"]["overall_score"]
    s_score = secondary_eval["overview"]["overall_score"]
    delta = round(p_score - s_score, 4)
    better_side = "主日志" if delta > 0 else ("对比日志" if delta < 0 else "两者持平")

    primary_mods = {m["name"]: m["score"] for m in primary_eval["visualization"]["module_scores"]}
    secondary_mods = {m["name"]: m["score"] for m in secondary_eval["visualization"]["module_scores"]}
    module_deltas = [{"name": name, "delta": round(primary_mods[name] - secondary_mods.get(name, 0), 4)} for name in primary_mods.keys()]
    module_deltas_sorted = sorted(module_deltas, key=lambda x: x["delta"], reverse=True)
    major_improvements = [x["name"] for x in module_deltas_sorted[:2] if x["delta"] > 0]
    major_regressions = [x["name"] for x in sorted(module_deltas, key=lambda x: x["delta"])[:2] if x["delta"] < 0]

    overview = {
        "overall_score": p_score,
        "overall_status": primary_eval["overview"]["overall_status"],
        "overall_status_class": primary_eval["overview"]["overall_status_class"],
        "major_anomaly_modules": primary_eval["overview"]["major_anomaly_modules"],
        "diagnosis": f"对比模式下，主日志整体得分为 {p_score:.4f}，对比日志整体得分为 {s_score:.4f}，差值为 {delta:.4f}。{better_side}整体表现更优。",
        "task_status": "评测完成",
        "reading_suggestion": "建议先查看总览中的优劣结论，再在评测详情中逐模块比对差值，最后结合可视化分析定位主要改善或退化来源。",
        "headline_metrics": {
            "主日志总体评分": p_score,
            "对比日志总体评分": s_score,
            "总体评分差值": delta,
            "更优结果": better_side,
        },
        "comparison": {
            "primary_overall": p_score,
            "secondary_overall": s_score,
            "delta": delta,
            "better_side": better_side,
            "major_improvements": major_improvements,
            "major_regressions": major_regressions,
        },
    }

    return {
        "mode": "compare",
        "overview": overview,
        "details": compare_details,
        "visualization": _comparison_visualization(primary_eval, secondary_eval, compare_details, task_id),
        "primary": primary_eval,
        "secondary": secondary_eval,
        "comparison": {
            "summary": overview["comparison"],
            "details": compare_details,
            "visualization": _comparison_visualization(primary_eval, secondary_eval, compare_details, task_id),
        },
    }




def run_task_evaluation(task_id: str) -> Dict[str, Any]:
    def updater(task):
        uploads = task.get("uploads") or {}
        if not uploads.get("primary"):
            raise ValueError("请先上传主日志")
        if task.get("mode") == "compare" and not uploads.get("secondary"):
            raise ValueError("链路对比评测需要上传对比日志")
        if not task.get("structure_confirmed"):
            raise ValueError("请先确认链路结构")
        config = task.get("config") or default_config()
        task["status"] = "running"
        traces_primary = _load_uploaded_traces(uploads["primary"]["path"])
        traces_secondary = _load_uploaded_traces(uploads["secondary"]["path"]) if uploads.get("secondary") else None
        results = _build_results(task_id, traces_primary, traces_secondary, config)
        task["results"] = results
        task["status"] = "completed"
        return task
    return _update_task(task_id, updater)

def create_demo_task_if_needed() -> None:
    tasks = _read_tasks()
    if tasks:
        return
    demo = create_task("示例评测任务")
    demo_path = generated_dir() / "benchmark_main_v1.jsonl"
    if not demo_path.exists():
        return
    demo_bytes = demo_path.read_bytes()
    upload_files(demo["id"], {"primary": (demo_path.name, demo_bytes)})
    validate_task_uploads(demo["id"])
    parse_task_chain(demo["id"])
    confirm_structure(demo["id"], True)
    run_task_evaluation(demo["id"])
