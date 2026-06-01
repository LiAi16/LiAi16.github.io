import copy
from typing import Any, Dict, List


def _find_span(trace: Dict[str, Any], span_id: str) -> Dict[str, Any]:
    for span in trace["trace"]:
        if span["span_id"] == span_id:
            return span
    raise ValueError(f"Span {span_id} not found")


def _remove_item_from_list(items: List[str], target: str) -> List[str]:
    return [x for x in items if x != target]


def _ensure_fault_labels(
    faulty: Dict[str, Any],
    issue_type: str,
    fault_module: str,
    recoverability: str,
) -> None:
    faulty["trace_type"] = "faulty"
    faulty["issue_type"] = issue_type
    faulty["fault_module"] = fault_module
    faulty["recoverability"] = recoverability


def _set_trace_id(trace: Dict[str, Any], base_trace_id: str, suffix: str) -> None:
    trace["trace_id"] = f"{base_trace_id}_{suffix}"


def _set_span_timing(span: Dict[str, Any], start_ms: int, end_ms: int) -> None:
    span["start_ms"] = start_ms
    span["end_ms"] = end_ms
    span["latency_ms"] = end_ms - start_ms


def inject_classic_recall_missing(
    trace: Dict[str, Any],
    missing_item: str = "sku_1033",
) -> Dict[str, Any]:
    faulty = copy.deepcopy(trace)
    _ensure_fault_labels(faulty, "recall_missing", "candidate_recall", "unrecoverable")
    _set_trace_id(faulty, trace["trace_id"], "recall_missing")

    s2 = _find_span(faulty, "s2")
    s3 = _find_span(faulty, "s3")
    s4 = _find_span(faulty, "s4")
    s5 = _find_span(faulty, "s5")
    s6 = _find_span(faulty, "s6")
    s7 = _find_span(faulty, "s7")

    for key in ["semantic_recall", "behavior_recall", "embedding_recall"]:
        if key in s2["output"]:
            s2["output"][key] = _remove_item_from_list(s2["output"][key], missing_item)

    merged_candidates = _remove_item_from_list(s3["output"]["merged_candidates"], missing_item)
    s3["output"]["merged_candidates"] = merged_candidates

    kept_candidates = _remove_item_from_list(s4["output"]["kept_candidates"], missing_item)
    s4["input"]["candidates"] = merged_candidates
    s4["output"]["kept_candidates"] = kept_candidates

    if missing_item in s5["output"]["scores"]:
        del s5["output"]["scores"][missing_item]
    s5["input"]["candidates"] = kept_candidates
    s5["output"]["topk"] = ["sku_1007", "sku_1015", "sku_1050"]

    s6["input"]["topk_from_coarse"] = ["sku_1007", "sku_1015", "sku_1050"]
    s6["output"]["scores"] = {"sku_1007": 0.91, "sku_1015": 0.85, "sku_1050": 0.79}
    s6["output"]["ranked_list"] = ["sku_1007", "sku_1015", "sku_1050"]

    s7["input"]["ranked_list"] = ["sku_1007", "sku_1015", "sku_1050"]
    s7["output"]["final_items"] = ["sku_1007", "sku_1015", "sku_1050"]
    faulty["final_output"]["items"] = ["sku_1007", "sku_1015", "sku_1050"]

    return faulty


def inject_classic_ranking_abnormal(trace: Dict[str, Any]) -> Dict[str, Any]:
    faulty = copy.deepcopy(trace)
    _ensure_fault_labels(faulty, "ranking_abnormal", "ranking_decision", "unrecoverable")
    _set_trace_id(faulty, trace["trace_id"], "ranking_abnormal")

    s5 = _find_span(faulty, "s5")
    s6 = _find_span(faulty, "s6")
    s7 = _find_span(faulty, "s7")

    s5["output"]["scores"] = {"sku_1007": 0.86, "sku_1033": 0.80, "sku_1015": 0.78, "sku_1050": 0.89}
    s5["output"]["topk"] = ["sku_1050", "sku_1007", "sku_1015"]

    s6["input"]["topk_from_coarse"] = ["sku_1050", "sku_1007", "sku_1015"]
    s6["output"]["scores"] = {"sku_1050": 0.92, "sku_1007": 0.88, "sku_1015": 0.84}
    s6["output"]["ranked_list"] = ["sku_1050", "sku_1007", "sku_1015"]

    s7["input"]["ranked_list"] = ["sku_1050", "sku_1007", "sku_1015"]
    s7["output"]["final_items"] = ["sku_1050", "sku_1007", "sku_1015"]
    faulty["final_output"]["items"] = ["sku_1050", "sku_1007", "sku_1015"]

    return faulty


