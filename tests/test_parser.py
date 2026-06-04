import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from processor.legal_parser.operations import classify_operations
from processor.legal_parser.provisions import segment_provisions
from processor.legal_parser.references import detect_references
from processor.jobs import build_affected_items


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
