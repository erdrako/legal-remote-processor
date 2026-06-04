from __future__ import annotations

import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import fitz
import requests


@dataclass(frozen=True)
class ExtractedPdf:
    source_url: str
    content_hash: str
    byte_count: int
    page_count: int
    text: str
    path: Path
    ocr_used: bool
    ocr_available: bool


def download_and_extract_pdf(source_url: str, data_dir: Path, job_id: str) -> ExtractedPdf:
    if not source_url.startswith(("http://", "https://")):
        raise ValueError(f"Unsupported source URL for processor job: {source_url}")

    data_dir.mkdir(parents=True, exist_ok=True)
    response = requests.get(source_url, timeout=120)
    response.raise_for_status()
    payload = response.content
    content_hash = "sha256-" + hashlib.sha256(payload).hexdigest()
    pdf_path = data_dir / f"{job_id}.pdf"
    pdf_path.write_bytes(payload)

    pages: list[str] = []
    ocr_used = False
    tesseract_available = shutil.which("tesseract") is not None
    with fitz.open(stream=payload, filetype="pdf") as document:
        for index, page in enumerate(document, start=1):
            page_text = page.get_text("text").strip()
            if not page_text and tesseract_available:
                page_text = ocr_page(page, data_dir, job_id, index)
                ocr_used = ocr_used or bool(page_text)
            if page_text:
                pages.append(f"\n\n--- PAGINA {index} ---\n{page_text}")
        page_count = document.page_count

    return ExtractedPdf(
        source_url=source_url,
        content_hash=content_hash,
        byte_count=len(payload),
        page_count=page_count,
        text="\n".join(pages).strip(),
        path=pdf_path,
        ocr_used=ocr_used,
        ocr_available=tesseract_available,
    )


def ocr_page(page: fitz.Page, data_dir: Path, job_id: str, page_number: int) -> str:
    image_path = data_dir / f"{job_id}-page-{page_number}.png"
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    pixmap.save(image_path)
    result = subprocess.run(
        ["tesseract", str(image_path), "stdout", "-l", "spa"],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    return result.stdout.strip() if result.returncode == 0 else ""
