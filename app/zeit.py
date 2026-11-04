"""Datum in Wiener Zeit (Preisdatum, SPEC 6.2). Tests ersetzen heute() per monkeypatch."""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from .config import get_settings


def heute() -> date:
    return datetime.now(ZoneInfo(get_settings().timezone)).date()


def jetzt() -> str:
    """Zeitpunkt in Wiener Zeit, sekundengenau (Entnahme, D-039)."""
    return datetime.now(ZoneInfo(get_settings().timezone)).replace(tzinfo=None).isoformat(timespec="seconds")
