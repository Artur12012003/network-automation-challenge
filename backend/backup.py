"""Criação do arquivo de backup a partir da running-config coletada."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def write_backup(hostname: str, running_config: str, backup_directory: Path) -> Path:
    """Salva exatamente a saída de ``show running-config`` em um arquivo local."""

    backup_directory.mkdir(parents=True, exist_ok=True)
    safe_hostname = re.sub(r"[^A-Za-z0-9_-]", "_", hostname)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_directory / f"{safe_hostname}_{stamp}_running-config.txt"

    suffix = 1
    while backup_file.exists():
        backup_file = backup_directory / f"{safe_hostname}_{stamp}_{suffix}_running-config.txt"
        suffix += 1

    backup_file.write_text(running_config, encoding="utf-8")
    return backup_file
