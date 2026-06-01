import copy
from typing import Any, Dict, Optional


def _make_meta(
    service_name: str,
    model_name: Optional[str] = None,
    retry_count: int = 0,
    error_code: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    meta = {
        "service_name": service_name,
        "retry_count": retry_count,
        "error_code": error_code,
    }
    if model_name is not None:
        meta["model_name"] = model_name
    if extra:
        meta.update(extra)
    return meta


def _make_span(
    span_id: str,
    parent_span_id: Optional[str],
    module: str,
    node_type: str,
    status: str,
    start_ms: int,
    end_ms: int,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    meta: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "module": module,
        "node_type": node_type,
        "status": status,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "latency_ms": end_ms - start_ms,
        "input": input_data,
        "output": output_data,
        "meta": meta,
    }


def _default_classic_scene() -> Dict[str, Any]:
    return {
        "query": "预算300元内，适合春季通勤的女士轻薄外套",
        "city": "guangzhou",
        "season": "spring",
        "user_profile": {
            "user_id": "u_1024",
            "gender": "female",
            "age_bucket": "25-34",
            "price_preference": "mid",
            "style_preference": ["commute", "minimal"],
            "recent_behaviors": ["clicked_trench_coat", "favorited_light_jacket"],
        },
        "context": {
            "channel": "search",
            "city": "guangzhou",
            "season": "spring",
        },
        "category": "women_outerwear",
        "constraints": {
            "max_price": 300,
            "season": "spring",
            "style": ["commute", "lightweight"],
        },
        "products": [
            {"sku_id": "sku_1007", "price": 269, "stock": 12, "season": "spring", "tags": ["commute", "lightweight"]},
            {"sku_id": "sku_1033", "price": 299, "stock": 8, "season": "spring", "tags": ["minimal", "commute"]},
            {"sku_id": "sku_1015", "price": 239, "stock": 20, "season": "spring", "tags": ["lightweight"]},
            {"sku_id": "sku_1050", "price": 279, "stock": 7, "season": "spring", "tags": ["commute"]},
            {"sku_id": "sku_1091", "price": 399, "stock": 5, "season": "spring", "tags": ["commute"]},
            {"sku_id": "sku_1088", "price": 199, "stock": 0, "season": "spring", "tags": ["casual"]},
            {"sku_id": "sku_1102", "price": 259, "stock": 11, "season": "winter", "tags": ["minimal"]},
        ],
        "ground_truth": {
            "expected_top_items": ["sku_1007", "sku_1033", "sku_1015"],
            "expected_evidence": [],
            "expected_tool_usage": [],
        },
    }


def _default_llm_scene() -> Dict[str, Any]:
    return {
        "query": "给我推荐三款适合上班通勤的女士鞋子，预算500元内，最好简约一点，并说明理由",
        "city": "shanghai",
        "season": "spring",
        "user_profile": {
            "user_id": "u_2048",
            "gender": "female",
            "age_bucket": "25-34",
            "style_preference": ["minimal", "commute"],
            "price_preference": "mid",
        },
        "context": {
            "channel": "chat_assistant",
            "season": "spring",
            "city": "shanghai",
        },
        "category": "women_shoes",
        "constraints": {
            "max_price": 500,
            "style": ["minimal", "commute"],
            "count": 3,
        },
        "products": [
            {"sku_id": "sku_2101", "price": 399, "stock": 15, "tags": ["minimal", "commute"]},
            {"sku_id": "sku_2120", "price": 459, "stock": 12, "tags": ["minimal", "office"]},
            {"sku_id": "sku_2133", "price": 429, "stock": 10, "tags": ["commute", "clean_shape"]},
            {"sku_id": "sku_2180", "price": 489, "stock": 6, "tags": ["commute"]},
            {"sku_id": "sku_2175", "price": 369, "stock": 9, "tags": ["casual"]},
            {"sku_id": "sku_2192", "price": 299, "stock": 14, "tags": ["simple"]},
        ],
        "ground_truth": {
            "expected_top_items": ["sku_2101", "sku_2120", "sku_2133"],
            "expected_evidence": [],
            "expected_tool_usage": [],
        },
    }


def _default_composite_scene() -> Dict[str, Any]:
    return {
        "query": "帮我推荐两款适合作为女生生日礼物的香薰，预算200元内，最好包装精致一点，并确认广州仓有货，说明推荐理由",
        "city": "guangzhou",
        "festival": "birthday_gift",
        "user_profile": {
            "user_id": "u_3099",
            "gender": "female",
            "gift_preference": ["practical", "good_packaging"],
            "price_preference": "mid_low",
        },
        "context": {
            "channel": "chat_assistant",
            "city": "guangzhou",
            "festival": "birthday_gift",
        },
        "category": "aroma",
        "constraints": {
            "budget_max": 200,
            "recipient": "female",
            "style_preference": ["giftable", "good_packaging"],
            "must_check_inventory": True,
            "warehouse": "guangzhou",
            "count": 2,
        },
        "products": [
            {"sku_id": "sku_3012", "price": 169, "stock": 18, "tags": ["giftable", "good_packaging"]},
            {"sku_id": "sku_3031", "price": 199, "stock": 26, "tags": ["giftable", "birthday"]},
            {"sku_id": "sku_3048", "price": 229, "stock": 0, "tags": ["premium"]},
            {"sku_id": "sku_3055", "price": 149, "stock": 4, "tags": ["basic_gift"]},
        ],
        "docs": [
            {
                "doc_id": "doc_gift_packaging_01",
                "title": "礼赠型商品包装要求说明",
                "snippet": "礼物场景下，包装精致、适合直接赠送的香薰类商品更受欢迎。",
            },
            {
                "doc_id": "doc_aroma_gift_guide_02",
                "title": "香薰礼物推荐指南",
                "snippet": "女生生日礼物场景下，香型温和、包装完整度高、价格适中的香薰更适合作为礼物。",
            },
        ],
        "ground_truth": {
            "expected_top_items": ["sku_3012", "sku_3031"],
            "expected_evidence": ["doc_gift_packaging_01", "doc_aroma_gift_guide_02"],
            "expected_tool_usage": ["inventory_api", "price_api"],
        },
    }


def _merge_scene(default_scene: Dict[str, Any], scene: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    merged = copy.deepcopy(default_scene)
    if not scene:
        return merged
    for k, v in scene.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k].update(v)
        else:
            merged[k] = v
    return merged


def _build_reference(scene_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "category": scene_data["category"],
        "constraints": copy.deepcopy(scene_data["constraints"]),
        "products": copy.deepcopy(scene_data["products"]),
        "docs": copy.deepcopy(scene_data.get("docs", [])),
    }


def generate_classic_gt(case_id: int, scene: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    scene_data = _merge_scene(_default_classic_scene(), scene)
    query = scene_data["query"]
    user_profile = scene_data["user_profile"]
    context = scene_data["context"]
    category = scene_data["category"]
    constraints = scene_data["constraints"]
    gt = scene_data["ground_truth"]

    semantic_recall = ["sku_1007", "sku_1015", "sku_1050", "sku_1091"]
    behavior_recall = ["sku_1033", "sku_1007", "sku_1088"]
    embedding_recall = ["sku_1015", "sku_1033", "sku_1102"]

    merged_candidates = ["sku_1007", "sku_1033", "sku_1015", "sku_1050", "sku_1091", "sku_1088", "sku_1102"]
    kept_candidates = ["sku_1007", "sku_1033", "sku_1015", "sku_1050"]
    filtered_out = {
        "sku_1091": "price_over_budget",
        "sku_1088": "out_of_stock",
        "sku_1102": "wrong_season",
    }

    coarse_scores = {"sku_1007": 0.88, "sku_1033": 0.84, "sku_1015": 0.82, "sku_1050": 0.71}
    fine_scores = {"sku_1007": 0.91, "sku_1033": 0.89, "sku_1015": 0.85}

    trace = [
        _make_span(
            "s1", None, "intent", "intent_understanding", "success", 0, 12,
            {"query": query},
            {"category": category, "constraints": copy.deepcopy(constraints)},
            _make_meta("intent_parser", model_name="intent_v1"),
        ),
        _make_span(
            "s2", "s1", "retrieval", "multi_recall", "success", 13, 38,
            {"parsed_constraints": {"category": category, **constraints}},
            {"semantic_recall": semantic_recall, "behavior_recall": behavior_recall, "embedding_recall": embedding_recall},
            _make_meta("recall_service", model_name="multi_recall_v2"),
        ),
        _make_span(
            "s3", "s2", "retrieval", "recall_merge_dedup", "success", 39, 44,
            {"semantic_recall": semantic_recall, "behavior_recall": behavior_recall, "embedding_recall": embedding_recall},
            {"merged_candidates": merged_candidates},
            _make_meta("merge_service"),
        ),
        _make_span(
            "s4", "s3", "retrieval", "business_filter", "success", 45, 55,
            {"candidates": merged_candidates, "constraints": {"max_price": constraints["max_price"], "season": constraints["season"]}},
            {"kept_candidates": kept_candidates, "filtered_out": filtered_out},
            _make_meta("rule_filter_service"),
        ),
        _make_span(
            "s5", "s4", "ranking", "coarse_rank", "success", 56, 69,
            {"candidates": kept_candidates},
            {"scores": coarse_scores, "topk": ["sku_1007", "sku_1033", "sku_1015"]},
            _make_meta("rank_service", model_name="coarse_rank_v3"),
        ),
        _make_span(
            "s6", "s5", "ranking", "fine_rank", "success", 70, 89,
            {"topk_from_coarse": ["sku_1007", "sku_1033", "sku_1015"]},
            {"scores": fine_scores, "ranked_list": ["sku_1007", "sku_1033", "sku_1015"]},
            _make_meta("rank_service", model_name="fine_rank_v5"),
        ),
        _make_span(
            "s7", "s6", "ranking", "strategy_layer", "success", 90, 98,
            {"ranked_list": ["sku_1007", "sku_1033", "sku_1015"]},
            {"final_items": ["sku_1007", "sku_1033", "sku_1015"]},
            _make_meta("strategy_service", extra={"policy_name": "default_diversity_policy"}),
        ),
    ]

    return {
        "trace_id": f"trace_classic_{case_id:04d}",
        "trace_type": "normal",
        "issue_type": "normal",
        "fault_module": "none",
        "recoverability": "none",
        "template_type": "classic",
        "scene": {"domain": "ecommerce_marketing", "entry": "search", "task": "item_recommendation"},
        "request": {"query": query, "user_profile": user_profile, "context": context},
        "reference": _build_reference(scene_data),
        "ground_truth": gt,
        "trace": trace,
        "final_output": {"items": ["sku_1007", "sku_1033", "sku_1015"], "text": "", "justification_sources": []},
    }


def generate_llm_hybrid_gt(case_id: int, scene: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    scene_data = _merge_scene(_default_llm_scene(), scene)

    query = scene_data["query"]
    user_profile = scene_data["user_profile"]
    context = scene_data["context"]
    category = scene_data["category"]
    constraints = scene_data["constraints"]
    gt = scene_data["ground_truth"]

    semantic_recall = ["sku_2101", "sku_2120", "sku_2133", "sku_2180"]
    behavior_recall = ["sku_2101", "sku_2175"]
    embedding_recall = ["sku_2120", "sku_2133", "sku_2192"]
    merged_candidates = ["sku_2101", "sku_2120", "sku_2133", "sku_2180", "sku_2175", "sku_2192"]
    pre_rank_scores = {
        "sku_2101": 0.90, "sku_2120": 0.87, "sku_2133": 0.84,
        "sku_2180": 0.75, "sku_2175": 0.70, "sku_2192": 0.69,
    }
    top_candidates = ["sku_2101", "sku_2120", "sku_2133", "sku_2180"]
    raw_response = {
        "recommended_items": ["sku_2101", "sku_2120", "sku_2133"],
        "reasons": [
            "sku_2101 适合日常通勤，风格简洁，价格符合预算",
            "sku_2120 更偏基础百搭，适合办公室和通勤穿搭",
            "sku_2133 鞋型利落，适合简约风用户",
        ],
    }

    trace = [
        _make_span(
            "s1", None, "intent", "intent_understanding", "success", 0, 11,
            {"query": query},
            {"category": category, "task_type": "recommend_and_explain", "constraints": copy.deepcopy(constraints)},
            _make_meta("intent_parser", model_name="intent_v1"),
        ),
        _make_span(
            "s2", "s1", "retrieval", "candidate_recall", "success", 12, 35,
            {"constraints": {"category": category, **constraints}},
            {"recall_sources": {"semantic_recall": semantic_recall, "behavior_recall": behavior_recall, "embedding_recall": embedding_recall}},
            _make_meta("recall_service", model_name="hybrid_recall_v2"),
        ),
        _make_span(
            "s3", "s2", "retrieval", "recall_merge", "success", 36, 42,
            {"recall_sources": {"semantic_recall": semantic_recall, "behavior_recall": behavior_recall, "embedding_recall": embedding_recall}},
            {"merged_candidates": merged_candidates},
            _make_meta("merge_service"),
        ),
        _make_span(
            "s4", "s3", "ranking", "candidate_pre_rank", "success", 43, 57,
            {"merged_candidates": merged_candidates},
            {"scores": pre_rank_scores, "top_candidates": top_candidates},
            _make_meta("rank_service", model_name="pre_rank_v1"),
        ),
        _make_span(
            "s5", "s4", "generation", "prompt_builder", "success", 58, 66,
            {
                "query": query,
                "user_profile": {"style_preference": user_profile["style_preference"], "price_preference": user_profile["price_preference"]},
                "top_candidates": top_candidates,
                "business_instruction": "输出3个商品并说明推荐理由，不能超预算",
            },
            {"prompt_summary": "基于用户通勤场景、简约风偏好和预算约束，对候选鞋款进行重排并生成理由。"},
            _make_meta("prompt_builder_service", extra={"template_name": "rec_reason_v1"}),
        ),
        _make_span(
            "s6", "s5", "generation", "llm_api_inference", "success", 67, 128,
            {"prompt_summary": "基于用户通勤场景、简约风偏好和预算约束，对候选鞋款进行重排并生成理由。"},
            {"raw_response": raw_response},
            _make_meta("llm_gateway", model_name="gpt_xxx_api", extra={
                "temperature": 0.2, "prompt_tokens": 214, "completion_tokens": 83,
                "total_tokens": 297, "estimated_cost": 0.0062
            }),
        ),
        _make_span(
            "s7", "s6", "generation", "llm_output_parser", "success", 129, 135,
            {"raw_response": raw_response},
            {
                "parsed_items": ["sku_2101", "sku_2120", "sku_2133"],
                "parsed_text": "推荐 sku_2101、sku_2120 和 sku_2133，它们整体更符合通勤、简约和预算约束。",
            },
            _make_meta("parser_service", extra={"format_name": "structured_rec_output"}),
        ),
        _make_span(
            "s8", "s7", "ranking", "post_filter_rule_check", "success", 136, 143,
            {"parsed_items": ["sku_2101", "sku_2120", "sku_2133"]},
            {"validated_items": ["sku_2101", "sku_2120", "sku_2133"], "rule_check_passed": True},
            _make_meta("rule_checker"),
        ),
    ]

    return {
        "trace_id": f"trace_llmhybrid_{case_id:04d}",
        "trace_type": "normal",
        "issue_type": "normal",
        "fault_module": "none",
        "recoverability": "none",
        "template_type": "llm_hybrid",
        "scene": {"domain": "ecommerce_marketing", "entry": "chat_recommendation", "task": "item_recommendation_with_reason"},
        "request": {"query": query, "user_profile": user_profile, "context": context},
        "reference": _build_reference(scene_data),
        "ground_truth": gt,
        "trace": trace,
        "final_output": {
            "items": ["sku_2101", "sku_2120", "sku_2133"],
            "text": "推荐 sku_2101、sku_2120 和 sku_2133，它们整体更符合通勤、简约和预算约束。",
            "justification_sources": [],
        },
    }


def generate_composite_gt(case_id: int, scene: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    scene_data = _merge_scene(_default_composite_scene(), scene)

    if "context" in scene_data and "city" in scene_data["context"]:
        scene_city = scene_data["context"]["city"]
        scene_data["city"] = scene_city
        scene_data["constraints"]["warehouse"] = scene_city
    elif "city" in scene_data:
        scene_data["constraints"]["warehouse"] = scene_data["city"]
        scene_data["context"]["city"] = scene_data["city"]
    if "festival" in scene_data:
        scene_data["context"]["festival"] = scene_data["festival"]

    query = scene_data["query"]
    user_profile = scene_data["user_profile"]
    context = scene_data["context"]
    constraints = scene_data["constraints"]
    docs = scene_data["docs"]
    gt = scene_data["ground_truth"]

    retrieved_docs = docs
    recalled_items = ["sku_3012", "sku_3031", "sku_3048", "sku_3055"]
    inventory_result = {"sku_3012": 18, "sku_3031": 26, "sku_3048": 0, "sku_3055": 4}
    price_result = {"sku_3012": 169, "sku_3031": 199, "sku_3048": 229, "sku_3055": 149}
    valid_candidates = ["sku_3012", "sku_3031", "sku_3055"]
    removed_candidates = {"sku_3048": "over_budget_and_out_of_stock"}
    rank_scores = {"sku_3012": 0.93, "sku_3031": 0.90, "sku_3055": 0.74}
    prompt_summary = "基于礼物场景知识证据、候选商品结果及库存和价格工具返回结果，输出两款推荐商品及理由。"

    trace = [
        _make_span(
            "s1", None, "intent", "intent_understanding", "success", 0, 10,
            {"query": query},
            {
                "task_type": "gift_recommendation_with_validation",
                "constraints": {
                    "category": "aroma",
                    "recipient": constraints["recipient"],
                    "budget_max": constraints["budget_max"],
                    "style_preference": constraints["style_preference"],
                    "must_check_inventory": constraints["must_check_inventory"],
                    "warehouse": constraints["warehouse"],
                    "count": constraints["count"],
                },
            },
            _make_meta("intent_parser", model_name="intent_v1"),
        ),
        _make_span(
            "s2", "s1", "agent", "enhancement_planning", "success", 11, 20,
            {"intent_result": {"category": "aroma", "budget_max": constraints["budget_max"], "must_check_inventory": constraints["must_check_inventory"], "warehouse": constraints["warehouse"]}},
            {
                "need_knowledge_retrieval": True,
                "need_tool_calls": True,
                "planned_tools": ["inventory_api", "price_api"],
                "planned_knowledge_scope": ["gift_packaging_rules", "aroma_gift_guides"],
            },
            _make_meta("planner_service", extra={"planner_name": "enhancement_planner_v1"}),
        ),
        _make_span(
            "s3", "s2", "retrieval", "knowledge_retrieval", "success", 21, 48,
            {"knowledge_scope": ["gift_packaging_rules", "aroma_gift_guides"], "query_focus": ["女生生日礼物", "香薰", "包装精致"]},
            {"retrieved_docs": retrieved_docs},
            _make_meta("kb_retriever", model_name="kb_dense_retrieval_v1"),
        ),
        _make_span(
            "s4", "s1", "retrieval", "candidate_recall", "success", 21, 39,
            {"category": "aroma", "gift_scene": "birthday", "budget_max": constraints["budget_max"]},
            {"recalled_items": recalled_items},
            _make_meta("recall_service", model_name="gift_recall_v1"),
        ),
        _make_span(
            "s5", "s2", "agent", "tool_call_inventory", "success", 49, 78,
            {"tool_name": "inventory_api", "warehouse": constraints["warehouse"], "item_ids": recalled_items},
            {"inventory_result": inventory_result},
            _make_meta("tool_gateway", extra={"tool_name": "inventory_api"}),
        ),
        _make_span(
            "s6", "s2", "agent", "tool_call_price", "success", 79, 96,
            {"tool_name": "price_api", "item_ids": recalled_items},
            {"price_result": price_result},
            _make_meta("tool_gateway", extra={"tool_name": "price_api"}),
        ),
        _make_span(
            "s7", "s3", "agent", "evidence_observation_aggregation", "success", 97, 109,
            {
                "retrieved_docs": [d["doc_id"] for d in retrieved_docs],
                "inventory_result": inventory_result,
                "price_result": price_result,
                "recalled_items": recalled_items,
            },
            {
                "valid_candidates": valid_candidates,
                "removed_candidates": removed_candidates,
                "selected_evidence_docs": ["doc_gift_packaging_01", "doc_aroma_gift_guide_02"],
            },
            _make_meta("aggregation_service"),
        ),
        _make_span(
            "s8", "s7", "ranking", "rank_with_evidence_and_tools", "success", 110, 128,
            {"valid_candidates": valid_candidates, "selected_evidence_docs": ["doc_gift_packaging_01", "doc_aroma_gift_guide_02"]},
            {"scores": rank_scores, "top_items": ["sku_3012", "sku_3031"]},
            _make_meta("rank_service", model_name="evidence_tool_rank_v1"),
        ),
        _make_span(
            "s9", "s8", "generation", "prompt_builder", "success", 129, 138,
            {
                "query": query,
                "top_items": ["sku_3012", "sku_3031"],
                "selected_evidence_docs": ["doc_gift_packaging_01", "doc_aroma_gift_guide_02"],
                "tool_observations": {"inventory_result": {"sku_3012": 18, "sku_3031": 26}, "price_result": {"sku_3012": 169, "sku_3031": 199}},
            },
            {"prompt_summary": prompt_summary},
            _make_meta("prompt_builder_service", extra={"template_name": "rag_agent_rec_v1"}),
        ),
        _make_span(
            "s10", "s9", "generation", "llm_final_recommendation", "success", 139, 188,
            {"prompt_summary": prompt_summary},
            {
                "recommended_items": ["sku_3012", "sku_3031"],
                "generated_reason": "推荐 sku_3012 和 sku_3031。这两款都在200元预算内，广州仓当前有货，同时更符合生日礼物场景下对包装完整度和礼赠属性的要求。",
            },
            _make_meta("llm_gateway", model_name="gpt_xxx_api", extra={
                "temperature": 0.2, "prompt_tokens": 268, "completion_tokens": 91,
                "total_tokens": 359, "estimated_cost": 0.0074
            }),
        ),
    ]

    return {
        "trace_id": f"trace_composite_{case_id:04d}",
        "trace_type": "normal",
        "issue_type": "normal",
        "fault_module": "none",
        "recoverability": "none",
        "template_type": "composite_enhanced",
        "scene": {"domain": "ecommerce_marketing", "entry": "chat_recommendation", "task": "knowledge_and_tool_augmented_recommendation"},
        "request": {"query": query, "user_profile": user_profile, "context": context},
        "reference": _build_reference(scene_data),
        "ground_truth": gt,
        "trace": trace,
        "final_output": {
            "items": ["sku_3012", "sku_3031"],
            "text": "推荐 sku_3012 和 sku_3031。这两款都在200元预算内，广州仓当前有货，同时更符合生日礼物场景下对包装完整度和礼赠属性的要求。",
            "justification_sources": ["doc_gift_packaging_01", "doc_aroma_gift_guide_02", "inventory_api", "price_api"],
        },
    }
