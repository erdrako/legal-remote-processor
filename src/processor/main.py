from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .config import ProcessorConfig, load_dotenv
from .preflight import run_preflight


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lexmapa-remote-processor")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("preflight")
    subparsers.add_parser("doctor")
    subparsers.add_parser("status")

    enroll_parser = subparsers.add_parser("enroll")
    enroll_parser.add_argument("--enrollment-token", required=True)

    once_parser = subparsers.add_parser("once")
    once_parser.add_argument("--release-on-empty", action="store_true")

    drain_parser = subparsers.add_parser("drain")
    drain_parser.add_argument("--max-jobs", type=int, default=0)

    subparsers.add_parser("worker")

    args = parser.parse_args(argv)
    load_dotenv()

    if args.command == "preflight":
        return print_preflight()
    if args.command == "doctor":
        return print_doctor()

    config = ProcessorConfig.from_env()
    from .api_client import LexMapaApiClient

    client = LexMapaApiClient(config)

    if args.command == "status":
        print_json(client.queue_status())
        return 0

    if args.command == "enroll":
        response = client.enroll(args.enrollment_token)
        safe_response = {
            "processor": response.get("processor"),
            "processorSecretReceived": bool(response.get("processorSecret")),
        }
        print_json(safe_response)
        return 0

    config.require_enrolled()

    if args.command == "once":
        return run_once(client, config)

    if args.command == "drain":
        return run_drain(client, config, max_jobs=args.max_jobs)

    if args.command == "worker":
        while True:
            result = run_once(client, config)
            if result != 0:
                return result
            client.sleep(config.poll_interval_seconds)

    return 1


def run_once(client: LexMapaApiClient, config: ProcessorConfig) -> int:
    run_once_status(client, config)
    return 0


def run_drain(client: LexMapaApiClient, config: ProcessorConfig, max_jobs: int = 0) -> int:
    processed_jobs = 0

    while True:
        status = run_once_status(client, config)
        if status == "IDLE":
            print_json(
                {
                    "status": "DRAINED",
                    "message": "No pending jobs. Processor will stop.",
                    "processedJobCount": processed_jobs,
                }
            )
            return 0

        processed_jobs += 1
        if max_jobs > 0 and processed_jobs >= max_jobs:
            print_json(
                {
                    "status": "DRAIN_LIMIT_REACHED",
                    "message": "Configured max job count reached.",
                    "processedJobCount": processed_jobs,
                }
            )
            return 0


def run_once_status(client: LexMapaApiClient, config: ProcessorConfig) -> str:
    from .jobs import process_job

    client.heartbeat()
    claim = client.claim_job()
    job = claim.get("job")
    if not job:
        print_json({"status": "IDLE", "message": "No pending jobs."})
        return "IDLE"

    job_id = job["id"]
    try:
        client.progress(job_id, "Job recibido por procesador remoto.", {"step": "CLAIMED"})
        result = process_job(job, config)
        client.progress(job_id, "Resultado generado localmente.", {"step": "RESULT_READY", "status": result["status"]})
        response = client.submit_result(job_id, result)
        client.heartbeat()
        print_json(
            {
                "status": "SUBMITTED",
                "jobId": job_id,
                "terminalStatus": result["status"],
                "artifactCount": len(result.get("artifacts", [])),
                "warningCount": len(result.get("warnings", [])),
                "apiJobStatus": response.get("job", {}).get("status"),
            }
        )
        return "SUBMITTED"
    except Exception as error:
        client.fail_job(
            job_id,
            "Processor failed while handling job.",
            {"type": error.__class__.__name__, "message": str(error)},
        )
        raise


def print_preflight() -> int:
    result = run_preflight(Path("."))
    print_json(result.__dict__)
    return 0 if result.can_install else 2


def print_doctor() -> int:
    config = ProcessorConfig.from_env()
    preflight = run_preflight(Path("."))
    report: dict[str, Any] = {
        "preflight": preflight.__dict__,
        "apiBaseUrl": config.api_base_url,
        "processorConfigured": bool(config.processor_id and config.processor_secret),
        "processorId": config.processor_id or None,
        "capabilities": config.capabilities,
        "ollamaEnabled": config.enable_ollama,
        "ollamaModel": config.ollama_model or None,
    }
    print_json(report)
    return 0 if preflight.can_install else 2


def print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
