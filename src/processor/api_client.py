from __future__ import annotations

import time
from typing import Any

import requests

from .config import ProcessorConfig


class LexMapaApiClient:
    def __init__(self, config: ProcessorConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"user-agent": f"lexmapa-remote-processor/{config.version}"})

    def queue_status(self, limit: int = 25) -> dict[str, Any]:
        return self._request("GET", f"/processing-queue?limit={limit}")

    def enroll(self, enrollment_token: str) -> dict[str, Any]:
        payload = {
            "displayName": self.config.processor_name,
            "tier": self.config.tier,
            "capabilities": self.config.capabilities,
            "modelName": self.config.ollama_model or "deterministic-no-ollama",
            "processorVersion": self.config.version,
        }
        return self._request("POST", "/processors/enroll", json=payload, token=enrollment_token)

    def heartbeat(self, current_job_id: str | None = None, status: str = "ONLINE") -> dict[str, Any]:
        payload = {
            "status": status,
            "currentJobId": current_job_id,
            "tier": self.config.tier,
            "capabilities": self.config.capabilities,
            "modelName": self.config.ollama_model or "deterministic-no-ollama",
            "processorVersion": self.config.version,
        }
        return self._request("POST", "/processors/heartbeat", json=payload, processor_auth=True)

    def claim_job(self) -> dict[str, Any]:
        payload = {
            "capabilities": self.config.capabilities,
            "maxLeaseSeconds": self.config.max_lease_seconds,
        }
        return self._request("POST", "/processors/jobs/claim", json=payload, processor_auth=True)

    def progress(self, job_id: str, message: str, progress: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/processors/jobs/{job_id}/progress",
            json={"message": message, "progress": progress},
            processor_auth=True,
        )

    def submit_result(self, job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/processors/jobs/{job_id}/result", json=payload, processor_auth=True)

    def fail_job(self, job_id: str, message: str, error: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/processors/jobs/{job_id}/fail",
            json={"message": message, "error": error},
            processor_auth=True,
        )

    def release_job(self, job_id: str) -> dict[str, Any]:
        return self._request("POST", f"/processors/jobs/{job_id}/release", json={}, processor_auth=True)

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        token: str | None = None,
        processor_auth: bool = False,
    ) -> dict[str, Any]:
        headers = {}
        if token:
            headers["authorization"] = f"Bearer {token}"
        if processor_auth:
            headers["authorization"] = f"Bearer {self.config.processor_secret}"
            headers["x-processor-id"] = self.config.processor_id

        response = self.session.request(
            method,
            f"{self.config.api_base_url}{path}",
            json=json,
            headers=headers,
            timeout=60,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"LexMapa API {method} {path} failed: {response.status_code} {response.text[:500]}")
        return response.json() if response.content else {}

    @staticmethod
    def sleep(seconds: int) -> None:
        time.sleep(seconds)
