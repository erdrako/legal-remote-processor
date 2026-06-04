from __future__ import annotations

import re
from dataclasses import dataclass


REFERENCE_PATTERNS = [
    ("LAW", re.compile(r"\bLey(?:es)?\s+(?:N[°º]?\s*)?([0-9]{1,3}\.?\d{3})\b", re.IGNORECASE)),
    ("DECREE", re.compile(r"\bDecreto\s+(?:N[°º]?\s*)?([0-9]+\/[0-9]{2,4})\b", re.IGNORECASE)),
    ("ARTICLE", re.compile(r"\bart[ií]culo\s+([0-9]+(?:[°º])?)\b", re.IGNORECASE)),
]


@dataclass(frozen=True)
class LegalReference:
    id: str
    kind: str
    label: str
    canonical_label: str
    normalized_number: str | None
    reference_text: str


def detect_references(text: str) -> list[LegalReference]:
    found: dict[str, LegalReference] = {}
    for kind, pattern in REFERENCE_PATTERNS:
        for match in pattern.finditer(text):
            raw_value = match.group(1)
            label = format_label(kind, raw_value)
            canonical_label = canonical_reference_label(kind, raw_value)
            key = f"{kind}:{label}".lower()
            found.setdefault(
                key,
                LegalReference(
                    id=sanitize_reference_id(key),
                    kind=kind,
                    label=label,
                    canonical_label=canonical_label,
                    normalized_number=normalize_reference_number(raw_value) if kind == "LAW" else None,
                    reference_text=match.group(0),
                ),
            )
    return list(found.values())


def format_label(kind: str, value: str) -> str:
    if kind == "LAW":
        return f"Ley {format_law_number(value)}"
    if kind == "DECREE":
        return f"Decreto {value}"
    return f"Articulo {value}"


def canonical_reference_label(kind: str, value: str) -> str:
    if kind == "LAW":
        return f"Ley {format_law_number(value)}"
    return format_label(kind, value)


def normalize_reference_number(value: str) -> str:
    return re.sub(r"\D+", "", value)


def format_law_number(value: str) -> str:
    digits = normalize_reference_number(value)
    if len(digits) <= 3:
        return digits
    return f"{int(digits[:-3])}.{digits[-3:]}"


def sanitize_reference_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
