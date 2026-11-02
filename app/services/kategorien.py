"""Kategorien und ihre Filter (SPEC 6.3). Eine Kategorie wird mit allen Filtern in einem Schritt gespeichert
(einfaches Formular Speichern / Verwerfen); die Versionsnummer verhindert stilles Überschreiben (SPEC 4.9).

Alle schreibenden Funktionen laufen innerhalb einer Transaktion des Aufrufers.
"""
from __future__ import annotations

import re
import sqlite3
from typing import Any

from ..fehler import Fehler
from ..texte import t
from . import produkte

# „farbe“ ist für die Oberfläche ein eigener Typ; gespeichert wird er als Mehrfachauswahl mit filter.farbe = 1 (D-031)
FILTER_TYPEN = ("mass", "einfach", "mehrfach", "janein", "farbe")
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
MASS_EINHEITEN = ("mm", "cm", "m", "kg", "Stk")
NAME_MAX = 60
_UMSCHRIFT = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"})


def liste(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Alle Kategorien mit Filtern, Auswahlen und Nutzungszahlen (für die Hinweise vor dem Speichern)."""
    kategorien = [dict(r) for r in conn.execute("""
        SELECT k.id, k.name, k.praefix, k.fest, k.version,
               (SELECT count(*) FROM produkt p WHERE p.kategorie_id = k.id) AS produkte,
               (SELECT count(*) FROM produkt p WHERE p.kategorie_id = k.id AND p.code_praefix = k.praefix) AS codes_mit_praefix
        FROM kategorie k ORDER BY k.fest, k.name COLLATE NOCASE""")]
    filter_je_kat: dict[int, list] = {}
    for f in conn.execute("""
            SELECT f.id, f.kategorie_id, f.name, f.typ, f.einheit, f.farbe,
                   (SELECT count(DISTINCT w.produkt_id) FROM produkt_wert w WHERE w.filter_id = f.id) AS produkte
            FROM filter f ORDER BY f.sortierung, f.id"""):
        filter_je_kat.setdefault(f["kategorie_id"], []).append({**dict(f), "farbe": bool(f["farbe"]), "optionen": []})
    optionen = {}
    for o in conn.execute("""
            SELECT o.id, o.filter_id, o.name, o.hex, o.grundfarbe,
                   (SELECT count(*) FROM produkt_wert w WHERE w.option_id = o.id) AS produkte
            FROM filter_option o ORDER BY o.sortierung, o.id"""):
        optionen.setdefault(o["filter_id"], []).append({"id": o["id"], "name": o["name"], "hex": o["hex"],
                                                         "grundfarbe": o["grundfarbe"], "produkte": o["produkte"]})
    for k in kategorien:
        k["fest"] = bool(k["fest"])
        k["filter"] = filter_je_kat.get(k["id"], [])
        for f in k["filter"]:
            f.pop("kategorie_id")
            f["optionen"] = optionen.get(f["id"], [])
    return kategorien


def praefix_vorschlag(conn: sqlite3.Connection, name: str, ausser_id: int | None = None) -> str:
    """Zwei Buchstaben aus dem Namen, die noch frei sind: „Fliese“ → FL, sonst F + späterer Buchstabe, sonst frei."""
    vergeben = {r[0] for r in conn.execute("SELECT praefix FROM kategorie WHERE id IS NOT ?", (ausser_id,))}
    buchstaben = [c for c in name.translate(_UMSCHRIFT).upper() if "A" <= c <= "Z"]
    kandidaten = []
    if buchstaben:
        kandidaten += [buchstaben[0] + b for b in buchstaben[1:]]
        kandidaten += [buchstaben[0] + chr(c) for c in range(ord("A"), ord("Z") + 1)]
    kandidaten += [chr(a) + chr(b) for a in range(ord("A"), ord("Z") + 1) for b in range(ord("A"), ord("Z") + 1)]
    return next(k for k in kandidaten if k not in vergeben)


def _name(wert: Any, feld: str = "name") -> str:
    name = " ".join(str(wert or "").split())
    if not name:
        raise Fehler(t("fehler.name_fehlt"), feld)
    if len(name) > NAME_MAX:
        raise Fehler(t("fehler.name_zu_lang"), feld)
    return name


def _praefix(conn: sqlite3.Connection, wert: Any, ausser_id: int | None) -> str:
    praefix = str(wert or "").strip().upper()
    if len(praefix) != 2 or not all("A" <= c <= "Z" for c in praefix):
        raise Fehler(t("fehler.praefix_form"), "praefix")
    besitzer = conn.execute("SELECT name FROM kategorie WHERE praefix = ? AND id IS NOT ?", (praefix, ausser_id)).fetchone()
    if besitzer:
        raise Fehler(t("fehler.praefix_vergeben", name=besitzer["name"]), "praefix")
    return praefix


def _name_frei(conn: sqlite3.Connection, name: str, ausser_id: int | None) -> None:
    if conn.execute("SELECT 1 FROM kategorie WHERE name = ? COLLATE NOCASE AND id IS NOT ?", (name, ausser_id)).fetchone():
        raise Fehler(t("fehler.kategorie_name_vergeben"), "name")


def anlegen(conn: sqlite3.Connection, daten: dict[str, Any]) -> int:
    name = _name(daten.get("name"))
    _name_frei(conn, name, None)
    praefix = _praefix(conn, daten.get("praefix") or praefix_vorschlag(conn, name), None)
    return conn.execute("INSERT INTO kategorie (name, praefix) VALUES (?, ?) RETURNING id", (name, praefix)).fetchone()[0]


def speichern(conn: sqlite3.Connection, kategorie_id: int, daten: dict[str, Any]) -> dict[str, int]:
    """Name, Präfix und die ganze Filterliste. Fehlende Filter/Auswahlen werden gelöscht (mit ihren Werten).

    Liefert, was sich an Produkten geändert hat: {"codes_geaendert": n}.
    """
    alt = conn.execute("SELECT praefix, version FROM kategorie WHERE id = ?", (kategorie_id,)).fetchone()
    if alt is None:
        raise Fehler(t("fehler.kategorie_unbekannt"), status=404)
    if daten.get("version") != alt["version"]:
        raise Fehler(t("fehler.veraltet"), status=409)
    name = _name(daten.get("name"))
    _name_frei(conn, name, kategorie_id)
    praefix = _praefix(conn, daten.get("praefix"), kategorie_id)
    conn.execute("UPDATE kategorie SET name = ?, praefix = ?, version = version + 1 WHERE id = ?", (name, praefix, kategorie_id))

    codes_geaendert = 0
    if praefix != alt["praefix"]:
        # Nur Codes mit dem bisherigen Präfix; Produkte mit behaltenem fremdem Code bleiben (SPEC 6.2)
        codes_geaendert = conn.execute("""
            UPDATE produkt SET code_praefix = ?, etikett = CASE etikett WHEN 'gedruckt' THEN 'neu_drucken' ELSE etikett END,
                   version = version + 1, geaendert_am = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
            WHERE kategorie_id = ? AND code_praefix = ?""", (praefix, kategorie_id, alt["praefix"])).rowcount

    _filter_speichern(conn, kategorie_id, daten.get("filter") or [])
    # Kategoriename, Codes und Auswahlnamen stehen im Suchtext der Produkte
    for (inv,) in conn.execute("SELECT inventar_nr FROM produkt WHERE kategorie_id = ?", (kategorie_id,)).fetchall():
        produkte.suchtext_erneuern(conn, inv)
    return {"codes_geaendert": codes_geaendert}


def _filter_speichern(conn: sqlite3.Connection, kategorie_id: int, filter_liste: list[dict[str, Any]]) -> None:
    bestehend = {r["id"]: dict(r) for r in conn.execute("SELECT id, typ, farbe FROM filter WHERE kategorie_id = ?", (kategorie_id,))}
    namen, behalten, geplant = set(), set(), []
    for pos, f in enumerate(filter_liste):
        name = _name(f.get("name"), "filter")
        if name.casefold() in namen:
            raise Fehler(t("fehler.filter_name_doppelt", name=name), "filter")
        namen.add(name.casefold())
        typ = f.get("typ")
        if typ == "mehrfach" and f.get("farbe"):
            typ = "farbe"
        if typ not in FILTER_TYPEN:
            raise Fehler(t("fehler.filter_typ"), "filter")
        farbe = typ == "farbe"
        typ = "mehrfach" if farbe else typ
        einheit = f.get("einheit") if typ == "mass" else None
        if typ == "mass" and einheit not in MASS_EINHEITEN:
            raise Fehler(t("fehler.filter_einheit"), "filter")
        fid = f.get("id")
        if fid in bestehend:
            if bestehend[fid]["typ"] != typ or bool(bestehend[fid]["farbe"]) != farbe:
                raise Fehler(t("fehler.filter_typ_fest"), "filter")
            behalten.add(fid)
        else:
            fid = None
        optionen = f.get("optionen") or []
        if typ in ("einfach", "mehrfach") and not any(" ".join(str(o.get("name") or "").split()) for o in optionen):
            raise Fehler(t("fehler.filter_optionen_fehlen", name=name), "filter")
        # Erst alle Namen vorübergehend frei machen, damit Umbenennen/Umsortieren nicht an UNIQUE scheitert
        if fid:
            conn.execute("UPDATE filter SET name = '~' || id WHERE id = ?", (fid,))
        geplant.append((fid, name, typ, farbe, einheit, pos, optionen))

    for fid in set(bestehend) - behalten:
        conn.execute("DELETE FROM filter WHERE id = ?", (fid,))
    for fid, name, typ, farbe, einheit, pos, optionen in geplant:
        if fid:
            conn.execute("UPDATE filter SET name = ?, einheit = ?, sortierung = ? WHERE id = ?", (name, einheit, pos, fid))
        else:
            fid = conn.execute("INSERT INTO filter (kategorie_id, name, typ, farbe, einheit, sortierung) VALUES (?, ?, ?, ?, ?, ?) RETURNING id",
                               (kategorie_id, name, typ, int(farbe), einheit, pos)).fetchone()[0]
        _optionen_speichern(conn, fid, optionen if typ in ("einfach", "mehrfach") else [], farbe)


def _optionen_speichern(conn: sqlite3.Connection, filter_id: int, optionen: list[dict[str, Any]], farbe: bool = False) -> None:
    """Auswahlen eines Filters; bei einem „Farbe“-Filter sind es Farbtöne mit Farbe und Grundfarbe (D-031)."""
    bestehend = {r[0] for r in conn.execute("SELECT id FROM filter_option WHERE filter_id = ?", (filter_id,))}
    sauber, namen = [], set()
    for o in optionen:
        name = " ".join(str(o.get("name") or "").split())
        if not name:
            continue
        if name.casefold() in namen:
            raise Fehler(t("fehler.option_doppelt", name=name), "filter")
        namen.add(name.casefold())
        hex_, grund = None, None
        if farbe:
            grund = o.get("grundfarbe")
            if grund not in produkte.FARBEN:
                raise Fehler(t("fehler.ton_grundfarbe", name=name), "filter")
            hex_ = o.get("hex") or None
            if hex_ is not None and not HEX.match(str(hex_)):
                raise Fehler(t("fehler.ton_farbe", name=name), "filter")
        sauber.append((o.get("id") if o.get("id") in bestehend else None, name, hex_, grund))
    behalten = {oid for oid, *_ in sauber if oid}
    for oid in bestehend - behalten:
        conn.execute("DELETE FROM filter_option WHERE id = ?", (oid,))
    for oid in behalten:
        conn.execute("UPDATE filter_option SET name = '~' || id WHERE id = ?", (oid,))
    for pos, (oid, name, hex_, grund) in enumerate(sauber):
        if oid:
            conn.execute("UPDATE filter_option SET name = ?, hex = ?, grundfarbe = ?, sortierung = ? WHERE id = ?",
                         (name, hex_, grund, pos, oid))
        else:
            conn.execute("INSERT INTO filter_option (filter_id, name, hex, grundfarbe, sortierung) VALUES (?, ?, ?, ?, ?)",
                         (filter_id, name, hex_, grund, pos))


def loeschen(conn: sqlite3.Connection, kategorie_id: int) -> None:
    """Nur leere Kategorien (D-011); „Sonstiges“ nie."""
    k = conn.execute("SELECT fest, (SELECT count(*) FROM produkt WHERE kategorie_id = ?) AS n FROM kategorie WHERE id = ?",
                     (kategorie_id, kategorie_id)).fetchone()
    if k is None:
        raise Fehler(t("fehler.kategorie_unbekannt"), status=404)
    if k["fest"]:
        raise Fehler(t("fehler.kategorie_fest"), status=409)
    if k["n"]:
        raise Fehler(t("fehler.kategorie_nicht_leer", n=k["n"]), status=409)
    conn.execute("DELETE FROM kategorie WHERE id = ?", (kategorie_id,))
