import json
from pathlib import Path
from typing import Any, Dict

from .generator import save_benchmark, load_jsonl
from .metrics import compute_all_metrics, save_metrics
from .plots import generate_plots


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def generated_dir() -> Path:
    return project_root() / "generated"


def run_all_experiments(repeats_per_scene: int = 4) -> Dict[str, Any]:
    out_dir = generated_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    benchmark_meta = save_benchmark(out_dir, repeats_per_scene=repeats_per_scene)
    traces = load_jsonl(out_dir / "benchmark_main_v1.jsonl")
    metric_outputs = compute_all_metrics(traces)
    metric_files = save_metrics(metric_outputs, out_dir)
    plot_files = generate_plots(metric_outputs, out_dir)

    run_meta = {
        "benchmark": benchmark_meta,
        "metric_files": metric_files,
        "plot_files": plot_files,
        "summary": metric_outputs["summary"],
    }

    run_meta_path = out_dir / "run_meta.json"
    run_meta_path.write_text(json.dumps(run_meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return run_meta


def ensure_outputs() -> Dict[str, Any]:
    out_dir = generated_dir()
    summary_path = out_dir / "summary.json"
    if not summary_path.exists():
        return run_all_experiments()
    run_meta_path = out_dir / "run_meta.json"
    if run_meta_path.exists():
        return json.loads(run_meta_path.read_text(encoding="utf-8"))
    return run_all_experiments()


def load_table_csv(name: str):
    import csv
    path = generated_dir() / name
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_summary():
    path = generated_dir() / "summary.json"
    if not path.exists():
        ensure_outputs()
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest():
    path = generated_dir() / "benchmark_main_v1_manifest.csv"
    if not path.exists():
        ensure_outputs()
    import csv
    with path.open("r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_traces():
    path = generated_dir() / "benchmark_main_v1.jsonl"
    if not path.exists():
        ensure_outputs()
    return load_jsonl(path)
