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
             "name": z["name"], "etikett": z["etikett"]} for z in zeilen]


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
    _schriften()
    b = bogen()
    produkte = _produkte(conn, ids)
    puffer = io.BytesIO()
    c = canvas.Canvas(puffer, pagesize=(b["seite_breite_mm"] * mm, b["seite_hoehe_mm"] * mm))
    c.setTitle("miaza finds – Etiketten")
    je_bogen = b["spalten"] * b["zeilen"]
    for i, p in enumerate(produkte):
        if i and i % je_bogen == 0:
            c.showPage()
        platz = i % je_bogen
        spalte, zeile = platz % b["spalten"], platz // b["spalten"]
        x = (b["rand_links_mm"] + spalte * (b["breite_mm"] + b["abstand_x_mm"])) * mm
        # PDF zählt von unten; Zeile 0 ist oben
        y = (b["seite_hoehe_mm"] - b["rand_oben_mm"] - (zeile + 1) * b["hoehe_mm"] - zeile * b["abstand_y_mm"]) * mm
        _etikett(c, x, y, b["breite_mm"] * mm, b["hoehe_mm"] * mm, p, basis_url)
    c.save()
    return puffer.getvalue()


def _etikett(c: canvas.Canvas, x: float, y: float, w: float, h: float, p: sqlite3.Row, basis_url: str) -> None:
    rand = 3 * mm
    code = nummern.code(p["code_praefix"], p["kategorie_nr"], p["inventar_nr"])
    name = p["name"] or t("produkt.unbenannt", nr=p["inventar_nr"])
    # QR als Vektor (scharf auf jedem Drucker); nur der bleibende Link mit der Inventarnummer
    qr = segno.make(f"{basis_url.rstrip('/')}/p/{p['inventar_nr']}", error="m")
    matrix = list(qr.matrix_iter(border=0))
    seite = min(w - 2 * rand, h * 0.54)
    modul = seite / len(matrix)
    qx, qy = x + (w - seite) / 2, y + h - rand - seite
    c.setFillColor(black)
    for r, reihe in enumerate(matrix):
        for s, an in enumerate(reihe):
            if an:
                c.rect(qx + s * modul, qy + seite - (r + 1) * modul, modul, modul, stroke=0, fill=1)
    # Name: höchstens zwei Zeilen, sonst gekürzt
    groesse = 8.5
    zeilen = _umbrechen(name, "Figtree-SemiBold", groesse, w - 2 * rand)
    # Ruhezone unter dem QR freihalten, sonst lesen manche Scanner schlecht
    text_y = qy - 6 * mm
    c.setFont("Figtree-SemiBold", groesse)
    for z in zeilen:
        c.drawCentredString(x + w / 2, text_y, z)
        text_y -= groesse * 1.2
    c.setFont("PlexMono", 8)
    c.drawCentredString(x + w / 2, y + rand, code)


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
