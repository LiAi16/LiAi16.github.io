from pathlib import Path
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generate_plots(outputs: Dict[str, Any], output_dir: Path) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_map = {}

    end_rows = outputs["end_to_end_table"]
    module_rows = outputs["module_response_table"]
    attr_summary = outputs["attribution_summary"][0] if outputs["attribution_summary"] else {}
    per_trace = outputs["per_trace"]

    # Chart 1: end-to-end ndcg by issue type
    plt.figure(figsize=(11, 6))
    issue_labels = [row["issue_type"] for row in end_rows]
    ndcg_values = [row["ndcg_at_k"] for row in end_rows]
    plt.bar(issue_labels, ndcg_values)
    plt.xticks(rotation=30, ha="right")
    plt.ylabel("Mean nDCG@K")
    plt.title("End-to-end performance by issue type")
    plt.tight_layout()
    path = output_dir / "chart_end_to_end.png"
    plt.savefig(path, dpi=180)
    plt.close()
    file_map["chart_end_to_end.png"] = str(path)

    # Chart 2: module score heatmap-like matrix
    plt.figure(figsize=(10, 5))
    score_keys = ["intent_score", "recall_score", "evidence_score", "ranking_score", "agent_score"]
    row_labels = [row["issue_type"] for row in module_rows]
    matrix = [[row[key] for key in score_keys] for row in module_rows]
    if not matrix:
        matrix = [[0 for _ in score_keys]]
        row_labels = ["no_data"]
    plt.imshow(matrix, aspect="auto")
    plt.colorbar(label="Score")
    plt.xticks(range(len(score_keys)), score_keys, rotation=30, ha="right")
    plt.yticks(range(len(row_labels)), row_labels)
    plt.title("Module response heatmap")
    plt.tight_layout()
    path = output_dir / "chart_module_heatmap.png"
    plt.savefig(path, dpi=180)
    plt.close()
    file_map["chart_module_heatmap.png"] = str(path)

    # Chart 3: attribution summary
    plt.figure(figsize=(8, 5))
    labels = ["Attribution accuracy", "Primary fault rate", "Cascade detection"]
    values = [
        attr_summary.get("attribution_accuracy", 0.0),
        attr_summary.get("primary_fault_identification_rate", 0.0),
        attr_summary.get("cascade_detection_rate", 0.0),
    ]
    plt.bar(labels, values)
    plt.ylim(0, 1.05)
    plt.ylabel("Rate")
    plt.title("Attribution performance")
    plt.tight_layout()
    path = output_dir / "chart_attribution.png"
    plt.savefig(path, dpi=180)
    plt.close()
    file_map["chart_attribution.png"] = str(path)

    # Chart 4: system latency / cost
    system_rows = [row for row in per_trace if row["issue_type"] in {"normal", "system_abnormal"}]
    grouped = {}
    for row in system_rows:
        key = f'{row["template_type"]}-{row["issue_type"]}'
        grouped.setdefault(key, {"latency": [], "cost": []})
        grouped[key]["latency"].append(row["system_latency_ms"])
        grouped[key]["cost"].append(row["llm_estimated_cost"])

    labels = list(grouped.keys())
    latency_vals = [sum(v["latency"]) / len(v["latency"]) for v in grouped.values()]
    cost_vals = [sum(v["cost"]) / len(v["cost"]) for v in grouped.values()]

    plt.figure(figsize=(12, 6))
    x = list(range(len(labels)))
    plt.bar(x, latency_vals)
    plt.xticks(x, labels, rotation=30, ha="right")
    plt.ylabel("Latency (ms)")
    plt.title("System latency under normal vs system abnormal traces")
    plt.tight_layout()
    path = output_dir / "chart_system_latency.png"
    plt.savefig(path, dpi=180)
    plt.close()
    file_map["chart_system_latency.png"] = str(path)

    plt.figure(figsize=(12, 6))
    plt.bar(x, cost_vals)
    plt.xticks(x, labels, rotation=30, ha="right")
    plt.ylabel("Estimated cost")
    plt.title("Estimated LLM cost under normal vs system abnormal traces")
    plt.tight_layout()
    path = output_dir / "chart_system_cost.png"
    plt.savefig(path, dpi=180)
    plt.close()
    file_map["chart_system_cost.png"] = str(path)

    return file_map
