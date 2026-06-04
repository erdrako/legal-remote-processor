from __future__ import annotations

from typing import Any


def validate_job_result(payload: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    status = payload.get("status")
    if status not in {"COMPLETED", "NEEDS_REVIEW", "NOT_COMPARABLE"}:
        warnings.append(f"Invalid terminal status: {status}")

    artifacts = payload.get("artifacts") or []
    if not artifacts:
        warnings.append("Result has no artifacts.")

    for artifact in artifacts:
        source_url = artifact.get("sourceUrl")
        if source_url and not str(source_url).startswith(("http://", "https://")):
            warnings.append(f"Artifact has non-official URL shape: {source_url}")

    return warnings
