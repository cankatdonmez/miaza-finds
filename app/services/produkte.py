"""Produkte: anlegen, lesen, ändern, löschen (SPEC 6.2). Pflicht ist nur der Name; der Rest wird später ergänzt.

Alle schreibenden Funktionen laufen innerhalb einer Transaktion des Aufrufers.
"""
from __future__ import annotations

import re
import sqlite3
from typing import Any

from .. import zeit
from ..fehler import Fehler
from ..texte import t
from . import nummern
from .suche import normalisieren

FARBEN = ("weiss", "beige", "braun", "terracotta", "gold", "rosa", "gruen", "blau", "grau", "schwarz")
PREIS_EINHEITEN = ("m2", "m", "stueck", "paket")
ARTEN = ("physisch", "digital")
TEXT_MAX = {"name": 120, "marke": 80, "abmessungen": 80, "link": 500, "notiz": 2000}


# ---------- Lesen ----------

def lesen(conn: sqlite3.Connection, inventar_nr: int) -> dict[str, Any]:
    p = conn.execute("""
        SELECT p.*, k.name AS kategorie_name FROM produkt p JOIN kategorie k ON k.id = p.kategorie_id
        WHERE p.inventar_nr = ?""", (inventar_nr,)).fetchone()
    if p is None:
        raise Fehler(t("fehler.produkt_unbekannt"), status=404)
    d = dict(p)
    d.pop("suchtext")
    d["code"] = nummern.code(p["code_praefix"], p["kategorie_nr"], p["inventar_nr"])
    d["farben"] = [r[0] for r in conn.execute("SELECT farbe FROM produkt_farbe WHERE produkt_id = ?", (inventar_nr,))]
    preis = conn.execute("SELECT cent, einheit, datum FROM preis WHERE produkt_id = ?", (inventar_nr,)).fetchone()
    d["preis"] = dict(preis) if preis else None
    d["werte"] = _werte_lesen(conn, inventar_nr)
    d["fotos"] = [dict(r) for r in conn.execute(
        "SELECT id, datei, breite, hoehe FROM foto WHERE produkt_id = ? ORDER BY sortierung, id", (inventar_nr,))]
    return d


def _werte_lesen(conn: sqlite3.Connection, inventar_nr: int) -> dict[str, Any]:
    """{filter_id: wert}; mass → Zahl, einfach → option_id, mehrfach → [option_id …], janein → bool."""
    werte: dict[str, Any] = {}
    for w in conn.execute("""SELECT w.filter_id, f.typ, w.option_id, w.zahl, w.janein FROM produkt_wert w
                             JOIN filter f ON f.id = w.filter_id WHERE w.produkt_id = ? ORDER BY w.id""", (inventar_nr,)):
        key = str(w["filter_id"])
        if w["typ"] == "mass":
            werte[key] = w["zahl"]
        elif w["typ"] == "einfach":
            werte[key] = w["option_id"]
        elif w["typ"] == "mehrfach":
            werte.setdefault(key, []).append(w["option_id"])
        else:
            werte[key] = bool(w["janein"])
    return werte


# ---------- Prüfen ----------

def _text(daten: dict[str, Any], feld: str) -> str | None:
    wert = " ".join(str(daten.get(feld) or "").split()) if feld != "notiz" else str(daten.get(feld) or "").strip()
    if len(wert) > TEXT_MAX[feld]:
        raise Fehler(t("fehler.zu_lang"), feld)
    return wert or None


def _link(daten: dict[str, Any]) -> str | None:
    link = _text(daten, "link")
    if link and not re.match(r"^https?://", link, re.I):
        link = "https://" + link
    return link


