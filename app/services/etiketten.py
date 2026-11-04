"""Produktetiketten (SPEC 6.6): Name, QR und Code – nie der Ort. Der QR trägt nur den bleibenden Link /p/<Nr>.

Das Raster kommt aus app/etikett_bogen.json (Etikettenpapier); bei anderem Papier ändert sich nur diese Datei.
Etiketten sind immer hell (SPEC 4.3).
"""
from __future__ import annotations

import io
import json
import sqlite3
import threading
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


# Papier: A4-Bogen (D-033) oder 38-mm-Rolle für den Brother QL-570, ein Etikett je Seite (D-035)
FORMATE = {"a4": "etikett_bogen.json", "rolle": "etikett_rolle.json"}


@lru_cache
def bogen(format: str = "a4") -> dict[str, Any]:
    if format not in FORMATE:
        raise Fehler(t("fehler.etikett_format"), "format")
    return json.loads((BASE_DIR / FORMATE[format]).read_text(encoding="utf-8"))


@lru_cache
def _schriften() -> None:
    ordner = BASE_DIR / "assets" / "fonts"
    pdfmetrics.registerFont(TTFont("Figtree", ordner / "Figtree-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("Figtree-SemiBold", ordner / "Figtree-SemiBold.ttf"))
    pdfmetrics.registerFont(TTFont("PlexMono", ordner / "IBMPlexMono-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("Comfortaa-SemiBold", ordner / "Comfortaa-SemiBold.ttf"))


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


def pdf(conn: sqlite3.Connection, ids: list[int], basis_url: str, format: str = "a4") -> bytes:
    """Bögen oder Rollenseiten nach der Papierdefinition, Etiketten in der gewählten Reihenfolge."""
    b = bogen(format)
    eintraege = [inhalt(conn, p["inventar_nr"]) for p in _produkte(conn, ids)]
    return _boegen(eintraege, lambda c, x, y, w, h, d: _etikett(c, x, y, w, h, d, basis_url), b)


def _boegen(eintraege: list, zeichnen, b: dict[str, Any]) -> bytes:
    """Gemeinsames Raster für Produkt- und Fach-Etiketten; auf der Rolle ist jede Seite ein Etikett."""
    _schriften()
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


# Aufbau nach der Vorlage „QR Code Sticker Paper.pdf“ (D-033), zentriert mit sicherem Rand (D-034); Maße in mm.
# Waagerecht: Rand | „miaza“ | QR | Text | Rand – der Block füllt das Etikett zwischen den Rändern.
# Senkrecht: der QR steht in der Mitte; der Text läuft von seiner Ober- bis zu seiner Unterkante.
RAND = 3.0                                        # gedachter Sicherheitsrand rundum
QR_SEITE = 26.0
# „miaza“ so lang wie ~70 % der QR-Höhe; Comfortaa SemiBold: Schriftbild 2,98 pt breit und 0,768 pt hoch je pt Größe
MARKE_PT = QR_SEITE * 0.70 / 25.4 * 72 / 2.98
MARKE_BREITE = MARKE_PT * 0.768 / 72 * 25.4
QR_LINKS = RAND + MARKE_BREITE + 2.0              # mindestens 2 mm frei neben dem QR (Ruhezone)
TEXT_LINKS, TEXT_RAND_RECHTS = QR_LINKS + QR_SEITE + 2.5, RAND
# Grundlinien ab der Oberkante des QR
NAME_GRUNDLINIEN = (3.3, 8.6)                     # zwei Zeilen Produktname, die erste bündig mit der QR-Oberkante
INFO_GRUNDLINIE, INFO_ABSTAND = 12.9, 2.25        # Marke, Artikelnummer, Maße, Merkmale
CODE_GRUNDLINIE = QR_SEITE                        # bündig mit der QR-Unterkante
NAME_PT, NAME_MIN_PT, INFO_PT, CODE_PT = 13.5, 9, 6, 9.5


def _qr_oben(oben: float, h: float) -> float:
    """Oberkante des QR: senkrecht mittig im Etikett."""
    return oben - (h - QR_SEITE * mm) / 2


def _marke(c: canvas.Canvas, x: float, y: float, h: float) -> None:
    """„miaza“ hochkant am linken Rand, von unten nach oben zu lesen, senkrecht mittig (D-034)."""
    c.saveState()
    c.setFillColor(black)
    c.setFont("Comfortaa-SemiBold", MARKE_PT)
    # Nach der Drehung um 90° liegt die Grundlinie senkrecht, die Buchstaben ragen nach links: Grundlinie also am
    # rechten Rand des Streifens, damit das Schriftbild genau zwischen RAND und RAND + MARKE_BREITE liegt.
    c.translate(x + (RAND + MARKE_BREITE) * mm, y + h / 2)
    c.rotate(90)
    c.drawCentredString(0, 0, "miaza")
    c.restoreState()


_PDFIUM = threading.Lock()


def _als_bild(zeichnen, eintrag: Any, format: str = "a4") -> bytes:
    """Ein Etikett allein als PNG, gezeichnet wie im PDF: die Vorschau zeigt genau, was gedruckt wird."""
    _schriften()
    b = bogen(format)
    w, h = b["breite_mm"] * mm, b["hoehe_mm"] * mm
    puffer = io.BytesIO()
    c = canvas.Canvas(puffer, pagesize=(w, h))
    zeichnen(c, 0, 0, w, h, eintrag)
    c.save()
    aus = io.BytesIO()
    # pdfium ist nicht threadsicher; die Vorschaubilder kommen aber gleichzeitig (ein Request je Etikett)
    with _PDFIUM:
        seite = pdfium.PdfDocument(puffer.getvalue())[0]
        bild = seite.render(scale=4).to_pil()
    bild.save(aus, "PNG", optimize=True)
    return aus.getvalue()


def vorschau(conn: sqlite3.Connection, inventar_nr: int, basis_url: str, format: str = "a4") -> bytes:
    return _als_bild(lambda c, x, y, w, h, d: _etikett(c, x, y, w, h, d, basis_url), inhalt(conn, inventar_nr), format)


def fach_vorschau(conn: sqlite3.Connection, fach_id: int, basis_url: str, format: str = "a4") -> bytes:
    return _als_bild(_fach_zeichnen(basis_url), _faecher(conn, [fach_id])[0], format)


def _qr(c: canvas.Canvas, inhalt: str, x: float, qr_oben: float) -> None:
    """QR als Vektor (scharf auf jedem Drucker); qr_oben = seine Oberkante."""
    matrix = list(segno.make(inhalt, error="m").matrix_iter(border=0))
    seite = QR_SEITE * mm
    modul = seite / len(matrix)
    qx, qy = x + QR_LINKS * mm, qr_oben - seite
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


def _info_zeilen(info: list[str], breite: float, max_zeilen: int = 4) -> list[str]:
    """Angaben auf höchstens max_zeilen Zeilen. Merkmale („10 cm | 30 cm | …“) brechen an den Trennstrichen um;
    was dann noch nicht passt, endet mit „…“."""
    zeilen: list[str] = []
    for text in info:
        zeile = ""
        for teil in text.split(" | "):
            probe = f"{zeile} | {teil}" if zeile else teil
            if zeile and pdfmetrics.stringWidth(probe, "Figtree", INFO_PT) > breite:
                zeilen.append(zeile)
                zeile = teil
            else:
                zeile = probe
        zeilen.append(zeile)
    if len(zeilen) > max_zeilen:
        zeilen = zeilen[:max_zeilen]
        zeilen[-1] += " …"
    return [_passend(z, "Figtree", INFO_PT, breite) for z in zeilen]


def _im_raster(c: canvas.Canvas, x: float, y: float, w: float, h: float, qr_inhalt: str,
               teile: list[tuple], linien: list[tuple[float, float, float, float]] = ()) -> None:
    """Zeichnet „miaza“, QR und Textzeilen im festen Raster innerhalb des Sicherheitsrands (D-034).

    Das Raster füllt den Bereich zwischen den Rändern und ist auf jedem Etikett gleich; senkrecht steht der QR mittig.
    teile: (Schrift, Größe in pt, Grundlinie in mm ab QR-Oberkante, Text[, linker Rand in mm ab Etikettkante]).
    linien: (x1, y1, x2, y2) in mm; x ab Etikettkante, y ab QR-Oberkante.
    """
    oben = _qr_oben(y + h, h)
    _marke(c, x, y, h)
    _qr(c, qr_inhalt, x, oben)
    c.setFillColor(black)
    for schrift, g, grund, text, *links in teile:
        c.setFont(schrift, g)
        c.drawString(x + (links[0] if links else TEXT_LINKS) * mm, oben - grund * mm, text)
    if linien:
        c.setStrokeColor(black)
        c.setLineWidth(0.5)
        c.setLineCap(1)
        for x1, y1, x2, y2 in linien:
            c.line(x + x1 * mm, oben - y1 * mm, x + x2 * mm, oben - y2 * mm)


def _spalte(w: float) -> float:
    """Größte Breite der Textspalte (wenn der Block das Etikett zwischen den Rändern füllt)."""
    return w - (TEXT_LINKS + TEXT_RAND_RECHTS) * mm


def _etikett(c: canvas.Canvas, x: float, y: float, w: float, h: float, d: dict[str, Any], basis_url: str) -> None:
    breite = _spalte(w)
    # Name: groß und fett in Versalien, zwei Zeilen; passt er nicht, wird er kleiner, zuletzt gekürzt
    name = d["name"].upper()
    groesse = NAME_PT

    def passt(g: float) -> bool:          # höchstens zwei Zeilen, keine Zeile (langes Wort) breiter als die Spalte
        zeilen = _umbrechen(name, "Figtree-SemiBold", g, breite, max_zeilen=9)
        return len(zeilen) <= 2 and all(pdfmetrics.stringWidth(z, "Figtree-SemiBold", g) <= breite for z in zeilen)
    while groesse > NAME_MIN_PT and not passt(groesse):
        groesse -= 0.5
    teile = [("Figtree-SemiBold", groesse, grund, _passend(zeile, "Figtree-SemiBold", groesse, breite))
             for zeile, grund in zip(_umbrechen(name, "Figtree-SemiBold", groesse, breite), NAME_GRUNDLINIEN)]
    # Marke, Artikelnummer, Maße, Merkmale – leere Zeilen entfallen; zu lange laufen in die freien Zeilen weiter
    teile += [("Figtree", INFO_PT, INFO_GRUNDLINIE + i * INFO_ABSTAND, zeile)
              for i, zeile in enumerate(_info_zeilen([z.upper() for z in d["info"]], breite))]
    teile.append(("Figtree", CODE_PT, CODE_GRUNDLINIE, d["code"]))
    # nur der bleibende Link mit der Inventarnummer
    _im_raster(c, x, y, w, h, f"{basis_url.rstrip('/')}/p/{d['inventar_nr']}", teile)


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
    p = plan.laden(conn)
    raum_name = {r["id"]: r["name"] or "" for r in p["raeume"]}
    for e in p["einheiten"]:
        for f in e["faecher"]:
            # Liste: Name des Fachs, sonst der Einheit (D-020); das Etikett zeigt Raum, Einheit, Fach untereinander (D-036)
            alle.append({"id": f["id"], "code": f["code"], "beschreibung": f["name"] or e["name"], "etikett": f["etikett"],
                         "orte": [raum_name.get(e["raum_id"], ""), e["name"] or "", f["name"] or ""]})
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


def fach_pdf(conn: sqlite3.Connection, ids: list[int], basis_url: str, format: str = "a4") -> bytes:
    """Gleicher Aufbau wie das Produktetikett (D-033): QR links, rechts groß der Fachcode, darunter Name."""
    b = bogen(format)
    return _boegen(_faecher(conn, ids), _fach_zeichnen(basis_url), b)


# Ortsangaben auf dem Fach-Etikett (D-036, D-037), Maße in mm
ORT_PT, ORT_EIN_ZEILE_MIN_PT, ORT_MIN_PT = 10, 7.5, 6.5
ORT_LUECKE = 2.2          # unter dem Code
ORT_EINZUG = 3.2          # Einheit und Fach stehen rechts der Baumlinie
ORT_ZEILE, ORT_GRUPPE = 1.18, 0.45     # Zeilenabstand und Zusatzabstand zwischen den Angaben, je Schriftgröße
VERSAL = 0.7              # Versalhöhe je Schriftgröße (Figtree, Plex Mono)


def _ort_satz(namen: list[str], breite: float, hoehe: float) -> tuple[float, list[list[str]]]:
    """Größte Schrift, bei der Raum, Einheit, Fach in die Höhe passen. Erst einzeilig (bis ORT_EIN_ZEILE_MIN_PT), dann mit
    Umbruch auf höchstens zwei Zeilen je Angabe (bis ORT_MIN_PT); erst danach „…“ (D-037).
    breite in pt, hoehe in mm (von der Oberkante der ersten bis zur Grundlinie der letzten Zeile)."""
    def spalte(i: int) -> float:
        return breite - (ORT_EINZUG * mm if i else 0)

    def satz(g: float, max_zeilen: int) -> list[list[str]] | None:
        zeilen = [_umbrechen(n, "Figtree", g, spalte(i), max_zeilen=9) for i, n in enumerate(namen)]
        if any(len(z) > max_zeilen or any(pdfmetrics.stringWidth(t_, "Figtree", g) > spalte(i) for t_ in z)
               for i, z in enumerate(zeilen)):
            return None
        g_mm = g / 72 * 25.4
        noetig = g_mm * (VERSAL + ORT_ZEILE * (sum(map(len, zeilen)) - 1) + ORT_GRUPPE * (len(zeilen) - 1))
        return zeilen if noetig <= hoehe else None

    for max_zeilen, kleinste in ((1, ORT_EIN_ZEILE_MIN_PT), (2, ORT_MIN_PT)):
        g = ORT_PT
        while g >= kleinste:
            if (zeilen := satz(g, max_zeilen)) is not None:
                return g, zeilen
            g -= 0.5
    # Notfall: kleinste Schrift, je Angabe zwei Zeilen, der Rest mit „…“
    return ORT_MIN_PT, [[_passend(z, "Figtree", ORT_MIN_PT, spalte(i)) for z in _umbrechen(n, "Figtree", ORT_MIN_PT, spalte(i))]
                        for i, n in enumerate(namen)]


def _fach_zeichnen(basis_url: str):
    def zeichnen(c: canvas.Canvas, x: float, y: float, w: float, h: float, f: dict[str, Any]) -> None:
        breite = _spalte(w)
        # Der Code ist das, was man im Regal liest: groß
        groesse = 22
        while groesse > 10 and pdfmetrics.stringWidth(f["code"], "PlexMono", groesse) > breite:
            groesse -= 1
        # Oberkante der Ziffern bündig mit der QR-Oberkante, wie der Produktname
        code_grund = groesse * VERSAL / 72 * 25.4
        teile: list[tuple] = [("PlexMono", groesse, code_grund, f["code"])]
        linien: list[tuple[float, float, float, float]] = []
        namen = [n.strip() for n in f["orte"] if n.strip()]
        if namen:
            # Raum, Einheit, Fach füllen den Platz zwischen Code und QR-Unterkante; die letzte Zeile schließt mit ihr ab
            oben_frei = code_grund + ORT_LUECKE
            g, saetze = _ort_satz(namen, breite, QR_SEITE - oben_frei)
            g_mm = g / 72 * 25.4
            zeile, gruppe = ORT_ZEILE * g_mm, ORT_GRUPPE * g_mm
            noetig = g_mm * VERSAL + zeile * (sum(map(len, saetze)) - 1) + gruppe * (len(saetze) - 1)
            # Übriger Platz verteilt sich gleich auf den Abstand unter dem Code und die Abstände zwischen den Angaben
            # (je höchstens 1,2 Schriftgrößen); was dann noch frei ist, bleibt unten
            extra = min((QR_SEITE - oben_frei - noetig) / len(saetze), g_mm * 1.2)
            gruppe += extra
            grund = oben_frei + extra + g_mm * VERSAL
            ast_x = TEXT_LINKS + 0.9
            mitte = g_mm * VERSAL / 2           # halbe Versalhöhe: dort setzt der Ast an
            stamm_oben = None
            for i, saetze_i in enumerate(saetze):
                links = TEXT_LINKS + (ORT_EINZUG if i else 0)
                if i == 0:
                    stamm_oben = grund + g_mm * 0.35 + zeile * (len(saetze_i) - 1)
                else:
                    linien.append((ast_x, grund - mitte, links - 0.8, grund - mitte))     # Ast (└)
                    stamm_unten = grund - mitte
                for z in saetze_i:
                    teile.append(("Figtree", g, grund, z, links))
                    grund += zeile
                grund += gruppe                        # zwischen den Angaben: Zeilen- plus Gruppenabstand
            if len(saetze) > 1:
                linien.append((ast_x, stamm_oben, ast_x, stamm_unten))                   # Stamm
        _im_raster(c, x, y, w, h, f"{basis_url.rstrip('/')}/f/{f['id']}", teile, linien)
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
