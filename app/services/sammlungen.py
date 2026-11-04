"""Sammlungen (SPEC 6.8, D-047): benannte Listen von Produkten, ohne Mengen.

Entfernen blendet eine Sammlung aus (entfernt_am); der Inhalt bleibt, „Rückgängig“ holt alles zurück.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from ..fehler import Fehler
from ..texte import t
from . import entnahme, nummern

NAME_MAX = 60
NOTIZ_MAX = 1000


def _name(roh: Any) -> str:
    name = " ".join(str(roh or "").split())
    if not name:
        raise Fehler(t("fehler.name_fehlt"), "name")
    if len(name) > NAME_MAX:
        raise Fehler(t("fehler.name_zu_lang"), "name")
    return name


def _notiz(roh: Any) -> str | None:
    text = str(roh or "").strip()
    if len(text) > NOTIZ_MAX:
        raise Fehler(t("fehler.notiz_zu_lang"), "notiz")
    return text or None


def _frei(conn: sqlite3.Connection, name: str, ausser: int | None = None) -> None:
    if conn.execute("SELECT 1 FROM sammlung WHERE entfernt_am IS NULL AND name = ? COLLATE NOCASE AND id IS NOT ?",
                    (name, ausser)).fetchone():
        raise Fehler(t("fehler.sammlung_doppelt", name=name), "name")


def _zeile(conn: sqlite3.Connection, sammlung_id: int, aktiv: bool = True) -> sqlite3.Row:
    z = conn.execute("SELECT id, name, notiz, entfernt_am FROM sammlung WHERE id = ?", (sammlung_id,)).fetchone()
    if z is None or (aktiv and z["entfernt_am"]):
        raise Fehler(t("fehler.sammlung_unbekannt"), status=404)
    return z


def _produkt(conn: sqlite3.Connection, inventar_nr: int) -> None:
    if conn.execute("SELECT 1 FROM produkt WHERE inventar_nr = ?", (inventar_nr,)).fetchone() is None:
        raise Fehler(t("fehler.produkt_unbekannt"), status=404)


def liste(conn: sqlite3.Connection, produkt: int | None = None) -> list[dict[str, Any]]:
    """Aktive Sammlungen mit Anzahl; mit `produkt` zusätzlich „enthalten“ (Ankreuzen im Produktdetail)."""
    zeilen = [dict(r) for r in conn.execute("""
        SELECT s.id, s.name, s.notiz,
               (SELECT count(*) FROM sammlung_produkt sp WHERE sp.sammlung_id = s.id) AS anzahl,
               EXISTS (SELECT 1 FROM sammlung_produkt sp WHERE sp.sammlung_id = s.id AND sp.produkt_id = ?) AS enthalten
        FROM sammlung s WHERE s.entfernt_am IS NULL ORDER BY s.name COLLATE NOCASE, s.id""", (produkt,))]
    for z in zeilen:
        z["enthalten"] = bool(z["enthalten"])
    return zeilen


def lesen(conn: sqlite3.Connection, sammlung_id: int) -> dict[str, Any]:
    z = _zeile(conn, sammlung_id)
    zeilen = conn.execute("""
        SELECT p.inventar_nr, p.code_praefix, p.kategorie_nr, p.name, p.marke, p.art, k.name AS kategorie,
               (SELECT f.datei FROM foto f WHERE f.produkt_id = p.inventar_nr ORDER BY f.sortierung, f.id LIMIT 1) AS foto,
               (SELECT e.ort FROM entnahme e WHERE e.produkt_id = p.inventar_nr AND e.zurueck_am IS NULL) AS genommen
        FROM sammlung_produkt sp JOIN produkt p ON p.inventar_nr = sp.produkt_id JOIN kategorie k ON k.id = p.kategorie_id
        WHERE sp.sammlung_id = ? ORDER BY sp.hinzugefuegt_am DESC, p.inventar_nr DESC""", (sammlung_id,)).fetchall()
    produkte = [{
        "inventar_nr": r["inventar_nr"], "code": nummern.code(r["code_praefix"], r["kategorie_nr"], r["inventar_nr"]),
        "name": r["name"], "marke": r["marke"], "art": r["art"], "kategorie": r["kategorie"], "foto": r["foto"],
        "genommen": entnahme.STATUS_NACH_ORT.get(r["genommen"]) if r["art"] == "physisch" else None,
    } for r in zeilen]
    return {"id": z["id"], "name": z["name"], "notiz": z["notiz"], "anzahl": len(produkte), "produkte": produkte}


def anlegen(conn: sqlite3.Connection, name_roh: Any, notiz_roh: Any = None) -> int:
    name = _name(name_roh)
    _frei(conn, name)
    return conn.execute("INSERT INTO sammlung (name, notiz) VALUES (?, ?)", (name, _notiz(notiz_roh))).lastrowid


def aendern(conn: sqlite3.Connection, sammlung_id: int, daten: dict[str, Any]) -> None:
    z = _zeile(conn, sammlung_id)
    name = _name(daten["name"]) if "name" in daten else z["name"]
    notiz = _notiz(daten["notiz"]) if "notiz" in daten else z["notiz"]
    _frei(conn, name, sammlung_id)
    conn.execute("UPDATE sammlung SET name = ?, notiz = ? WHERE id = ?", (name, notiz, sammlung_id))


def entfernen(conn: sqlite3.Connection, sammlung_id: int) -> None:
    _zeile(conn, sammlung_id)
    conn.execute("UPDATE sammlung SET entfernt_am = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = ?", (sammlung_id,))


def zurueckholen(conn: sqlite3.Connection, sammlung_id: int) -> None:
    z = _zeile(conn, sammlung_id, aktiv=False)
    if z["entfernt_am"]:
        _frei(conn, z["name"], sammlung_id)
        conn.execute("UPDATE sammlung SET entfernt_am = NULL WHERE id = ?", (sammlung_id,))


def hinzufuegen(conn: sqlite3.Connection, sammlung_id: int, inventar_nr: int) -> None:
    _zeile(conn, sammlung_id)
    _produkt(conn, inventar_nr)
    conn.execute("INSERT OR IGNORE INTO sammlung_produkt (sammlung_id, produkt_id) VALUES (?, ?)", (sammlung_id, inventar_nr))


def herausnehmen(conn: sqlite3.Connection, sammlung_id: int, inventar_nr: int) -> None:
    _zeile(conn, sammlung_id)
    conn.execute("DELETE FROM sammlung_produkt WHERE sammlung_id = ? AND produkt_id = ?", (sammlung_id, inventar_nr))