def preis_lesen(text: Any) -> int:
    """Deutsche Schreibweise → Cent: „36,50“ → 3650, „1.234,56“ → 123456, „10“ → 1000."""
    s = str(text).strip().replace("€", "").replace(" ", "")
    if not re.fullmatch(r"\d{1,3}(\.\d{3})*(,\d{1,2})?|\d+(,\d{1,2})?", s):
        raise Fehler(t("fehler.preis_form"), "preis")
    euro, _, cent = s.replace(".", "").partition(",")
    return int(euro) * 100 + int((cent + "00")[:2])


def _kategorie(conn: sqlite3.Connection, kategorie_id: Any) -> sqlite3.Row:
    k = conn.execute("SELECT id, praefix FROM kategorie WHERE id = ?", (kategorie_id,)).fetchone()
    if k is None:
        raise Fehler(t("fehler.kategorie_unbekannt"), "kategorie_id")
    return k


def _felder(daten: dict[str, Any], name_pflicht: bool = True) -> dict[str, Any]:
    name = _text(daten, "name")
    if name is None and name_pflicht:
        raise Fehler(t("fehler.name_fehlt"), "name")
    art = daten.get("art") or "physisch"
    if art not in ARTEN:
        raise Fehler(t("fehler.art"), "art")
    anzahl = daten.get("anzahl")
    if anzahl in ("", None):
        anzahl = None
    else:
        try:
            anzahl = int(anzahl)
        except (TypeError, ValueError):
            raise Fehler(t("fehler.anzahl"), "anzahl") from None
        if anzahl < 0:
            raise Fehler(t("fehler.anzahl"), "anzahl")
    return {"name": name, "art": art, "marke": _text(daten, "marke"), "abmessungen": _text(daten, "abmessungen"),
            "link": _link(daten), "anzahl": anzahl, "notiz": _text(daten, "notiz")}


# ---------- Schreiben ----------

def anlegen(conn: sqlite3.Connection, daten: dict[str, Any], name_pflicht: bool = True) -> int:
    """Neues Produkt; Inventarnummer und Kategorienummer aus den Zählern (SPEC 6.2)."""
    felder = _felder(daten, name_pflicht)
    kat = _kategorie(conn, daten.get("kategorie_id"))
    inv = nummern.naechste_inventar_nr(conn)
    nr = nummern.naechste_kategorie_nr(conn, kat["id"])
    conn.execute("""INSERT INTO produkt (inventar_nr, kategorie_id, code_praefix, kategorie_nr, name, art, marke,
                                         abmessungen, link, anzahl, notiz)
                    VALUES (:inv, :kat, :praefix, :nr, :name, :art, :marke, :abmessungen, :link, :anzahl, :notiz)""",
                 {**felder, "inv": inv, "kat": kat["id"], "praefix": kat["praefix"], "nr": nr})
    _nebendaten(conn, inv, kat["id"], daten)
    suchtext_erneuern(conn, inv)
    return inv


def aendern(conn: sqlite3.Connection, inventar_nr: int, daten: dict[str, Any]) -> dict[str, Any]:
    """Ändert ein Produkt. Bei Kategoriewechsel: daten["code"] = "behalten" | "neu" (SPEC 6.2).

    Werte der Filter der alten Kategorie entfallen (sie gelten in der neuen nicht).
    """
    alt = conn.execute("SELECT kategorie_id, etikett, version FROM produkt WHERE inventar_nr = ?", (inventar_nr,)).fetchone()
    if alt is None:
        raise Fehler(t("fehler.produkt_unbekannt"), status=404)
    if daten.get("version") != alt["version"]:
        raise Fehler(t("fehler.veraltet"), status=409)
    felder = _felder(daten)
    kat = _kategorie(conn, daten.get("kategorie_id", alt["kategorie_id"]))
    conn.execute("""UPDATE produkt SET name = :name, art = :art, marke = :marke, abmessungen = :abmessungen,
                    link = :link, anzahl = :anzahl, notiz = :notiz, version = version + 1,
                    geaendert_am = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE inventar_nr = :inv""",
                 {**felder, "inv": inventar_nr})
    if kat["id"] != alt["kategorie_id"]:
        kategorie_wechseln(conn, inventar_nr, kat["id"], neuer_code=daten.get("code") == "neu")
    _nebendaten(conn, inventar_nr, kat["id"], daten)
    suchtext_erneuern(conn, inventar_nr)
    return lesen(conn, inventar_nr)


