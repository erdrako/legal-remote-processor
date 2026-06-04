from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from .config import ProcessorConfig
from .extractors.pdf import download_and_extract_pdf
from .legal_parser.operations import classify_operations
from .legal_parser.provisions import segment_provisions
from .legal_parser.references import detect_references
from .validators.result import validate_job_result


def process_job(job: dict[str, Any], config: ProcessorConfig) -> dict[str, Any]:
    job_type = job.get("jobType")
    if job_type == "RESOLVE_DIFF_FALLBACK":
        return process_resolve_diff_fallback(job, config)
    if job_type != "GENERATE_DIFF_CANDIDATES":
        return not_comparable_result(job, f"Unsupported job type: {job_type}")

    return process_generate_diff_candidates(job, config)


def process_resolve_diff_fallback(job: dict[str, Any], config: ProcessorConfig) -> dict[str, Any]:
    job_input = job.get("input", {})
    candidate = job_input.get("candidate", {})
    resolution = job_input.get("resolution", {})
    ai_suggestion = suggest_with_ollama(job_input, config) if config.enable_ollama and config.ollama_model else {}
    fallback = build_fallback_resolution(candidate, resolution, ai_suggestion)
    warnings = [
        "REMOTE_DIFF_FALLBACK_USED: el candidato no pudo cerrarse solo con el primer pase deterministico.",
        *fallback.get("validationWarnings", []),
    ]
    if not ai_suggestion:
        warnings.append("OLLAMA_NOT_USED: fallback remoto ejecutado en modo deterministico conservador.")

    return {
        "status": "NEEDS_REVIEW",
        "result": {"fallbackDiffResolutions": [fallback]},
        "artifacts": [
            {
                "artifactType": "VALIDATION_REPORT",
                "content": {
                    "jobId": job.get("id"),
                    "candidateId": fallback.get("candidateId"),
                    "remoteAssisted": bool(ai_suggestion),
                    "suggestion": fallback,
                },
            }
        ],
        "warnings": warnings,
        "confidence": {
            "ocr": 0,
            "referenceResolution": 0.4,
            "operationClassification": 0.4,
            "diffGeneration": 0.3 if ai_suggestion else 0.2,
        },
    }


def build_fallback_resolution(
    candidate: dict[str, Any],
    resolution: dict[str, Any],
    ai_suggestion: dict[str, Any],
) -> dict[str, Any]:
    current_version = resolution.get("currentVersion") or {}
    proposed_version = resolution.get("proposedVersion") or {}
    operation_type = (
        ai_suggestion.get("operationType")
        or resolution.get("operationType")
        or candidate.get("operationType")
        or "UNKNOWN_OPERATION"
    )
    target_label = (
        ai_suggestion.get("targetLabel")
        or resolution.get("targetLabel")
        or extract_article_label(candidate.get("evidenceText", ""))
    )
    validation_warnings = list(dict.fromkeys([
        *(resolution.get("validationWarnings") or []),
        *(candidate.get("validationWarnings") or []),
        *(ai_suggestion.get("validationWarnings") or []),
    ]))

    return {
        "candidateId": candidate.get("id"),
        "title": ai_suggestion.get("title") or resolution.get("title") or candidate.get("title"),
        "operationType": operation_type,
        "changeType": ai_suggestion.get("changeType") or resolution.get("changeType") or candidate.get("changeType"),
        "targetLabel": target_label,
        "currentText": ai_suggestion.get("currentText") or current_version.get("text"),
        "proposedText": ai_suggestion.get("proposedText") or proposed_version.get("text"),
        "explanationPlainLanguage": ai_suggestion.get("explanationPlainLanguage")
        or resolution.get("explanationPlainLanguage")
        or "El procesador remoto genero una sugerencia de comparacion pendiente de validacion deterministica.",
        "practicalImpact": ai_suggestion.get("practicalImpact")
        or resolution.get("practicalImpact")
        or "Usar como comparacion asistida, revisando fuentes y advertencias.",
        "confidence": ai_suggestion.get("confidence") or "LOW",
        "validationWarnings": validation_warnings,
        "remoteAssisted": True,
    }


