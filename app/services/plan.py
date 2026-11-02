"""Büroplan: Räume, Einheiten, Fächer (SPEC 6.4, 7). Der Plan wird als Entwurf im Ganzen gespeichert (SPEC 4.6);
die Versionsnummer verhindert stilles Überschreiben (SPEC 4.9). Fächer speichert der Fach-Editor je Einheit,
ebenfalls gegen die Planversion.

Codes: Raum.Einheit.Fach, z. B. 2.2.5. Ein Produkt hängt an der bleibenden Fach-Kennung; die Codes werden abgeleitet.
Alle schreibenden Funktionen laufen innerhalb einer Transaktion des Aufrufers.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from PIL import Image

from ..fehler import Fehler
from ..texte import t
from . import nummern
from .fotos import GROESSE_GROSS, MAX_BYTES, bild_oeffnen

NAME_MAX = 60
NR_MAX = 999
PUNKTE_MAX = 200
# Beim Umnummerieren erst alle Nummern aus dem Weg schieben, damit Tauschen nicht an UNIQUE scheitert
AUSWEICHEN = 100_000


# ---------- Lesen ----------

def code_einheit(raum_nr: int | None, nr: int) -> str:
    return f"{raum_nr if raum_nr is not None else '–'}.{nr}"


def laden(conn: sqlite3.Connection) -> dict[str, Any]:
    p = conn.execute("SELECT * FROM plan WHERE id = 1").fetchone()
    raeume = [{"id": r["id"], "nr": r["nr"], "name": r["name"], "punkte": json.loads(r["punkte"])}
              for r in conn.execute("SELECT * FROM raum ORDER BY nr")]
    raum_nr = {r["id"]: r["nr"] for r in raeume}
    produkte_je_fach = dict(conn.execute("SELECT fach_id, count(*) FROM produkt WHERE fach_id IS NOT NULL GROUP BY fach_id").fetchall())
    faecher: dict[int, list] = {}
    for f in conn.execute("SELECT * FROM fach ORDER BY nr"):
        faecher.setdefault(f["einheit_id"], []).append({
            "id": f["id"], "nr": f["nr"], "punkte": json.loads(f["punkte"]), "etikett": f["etikett"],
            "produkte": produkte_je_fach.get(f["id"], 0)})
    einheiten = []
    for e in conn.execute("SELECT * FROM einheit ORDER BY raum_id IS NULL, raum_id, nr"):
        code = code_einheit(raum_nr.get(e["raum_id"]), e["nr"])
        fs = faecher.get(e["id"], [])
        for f in fs:
            f["code"] = f"{code}.{f['nr']}"
        einheiten.append({
            "id": e["id"], "raum_id": e["raum_id"], "nr": e["nr"], "name": e["name"], "code": code,
            "punkte": json.loads(e["punkte"]), "foto": e["foto"], "foto_breite": e["foto_breite"],
            "foto_hoehe": e["foto_hoehe"], "faecher": fs, "produkte": sum(f["produkte"] for f in fs)})
    unterlage = None
    if p["unterlage"]:
        unterlage = {"datei": p["unterlage"], "breite": p["unterlage_breite"], "hoehe": p["unterlage_hoehe"],
                     "x": p["unterlage_x"], "y": p["unterlage_y"], "massstab": p["unterlage_massstab"],
                     "drehung": p["unterlage_drehung"]}
    return {"version": p["version"], "unterlage": unterlage, "unterlage_im_buero": bool(p["unterlage_im_buero"]),
            "raeume": raeume, "einheiten": einheiten,
            "ohne_platz": conn.execute("SELECT count(*) FROM produkt WHERE art = 'physisch' AND fach_id IS NULL").fetchone()[0]}


def fach(conn: sqlite3.Connection, fach_id: int) -> dict[str, Any] | None:
    """Ein Fach mit Einheit und Code (für Fach-Seite, Produktdetail, Etiketten)."""
    z = conn.execute("""
        SELECT f.id, f.nr, f.einheit_id, f.etikett, e.nr AS e_nr, e.name AS e_name, r.nr AS r_nr, r.name AS r_name
        FROM fach f JOIN einheit e ON e.id = f.einheit_id LEFT JOIN raum r ON r.id = e.raum_id
        WHERE f.id = ?""", (fach_id,)).fetchone()
    if z is None:
        return None
    einheit = code_einheit(z["r_nr"], z["e_nr"])
    return {"id": z["id"], "code": f"{einheit}.{z['nr']}", "einheit_id": z["einheit_id"], "einheit_code": einheit,
            "einheit_name": z["e_name"], "raum_name": z["r_name"] or "", "etikett": z["etikett"]}


def produkte_im_fach(conn: sqlite3.Connection, fach_id: int) -> list[dict[str, Any]]:
    return [{"inventar_nr": r["inventar_nr"], "name": r["name"], "foto": r["foto"],
             "code": nummern.code(r["code_praefix"], r["kategorie_nr"], r["inventar_nr"])}
            for r in conn.execute("""
        SELECT p.inventar_nr, p.name, p.code_praefix, p.kategorie_nr,
               (SELECT datei FROM foto WHERE produkt_id = p.inventar_nr ORDER BY sortierung LIMIT 1) AS foto
        FROM produkt p WHERE p.fach_id = ? ORDER BY p.name COLLATE NOCASE, p.inventar_nr""", (fach_id,))]


# ---------- Prüfen ----------

def _text(wert: Any, feld: str) -> str:
    text = " ".join(str(wert or "").split())
    if len(text) > NAME_MAX:
        raise Fehler(t("fehler.name_zu_lang"), feld)
    return text


def _nr(wert: Any, feld: str) -> int:
    try:
        nr = int(wert)
    except (TypeError, ValueError):
        raise Fehler(t("fehler.plan_nr"), feld) from None
    if not 1 <= nr <= NR_MAX:
        raise Fehler(t("fehler.plan_nr"), feld)
    return nr


def _punkte(wert: Any, feld: str, prozent: bool = False) -> list[list[float]]:
    if not isinstance(wert, list) or not 3 <= len(wert) <= PUNKTE_MAX:
        raise Fehler(t("fehler.plan_form"), feld)
    punkte = []
    for p in wert:
        if not (isinstance(p, list) and len(p) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in p)):
            raise Fehler(t("fehler.plan_form"), feld)
        x, y = (round(float(v), 2) for v in p)
        if prozent and not (0 <= x <= 100 and 0 <= y <= 100):
            raise Fehler(t("fehler.plan_form"), feld)
        if not prozent and not (-1e6 < x < 1e6 and -1e6 < y < 1e6):
            raise Fehler(t("fehler.plan_form"), feld)
        punkte.append([x, y])
    return punkte


def _version(conn: sqlite3.Connection, version: Any) -> None:
    if version != conn.execute("SELECT version FROM plan WHERE id = 1").fetchone()[0]:
        raise Fehler(t("fehler.plan_veraltet"), status=409)


def _eindeutig(nummern: list, text: str) -> None:
    gesehen = set()
    for n in nummern:
        if n in gesehen:
            raise Fehler(text)
        gesehen.add(n)


def _entwurf(conn: sqlite3.Connection, daten: dict[str, Any]) -> dict[str, Any]:
    """Prüft einen Planentwurf; Räume werden über „schluessel“ angesprochen (neue haben noch keine id)."""
    alte_raeume = {r[0] for r in conn.execute("SELECT id FROM raum")}
    alte_einheiten = {r[0] for r in conn.execute("SELECT id FROM einheit")}
    raeume, schluessel = [], set()
    for r in daten.get("raeume") or []:
        rid = r.get("id")
        if rid is not None and rid not in alte_raeume:
            raise Fehler(t("fehler.plan_veraltet"), status=409)
        s = str(r.get("schluessel") or "")
        if not s or s in schluessel:
            raise Fehler(t("fehler.plan_form"))
        schluessel.add(s)
        raeume.append({"id": rid, "schluessel": s, "nr": _nr(r.get("nr"), "raum_nr"),
                       "name": _text(r.get("name"), "raum_name"), "punkte": _punkte(r.get("punkte"), "raum")})
    _eindeutig([r["nr"] for r in raeume], t("fehler.raum_nr_doppelt"))
    einheiten = []
    for e in daten.get("einheiten") or []:
        eid = e.get("id")
        if eid is not None and eid not in alte_einheiten:
            raise Fehler(t("fehler.plan_veraltet"), status=409)
        raum = e.get("raum")
        if raum is not None and raum not in schluessel:
            raise Fehler(t("fehler.plan_form"))
        einheiten.append({"id": eid, "raum": raum, "nr": _nr(e.get("nr"), "einheit_nr"),
                          "name": _text(e.get("name"), "einheit_name"), "punkte": _punkte(e.get("punkte"), "einheit")})
    _eindeutig([(e["raum"], e["nr"]) for e in einheiten if e["raum"] is not None], t("fehler.einheit_nr_doppelt"))
    unterlage = daten.get("unterlage")
    if unterlage is not None:
        datei = str(unterlage.get("datei") or "")
        if not datei.isalnum():
            raise Fehler(t("fehler.plan_form"))
        try:
            unterlage = {"datei": datei, "breite": int(unterlage["breite"]), "hoehe": int(unterlage["hoehe"]),
                         "x": float(unterlage.get("x", 0)), "y": float(unterlage.get("y", 0)),
                         "massstab": float(unterlage.get("massstab", 1)), "drehung": int(unterlage.get("drehung", 0))}
        except (KeyError, TypeError, ValueError):
            raise Fehler(t("fehler.plan_form")) from None
        if unterlage["massstab"] <= 0 or unterlage["drehung"] not in (0, 90, 180, 270):
            raise Fehler(t("fehler.plan_form"))
    return {"raeume": raeume, "einheiten": einheiten, "unterlage": unterlage,
            "unterlage_im_buero": bool(daten.get("unterlage_im_buero"))}


# ---------- Wirkung und Speichern ----------

def _alte_codes(conn: sqlite3.Connection) -> dict[int, str]:
    return {e["id"]: code_einheit(e["r_nr"], e["nr"]) for e in conn.execute(
        "SELECT e.id, e.nr, r.nr AS r_nr FROM einheit e LEFT JOIN raum r ON r.id = e.raum_id")}


def _neue_codes(entwurf: dict[str, Any]) -> dict[int, str]:
    raum_nr = {r["schluessel"]: r["nr"] for r in entwurf["raeume"]}
    return {e["id"]: code_einheit(raum_nr.get(e["raum"]), e["nr"]) for e in entwurf["einheiten"] if e["id"] is not None}


def wirkung(conn: sqlite3.Connection, daten: dict[str, Any]) -> dict[str, int]:
    """Was das Speichern an Produkten und Etiketten ändert (Hinweis vor dem Speichern, SPEC 4.6)."""
    return _wirkung(conn, _entwurf(conn, daten))


def _wirkung(conn: sqlite3.Connection, entwurf: dict[str, Any]) -> dict[str, int]:
    alt, neu = _alte_codes(conn), _neue_codes(entwurf)
    weg = [eid for eid in alt if eid not in neu]
    umbenannt = [eid for eid, code in neu.items() if alt.get(eid) != code]

    def zahl(sql: str, ids: list[int]) -> int:
        if not ids:
            return 0
        return conn.execute(sql.format(",".join("?" * len(ids))), ids).fetchone()[0]

    return {
        "einheiten_weg": len(weg),
        "faecher_weg": zahl("SELECT count(*) FROM fach WHERE einheit_id IN ({})", weg),
        "ohne_platz": zahl("SELECT count(*) FROM produkt p JOIN fach f ON f.id = p.fach_id WHERE f.einheit_id IN ({})", weg),
        "etiketten_neu": zahl("SELECT count(*) FROM fach WHERE etikett = 'gedruckt' AND einheit_id IN ({})", umbenannt),
    }


def speichern(conn: sqlite3.Connection, media_dir: Path, daten: dict[str, Any]) -> dict[str, Any]:
    _version(conn, daten.get("version"))
    entwurf = _entwurf(conn, daten)
    wirkung_ = _wirkung(conn, entwurf)
    umbenannt = [eid for eid, code in _neue_codes(entwurf).items() if _alte_codes(conn).get(eid) != code]

    # Räume: löschen, Nummern aus dem Weg, dann aktualisieren / anlegen
    behalten = [r["id"] for r in entwurf["raeume"] if r["id"] is not None]
    conn.execute(f"DELETE FROM raum WHERE id NOT IN ({','.join('?' * len(behalten))})", behalten)
    conn.execute("UPDATE raum SET nr = nr + ?", (AUSWEICHEN,))
    raum_id = {}
    for r in entwurf["raeume"]:
        werte = (r["nr"], r["name"], json.dumps(r["punkte"]))
        if r["id"] is None:
            raum_id[r["schluessel"]] = conn.execute("INSERT INTO raum (nr, name, punkte) VALUES (?, ?, ?) RETURNING id", werte).fetchone()[0]
        else:
            conn.execute("UPDATE raum SET nr = ?, name = ?, punkte = ? WHERE id = ?", (*werte, r["id"]))
            raum_id[r["schluessel"]] = r["id"]

    # Einheiten: gelöschte nehmen ihre Fächer mit, die Produkte werden „Ohne Platz“ (ON DELETE)
    behalten = [e["id"] for e in entwurf["einheiten"] if e["id"] is not None]
    weg_fotos = [z[0] for z in conn.execute(
        f"SELECT foto FROM einheit WHERE foto IS NOT NULL AND id NOT IN ({','.join('?' * len(behalten))})", behalten)]
    conn.execute(f"DELETE FROM einheit WHERE id NOT IN ({','.join('?' * len(behalten))})", behalten)
    conn.execute("UPDATE einheit SET nr = nr + ?", (AUSWEICHEN,))
    for e in entwurf["einheiten"]:
        werte = (raum_id.get(e["raum"]), e["nr"], e["name"], json.dumps(e["punkte"]))
        if e["id"] is None:
            conn.execute("INSERT INTO einheit (raum_id, nr, name, punkte) VALUES (?, ?, ?, ?)", werte)
        else:
            conn.execute("UPDATE einheit SET raum_id = ?, nr = ?, name = ?, punkte = ? WHERE id = ?", (*werte, e["id"]))
    # Neuer Code → gedruckte Fach-Etiketten stimmen nicht mehr (SPEC 6.4)
    if umbenannt:
        conn.execute(f"UPDATE fach SET etikett = 'neu_drucken' WHERE etikett = 'gedruckt' AND einheit_id IN ({','.join('?' * len(umbenannt))})",
                     umbenannt)

    u = entwurf["unterlage"]
    alte_unterlage = conn.execute("SELECT unterlage FROM plan WHERE id = 1").fetchone()[0]
    if u and u["datei"] != alte_unterlage and not (unterlage_ordner(media_dir) / f"{u['datei']}.png").exists():
        raise Fehler(t("fehler.plan_form"))
    lage = (u["datei"], u["breite"], u["hoehe"], u["x"], u["y"], u["massstab"], u["drehung"]) if u else (None, None, None, 0, 0, 1, 0)
    conn.execute("""UPDATE plan SET version = version + 1, unterlage = ?, unterlage_breite = ?, unterlage_hoehe = ?,
                    unterlage_x = ?, unterlage_y = ?, unterlage_massstab = ?, unterlage_drehung = ?, unterlage_im_buero = ?
                    WHERE id = 1""", (*lage, int(entwurf["unterlage_im_buero"])))
    return {"wirkung": wirkung_, "dateien_weg": weg_fotos}


def faecher_speichern(conn: sqlite3.Connection, einheit_id: int, daten: dict[str, Any]) -> dict[str, int]:
    """Fach-Editor einer Einheit: ganze Fachliste mit Kennung (bleibt) oder ohne (neu)."""
    _version(conn, daten.get("version"))
    if conn.execute("SELECT 1 FROM einheit WHERE id = ?", (einheit_id,)).fetchone() is None:
        raise Fehler(t("fehler.plan_veraltet"), status=409)
    alte = {r["id"]: r for r in conn.execute("SELECT id, nr, etikett FROM fach WHERE einheit_id = ?", (einheit_id,))}
    faecher = []
    for f in daten.get("faecher") or []:
        fid = f.get("id")
        if fid is not None and fid not in alte:
            raise Fehler(t("fehler.plan_veraltet"), status=409)
        faecher.append({"id": fid, "nr": _nr(f.get("nr"), "fach_nr"), "punkte": _punkte(f.get("punkte"), "fach", prozent=True)})
    _eindeutig([f["nr"] for f in faecher], t("fehler.fach_nr_doppelt"))

    behalten = [f["id"] for f in faecher if f["id"] is not None]
    weg = [fid for fid in alte if fid not in behalten]
    ohne_platz = 0
    if weg:
        ohne_platz = conn.execute(f"SELECT count(*) FROM produkt WHERE fach_id IN ({','.join('?' * len(weg))})", weg).fetchone()[0]
        conn.execute(f"DELETE FROM fach WHERE id IN ({','.join('?' * len(weg))})", weg)
    conn.execute("UPDATE fach SET nr = nr + ? WHERE einheit_id = ?", (AUSWEICHEN, einheit_id))
    etiketten_neu = 0
    for f in faecher:
        if f["id"] is None:
            conn.execute("INSERT INTO fach (einheit_id, nr, punkte) VALUES (?, ?, ?)", (einheit_id, f["nr"], json.dumps(f["punkte"])))
            continue
        a = alte[f["id"]]
        etikett = a["etikett"]
        if a["nr"] != f["nr"] and etikett == "gedruckt":
            etikett = "neu_drucken"
            etiketten_neu += 1
        conn.execute("UPDATE fach SET nr = ?, punkte = ?, etikett = ? WHERE id = ?", (f["nr"], json.dumps(f["punkte"]), etikett, f["id"]))
    conn.execute("UPDATE plan SET version = version + 1 WHERE id = 1")
    return {"faecher_weg": len(weg), "ohne_platz": ohne_platz, "etiketten_neu": etiketten_neu}


# ---------- Dateien: Unterlage und Einheitsfoto ----------

def unterlage_ordner(media_dir: Path) -> Path:
    o = media_dir / "plan"
    o.mkdir(parents=True, exist_ok=True)
    return o


def unterlage_hochladen(media_dir: Path, daten: bytes, dateiname: str) -> dict[str, Any]:
    """PDF (erste Seite) oder Bild → PNG in media/plan/. Gilt erst, wenn der Plan mit ihr gespeichert wird."""
    if daten[:5] == b"%PDF-":
        if len(daten) > MAX_BYTES:
            raise Fehler(t("fehler.bild_gross"), "unterlage")
        import pypdfium2 as pdfium      # nur hier gebraucht
        try:
            pdf = pdfium.PdfDocument(daten)
            seite = pdf[0]
            b, h = seite.get_size()
            bild = seite.render(scale=GROESSE_GROSS / max(b, h)).to_pil().convert("RGB")
            pdf.close()
        except pdfium.PdfiumError:
            raise Fehler(t("fehler.unterlage_format"), "unterlage") from None
    else:
        bild = bild_oeffnen(daten, "unterlage")
        bild.thumbnail((GROESSE_GROSS, GROESSE_GROSS), Image.Resampling.LANCZOS)
    name = uuid.uuid4().hex
    bild.save(unterlage_ordner(media_dir) / f"{name}.png", "PNG", optimize=True)
    return {"datei": name, "breite": bild.width, "hoehe": bild.height}


def unterlagen_aufraeumen(conn: sqlite3.Connection, media_dir: Path, aelter_als_s: int = 3600) -> None:
    """Hochgeladene, aber nie gespeicherte Unterlagen entfernen (nach dem Speichern)."""
    aktuell = conn.execute("SELECT unterlage FROM plan WHERE id = 1").fetchone()[0]
    grenze = time.time() - aelter_als_s
    for p in unterlage_ordner(media_dir).glob("*.png"):
        if p.stem != aktuell and p.stat().st_mtime < grenze:
            p.unlink(missing_ok=True)


def einheit_ordner(media_dir: Path) -> Path:
    o = media_dir / "einheiten"
    o.mkdir(parents=True, exist_ok=True)
    return o


def einheit_dateien(media_dir: Path, name: str) -> list[Path]:
    o = einheit_ordner(media_dir)
    return [o / f"{name}.jpg", o / f"{name}-960.webp"]


def einheit_foto(conn: sqlite3.Connection, media_dir: Path, einheit_id: int, daten: bytes) -> dict[str, Any]:
    """Foto einer Einheit (Desktop und Telefon, SPEC 6.4). Wirkt sofort; die Fächer bleiben (Prozentangaben)."""
    alt = conn.execute("SELECT foto FROM einheit WHERE id = ?", (einheit_id,)).fetchone()
    if alt is None:
        raise Fehler(t("fehler.plan_veraltet"), status=409)
    bild = bild_oeffnen(daten)
    name = uuid.uuid4().hex
    gross, mittel = einheit_dateien(media_dir, name)
    bild.thumbnail((GROESSE_GROSS, GROESSE_GROSS), Image.Resampling.LANCZOS)
    bild.save(gross, "JPEG", quality=88, optimize=True)
    v = bild.copy()
    v.thumbnail((960, 960), Image.Resampling.LANCZOS)
    v.save(mittel, "WEBP", quality=80)
    conn.execute("UPDATE einheit SET foto = ?, foto_breite = ?, foto_hoehe = ? WHERE id = ?", (name, bild.width, bild.height, einheit_id))
    return {"foto": name, "foto_breite": bild.width, "foto_hoehe": bild.height, "alt": alt[0]}


def einheit_dateien_entfernen(media_dir: Path, namen: list[str | None]) -> None:
    for name in namen:
        if name:
            for p in einheit_dateien(media_dir, name):
                p.unlink(missing_ok=True)


# ---------- Platz des Produkts ----------

def platz_setzen(conn: sqlite3.Connection, inventar_nr: int, fach_id: int | None) -> dict[str, Any] | None:
    z = conn.execute("SELECT art, fach_id FROM produkt WHERE inventar_nr = ?", (inventar_nr,)).fetchone()
    if z is None:
        raise Fehler(t("fehler.produkt_unbekannt"), status=404)
    if z["art"] == "digital" and fach_id is not None:
        raise Fehler(t("fehler.digital_kein_platz"))
    ziel = None
    if fach_id is not None:
        ziel = fach(conn, fach_id)
        if ziel is None:
            raise Fehler(t("fehler.fach_unbekannt"), status=404)
    conn.execute("UPDATE produkt SET fach_id = ?, version = version + 1, geaendert_am = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') "
                 "WHERE inventar_nr = ?", (fach_id, inventar_nr))
    return {"vorher": z["fach_id"], "fach": ziel}
