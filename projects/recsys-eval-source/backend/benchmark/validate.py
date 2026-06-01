from typing import Any, Dict, List


def validate_trace(trace: Dict[str, Any]) -> List[str]:
    errors = []

    if trace.get("trace_type") not in {"normal", "faulty"}:
        errors.append("invalid trace_type")

    if trace.get("trace_type") == "faulty":
        for k in ["issue_type", "fault_module", "recoverability"]:
            if k not in trace:
                errors.append(f"missing faulty label: {k}")

    seen = set()
    for span in trace.get("trace", []):
        sid = span.get("span_id")
        if sid in seen:
            errors.append(f"duplicate span_id: {sid}")
        seen.add(sid)

        parent_sid = span.get("parent_span_id")
        if parent_sid is not None and parent_sid not in seen and parent_sid not in {s.get("span_id") for s in trace.get("trace", [])}:
            errors.append(f"missing parent span_id reference in {sid}: {parent_sid}")

        start_ms = span.get("start_ms")
        end_ms = span.get("end_ms")
        latency_ms = span.get("latency_ms")
        if start_ms is None or end_ms is None or latency_ms is None:
            errors.append(f"missing timing fields in {sid}")
        elif latency_ms != end_ms - start_ms:
            errors.append(f"latency mismatch in {sid}")

    return errors