def suggest_with_ollama(job_input: dict[str, Any], config: ProcessorConfig) -> dict[str, Any]:
    import requests

    prompt = {
        "task": "Sugerir un diff legal estructurado. No inventar fuentes. Responder solo JSON.",
        "input": job_input,
        "schema": {
            "operationType": "string",
            "changeType": "ADDED|REMOVED|MODIFIED",
            "targetLabel": "string|null",
            "currentText": "string|null",
            "proposedText": "string|null",
            "explanationPlainLanguage": "string",
            "practicalImpact": "string",
            "confidence": "LOW|MEDIUM|HIGH",
            "validationWarnings": ["string"],
        },
    }
    try:
        response = requests.post(
            f"{config.ollama_base_url}/api/generate",
            json={
                "model": config.ollama_model,
                "prompt": json.dumps(prompt, ensure_ascii=False),
                "stream": False,
                "format": "json",
            },
            timeout=90,
        )
        response.raise_for_status()
        raw = response.json().get("response", "{}")
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def extract_article_label(text: str) -> str | None:
    match = re.search(r"\bart[íi]culo\s+(\d+[°º]?(?:\s*(?:bis|ter|quater))?)", str(text), re.IGNORECASE)
    if not match:
        return None
    return f"Articulo {match.group(1).replace('°', '').replace('º', '').strip()}"


def process_generate_diff_candidates(job: dict[str, Any], config: ProcessorConfig) -> dict[str, Any]:
    source_url = job.get("sourceUrl") or find_source_url(job.get("input", {}))
    job_id = job["id"]
    retrieved_at = now_iso()
    pdf = download_and_extract_pdf(source_url, config.data_dir, job_id)
    warnings: list[str] = []

    if pdf.ocr_used:
        warnings.append("OCR_USED: el PDF no tenia texto embebido suficiente y se uso OCR local.")
    if len(pdf.text) < 200 and not pdf.ocr_available:
        warnings.append("OCR_REQUIRED: el texto extraido es bajo y Tesseract no esta disponible en esta imagen.")
    elif len(pdf.text) < 200:
        warnings.append("PDF_TEXT_TOO_SHORT: el texto extraido sigue siendo bajo aun con OCR disponible.")

    provisions = segment_provisions(pdf.text)
    references = detect_references(pdf.text)
    operations = classify_operations(provisions, references)
    affected_items = build_affected_items(job, references, operations, retrieved_at)
    affected_item_ids = {item["legalItemId"]: item["id"] for item in affected_items if item.get("legalItemId")}
    diff_candidates = build_diff_candidates(job, provisions, operations, affected_item_ids, source_url, retrieved_at)
    result_status = "NEEDS_REVIEW"
    warnings.append("CURRENT_TEXT_PENDING: falta resolver texto vigente para comparar articulo por articulo.")

    payload = {
        "status": result_status,
        "result": {
            "affectedLegalItems": affected_items,
            "extractedProvisions": [
                {
                    "id": provision_id(job_id, provision.id),
                    "proposalId": proposal_id(job),
                    "legalItemId": None,
                    "provisionLabel": provision.label,
                    "provisionType": provision.provision_type,
                    "provisionOrder": provision.order,
                    "textOriginal": provision.text,
                    "sourceUrl": source_url,
                    "contentHash": pdf.content_hash,
                }
                for provision in provisions
            ],
            "changeOperations": [
                {
                    "id": operation_id(job_id, operation.id),
                    "proposalId": proposal_id(job),
                    "affectedLegalItemId": affected_item_ids.get(operation.target_reference_id)
                    or (affected_items[0]["id"] if affected_items else None),
                    "operationType": operation.operation_type,
                    "detectedVerb": operation.detected_verb,
                    "sourceProvisionId": provision_id(job_id, operation.source_provision_id),
                    "targetLegalItemId": operation.target_reference_id,
                    "targetProvisionId": None,
                    "evidenceText": operation.evidence_text,
                    "confidence": operation.confidence,
                    "reviewStatus": "AUTO_EXTRACTED",
                }
                for operation in operations
            ],
            "diffCandidates": diff_candidates,
        },
        "artifacts": [
            {
                "artifactType": "NORMALIZED_TEXT",
                "content": {
                    "sourceUrl": source_url,
                    "contentHash": pdf.content_hash,
                    "byteCount": pdf.byte_count,
                    "pageCount": pdf.page_count,
                    "charCount": len(pdf.text),
                    "ocrUsed": pdf.ocr_used,
                    "ocrAvailable": pdf.ocr_available,
                    "textPreview": pdf.text[:20000],
                    "truncated": len(pdf.text) > 20000,
                },
                "contentHash": pdf.content_hash,
                "sourceUrl": source_url,
            },
            {
                "artifactType": "PROVISIONS",
                "content": {
                    "count": len(provisions),
                    "items": [
                        {
                            "id": provision.id,
                            "label": provision.label,
                            "order": provision.order,
                            "textPreview": provision.text[:1200],
                        }
                        for provision in provisions[:50]
                    ],
                },
                "contentHash": pdf.content_hash,
                "sourceUrl": source_url,
            },
            {
                "artifactType": "REFERENCES",
                "content": {
                    "count": len(references),
                    "items": [reference.__dict__ for reference in references[:100]],
                },
                "contentHash": pdf.content_hash,
                "sourceUrl": source_url,
            },
            {
                "artifactType": "OPERATIONS",
                "content": {
                    "count": len(operations),
                    "items": [operation.__dict__ for operation in operations],
                },
                "contentHash": pdf.content_hash,
                "sourceUrl": source_url,
            },
            {
                "artifactType": "DIFF_CANDIDATES",
                "content": {
                    "count": len(diff_candidates),
                    "items": diff_candidates,
                },
                "contentHash": pdf.content_hash,
                "sourceUrl": source_url,
            },
        ],
        "warnings": warnings,
        "confidence": {
            "ocr": 0 if warnings and warnings[0].startswith("PDF_TEXT_TOO_SHORT") else 1,
            "referenceResolution": 0.5 if references else 0.1,
            "operationClassification": 0.5 if operations else 0.1,
            "diffGeneration": 0.2,
        },
    }

    validation_warnings = validate_job_result(payload)
    payload["warnings"].extend(validation_warnings)
    return payload


