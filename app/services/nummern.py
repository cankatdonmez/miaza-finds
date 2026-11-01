"""Produktcode KK-KKK-EEE (SPEC 6.2). Nummern kommen aus Zählern und werden nie wiederverwendet.

Alle Funktionen laufen innerhalb einer Transaktion des Aufrufers (db.transaction).
"""
from __future__ import annotations

import sqlite3


def naechste_inventar_nr(conn: sqlite3.Connection) -> int:
    """Nächste Inventarnummer im ganzen Bestand; Löschen gibt keine Nummer zurück."""
    return conn.execute("UPDATE zaehler SET wert = wert + 1 WHERE name = 'inventar' RETURNING wert").fetchone()[0]


def naechste_kategorie_nr(conn: sqlite3.Connection, kategorie_id: int) -> int:
    """Nächste laufende Nummer innerhalb der Kategorie (KKK).

    Nummern, die ein hierher verschobenes Produkt mit behaltenem Code schon trägt, werden übersprungen.
    """
    while True:
        zeile = conn.execute("UPDATE kategorie SET naechste_nr = naechste_nr + 1 WHERE id = ? RETURNING naechste_nr - 1",
                             (kategorie_id,)).fetchone()
        if zeile is None:
            raise LookupError(f"Kategorie {kategorie_id} gibt es nicht.")
        if not conn.execute("SELECT 1 FROM produkt WHERE kategorie_id = ? AND kategorie_nr = ?",
                            (kategorie_id, zeile[0])).fetchone():
            return zeile[0]


def code(praefix: str, kategorie_nr: int, inventar_nr: int) -> str:
    """ST-005-265; Nummern beginnen dreistellig und werden ab 1000 vierstellig."""
    return f"{praefix}-{kategorie_nr:03d}-{inventar_nr:03d}"
