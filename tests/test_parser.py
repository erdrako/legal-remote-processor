import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from processor.legal_parser.operations import classify_operations
from processor.legal_parser.provisions import segment_provisions
from processor.legal_parser.references import detect_references
from processor.jobs import build_affected_items, process_resolve_diff_fallback
from processor.config import ProcessorConfig


def test_segments_articles_and_detects_repeal():
    text = """
    ARTICULO 1.- Derogase la Ley 12.345.

    ARTICULO 2.- Sustituyese el articulo 3 de la Ley 27.640.
    """
    provisions = segment_provisions(text)
    references = detect_references(text)
    operations = classify_operations(provisions, references)

    assert len(provisions) == 2
    assert any(reference.label == "Ley 12.345" for reference in references)
    assert operations[0].operation_type == "REPEAL_LAW"


def test_affected_items_include_canonical_reference_and_evidence():
    text = "ARTICULO 1.- Sustituyese el articulo 3 de la Ley N° 27.640."
    provisions = segment_provisions(text)
    references = detect_references(text)
    operations = classify_operations(provisions, references)
    items = build_affected_items(
        {"id": "job-test", "input": {"agendaItem": {"id": "agenda-test"}}},
        references,
        operations,
        "2026-06-04T00:00:00Z",
    )

    assert items[0]["canonicalReferenceText"] == "Ley 27.640"
    assert items[0]["currentSource"]["lawNumber"] == "27640"
    assert items[0]["detectionEvidence"]["detectedVerb"]
    assert items[0]["detectionEvidence"]["requiresReview"] is True


def test_resolve_diff_fallback_returns_structured_hint(tmp_path):
    config = ProcessorConfig(
        api_base_url="https://example.test",
        processor_id="processor-test",
        processor_secret="secret",
        processor_name="test",
        tier=1,
        version="0.1.0",
        capabilities=["LEGAL_DIFF_FALLBACK"],
        poll_interval_seconds=1,
        max_lease_seconds=60,
        data_dir=tmp_path,
        enable_ollama=False,
        ollama_base_url="http://localhost:11434",
        ollama_model="",
    )
    result = process_resolve_diff_fallback(
        {
            "id": "job-fallback",
            "input": {
                "candidate": {
                    "id": "candidate-1",
                    "title": "Candidato 1",
                    "operationType": "MODIFY_ARTICLE",
                    "changeType": "MODIFIED",
                    "evidenceText": "Sustituyese el articulo 3 de la Ley 27.640.",
                    "validationWarnings": ["TARGET_ARTICLE_NOT_FOUND"],
                },
                "resolution": {
                    "proposedVersion": {"text": "Texto propuesto"},
                    "validationWarnings": ["TARGET_ARTICLE_NOT_FOUND"],
                },
            },
        },
        config,
    )

    assert result["status"] == "NEEDS_REVIEW"
    assert result["result"]["fallbackDiffResolutions"][0]["candidateId"] == "candidate-1"
    assert result["result"]["fallbackDiffResolutions"][0]["targetLabel"] == "Articulo 3"