def build_affected_items(
    job: dict[str, Any],
    references: list[Any],
    operations: list[Any],
    retrieved_at: str,
) -> list[dict[str, Any]]:
    law_refs = [reference for reference in references if reference.kind == "LAW"]
    selected = law_refs[:50] or references[:10]
    default_operation = operations[0].operation_type if operations else "NEEDS_REVIEW"
    operation_by_reference_id = {
        operation.target_reference_id: operation
        for operation in operations
        if operation.target_reference_id
    }

    items: list[dict[str, Any]] = []
    for reference in selected:
        operation = operation_by_reference_id.get(reference.id)
        operation_type = operation.operation_type if operation else default_operation
        evidence_text = operation.evidence_text if operation else reference.reference_text
        detected_verb = operation.detected_verb if operation else ""
        source_provision_id = provision_id(job["id"], operation.source_provision_id) if operation else None
        confidence = operation.confidence if operation else "LOW"
        review_reason = "Fuente vigente pendiente y matching articulo por articulo no validado."
        items.append(
            {
                "id": affected_item_id(job["id"], reference.id),
                "proposalId": proposal_id(job),
                "legalItemId": reference.id,
                "title": reference.label,
                "legalItemType": "LAW" if reference.kind == "LAW" else None,
                "referenceText": reference.reference_text,
                "canonicalReferenceText": reference.canonical_label,
                "operationType": operation_type,
                "currentSource": {
                    "status": "PENDING",
                    "lawNumber": reference.normalized_number,
                    "label": "Texto vigente original",
                    "retrievedAt": retrieved_at,
                    "official": True,
                    "note": "El procesador detecto la norma afectada, pero falta resolver el texto vigente oficial.",
                },
                "sourceStatus": "PENDING",
                "affectedProvisionIds": [],
                "detectionEvidence": {
                    "referenceText": reference.reference_text,
                    "canonicalReferenceText": reference.canonical_label,
                    "evidenceText": evidence_text,
                    "detectedVerb": detected_verb,
                    "sourceProvisionId": source_provision_id,
                    "confidence": confidence,
                    "requiresReview": True,
                    "reviewReason": review_reason,
                },
                "reviewReason": review_reason,
                "notes": "Referencia candidata detectada automaticamente desde texto propuesto.",
            }
        )

    return items