def inject_llm_understanding_bias(trace: Dict[str, Any]) -> Dict[str, Any]:
    faulty = copy.deepcopy(trace)
    _ensure_fault_labels(faulty, "understanding_bias", "intent_understanding", "unrecoverable")
    _set_trace_id(faulty, trace["trace_id"], "understanding_bias")

    s1 = _find_span(faulty, "s1")
    s2 = _find_span(faulty, "s2")
    s3 = _find_span(faulty, "s3")
    s4 = _find_span(faulty, "s4")
    s5 = _find_span(faulty, "s5")
    s6 = _find_span(faulty, "s6")
    s7 = _find_span(faulty, "s7")
    s8 = _find_span(faulty, "s8")

    s1["output"]["constraints"]["style"] = ["casual", "basic"]

    wrong_semantic = ["sku_2175", "sku_2192", "sku_2101", "sku_2180"]
    wrong_behavior = ["sku_2175", "sku_2192"]
    wrong_embedding = ["sku_2192", "sku_2175", "sku_2180"]

    s2["input"]["constraints"]["style"] = ["casual", "basic"]
    s2["output"]["recall_sources"] = {
        "semantic_recall": wrong_semantic,
        "behavior_recall": wrong_behavior,
        "embedding_recall": wrong_embedding,
    }

    merged_candidates = ["sku_2175", "sku_2192", "sku_2101", "sku_2180"]
    s3["output"]["merged_candidates"] = merged_candidates

    s4["input"]["merged_candidates"] = merged_candidates
    s4["output"]["scores"] = {"sku_2175": 0.91, "sku_2192": 0.88, "sku_2101": 0.82, "sku_2180": 0.78}
    s4["output"]["top_candidates"] = ["sku_2175", "sku_2192", "sku_2101", "sku_2180"]

    s5["input"]["top_candidates"] = ["sku_2175", "sku_2192", "sku_2101", "sku_2180"]
    s5["output"]["prompt_summary"] = "基于用户日常休闲和基础风格偏好，对候选鞋款进行重排并生成理由。"

    s6["input"]["prompt_summary"] = s5["output"]["prompt_summary"]
    s6["output"]["raw_response"] = {
        "recommended_items": ["sku_2175", "sku_2192", "sku_2101"],
        "reasons": [
            "sku_2175 更偏基础日常风格",
            "sku_2192 风格简单，更适合休闲使用",
            "sku_2101 作为补充候选保留",
        ],
    }

    s7["input"]["raw_response"] = s6["output"]["raw_response"]
    s7["output"]["parsed_items"] = ["sku_2175", "sku_2192", "sku_2101"]
    s7["output"]["parsed_text"] = "推荐 sku_2175、sku_2192 和 sku_2101，它们整体更偏基础和日常风格。"

    s8["input"]["parsed_items"] = ["sku_2175", "sku_2192", "sku_2101"]
    s8["output"]["validated_items"] = ["sku_2175", "sku_2192", "sku_2101"]
    s8["output"]["rule_check_passed"] = True

    faulty["final_output"]["items"] = ["sku_2175", "sku_2192", "sku_2101"]
    faulty["final_output"]["text"] = "推荐 sku_2175、sku_2192 和 sku_2101，它们整体更偏基础和日常风格。"

    return faulty


