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
    return _boegen(_produkte(conn, ids), lambda c, x, y, w, h, p: _etikett(c, x, y, w, h, p, basis_url))


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


def _qr(c: canvas.Canvas, inhalt: str, x: float, y: float, w: float, h: float, rand: float) -> float:
    """QR als Vektor (scharf auf jedem Drucker), oben mittig; liefert die Unterkante."""
    matrix = list(segno.make(inhalt, error="m").matrix_iter(border=0))
    seite = min(w - 2 * rand, h * 0.54)
    modul = seite / len(matrix)
    qx, qy = x + (w - seite) / 2, y + h - rand - seite
    c.setFillColor(black)
    for r, reihe in enumerate(matrix):
        for s, an in enumerate(reihe):
            if an:
                c.rect(qx + s * modul, qy + seite - (r + 1) * modul, modul, modul, stroke=0, fill=1)
    return qy


def _etikett(c: canvas.Canvas, x: float, y: float, w: float, h: float, p: sqlite3.Row, basis_url: str) -> None:
    rand = 3 * mm
    code = nummern.code(p["code_praefix"], p["kategorie_nr"], p["inventar_nr"])
    name = p["name"] or t("produkt.unbenannt", nr=p["inventar_nr"])
    # nur der bleibende Link mit der Inventarnummer
    qy = _qr(c, f"{basis_url.rstrip('/')}/p/{p['inventar_nr']}", x, y, w, h, rand)
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
    def zeichnen(c: canvas.Canvas, x: float, y: float, w: float, h: float, f: dict[str, Any]) -> None:
        rand = 3 * mm
        qy = _qr(c, f"{basis_url.rstrip('/')}/f/{f['id']}", x, y, w, h, rand)
        # Der Code ist das, was man im Regal liest: groß
        groesse = 20
        while groesse > 10 and pdfmetrics.stringWidth(f["code"], "PlexMono", groesse) > w - 2 * rand:
            groesse -= 1
        c.setFont("PlexMono", groesse)
        c.drawCentredString(x + w / 2, qy - 5 * mm - groesse * 0.7, f["code"])
        if f["beschreibung"]:
            c.setFont("Figtree", 8)
            c.drawCentredString(x + w / 2, y + rand, _umbrechen(f["beschreibung"], "Figtree", 8, w - 2 * rand, 1)[0])
    return _boegen(_faecher(conn, ids), zeichnen)


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
