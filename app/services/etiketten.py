"""Produktetiketten (SPEC 6.6): Name, QR und Code – nie der Ort. Der QR trägt nur den bleibenden Link /p/<Nr>.

Das Raster kommt aus app/etikett_bogen.json (Etikettenpapier); bei anderem Papier ändert sich nur diese Datei.
Etiketten sind immer hell (SPEC 4.3).
"""
from __future__ import annotations

import io
import json
import sqlite3
from functools import lru_cache
from typing import Any

import pypdfium2 as pdfium
import segno
from reportlab.lib.colors import black
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from ..config import BASE_DIR
from ..fehler import Fehler
from ..texte import t
from . import nummern
from .suche import normalisieren

ZUSTAENDE = ("ungedruckt", "gedruckt", "neu_drucken")


@lru_cache
def bogen() -> dict[str, Any]:
    return json.loads((BASE_DIR / "etikett_bogen.json").read_text(encoding="utf-8"))


@lru_cache
def _schriften() -> None:
    ordner = BASE_DIR / "assets" / "fonts"
    pdfmetrics.registerFont(TTFont("Figtree", ordner / "Figtree-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("Figtree-SemiBold", ordner / "Figtree-SemiBold.ttf"))
    pdfmetrics.registerFont(TTFont("PlexMono", ordner / "IBMPlexMono-Regular.ttf"))


def liste(conn: sqlite3.Connection, q: str = "", zustand: str | None = None) -> list[dict[str, Any]]:
    """Physische Produkte für die Etikettenseite; digitale haben kein Etikett."""
    wo, args = ["p.art = 'physisch'"], []
    for wort in normalisieren(q).split():
        wo.append("instr(p.suchtext, ?) > 0")
        args.append(wort)
    if zustand in ZUSTAENDE:
        wo.append("p.etikett = ?")
        args.append(zustand)
    zeilen = conn.execute(f"""SELECT p.inventar_nr, p.code_praefix, p.kategorie_nr, p.name, p.etikett FROM produkt p
                              WHERE {' AND '.join(wo)} ORDER BY p.inventar_nr DESC""", args).fetchall()
    return [{"inventar_nr": z["inventar_nr"], "code": nummern.code(z["code_praefix"], z["kategorie_nr"], z["inventar_nr"]),
             "name": z["name"], "etikett": z["etikett"], "info": inhalt(conn, z["inventar_nr"])["info"]} for z in zeilen]


def zahlen(conn: sqlite3.Connection) -> dict[str, int]:
    return {z: conn.execute("SELECT count(*) FROM produkt WHERE art = 'physisch' AND etikett = ?", (z,)).fetchone()[0]
            for z in ("ungedruckt", "neu_drucken")}


def _produkte(conn: sqlite3.Connection, ids: list[int]) -> list[sqlite3.Row]:
    if not ids:
        raise Fehler(t("fehler.sammel_leer"), "produkte")
    zeilen = {z["inventar_nr"]: z for z in conn.execute(
        f"SELECT inventar_nr, code_praefix, kategorie_nr, name, etikett FROM produkt WHERE inventar_nr IN ({','.join('?' * len(ids))})", ids)}
    if len(zeilen) != len(set(ids)):
        raise Fehler(t("fehler.produkt_unbekannt"), "produkte", status=404)
    return [zeilen[i] for i in dict.fromkeys(ids)]      # Reihenfolge der Auswahl


def pdf(conn: sqlite3.Connection, ids: list[int], basis_url: str) -> bytes:
    """A4-Bögen nach der Bogendefinition, Etiketten in der gewählten Reihenfolge."""
    eintraege = [inhalt(conn, p["inventar_nr"]) for p in _produkte(conn, ids)]
    return _boegen(eintraege, lambda c, x, y, w, h, d: _etikett(c, x, y, w, h, d, basis_url))


def _boegen(eintraege: list, zeichnen) -> bytes:
    """Gemeinsames Raster für Produkt- und Fach-Etiketten."""
    _schriften()
    b = bogen()
    puffer = io.BytesIO()
    c = canvas.Canvas(puffer, pagesize=(b["seite_breite_mm"] * mm, b["seite_hoehe_mm"] * mm))
    c.setTitle("miaza finds – Etiketten")
    je_bogen = b["spalten"] * b["zeilen"]
    for i, p in enumerate(eintraege):
        if i and i % je_bogen == 0:
            c.showPage()
        platz = i % je_bogen
        spalte, zeile = platz % b["spalten"], platz // b["spalten"]
        x = (b["rand_links_mm"] + spalte * (b["breite_mm"] + b["abstand_x_mm"])) * mm
        # PDF zählt von unten; Zeile 0 ist oben
        y = (b["seite_hoehe_mm"] - b["rand_oben_mm"] - (zeile + 1) * b["hoehe_mm"] - zeile * b["abstand_y_mm"]) * mm
        zeichnen(c, x, y, b["breite_mm"] * mm, b["hoehe_mm"] * mm, p)
    c.save()
    return puffer.getvalue()


# Maße aus der Vorlage „QR Code Sticker Paper.pdf“ (D-033), gemessen ab der linken oberen Ecke des Etiketts, in mm
QR_LINKS, QR_OBEN, QR_SEITE = 4.9, 5.2, 29.6
TEXT_LINKS, TEXT_RAND_RECHTS = 38.5, 2.5
NAME_GRUNDLINIEN = (8.6, 14.4)                    # zwei Zeilen Produktname
INFO_GRUNDLINIE, INFO_ABSTAND = 19.6, 2.47        # Marke, Artikelnummer, Maße, Merkmale
CODE_GRUNDLINIE = 35.0
NAME_PT, NAME_MIN_PT, INFO_PT, CODE_PT = 13.5, 9, 6, 9.5


def _als_bild(zeichnen, eintrag: Any) -> bytes:
    """Ein Etikett allein als PNG, gezeichnet wie im PDF: die Vorschau zeigt genau, was gedruckt wird."""
    _schriften()
    b = bogen()
    w, h = b["breite_mm"] * mm, b["hoehe_mm"] * mm
    puffer = io.BytesIO()
    c = canvas.Canvas(puffer, pagesize=(w, h))
    zeichnen(c, 0, 0, w, h, eintrag)
    c.save()
    seite = pdfium.PdfDocument(puffer.getvalue())[0]
    aus = io.BytesIO()
    seite.render(scale=4).to_pil().save(aus, "PNG", optimize=True)
    return aus.getvalue()


def vorschau(conn: sqlite3.Connection, inventar_nr: int, basis_url: str) -> bytes:
    return _als_bild(lambda c, x, y, w, h, d: _etikett(c, x, y, w, h, d, basis_url), inhalt(conn, inventar_nr))


def fach_vorschau(conn: sqlite3.Connection, fach_id: int, basis_url: str) -> bytes:
    return _als_bild(_fach_zeichnen(basis_url), _faecher(conn, [fach_id])[0])


def _qr(c: canvas.Canvas, inhalt: str, x: float, oben: float) -> None:
    """QR als Vektor (scharf auf jedem Drucker) links im Etikett; oben = Oberkante des Etiketts."""
    matrix = list(segno.make(inhalt, error="m").matrix_iter(border=0))
    seite = QR_SEITE * mm
    modul = seite / len(matrix)
    qx, qy = x + QR_LINKS * mm, oben - QR_OBEN * mm - seite
    c.setFillColor(black)
    for r, reihe in enumerate(matrix):
        for s, an in enumerate(reihe):
            if an:
                c.rect(qx + s * modul, qy + seite - (r + 1) * modul, modul, modul, stroke=0, fill=1)


def _merkmale(conn: sqlite3.Connection, inventar_nr: int, kategorie_id: int) -> str:
    """Filterwerte für das Etikett, in der Reihenfolge der Filter, mit „ | “ getrennt: WANDFLISE | R9."""
    teile = []
    for f in conn.execute("SELECT id, name, typ, einheit FROM filter WHERE kategorie_id = ? ORDER BY sortierung, id", (kategorie_id,)):
        for z in conn.execute("""SELECT w.zahl, w.janein, o.name FROM produkt_wert w LEFT JOIN filter_option o ON o.id = w.option_id
                                 WHERE w.produkt_id = ? AND w.filter_id = ? ORDER BY o.sortierung""", (inventar_nr, f["id"])):
            if f["typ"] == "mass" and z["zahl"] is not None:
                teile.append(f"{z['zahl']:g}".replace(".", ",") + f" {f['einheit']}")
            elif f["typ"] == "janein":
                if z["janein"]:
                    teile.append(f["name"])            # „Rektifiziert“ steht da, wenn es zutrifft
            elif z["name"]:
                teile.append(z["name"])
    return " | ".join(teile)


def inhalt(conn: sqlite3.Connection, inventar_nr: int) -> dict[str, Any]:
    """Was auf dem Produktetikett steht (D-033); auch für die Vorschau und für „neu drucken“."""
    p = conn.execute("""SELECT inventar_nr, code_praefix, kategorie_nr, kategorie_id, name, marke, artikelnummer, abmessungen
                        FROM produkt WHERE inventar_nr = ?""", (inventar_nr,)).fetchone()
    if p is None:
        raise Fehler(t("fehler.produkt_unbekannt"), "produkte", status=404)
    info = [p["marke"], p["artikelnummer"], p["abmessungen"], _merkmale(conn, inventar_nr, p["kategorie_id"])]
    return {"inventar_nr": p["inventar_nr"], "name": p["name"] or t("produkt.unbenannt", nr=p["inventar_nr"]),
            "info": [x for x in info if x], "code": nummern.code(p["code_praefix"], p["kategorie_nr"], p["inventar_nr"])}


def _passend(text: str, schrift: str, groesse: float, breite: float) -> str:
    """Eine Zeile, notfalls mit „…“ gekürzt."""
    if pdfmetrics.stringWidth(text, schrift, groesse) <= breite:
        return text
    while text and pdfmetrics.stringWidth(text + "…", schrift, groesse) > breite:
        text = text[:-1]
    return text.rstrip() + "…"


def _etikett(c: canvas.Canvas, x: float, y: float, w: float, h: float, d: dict[str, Any], basis_url: str) -> None:
    oben = y + h
    # nur der bleibende Link mit der Inventarnummer
    _qr(c, f"{basis_url.rstrip('/')}/p/{d['inventar_nr']}", x, oben)
    tx, breite = x + TEXT_LINKS * mm, w - (TEXT_LINKS + TEXT_RAND_RECHTS) * mm
    c.setFillColor(black)
    # Name: groß und fett in Versalien, zwei Zeilen; passt er nicht, wird er kleiner, zuletzt gekürzt
    name = d["name"].upper()
    groesse = NAME_PT

    def passt(g: float) -> bool:          # höchstens zwei Zeilen, keine Zeile (langes Wort) breiter als die Spalte
        zeilen = _umbrechen(name, "Figtree-SemiBold", g, breite, max_zeilen=9)
        return len(zeilen) <= 2 and all(pdfmetrics.stringWidth(z, "Figtree-SemiBold", g) <= breite for z in zeilen)
    while groesse > NAME_MIN_PT and not passt(groesse):
        groesse -= 0.5
    c.setFont("Figtree-SemiBold", groesse)
    for zeile, grund in zip(_umbrechen(name, "Figtree-SemiBold", groesse, breite), NAME_GRUNDLINIEN):
        c.drawString(tx, oben - grund * mm, _passend(zeile, "Figtree-SemiBold", groesse, breite))
    # Marke, Artikelnummer, Maße, Merkmale – leere Zeilen entfallen
    c.setFont("Figtree", INFO_PT)
    for i, zeile in enumerate(d["info"][:4]):
        c.drawString(tx, oben - (INFO_GRUNDLINIE + i * INFO_ABSTAND) * mm, _passend(zeile.upper(), "Figtree", INFO_PT, breite))
    c.setFont("Figtree", CODE_PT)
    c.drawString(tx, oben - CODE_GRUNDLINIE * mm, d["code"])


def _umbrechen(text: str, schrift: str, groesse: float, breite: float, max_zeilen: int = 2) -> list[str]:
    worte, zeilen, zeile = text.split(), [], ""
    for wort in worte:
        probe = f"{zeile} {wort}".strip()
        if pdfmetrics.stringWidth(probe, schrift, groesse) <= breite:
            zeile = probe
        else:
            if zeile:
                zeilen.append(zeile)
            zeile = wort
    if zeile:
        zeilen.append(zeile)
    if len(zeilen) > max_zeilen:
        zeilen = zeilen[:max_zeilen]
        letzte = zeilen[-1]
        while letzte and pdfmetrics.stringWidth(letzte + " …", schrift, groesse) > breite:
            letzte = letzte[:-1]
        zeilen[-1] = letzte.rstrip() + " …"
    return zeilen


def als_gedruckt(conn: sqlite3.Connection, ids: list[int]) -> list[dict[str, Any]]:
    """Markiert als gedruckt; liefert den vorherigen Zustand für „Rückgängig“."""
    vorher = [{"inventar_nr": p["inventar_nr"], "etikett": p["etikett"]} for p in _produkte(conn, ids)]
    conn.executemany("UPDATE produkt SET etikett = 'gedruckt' WHERE inventar_nr = ?", [(v["inventar_nr"],) for v in vorher])
    return vorher


def zuruecksetzen(conn: sqlite3.Connection, vorher: list[dict[str, Any]]) -> int:
    n = 0
    for v in vorher:
        if v.get("etikett") in ZUSTAENDE and isinstance(v.get("inventar_nr"), int):
            n += conn.execute("UPDATE produkt SET etikett = ? WHERE inventar_nr = ? AND etikett = 'gedruckt'",
                              (v["etikett"], v["inventar_nr"])).rowcount
    return n


def auf_druckliste(conn: sqlite3.Connection, inventar_nr: int) -> str:
    """„Auf die Druckliste“ aus dem Produktdetail (SPEC 5): Gedrucktes wird „neu drucken“."""
    p = conn.execute("SELECT etikett FROM produkt WHERE inventar_nr = ?", (inventar_nr,)).fetchone()
    if p is None:
        raise Fehler(t("fehler.produkt_unbekannt"), status=404)
    if p["etikett"] == "gedruckt":
        conn.execute("UPDATE produkt SET etikett = 'neu_drucken' WHERE inventar_nr = ?", (inventar_nr,))
        return "neu_drucken"
    return p["etikett"]


# ---------- Fach-Etiketten (SPEC 6.6): QR mit der bleibenden Fach-Kennung, großer Code ----------

def _faecher_alle(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    from . import plan        # Plan kennt die Codes
    alle = []
    for e in plan.laden(conn)["einheiten"]:
        for f in e["faecher"]:
            # Unter dem Code: Name des Fachs, sonst der Einheit (D-020)
            alle.append({"id": f["id"], "code": f["code"], "beschreibung": f["name"] or e["name"], "etikett": f["etikett"]})
    return alle


def fach_liste(conn: sqlite3.Connection, q: str = "", zustand: str | None = None) -> list[dict[str, Any]]:
    worte = normalisieren(q).split()
    return [f for f in _faecher_alle(conn)
            if (zustand not in ZUSTAENDE or f["etikett"] == zustand)
            and all(w in normalisieren(f"{f['code']} {f['beschreibung']}") for w in worte)]


def fach_zahlen(conn: sqlite3.Connection) -> dict[str, int]:
    return {z: conn.execute("SELECT count(*) FROM fach WHERE etikett = ?", (z,)).fetchone()[0] for z in ("ungedruckt", "neu_drucken")}


def _faecher(conn: sqlite3.Connection, ids: list[int]) -> list[dict[str, Any]]:
    if not ids:
        raise Fehler(t("fehler.sammel_leer"), "faecher")
    alle = {f["id"]: f for f in _faecher_alle(conn)}
    if any(i not in alle for i in ids):
        raise Fehler(t("fehler.fach_unbekannt"), "faecher", status=404)
    return [alle[i] for i in dict.fromkeys(ids)]


def fach_pdf(conn: sqlite3.Connection, ids: list[int], basis_url: str) -> bytes:
    """Gleicher Aufbau wie das Produktetikett (D-033): QR links, rechts groß der Fachcode, darunter Name."""
    return _boegen(_faecher(conn, ids), _fach_zeichnen(basis_url))


def _fach_zeichnen(basis_url: str):
    def zeichnen(c: canvas.Canvas, x: float, y: float, w: float, h: float, f: dict[str, Any]) -> None:
        oben = y + h
        _qr(c, f"{basis_url.rstrip('/')}/f/{f['id']}", x, oben)
        tx, breite = x + TEXT_LINKS * mm, w - (TEXT_LINKS + TEXT_RAND_RECHTS) * mm
        # Der Code ist das, was man im Regal liest: groß
        groesse = 22
        while groesse > 10 and pdfmetrics.stringWidth(f["code"], "PlexMono", groesse) > breite:
            groesse -= 1
        c.setFillColor(black)
        c.setFont("PlexMono", groesse)
        c.drawString(tx, oben - 14.4 * mm, f["code"])
        if f["beschreibung"]:
            c.setFont("Figtree", 9)
            for i, zeile in enumerate(_umbrechen(f["beschreibung"], "Figtree", 9, breite)):
                c.drawString(tx, oben - (21 + i * 4) * mm, zeile)
    return zeichnen


def faecher_als_gedruckt(conn: sqlite3.Connection, ids: list[int]) -> list[dict[str, Any]]:
    vorher = [{"id": f["id"], "etikett": f["etikett"]} for f in _faecher(conn, ids)]
    conn.executemany("UPDATE fach SET etikett = 'gedruckt' WHERE id = ?", [(v["id"],) for v in vorher])
    return vorher


def faecher_zuruecksetzen(conn: sqlite3.Connection, vorher: list[dict[str, Any]]) -> int:
    n = 0
    for v in vorher:
        if v.get("etikett") in ZUSTAENDE and isinstance(v.get("id"), int):
            n += conn.execute("UPDATE fach SET etikett = ? WHERE id = ? AND etikett = 'gedruckt'", (v["etikett"], v["id"])).rowcount
    return n
