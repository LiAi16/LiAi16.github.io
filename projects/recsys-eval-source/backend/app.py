
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from flask import Flask, jsonify, request, send_from_directory

from backend.benchmark.experiment_runner import ensure_outputs, project_root
from backend.task_service import (
    create_demo_task_if_needed,
    list_tasks,
    create_task,
    get_task,
    save_mode,
    upload_files,
    validate_task_uploads,
    parse_task_chain,
    confirm_structure,
    save_config,
    run_task_evaluation,
    default_config,
)

ROOT = project_root()
FRONTEND_DIR = ROOT / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")


def _ok(data=None, message="ok"):
    return jsonify({"message": message, "data": data})


def _error(message: str, status_code: int = 400):
    return jsonify({"error": message}), status_code


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/default-config")
def api_default_config():
    return _ok(default_config())


@app.route("/api/tasks", methods=["GET", "POST"])
def api_tasks():
    if request.method == "GET":
        return _ok(list_tasks())

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return _error("请输入任务名称")
    return _ok(create_task(name), "task created")


@app.route("/api/tasks/<task_id>", methods=["GET"])
def api_task_detail(task_id: str):
    task = get_task(task_id)
    if not task:
        return _error("任务不存在", 404)
    return _ok(task)


@app.route("/api/tasks/<task_id>/mode", methods=["PUT"])
def api_task_mode(task_id: str):
    payload = request.get_json(silent=True) or {}
    mode = payload.get("mode", "single")
    if mode not in {"single", "compare"}:
        return _error("评测模式不合法")
    try:
        return _ok(save_mode(task_id, mode), "mode saved")
    except KeyError:
        return _error("任务不存在", 404)


@app.route("/api/tasks/<task_id>/upload", methods=["POST"])
def api_task_upload(task_id: str):
    if "primary" not in request.files and "secondary" not in request.files:
        return _error("请至少上传一份 Trace 日志")
    files = {}
    for key in ["primary", "secondary"]:
        file = request.files.get(key)
        if file and file.filename:
            files[key] = (file.filename, file.read())
    try:
        task = upload_files(task_id, files)
        return _ok(task, "upload success")
    except KeyError:
        return _error("任务不存在", 404)
    except Exception as e:
        return _error(str(e))


@app.route("/api/tasks/<task_id>/validate", methods=["POST"])
def api_task_validate(task_id: str):
    try:
        return _ok(validate_task_uploads(task_id), "validated")
    except KeyError:
        return _error("任务不存在", 404)
    except Exception as e:
        return _error(str(e))


@app.route("/api/tasks/<task_id>/parse", methods=["POST"])
def api_task_parse(task_id: str):
    try:
        return _ok(parse_task_chain(task_id), "parsed")
    except KeyError:
        return _error("任务不存在", 404)
    except Exception as e:
        return _error(str(e))


@app.route("/api/tasks/<task_id>/confirm-structure", methods=["POST"])
def api_confirm_structure(task_id: str):
    payload = request.get_json(silent=True) or {}
    confirmed = bool(payload.get("confirmed", True))
    try:
        return _ok(confirm_structure(task_id, confirmed), "structure confirmed")
    except KeyError:
        return _error("任务不存在", 404)
    except Exception as e:
        return _error(str(e))


@app.route("/api/tasks/<task_id>/config", methods=["PUT"])
def api_task_config(task_id: str):
    payload = request.get_json(silent=True) or {}
    config = payload.get("config")
    if not isinstance(config, dict):
        return _error("配置格式不正确")
    try:
        return _ok(save_config(task_id, config), "config saved")
    except KeyError:
        return _error("任务不存在", 404)


@app.route("/api/tasks/<task_id>/run", methods=["POST"])
def api_task_run(task_id: str):
    try:
        return _ok(run_task_evaluation(task_id), "evaluation completed")
    except KeyError:
        return _error("任务不存在", 404)
    except Exception as e:
        return _error(str(e))


@app.route("/api/tasks/<task_id>/results", methods=["GET"])
def api_task_results(task_id: str):
    task = get_task(task_id)
    if not task:
        return _error("任务不存在", 404)
    if not task.get("results"):
        return _error("该任务尚未完成评测", 400)
    return _ok(task["results"])


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def static_proxy(path: str):
    full_path = FRONTEND_DIR / path
    if full_path.exists():
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")


if __name__ == "__main__":
    ensure_outputs()
    create_demo_task_if_needed()
    app.run(host="0.0.0.0", port=8000, debug=False)
