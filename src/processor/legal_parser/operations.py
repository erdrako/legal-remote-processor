from __future__ import annotations

import re
from dataclasses import dataclass

from .provisions import ProvisionCandidate
from .references import LegalReference


OPERATION_RULES = [
    ("REPEAL_LAW", re.compile(r"\bder[oó]g(?:ase|anse|ar|a|an|ado|ada|ados|adas)\b", re.IGNORECASE), "REMOVED"),
    ("MODIFY_PROVISION", re.compile(r"\bmodif[ií]c(?:ase|anse|ar|a|an|ado|ada|ados|adas)\b", re.IGNORECASE), "MODIFIED"),
    ("MODIFY_PROVISION", re.compile(r"\bsustit[uú]y(?:ese|anse|en|e|a|an)\b", re.IGNORECASE), "MODIFIED"),
    ("ADD_PROVISION", re.compile(r"\bincorp[oó]r(?:ase|anse|ar|a|an|ado|ada|ados|adas)\b", re.IGNORECASE), "ADDED"),
    ("ADD_PROVISION", re.compile(r"\bagreg(?:ase|anse|ar|a|an|ado|ada|ados|adas)\b", re.IGNORECASE), "ADDED"),
    ("APPROVAL_ONLY", re.compile(r"\bapr[uú]eb(?:ase|anse|a|an|a)\b", re.IGNORECASE), "ADDED"),
]


@dataclass(frozen=True)
class OperationCandidate:
    id: str
    operation_type: str
    change_type: str
    detected_verb: str
    source_provision_id: str
    evidence_text: str
    target_reference_id: str | None
    confidence: str


def classify_operations(
    provisions: list[ProvisionCandidate],
    references: list[LegalReference],
    *,
    max_operations: int = 25,
) -> list[OperationCandidate]:
    reference_by_label = {reference.label.lower(): reference for reference in references}
    operations: list[OperationCandidate] = []

    for provision in provisions:
        for operation_type, pattern, change_type in OPERATION_RULES:
            match = pattern.search(provision.text)
            if not match:
                continue

            target = first_reference_in_text(provision.text, reference_by_label)
            operations.append(
                OperationCandidate(
                    id=f"operation-{len(operations) + 1}",
                    operation_type=operation_type,
                    change_type=change_type,
                    detected_verb=match.group(0),
                    source_provision_id=provision.id,
                    evidence_text=compact_text(provision.text),
                    target_reference_id=target.id if target else None,
                    confidence="MEDIUM" if target else "LOW",
                )
            )
            break

        if len(operations) >= max_operations:
            break

    if not operations and provisions:
        first = provisions[0]
        operations.append(
            OperationCandidate(
                id="operation-1",
                operation_type="NEEDS_REVIEW",
                change_type="MODIFIED",
                detected_verb="",
                source_provision_id=first.id,
                evidence_text=compact_text(first.text),
                target_reference_id=None,
                confidence="LOW",
            )
        )

    return operations


def first_reference_in_text(text: str, reference_by_label: dict[str, LegalReference]) -> LegalReference | None:
    lowered = text.lower()
    for label, reference in reference_by_label.items():
        if label in lowered or reference.reference_text.lower() in lowered:
            return reference
    return None


def compact_text(text: str, limit: int = 1600) -> str:
    one_line = re.sub(r"\s+", " ", text).strip()
    return one_line[:limit]