def kategorie_wechseln(conn: sqlite3.Connection, inventar_nr: int, kategorie_id: int, neuer_code: bool) -> None:
    """Auch für die Sammelbearbeitung (D-012). Die Inventarnummer bleibt immer."""
    if neuer_code:
        praefix = conn.execute("SELECT praefix FROM kategorie WHERE id = ?", (kategorie_id,)).fetchone()[0]
        nr = nummern.naechste_kategorie_nr(conn, kategorie_id)
        conn.execute("""UPDATE produkt SET kategorie_id = ?, code_praefix = ?, kategorie_nr = ?,
                        etikett = CASE etikett WHEN 'gedruckt' THEN 'neu_drucken' ELSE etikett END
                        WHERE inventar_nr = ?""", (kategorie_id, praefix, nr, inventar_nr))
    else:
        # Code behalten: die alte Nummer bleibt, darf aber in der neuen Kategorie nicht doppelt vorkommen
        p = conn.execute("SELECT kategorie_nr FROM produkt WHERE inventar_nr = ?", (inventar_nr,)).fetchone()
        belegt = conn.execute("SELECT 1 FROM produkt WHERE kategorie_id = ? AND kategorie_nr = ?",
                              (kategorie_id, p["kategorie_nr"])).fetchone()
        if belegt:
            # Seltener Fall: gleiche Nummer schon vergeben → neuer Code ist unvermeidbar
            kategorie_wechseln(conn, inventar_nr, kategorie_id, neuer_code=True)
            return
        conn.execute("UPDATE produkt SET kategorie_id = ? WHERE inventar_nr = ?", (kategorie_id, inventar_nr))
    conn.execute("""DELETE FROM produkt_wert WHERE produkt_id = ?
                    AND filter_id NOT IN (SELECT id FROM filter WHERE kategorie_id = ?)""", (inventar_nr, kategorie_id))


def _nebendaten(conn: sqlite3.Connection, inv: int, kategorie_id: int, daten: dict[str, Any]) -> None:
    if "farben" in daten:
        farben = list(dict.fromkeys(daten.get("farben") or []))
        if any(f not in FARBEN for f in farben):
            raise Fehler(t("fehler.farbe"), "farben")
        conn.execute("DELETE FROM produkt_farbe WHERE produkt_id = ?", (inv,))
        conn.executemany("INSERT INTO produkt_farbe (produkt_id, farbe) VALUES (?, ?)", [(inv, f) for f in farben])
    if "preis" in daten:
        _preis_speichern(conn, inv, daten.get("preis"))
    if "werte" in daten:
        werte_speichern(conn, inv, kategorie_id, daten.get("werte") or {})


def _preis_speichern(conn: sqlite3.Connection, inv: int, preis: dict[str, Any] | None) -> None:
    """Datum wird heute, sobald sich Betrag oder Einheit ändert (SPEC 6.2)."""
    if not preis or str(preis.get("betrag") or "").strip() == "":
        conn.execute("DELETE FROM preis WHERE produkt_id = ?", (inv,))
        return
    cent = preis_lesen(preis["betrag"])
    einheit = preis.get("einheit")
    if einheit not in PREIS_EINHEITEN:
        raise Fehler(t("fehler.preis_einheit"), "preis")
    alt = conn.execute("SELECT cent, einheit FROM preis WHERE produkt_id = ?", (inv,)).fetchone()
    if alt and (alt["cent"], alt["einheit"]) == (cent, einheit):
        return
    conn.execute("""INSERT INTO preis (produkt_id, cent, einheit, datum) VALUES (?, ?, ?, ?)
                    ON CONFLICT (produkt_id) DO UPDATE SET cent = excluded.cent, einheit = excluded.einheit,
                    datum = excluded.datum""", (inv, cent, einheit, zeit.heute().isoformat()))


