"""Einstellungen des ganzen Büros (SPEC 6.11). Nur Schalter mit festem Standard; was fehlt, gilt als Standard."""
from __future__ import annotations

import sqlite3
from typing import Any

from ..fehler import Fehler
from ..texte import t

# Schlüssel → Standard. Nur Ja/Nein-Schalter bisher.
STANDARD: dict[str, bool] = {
    "fach_bestaetigen": True,      # Fach-Etikett beim Zurücklegen scannen (D-042)
}


def lesen(conn: sqlite3.Connection) -> dict[str, Any]:
    gespeichert = {r["schluessel"]: r["wert"] for r in conn.execute("SELECT schluessel, wert FROM einstellung")}
    return {k: (gespeichert[k] == "1") if k in gespeichert else std for k, std in STANDARD.items()}


def aendern(conn: sqlite3.Connection, daten: dict[str, Any]) -> dict[str, Any]:
    for k, w in daten.items():
        if k not in STANDARD or not isinstance(w, bool):
            raise Fehler(t("fehler.einstellung"), k)
        conn.execute("INSERT INTO einstellung (schluessel, wert) VALUES (?, ?) ON CONFLICT (schluessel) DO UPDATE SET wert = excluded.wert",
                     (k, "1" if w else "0"))
    return lesen(conn)
