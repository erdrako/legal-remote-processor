import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from processor.legal_parser.operations import classify_operations
from processor.legal_parser.provisions import segment_provisions
from processor.legal_parser.references import detect_references


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
