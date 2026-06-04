from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CAPABILITIES = [
    "PDF_TEXT",
    "LEGAL_REFERENCES",
    "AFFECTED_LEGAL_ITEMS",
    "LEGAL_DIFF_CANDIDATES",
    "LEGAL_DIFF_FALLBACK",
]


def load_dotenv(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True)
class ProcessorConfig:
    api_base_url: str
    processor_id: str
    processor_secret: str
    processor_name: str
    tier: int
    version: str
    capabilities: list[str]
    poll_interval_seconds: int
    max_lease_seconds: int
    data_dir: Path
    enable_ollama: bool
    ollama_base_url: str
    ollama_model: str

    @classmethod
    def from_env(cls) -> "ProcessorConfig":
        load_dotenv()
        capabilities = [
            item.strip()
            for item in os.environ.get("PROCESSOR_CAPABILITIES", ",".join(DEFAULT_CAPABILITIES)).split(",")
            if item.strip()
        ]
        return cls(
            api_base_url=os.environ.get("LEXMAPA_API_BASE_URL", "https://lexmapa-api.linqorait.com").rstrip("/"),
            processor_id=os.environ.get("LEXMAPA_PROCESSOR_ID", "").strip(),
            processor_secret=os.environ.get("LEXMAPA_PROCESSOR_SECRET", "").strip(),
            processor_name=os.environ.get("LEXMAPA_PROCESSOR_NAME", "Procesador remoto LexMapa").strip(),
            tier=int(os.environ.get("LEXMAPA_PROCESSOR_TIER", "1")),
            version=os.environ.get("LEXMAPA_PROCESSOR_VERSION", "0.1.0").strip(),
            capabilities=capabilities,
            poll_interval_seconds=int(os.environ.get("PROCESSOR_POLL_INTERVAL_SECONDS", "20")),
            max_lease_seconds=int(os.environ.get("PROCESSOR_MAX_LEASE_SECONDS", "900")),
            data_dir=Path(os.environ.get("PROCESSOR_DATA_DIR", "data")),
            enable_ollama=os.environ.get("PROCESSOR_ENABLE_OLLAMA", "false").lower() == "true",
            ollama_base_url=os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip("/"),
            ollama_model=os.environ.get("OLLAMA_MODEL", "").strip(),
        )

    def require_enrolled(self) -> None:
        if not self.processor_id or not self.processor_secret:
            raise RuntimeError("Processor is not enrolled. Run scripts/enroll-local.ps1 first.")
