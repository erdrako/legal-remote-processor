from __future__ import annotations

import re
from dataclasses import dataclass


ARTICLE_PATTERN = re.compile(
    r"(?im)(^|\n)\s*(ART[IÍ]CULO|Art\.?)\s+([0-9]+(?:[°º])?)\s*[.\-:)]?",
)


@dataclass(frozen=True)
class ProvisionCandidate:
    id: str
    label: str
    provision_type: str
    order: int
    text: str


def segment_provisions(text: str, *, max_text_chars: int = 50000) -> list[ProvisionCandidate]:
    normalized = normalize_legal_text(text)
    matches = list(ARTICLE_PATTERN.finditer(normalized))

    if not matches:
        return [
            ProvisionCandidate(
                id="provision-documento-completo",
                label="Documento completo",
                provision_type="DOCUMENT",
                order=1,
                text=normalized[:max_text_chars],
            )
        ]

    provisions: list[ProvisionCandidate] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        label = f"Articulo {match.group(3)}"
        provisions.append(
            ProvisionCandidate(
                id=f"provision-articulo-{sanitize_id(match.group(3))}",
                label=label,
                provision_type="ARTICLE",
                order=index + 1,
                text=normalized[start:end].strip()[:max_text_chars],
            )
        )

    return provisions


def normalize_legal_text(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def sanitize_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
