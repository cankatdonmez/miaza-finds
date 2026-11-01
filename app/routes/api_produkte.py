"""/api/produkte: ein Produkt anlegen, lesen, ändern, löschen; Fotos (SPEC 6.2). Regeln in services/."""
from __future__ import annotations

import sqlite3
import time
import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, File, Request, UploadFile

from ..db import transaction
from ..deps import get_db
from ..fehler import Fehler
from ..services import fotos, produkte, sammel
from ..texte import t

router = APIRouter(prefix="/api/produkte")


# ---------- Sammelbearbeitung (D-012) ----------
# Der vorherige Stand bleibt kurz im Speicher, damit „Rückgängig“ ohne Rückfrage möglich ist (SPEC 4.5).
RUECKGAENGIG_SEKUNDEN = 10 * 60


def _ablage(request: Request) -> dict:
    ablage = request.app.state.sammel_vorher
    jetzt = time.monotonic()
    for k in [k for k, (zeit, _) in ablage.items() if jetzt - zeit > RUECKGAENGIG_SEKUNDEN]:
        del ablage[k]
    return ablage


@router.post("/sammel/vorschau")
def sammel_vorschau(daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    return sammel.vorschau(db, daten.get("produkte") or [], daten.get("aenderung") or {})


@router.post("/sammel")
def sammel_anwenden(request: Request, daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        vorher = sammel.anwenden(db, daten.get("produkte") or [], daten.get("aenderung") or {})
    schluessel = uuid.uuid4().hex
    _ablage(request)[schluessel] = (time.monotonic(), vorher)
    return {"geaendert": len(vorher), "rueckgaengig": schluessel}


@router.post("/sammel/rueckgaengig/{schluessel}")
def sammel_rueckgaengig(schluessel: str, request: Request, db: sqlite3.Connection = Depends(get_db)):
    eintrag = _ablage(request).pop(schluessel, None)
    if eintrag is None:
        raise Fehler(t("fehler.sammel_abgelaufen"), status=410)
    with transaction(db):
        return sammel.rueckgaengig(db, eintrag[1])


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
