"""/api/plan, /api/einheiten, /api/faecher: Büroplan und Platz der Produkte (SPEC 6.4–6.7). Regeln in services/plan.py."""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Body, Depends, File, Request, UploadFile

from ..db import transaction
from ..deps import get_db
from ..fehler import Fehler
from ..services import fotos, plan
from ..texte import t

router = APIRouter(prefix="/api")


@router.get("/plan")
def laden(db: sqlite3.Connection = Depends(get_db)):
    return plan.laden(db)


@router.post("/plan/wirkung")
def wirkung(daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    return plan.wirkung(db, daten)


@router.put("/plan")
def speichern(request: Request, daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    media = request.app.state.media_dir
    with transaction(db):
        ergebnis = plan.speichern(db, media, daten)
    plan.einheit_dateien_entfernen(media, ergebnis["dateien_weg"])
    plan.unterlagen_aufraeumen(db, media)
    return {"wirkung": ergebnis["wirkung"], "plan": plan.laden(db)}


@router.post("/plan/unterlage", status_code=201)
async def unterlage(request: Request, datei: UploadFile = File(...)):
    daten = await datei.read(fotos.MAX_BYTES + 1)
    return plan.unterlage_hochladen(request.app.state.media_dir, daten, datei.filename or "")


@router.post("/einheiten/{einheit_id}/foto", status_code=201)
async def einheit_foto(einheit_id: int, request: Request, foto: UploadFile = File(...),
                       db: sqlite3.Connection = Depends(get_db)):
    daten = await foto.read(fotos.MAX_BYTES + 1)
    media = request.app.state.media_dir
    with transaction(db):
        ergebnis = plan.einheit_foto(db, media, einheit_id, daten)
    plan.einheit_dateien_entfernen(media, [ergebnis.pop("alt")])
    return ergebnis


@router.put("/einheiten/{einheit_id}/faecher")
def faecher(einheit_id: int, daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        wirkung_ = plan.faecher_speichern(db, einheit_id, daten)
    return {"wirkung": wirkung_, "plan": plan.laden(db)}


@router.get("/faecher/{fach_id}")
def fach(fach_id: int, db: sqlite3.Connection = Depends(get_db)):
    f = plan.fach(db, fach_id)
    if f is None:
        raise Fehler(t("fehler.fach_unbekannt"), status=404)
    return {**f, "produkte": plan.produkte_im_fach(db, fach_id)}


@router.put("/produkte/{inventar_nr}/platz")
def platz(inventar_nr: int, daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    fach_id = daten.get("fach_id")
    if fach_id is not None and not isinstance(fach_id, int):
        raise Fehler(t("fehler.fach_unbekannt"), status=404)
    with transaction(db):
        return plan.platz_setzen(db, inventar_nr, fach_id)