def build_diff_candidates(
    job: dict[str, Any],
    provisions: list[Any],
    operations: list[Any],
    affected_item_ids: dict[str, str],
    source_url: str,
    retrieved_at: str,
) -> list[dict[str, Any]]:
    provision_by_id = {provision.id: provision for provision in provisions}
    candidates: list[dict[str, Any]] = []

    for index, operation in enumerate(operations[:12], start=1):
        provision = provision_by_id.get(operation.source_provision_id) or provisions[0]
        candidates.append(
            {
                "id": f"{job['id']}-diff-candidate-{index}",
                "proposalId": proposal_id(job),
                "operationId": operation_id(job["id"], operation.id),
                "affectedLegalItemId": affected_item_ids.get(operation.target_reference_id)
                if operation.target_reference_id
                else None,
                "title": f"Candidato {index}: {operation.operation_type.replace('_', ' ').title()}",
                "changeType": operation.change_type,
                "currentVersion": None,
                "proposedVersion": {
                    "id": f"{job['id']}-proposed-{provision.id}",
                    "label": "Texto propuesto",
                    "legalItemTitle": job.get("sourceLabel") or "Proyecto Senado",
                    "provisionId": provision_id(job["id"], provision.id),
                    "provisionLabel": provision.label,
                    "text": provision.text,
                    "status": "PROPUESTO",
                    "source": {
                        "id": "senado-proposed-text",
                        "name": "Senado de la Nacion Argentina",
                        "sourceUrl": source_url,
                        "retrievedAt": retrieved_at,
                        "official": True,
                    },
                    "sourceStatus": "LOADED",
                    "originalSource": {
                        "status": "LOADED",
                        "label": "Texto propuesto original",
                        "name": "Senado de la Nacion Argentina",
                        "sourceUrl": source_url,
                        "retrievedAt": retrieved_at,
                        "official": True,
                    },
                },
                "explanationPlainLanguage": "El procesador detecto una operacion legal candidata en el texto propuesto.",
                "practicalImpact": "Requiere resolver el texto vigente y revision legal antes de publicarse como comparacion.",
                "confidence": operation.confidence,
                "reviewStatus": "NEEDS_REVIEW",
                "validationWarnings": ["CURRENT_VERSION_PENDING"],
            }
        )

    return candidates


def not_comparable_result(job: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "status": "NOT_COMPARABLE",
        "result": {},
        "artifacts": [
            {
                "artifactType": "VALIDATION_REPORT",
                "content": {"jobId": job.get("id"), "reason": reason},
            }
        ],
        "warnings": [reason],
        "confidence": {
            "ocr": 0,
            "referenceResolution": 0,
            "operationClassification": 0,
            "diffGeneration": 0,
        },
    }


def find_source_url(job_input: dict[str, Any]) -> str:
    for source in job_input.get("documentSources", []):
        if source.get("role") == "PROPOSED_TEXT" and str(source.get("url", "")).startswith(("http://", "https://")):
            return source["url"]
    raise ValueError("Job has no HTTP/HTTPS proposed text source URL.")


def proposal_id(job: dict[str, Any]) -> str:
    agenda_item = (job.get("input") or {}).get("agendaItem") or {}
    return str(agenda_item.get("id") or job.get("sourceLabel") or job["id"])


def provision_id(job_id: str, raw_id: str) -> str:
    return f"{job_id}-{raw_id}"


def operation_id(job_id: str, raw_id: str) -> str:
    return f"{job_id}-{raw_id}"


def affected_item_id(job_id: str, reference_id: str) -> str:
    return f"{job_id}-affected-{reference_id}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