def werte_speichern(conn: sqlite3.Connection, inv: int, kategorie_id: int, werte: dict[str, Any]) -> None:
    """Ersetzt die Filterwerte. Leere Angaben (None, "", []) bedeuten „kein Wert“."""
    filter_ = {r["id"]: r for r in conn.execute("SELECT id, name, typ FROM filter WHERE kategorie_id = ?", (kategorie_id,))}
    zeilen = []
    for key, wert in werte.items():
        if wert in (None, "", []):
            continue
        try:
            f = filter_[int(key)]
        except (KeyError, ValueError):
            raise Fehler(t("fehler.wert_filter"), "werte") from None
        if f["typ"] == "mass":
            try:
                zahl = float(str(wert).replace(",", "."))
            except ValueError:
                raise Fehler(t("fehler.wert_zahl", name=f["name"]), "werte") from None
            zeilen.append((inv, f["id"], None, zahl, None))
        elif f["typ"] == "janein":
            zeilen.append((inv, f["id"], None, None, 1 if wert in (True, 1, "1", "ja") else 0))
        else:
            ids = wert if isinstance(wert, list) else [wert]
            if f["typ"] == "einfach" and len(ids) > 1:
                raise Fehler(t("fehler.wert_einfach", name=f["name"]), "werte")
            erlaubt = {r[0] for r in conn.execute("SELECT id FROM filter_option WHERE filter_id = ?", (f["id"],))}
            for oid in dict.fromkeys(ids):
                if oid not in erlaubt:
                    raise Fehler(t("fehler.wert_auswahl", name=f["name"]), "werte")
                zeilen.append((inv, f["id"], oid, None, None))
    conn.execute("DELETE FROM produkt_wert WHERE produkt_id = ?", (inv,))
    conn.executemany("INSERT INTO produkt_wert (produkt_id, filter_id, option_id, zahl, janein) VALUES (?, ?, ?, ?, ?)", zeilen)


def suchtext_erneuern(conn: sqlite3.Connection, inv: int) -> None:
    """Name, Marke, Code, Inventarnummer, Kategorie, Maße und Filterwerte (z. B. „R11“) – SPEC 6.1."""
    p = conn.execute("""SELECT p.*, k.name AS kategorie FROM produkt p JOIN kategorie k ON k.id = p.kategorie_id
                        WHERE p.inventar_nr = ?""", (inv,)).fetchone()
    teile = [p["name"], p["marke"], p["abmessungen"], p["kategorie"],
             nummern.code(p["code_praefix"], p["kategorie_nr"], p["inventar_nr"]), str(p["inventar_nr"])]
    teile += [r[0] for r in conn.execute("""SELECT o.name FROM produkt_wert w JOIN filter_option o ON o.id = w.option_id
                                            WHERE w.produkt_id = ?""", (inv,))]
    conn.execute("UPDATE produkt SET suchtext = ? WHERE inventar_nr = ?",
                 (normalisieren(" ".join(x for x in teile if x)), inv))


def loeschen(conn: sqlite3.Connection, inventar_nr: int) -> list[str]:
    """Löscht das Produkt mit Werten, Preis und Fotos; liefert die Fotodateien, die der Aufrufer entfernt."""
    if conn.execute("SELECT 1 FROM produkt WHERE inventar_nr = ?", (inventar_nr,)).fetchone() is None:
        raise Fehler(t("fehler.produkt_unbekannt"), status=404)
    dateien = [r[0] for r in conn.execute("SELECT datei FROM foto WHERE produkt_id = ?", (inventar_nr,))]
    conn.execute("DELETE FROM produkt WHERE inventar_nr = ?", (inventar_nr,))
    return dateien