def inject_llm_ranking_abnormal(
    trace: Dict[str, Any],
    injected_item: str = "sku_2180",
) -> Dict[str, Any]:
    faulty = copy.deepcopy(trace)
    _ensure_fault_labels(faulty, "ranking_abnormal", "ranking_decision", "recoverable")
    _set_trace_id(faulty, trace["trace_id"], "ranking_abnormal")

    s5 = _find_span(faulty, "s5")
    s6 = _find_span(faulty, "s6")
    s7 = _find_span(faulty, "s7")
    s8 = _find_span(faulty, "s8")

    s6["input"]["prompt_summary"] = s5["output"]["prompt_summary"]
    s6["output"]["raw_response"] = {
        "recommended_items": [injected_item, "sku_2101", "sku_2120"],
        "reasons": [
            f"{injected_item} 被模型错误地判断为更优先的候选",
            "sku_2101 仍被保留在结果中",
            "sku_2120 仍被保留在结果中",
        ],
    }

    s7["input"]["raw_response"] = s6["output"]["raw_response"]
    s7["output"]["parsed_items"] = [injected_item, "sku_2101", "sku_2120"]
    s7["output"]["parsed_text"] = f"推荐 {injected_item}、sku_2101 和 sku_2120，它们整体较符合通勤需求。"

    s8["input"]["parsed_items"] = [injected_item, "sku_2101", "sku_2120"]
    s8["output"]["validated_items"] = [injected_item, "sku_2101", "sku_2120"]
    s8["output"]["rule_check_passed"] = True

    faulty["final_output"]["items"] = [injected_item, "sku_2101", "sku_2120"]
    faulty["final_output"]["text"] = f"推荐 {injected_item}、sku_2101 和 sku_2120，它们整体较符合通勤需求。"

    return faulty


def inject_llm_system_abnormal(trace: Dict[str, Any]) -> Dict[str, Any]:
    faulty = copy.deepcopy(trace)
    _ensure_fault_labels(faulty, "system_abnormal", "system_engineering", "recoverable")
    _set_trace_id(faulty, trace["trace_id"], "system_abnormal")

    s5 = _find_span(faulty, "s5")
    s6 = _find_span(faulty, "s6")
    s7 = _find_span(faulty, "s7")
    s8 = _find_span(faulty, "s8")

    _set_span_timing(s5, 58, 82)
    _set_span_timing(s6, 83, 245)
    _set_span_timing(s7, 246, 260)
    _set_span_timing(s8, 261, 272)

    s6["status"] = "degraded"
    s6["meta"]["retry_count"] = 2
    s6["meta"]["error_code"] = "RETRY_SUCCESS_AFTER_429"
    s6["meta"]["transient_errors"] = ["429", "timeout"]
    s6["meta"]["prompt_tokens"] = 214
    s6["meta"]["completion_tokens"] = 96
    s6["meta"]["total_tokens"] = 310
    s6["meta"]["estimated_cost"] = 0.0074

    s8["meta"]["retry_count"] = 1
    s8["meta"]["error_code"] = "RULE_CHECK_RETRY"
    return faulty


