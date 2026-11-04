"""Personen des Büros (SPEC 6.7, D-038): wer ein Produkt nimmt, wer gerade bearbeitet. Nur ein Name, keine Konten.

Entfernen blendet eine Person aus (entfernt_am), statt sie zu löschen: frühere Ausleihen behalten ihren Namen,
und „Rückgängig“ holt sie unverändert zurück.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from ..fehler import Fehler
from ..texte import t

NAME_MAX = 60


def liste(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(
        "SELECT id, name FROM person WHERE entfernt_am IS NULL ORDER BY name COLLATE NOCASE, id")]


def _name(roh: Any) -> str:
    name = " ".join(str(roh or "").split())
    if not name:
        raise Fehler(t("fehler.name_fehlt"), "name")
    if len(name) > NAME_MAX:
        raise Fehler(t("fehler.name_zu_lang"), "name")
    return name


def _frei(conn: sqlite3.Connection, name: str, ausser: int | None = None) -> None:
    gleich = conn.execute("SELECT id FROM person WHERE entfernt_am IS NULL AND name = ? COLLATE NOCASE AND id IS NOT ?",
                          (name, ausser)).fetchone()
    if gleich:
        raise Fehler(t("fehler.person_doppelt", name=name), "name")


def _aktiv(conn: sqlite3.Connection, person_id: int) -> sqlite3.Row:
    p = conn.execute("SELECT id, name, entfernt_am FROM person WHERE id = ?", (person_id,)).fetchone()
    if p is None:
        raise Fehler(t("fehler.person_unbekannt"), status=404)
    return p


def anlegen(conn: sqlite3.Connection, roh: Any) -> int:
    name = _name(roh)
    _frei(conn, name)
    return conn.execute("INSERT INTO person (name) VALUES (?)", (name,)).lastrowid


def umbenennen(conn: sqlite3.Connection, person_id: int, roh: Any) -> None:
    _aktiv(conn, person_id)
    name = _name(roh)
    _frei(conn, name, person_id)
    conn.execute("UPDATE person SET name = ? WHERE id = ?", (name, person_id))


def entfernen(conn: sqlite3.Connection, person_id: int) -> None:
    _aktiv(conn, person_id)
    conn.execute("UPDATE person SET entfernt_am = ? WHERE id = ? AND entfernt_am IS NULL",
                 (datetime.now().isoformat(timespec="seconds"), person_id))


def zurueckholen(conn: sqlite3.Connection, person_id: int) -> None:
    p = _aktiv(conn, person_id)
    if p["entfernt_am"] is None:
        return
    _frei(conn, p["name"], person_id)
    conn.execute("UPDATE person SET entfernt_am = NULL WHERE id = ?", (person_id,))
