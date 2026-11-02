"""/api/system: der einzige Bereich mit Anmeldung (SPEC 6.13, D-006). Sitzung per Cookie + CSRF-Schlüssel (D-007)."""
from __future__ import annotations

import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, File, Request, Response, UploadFile
from fastapi.responses import FileResponse

from ..config import get_settings
from ..db import transaction
from ..deps import get_db
from ..fehler import Fehler
from ..services import sicherung, verwalter
from ..texte import t

router = APIRouter(prefix="/api/system")
COOKIE = "mf_system"


def _cookie_setzen(antwort: Response, kennung: str) -> None:
    antwort.set_cookie(COOKIE, kennung, httponly=True, samesite="strict", secure=get_settings().secure_cookies, path="/")


def angemeldet(request: Request, db: sqlite3.Connection = Depends(get_db)) -> dict:
    """Abhängigkeit für alles hinter der Anmeldung; ändernde Anfragen brauchen zusätzlich den CSRF-Schlüssel."""
    with transaction(db):
        s = verwalter.sitzung(db, request.cookies.get(COOKIE))
    if s is None:
        raise Fehler(t("fehler.system_anmelden"), status=401)
    if request.method not in ("GET", "HEAD") and request.headers.get("x-csrf-token") != s["csrf"]:
        raise Fehler(t("fehler.system_anmelden"), status=401)
    return s


# ---------- ohne Anmeldung ----------

@router.get("/stand")
def stand(request: Request, db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        s = verwalter.sitzung(db, request.cookies.get(COOKIE))
    letzte = sicherung.liste(request.app.state.sicherung_dir)
    return {"eingerichtet": verwalter.eingerichtet(db), "angemeldet": s is not None, "csrf": s["csrf"] if s else None,
            "letzte_sicherung": letzte[0]["zeit"] if letzte else None}


@router.post("/einrichten")
def einrichten(antwort: Response, daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        schluessel = verwalter.einrichten(db, daten.get("benutzername"), daten.get("passwort"), daten.get("passwort2"))
        kennung, csrf = verwalter.sitzung_anlegen(db)
    _cookie_setzen(antwort, kennung)
    return {"schluessel": schluessel, "csrf": csrf}


@router.post("/anmelden")
def anmelden(antwort: Response, daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    # Der Fehlversuch muss gespeichert bleiben → erst committen, dann den Fehler melden
    with transaction(db):
        ergebnis = verwalter.anmelden(db, daten.get("benutzername"), daten.get("passwort"))
    if ergebnis is None:
        raise Fehler(t("fehler.anmeldung"), "passwort", status=401)
    _cookie_setzen(antwort, ergebnis[0])
    return {"csrf": ergebnis[1]}


@router.post("/vergessen")
def vergessen(antwort: Response, daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        neu = verwalter.mit_schluessel_zuruecksetzen(db, daten.get("schluessel"), daten.get("passwort"), daten.get("passwort2"))
    if neu is None:
        raise Fehler(t("fehler.schluessel"), "schluessel", status=401)
    with transaction(db):
        kennung, csrf = verwalter.sitzung_anlegen(db)
    _cookie_setzen(antwort, kennung)
    return {"schluessel": neu, "csrf": csrf}


@router.post("/abmelden")
def abmelden(request: Request, antwort: Response, db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        verwalter.abmelden(db, request.cookies.get(COOKIE))
    antwort.delete_cookie(COOKIE, path="/")
    return {"ok": True}


# ---------- mit Anmeldung ----------

@router.get("/uebersicht")
def uebersicht(request: Request, _: dict = Depends(angemeldet), db: sqlite3.Connection = Depends(get_db)):
    return {"sicherungen": sicherung.liste(request.app.state.sicherung_dir), "wirkung": sicherung.wirkung(db),
            "ordner": str(request.app.state.sicherung_dir)}


@router.post("/sicherung")
def sicherung_erstellen(request: Request, _: dict = Depends(angemeldet)):
    s = request.app.state
    datei = sicherung.erstellen(s.db_path, s.media_dir, s.sicherung_dir)
    return {"name": datei.name, "sicherungen": sicherung.liste(s.sicherung_dir)}


@router.get("/sicherung/{name}")
def sicherung_laden(name: str, request: Request, _: dict = Depends(angemeldet)):
    return FileResponse(sicherung.datei(request.app.state.sicherung_dir, name), media_type="application/zip", filename=name)


@router.post("/wiederherstellen")
def wiederherstellen(request: Request, daten: dict[str, Any] = Body(...), _: dict = Depends(angemeldet)):
    s = request.app.state
    quelle = sicherung.datei(s.sicherung_dir, daten.get("name"))
    return sicherung.einspielen(s.db_path, s.media_dir, s.sicherung_dir, quelle)


@router.post("/uebernehmen")
async def uebernehmen(request: Request, datei: UploadFile = File(...), _: dict = Depends(angemeldet)):
    """Datenübernahme aus einer hochgeladenen Sicherung (z. B. vom alten Server, D-009)."""
    s = request.app.state
    with tempfile.TemporaryDirectory() as tmp:
        ziel = Path(tmp) / "upload.zip"
        with ziel.open("wb") as f:
            shutil.copyfileobj(datei.file, f)
        return sicherung.einspielen(s.db_path, s.media_dir, s.sicherung_dir, ziel)


@router.post("/uebernehmen-pfad")
def uebernehmen_pfad(request: Request, daten: dict[str, Any] = Body(...), _: dict = Depends(angemeldet)):
    """Datenübernahme aus einem auf den Server kopierten Ordner oder einer ZIP-Datei (D-009)."""
    s = request.app.state
    quelle = Path(str(daten.get("pfad") or "").strip().strip('"'))
    if not str(quelle) or not quelle.exists():
        raise Fehler(t("fehler.pfad_unbekannt"), "pfad", status=404)
    return sicherung.einspielen(s.db_path, s.media_dir, s.sicherung_dir, quelle)


@router.post("/loeschen")
def loeschen(request: Request, daten: dict[str, Any] = Body(...), _: dict = Depends(angemeldet),
             db: sqlite3.Connection = Depends(get_db)):
    s = request.app.state
    was = daten.get("was")
    if was not in ("produkte", "alles"):
        raise Fehler(t("fehler.art"), "was")
    vorher = sicherung.erstellen(s.db_path, s.media_dir, s.sicherung_dir, "vor-loeschen")
    with transaction(db):
        (sicherung.produkte_loeschen if was == "produkte" else sicherung.alles_loeschen)(db, s.media_dir)
    return {"sicherung_vorher": vorher.name, "wirkung": sicherung.wirkung(db)}


@router.post("/passwort")
def passwort(daten: dict[str, Any] = Body(...), _: dict = Depends(angemeldet), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        verwalter.passwort_aendern(db, daten.get("alt"), daten.get("neu"), daten.get("neu2"))
    return {"ok": True}


@router.post("/schluessel")
def schluessel(_: dict = Depends(angemeldet), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        return {"schluessel": verwalter.schluessel_erneuern(db)}
