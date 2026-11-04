"""„Wird bearbeitet“ (SPEC 4.9, D-044): ein Hinweis, kein Schloss. Er lebt nur im Speicher des Servers und fällt von
selbst weg: 2 Minuten ohne Signal oder 15 Minuten ohne Änderung. So gibt es nie etwas von Hand aufzuräumen.
"""
from __future__ import annotations

import sqlite3
import threading
import time
from typing import Any

from ..fehler import Fehler
from ..texte import t

# Plan und Einheitsfoto speichern in dieselbe Plan-Version, darum teilen sie sich „plan“
ARTEN = ("produkt", "kategorie", "plan")
SIGNAL_MAX = 120          # Sekunden ohne Lebenszeichen
RUHE_MAX = 15 * 60        # Sekunden ohne Änderung

_sperre = threading.Lock()
jetzt = time.monotonic    # Tests ersetzen das


def _schluessel(daten: dict[str, Any]) -> tuple[str, int]:
    art, rid = daten.get("art"), daten.get("id")
    if art not in ARTEN or isinstance(rid, bool) or not isinstance(rid, int):
        raise Fehler(t("fehler.bearbeitung"))
    return art, rid


def _geraet(daten: dict[str, Any]) -> str:
    g = str(daten.get("geraet") or "")
    if not 8 <= len(g) <= 64:
        raise Fehler(t("fehler.bearbeitung"))
    return g


def _gueltig(m: dict[str, Any] | None) -> bool:
    return bool(m) and jetzt() - m["signal"] <= SIGNAL_MAX and jetzt() - m["geaendert"] <= RUHE_MAX


def _belegt(m: dict[str, Any]) -> dict[str, Any]:
    return {"frei": False, "wer": m["wer"], "minuten": max(1, round((jetzt() - m["seit"]) / 60))}


def beginnen(speicher: dict, conn: sqlite3.Connection, daten: dict[str, Any]) -> dict[str, Any]:
    """Setzt den Hinweis für dieses Gerät, wenn niemand sonst bearbeitet; sonst: wer und seit wann."""
    k, g = _schluessel(daten), _geraet(daten)
    wer = None
    if isinstance(daten.get("person_id"), int):
        p = conn.execute("SELECT name FROM person WHERE id = ? AND entfernt_am IS NULL", (daten["person_id"],)).fetchone()
        wer = p["name"] if p else None
    with _sperre:
        m = speicher.get(k)
        if _gueltig(m) and m["geraet"] != g:
            return _belegt(m)
        n = jetzt()
        speicher[k] = {"geraet": g, "wer": wer, "seit": m["seit"] if _gueltig(m) else n, "signal": n,
                       "geaendert": m["geaendert"] if _gueltig(m) else n}
        return {"frei": True}


def signal(speicher: dict, daten: dict[str, Any]) -> dict[str, Any]:
    """Lebenszeichen des bearbeitenden Geräts; geaendert=True, wenn seit dem letzten Signal getippt wurde."""
    k, g = _schluessel(daten), _geraet(daten)
    with _sperre:
        m = speicher.get(k)
        if not _gueltig(m) or m["geraet"] != g:
            # abgelaufen oder übernommen: das Gerät erfährt es und kann neu beginnen
            return _belegt(m) if _gueltig(m) else {"frei": False, "abgelaufen": True}
        m["signal"] = jetzt()
        if daten.get("geaendert"):
            m["geaendert"] = m["signal"]
        return {"frei": True}


def ende(speicher: dict, daten: dict[str, Any]) -> None:
    k, g = _schluessel(daten), _geraet(daten)
    with _sperre:
        if speicher.get(k, {}).get("geraet") == g:
            del speicher[k]


def stand(speicher: dict, daten: dict[str, Any]) -> dict[str, Any]:
    """Für die Wartenden: ist es frei (für dieses Gerät)?"""
    k = _schluessel(daten)
    g = str(daten.get("geraet") or "")
    with _sperre:
        m = speicher.get(k)
        if not _gueltig(m) or m["geraet"] == g:
            return {"frei": True}
        return _belegt(m)