def inject_composite_understanding_bias(trace: Dict[str, Any]) -> Dict[str, Any]:
    faulty = copy.deepcopy(trace)
    _ensure_fault_labels(faulty, "understanding_bias", "intent_understanding", "unrecoverable")
    _set_trace_id(faulty, trace["trace_id"], "understanding_bias")

    s1 = _find_span(faulty, "s1")
    s2 = _find_span(faulty, "s2")
    s5 = _find_span(faulty, "s5")
    s7 = _find_span(faulty, "s7")
    s8 = _find_span(faulty, "s8")
    s9 = _find_span(faulty, "s9")
    s10 = _find_span(faulty, "s10")

    s1["output"]["constraints"]["warehouse"] = "shenzhen"
    s1["output"]["constraints"]["style_preference"] = ["basic_gift"]

    s2["input"]["intent_result"]["warehouse"] = "shenzhen"
    s2["output"]["planned_knowledge_scope"] = ["gift_packaging_rules"]

    s5["input"]["warehouse"] = "shenzhen"
    s5["output"]["inventory_result"] = {
        "sku_3012": 1,
        "sku_3031": 0,
        "sku_3048": 0,
        "sku_3055": 4,
    }

    s7["input"]["inventory_result"] = {"sku_3012": 1, "sku_3031": 0, "sku_3048": 0, "sku_3055": 4}
    s7["output"]["valid_candidates"] = ["sku_3055", "sku_3012"]
    s7["output"]["removed_candidates"] = {
        "sku_3031": "no_stock_under_wrong_warehouse",
        "sku_3048": "over_budget_and_no_stock",
    }
    s7["output"]["selected_evidence_docs"] = ["doc_gift_packaging_01"]

    s8["input"]["valid_candidates"] = ["sku_3055", "sku_3012"]
    s8["input"]["selected_evidence_docs"] = ["doc_gift_packaging_01"]
    s8["output"]["scores"] = {"sku_3055": 0.88, "sku_3012": 0.83}
    s8["output"]["top_items"] = ["sku_3055", "sku_3012"]

    s9["input"]["top_items"] = ["sku_3055", "sku_3012"]
    s9["input"]["selected_evidence_docs"] = ["doc_gift_packaging_01"]
    s9["input"]["tool_observations"] = {
        "inventory_result": {"sku_3055": 4, "sku_3012": 1},
        "price_result": {"sku_3055": 149, "sku_3012": 169},
    }
    s9["output"]["prompt_summary"] = "基于礼物场景知识证据、候选商品结果及库存和价格工具返回结果，输出两款推荐商品及理由。"

    s10["input"]["prompt_summary"] = s9["output"]["prompt_summary"]
    s10["output"]["recommended_items"] = ["sku_3055", "sku_3012"]
    s10["output"]["generated_reason"] = "推荐 sku_3055 和 sku_3012。这两款在预算范围内，且更符合当前解析到的礼物场景需求。"

    faulty["final_output"]["items"] = ["sku_3055", "sku_3012"]
    faulty["final_output"]["text"] = "推荐 sku_3055 和 sku_3012。这两款在预算范围内，且更符合当前解析到的礼物场景需求。"
    faulty["final_output"]["justification_sources"] = ["doc_gift_packaging_01", "inventory_api", "price_api"]

    return faulty


def inject_composite_evidence_insufficient(trace: Dict[str, Any]) -> Dict[str, Any]:
    faulty = copy.deepcopy(trace)
    _ensure_fault_labels(faulty, "evidence_insufficient", "knowledge_retrieval", "recoverable")
    _set_trace_id(faulty, trace["trace_id"], "evidence_insufficient")

    s3 = _find_span(faulty, "s3")
    s7 = _find_span(faulty, "s7")
    s8 = _find_span(faulty, "s8")
    s9 = _find_span(faulty, "s9")
    s10 = _find_span(faulty, "s10")

    s3["output"]["retrieved_docs"] = [{
        "doc_id": "doc_gift_packaging_01",
        "title": "礼赠型商品包装要求说明",
        "snippet": "礼物场景下，包装精致、适合直接赠送的香薰类商品更受欢迎。",
    }]

    s7["input"]["retrieved_docs"] = ["doc_gift_packaging_01"]
    s7["output"]["selected_evidence_docs"] = ["doc_gift_packaging_01"]

    s8["input"]["selected_evidence_docs"] = ["doc_gift_packaging_01"]
    s8["output"]["scores"] = {"sku_3012": 0.92, "sku_3031": 0.89, "sku_3055": 0.75}
    s8["output"]["top_items"] = ["sku_3012", "sku_3031"]

    s9["input"]["selected_evidence_docs"] = ["doc_gift_packaging_01"]
    s9["output"]["prompt_summary"] = "基于部分礼物场景知识证据、候选商品结果及库存和价格工具返回结果，输出两款推荐商品及理由。"

    s10["input"]["prompt_summary"] = s9["output"]["prompt_summary"]
    s10["output"]["recommended_items"] = ["sku_3012", "sku_3031"]
    s10["output"]["generated_reason"] = "推荐 sku_3012 和 sku_3031。这两款在预算范围内，且包装表现较适合作为礼物。"

    faulty["final_output"]["items"] = ["sku_3012", "sku_3031"]
    faulty["final_output"]["text"] = "推荐 sku_3012 和 sku_3031。这两款在预算范围内，且包装表现较适合作为礼物。"
    faulty["final_output"]["justification_sources"] = ["doc_gift_packaging_01", "inventory_api", "price_api"]

    return faulty


