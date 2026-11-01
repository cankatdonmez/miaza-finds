"""Konfiguration über Umgebungsvariablen (Präfix MF_)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Daten nie im Drive-Ordner des Codes (D-008): Standard ist %USERPROFILE%\miaza-local\finds
LOKAL_DIR = Path(os.environ.get("MF_LOKAL_DIR", Path.home() / "miaza-local" / "finds"))


@dataclass(frozen=True)
class Settings:
    db_path: Path = field(default_factory=lambda: Path(os.environ.get("MF_DB_PATH", LOKAL_DIR / "data" / "finds.db")))
    media_dir: Path = field(default_factory=lambda: Path(os.environ.get("MF_MEDIA_DIR", LOKAL_DIR / "media")))
    backup_dir: Path = field(default_factory=lambda: Path(os.environ.get("MF_BACKUP_DIR", LOKAL_DIR / "backups")))
    timezone: str = os.environ.get("MF_TIMEZONE", "Europe/Vienna")
    # Cookies des Systembereichs nur über HTTPS senden. Im Büronetz ohne TLS bleibt das aus.
    secure_cookies: bool = os.environ.get("MF_SECURE_COOKIES", "0") == "1"


def get_settings() -> Settings:
    return Settings()
