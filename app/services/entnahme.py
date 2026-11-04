"""Nehmen und Zurücklegen (SPEC 6.7, D-039). Der Status eines Produkts steht nirgends als Feld:
ein offener Entnahme-Eintrag heißt In Benutzung (im Büro) oder Außer Haus; sonst liegt es am Platz (wenn es einen hat).
"""
from __future__ import annotations

import sqlite3
from typing import Any

from .. import zeit
from ..fehler import Fehler
from ..texte import t

ORTE = ("buero", "ausser_haus")
STATUS_NACH_ORT = {"buero": "in_benutzung", "ausser_haus": "ausser_haus"}
NOTIZ_MAX = 300


def offen(conn: sqlite3.Connection, inventar_nr: int) -> dict[str, Any] | None:
    """Der offene Eintrag mit dem Namen der Person (auch wenn sie inzwischen entfernt wurde)."""
    z = conn.execute("""
        SELECT e.id, e.ort, e.notiz, e.genommen_am, e.person_id, pe.name AS person
        FROM entnahme e LEFT JOIN person pe ON pe.id = e.person_id
        WHERE e.produkt_id = ? AND e.zurueck_am IS NULL""", (inventar_nr,)).fetchone()
    return dict(z) if z else None


def status(produkt: dict[str, Any] | sqlite3.Row, eintrag: dict[str, Any] | None) -> str | None:
    """Status für die Anzeige; digitale Produkte haben keinen."""
    if produkt["art"] != "physisch":
        return None
    if eintrag:
        return STATUS_NACH_ORT[eintrag["ort"]]
    return "am_platz" if produkt["fach_id"] else "ohne_platz"


def _physisch(conn: sqlite3.Connection, inventar_nr: int) -> None:
    p = conn.execute("SELECT art FROM produkt WHERE inventar_nr = ?", (inventar_nr,)).fetchone()
    if p is None:
        raise Fehler(t("fehler.produkt_unbekannt"), status=404)
    if p["art"] != "physisch":
        raise Fehler(t("fehler.nehmen_digital"))


def nehmen(conn: sqlite3.Connection, inventar_nr: int, daten: dict[str, Any]) -> int:
    _physisch(conn, inventar_nr)
    if offen(conn, inventar_nr):
        raise Fehler(t("fehler.schon_genommen"), status=409)
    ort = daten.get("ort") or "buero"
    if ort not in ORTE:
        raise Fehler(t("fehler.ort"), "ort")
    person_id = daten.get("person_id")
    if person_id is not None:
        if conn.execute("SELECT 1 FROM person WHERE id = ? AND entfernt_am IS NULL", (person_id,)).fetchone() is None:
            raise Fehler(t("fehler.person_unbekannt"), "person_id")
    notiz = " ".join(str(daten.get("notiz") or "").split()) or None
    if notiz and len(notiz) > NOTIZ_MAX:
        raise Fehler(t("fehler.zu_lang"), "notiz")
    return conn.execute("""INSERT INTO entnahme (produkt_id, person_id, ort, notiz, genommen_am) VALUES (?, ?, ?, ?, ?)""",
                        (inventar_nr, person_id, ort, notiz, zeit.jetzt())).lastrowid


def zuruecklegen(conn: sqlite3.Connection, inventar_nr: int) -> int:
    """Schließt den offenen Eintrag; liefert seine id für „Rückgängig“."""
    _physisch(conn, inventar_nr)
    e = offen(conn, inventar_nr)
    if e is None:
        raise Fehler(t("fehler.nicht_genommen"), status=409)
    conn.execute("UPDATE entnahme SET zurueck_am = ? WHERE id = ?", (zeit.jetzt(), e["id"]))
    return e["id"]


def _eintrag(conn: sqlite3.Connection, entnahme_id: int) -> sqlite3.Row:
    e = conn.execute("SELECT id, produkt_id, zurueck_am FROM entnahme WHERE id = ?", (entnahme_id,)).fetchone()
    if e is None:
        raise Fehler(t("fehler.entnahme_unbekannt"), status=404)
    return e


def nehmen_zuruecknehmen(conn: sqlite3.Connection, entnahme_id: int) -> int:
    """„Rückgängig“ nach Nehmen: der Eintrag verschwindet, als wäre nichts gewesen. Nur solange er offen ist."""
    e = _eintrag(conn, entnahme_id)
    if e["zurueck_am"] is not None:
        raise Fehler(t("fehler.rueckgaengig_vorbei"), status=409)
    conn.execute("DELETE FROM entnahme WHERE id = ?", (entnahme_id,))
    return e["produkt_id"]


def zuruecklegen_zuruecknehmen(conn: sqlite3.Connection, entnahme_id: int) -> int:
    """„Rückgängig“ nach Zurücklegen: der Eintrag ist wieder offen, sofern das Produkt nicht schon neu genommen wurde."""
    e = _eintrag(conn, entnahme_id)
    if e["zurueck_am"] is None:
        return e["produkt_id"]
    if offen(conn, e["produkt_id"]):
        raise Fehler(t("fehler.rueckgaengig_vorbei"), status=409)
    conn.execute("UPDATE entnahme SET zurueck_am = NULL, fach_bestaetigt = NULL WHERE id = ?", (entnahme_id,))
    return e["produkt_id"]