def inject_composite_tool_failure(trace: Dict[str, Any]) -> Dict[str, Any]:
    faulty = copy.deepcopy(trace)
    _ensure_fault_labels(faulty, "tool_failure", "agent_execution", "recoverable")
    _set_trace_id(faulty, trace["trace_id"], "tool_failure")

    s5 = _find_span(faulty, "s5")
    s7 = _find_span(faulty, "s7")
    s8 = _find_span(faulty, "s8")
    s9 = _find_span(faulty, "s9")
    s10 = _find_span(faulty, "s10")

    s5["status"] = "degraded"
    s5["output"] = {"inventory_result": {}}
    s5["meta"]["error_code"] = "TIMEOUT"
    s5["meta"]["retry_count"] = 1

    s7["input"]["inventory_result"] = {}
    s7["output"]["valid_candidates"] = ["sku_3012", "sku_3031", "sku_3055"]
    s7["output"]["removed_candidates"] = {}
    s7["output"]["selected_evidence_docs"] = ["doc_gift_packaging_01", "doc_aroma_gift_guide_02"]

    s8["input"]["valid_candidates"] = ["sku_3012", "sku_3031", "sku_3055"]
    s8["output"]["scores"] = {"sku_3012": 0.91, "sku_3031": 0.88, "sku_3055": 0.76}
    s8["output"]["top_items"] = ["sku_3012", "sku_3031"]

    s9["input"]["tool_observations"] = {
        "inventory_result": {},
        "price_result": {"sku_3012": 169, "sku_3031": 199},
    }
    s9["output"]["prompt_summary"] = "基于礼物场景知识证据、候选商品结果及可用工具返回结果，输出两款推荐商品及理由。"

    s10["input"]["prompt_summary"] = s9["output"]["prompt_summary"]
    s10["output"]["recommended_items"] = ["sku_3012", "sku_3031"]
    s10["output"]["generated_reason"] = "推荐 sku_3012 和 sku_3031。这两款都在200元预算内，且更符合生日礼物场景下对包装完整度和礼赠属性的要求。"

    faulty["final_output"]["items"] = ["sku_3012", "sku_3031"]
    faulty["final_output"]["text"] = "推荐 sku_3012 和 sku_3031。这两款都在200元预算内，且更符合生日礼物场景下对包装完整度和礼赠属性的要求。"
    faulty["final_output"]["justification_sources"] = ["doc_gift_packaging_01", "doc_aroma_gift_guide_02", "price_api"]

    return faulty


def inject_composite_system_abnormal(trace: Dict[str, Any]) -> Dict[str, Any]:
    faulty = copy.deepcopy(trace)
    _ensure_fault_labels(faulty, "system_abnormal", "system_engineering", "recoverable")
    _set_trace_id(faulty, trace["trace_id"], "system_abnormal")

    s5 = _find_span(faulty, "s5")
    s6 = _find_span(faulty, "s6")
    s9 = _find_span(faulty, "s9")
    s10 = _find_span(faulty, "s10")

    _set_span_timing(s5, 49, 132)
    _set_span_timing(s6, 133, 168)
    _set_span_timing(s9, 169, 198)
    _set_span_timing(s10, 199, 338)

    s5["status"] = "degraded"
    s5["meta"]["retry_count"] = 1
    s5["meta"]["error_code"] = "INVENTORY_TIMEOUT_RETRY"
    s5["meta"]["transient_errors"] = ["timeout"]

    s10["status"] = "degraded"
    s10["meta"]["retry_count"] = 2
    s10["meta"]["error_code"] = "LLM_RETRY_SUCCESS"
    s10["meta"]["transient_errors"] = ["429", "timeout"]
    s10["meta"]["prompt_tokens"] = 286
    s10["meta"]["completion_tokens"] = 104
    s10["meta"]["total_tokens"] = 390
    s10["meta"]["estimated_cost"] = 0.0091

    return faulty
