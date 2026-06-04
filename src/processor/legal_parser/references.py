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
    reference_text: str


def detect_references(text: str) -> list[LegalReference]:
    found: dict[str, LegalReference] = {}
    for kind, pattern in REFERENCE_PATTERNS:
        for match in pattern.finditer(text):
            raw_value = match.group(1)
            label = format_label(kind, raw_value)
            key = f"{kind}:{label}".lower()
            found.setdefault(
                key,
                LegalReference(
                    id=sanitize_reference_id(key),
                    kind=kind,
                    label=label,
                    reference_text=match.group(0),
                ),
            )
    return list(found.values())


def format_label(kind: str, value: str) -> str:
    if kind == "LAW":
        return f"Ley {value}"
    if kind == "DECREE":
        return f"Decreto {value}"
    return f"Articulo {value}"


def sanitize_reference_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
