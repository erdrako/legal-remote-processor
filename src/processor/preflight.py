from __future__ import annotations

import platform
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PreflightResult:
    os_name: str
    architecture: str
    cpu_count: int
    ram_gb: float
    free_disk_gb: float
    docker_available: bool
    ollama_available: bool
    tier: int | None
    can_install: bool
    reasons: list[str]


def run_preflight(path: str | Path = ".") -> PreflightResult:
    ram_gb = detect_ram_gb()
    free_disk_gb = shutil.disk_usage(path).free / 1024 / 1024 / 1024
    architecture = platform.machine().lower()
    cpu_count = os.cpu_count() or 1
    reasons: list[str] = []

    if "64" not in architecture and "amd64" not in architecture and "x86_64" not in architecture:
        reasons.append("CPU 64-bit requerida.")
    if ram_gb < 8:
        reasons.append("RAM insuficiente: se requieren al menos 8 GB.")
    if free_disk_gb < 20:
        reasons.append("Disco libre insuficiente: se requieren al menos 20 GB.")

    tier = choose_tier(ram_gb, free_disk_gb, cpu_count) if not reasons else None
    return PreflightResult(
        os_name=platform.system(),
        architecture=architecture,
        cpu_count=cpu_count,
        ram_gb=ram_gb,
        free_disk_gb=free_disk_gb,
        docker_available=shutil.which("docker") is not None,
        ollama_available=shutil.which("ollama") is not None,
        tier=tier,
        can_install=not reasons,
        reasons=reasons,
    )


def choose_tier(ram_gb: float, free_disk_gb: float, cpu_count: int) -> int:
    if ram_gb >= 64 and cpu_count >= 12 and free_disk_gb >= 120:
        return 5
    if ram_gb >= 32 and cpu_count >= 8 and free_disk_gb >= 80:
        return 4
    if ram_gb >= 16 and cpu_count >= 6 and free_disk_gb >= 50:
        return 3
    if ram_gb >= 12 and cpu_count >= 4 and free_disk_gb >= 30:
        return 2
    return 1


def detect_ram_gb() -> float:
    if platform.system().lower() == "windows":
        try:
            import ctypes

            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MemoryStatus()
            status.dwLength = ctypes.sizeof(MemoryStatus)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            return status.ullTotalPhys / 1024 / 1024 / 1024
        except Exception:
            return 0

    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                kb = float(line.split()[1])
                return kb / 1024 / 1024
    return 0
