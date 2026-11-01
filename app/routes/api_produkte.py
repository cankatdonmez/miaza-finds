"""/api/produkte: ein Produkt anlegen, lesen, ändern, löschen; Fotos (SPEC 6.2). Regeln in services/."""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Body, Depends, File, Request, UploadFile

from ..db import transaction
from ..deps import get_db
from ..services import fotos, produkte

router = APIRouter(prefix="/api/produkte")


@router.get("/{inventar_nr}")
def lesen(inventar_nr: int, db: sqlite3.Connection = Depends(get_db)):
    return produkte.lesen(db, inventar_nr)


@router.post("", status_code=201)
def anlegen(daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        inv = produkte.anlegen(db, daten)
    return produkte.lesen(db, inv)


@router.put("/{inventar_nr}")
def aendern(inventar_nr: int, daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        return produkte.aendern(db, inventar_nr, daten)


@router.delete("/{inventar_nr}")
def loeschen(inventar_nr: int, request: Request, db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        dateien = produkte.loeschen(db, inventar_nr)
    # Erst nach dem Commit: schlägt das Löschen fehl, sind die Fotos noch da
    fotos.dateien_entfernen(request.app.state.media_dir, dateien)
    return {"geloescht": inventar_nr}


@router.post("/{inventar_nr}/fotos", status_code=201)
async def foto_hochladen(inventar_nr: int, request: Request, foto: UploadFile = File(...),
                         db: sqlite3.Connection = Depends(get_db)):
    daten = await foto.read(fotos.MAX_BYTES + 1)
    with transaction(db):
        return fotos.speichern(db, request.app.state.media_dir, inventar_nr, daten)


@router.delete("/{inventar_nr}/fotos/{foto_id}")
def foto_loeschen(inventar_nr: int, foto_id: int, request: Request, db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        name = fotos.loeschen(db, inventar_nr, foto_id)
    fotos.dateien_entfernen(request.app.state.media_dir, [name])
    return {"geloescht": foto_id}
