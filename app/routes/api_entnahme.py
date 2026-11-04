"""Nehmen und Zurücklegen (SPEC 6.7, D-039). Regeln in services/entnahme.py; jede Antwort bringt das Produkt neu mit."""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Body, Depends

from ..db import transaction
from ..deps import get_db
from ..services import entnahme, produkte

router = APIRouter(prefix="/api")


@router.post("/produkte/{inventar_nr}/nehmen", status_code=201)
def nehmen(inventar_nr: int, daten: dict[str, Any] = Body(default={}), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        eid = entnahme.nehmen(db, inventar_nr, daten)
    return {"entnahme": eid, "produkt": produkte.lesen(db, inventar_nr)}


@router.post("/produkte/{inventar_nr}/zuruecklegen")
def zuruecklegen(inventar_nr: int, daten: dict[str, Any] = Body(default={}), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        eid, vorher = entnahme.zuruecklegen(db, inventar_nr, daten)
    return {"entnahme": eid, "platz_vorher": vorher, "produkt": produkte.lesen(db, inventar_nr)}


@router.delete("/entnahmen/{entnahme_id}")
def nehmen_rueckgaengig(entnahme_id: int, db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        nr = entnahme.nehmen_zuruecknehmen(db, entnahme_id)
    return {"produkt": produkte.lesen(db, nr)}


@router.post("/entnahmen/{entnahme_id}/offen")
def zuruecklegen_rueckgaengig(entnahme_id: int, daten: dict[str, Any] = Body(default={}), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        nr = entnahme.zuruecklegen_zuruecknehmen(db, entnahme_id, daten.get("platz"))
    return {"produkt": produkte.lesen(db, nr)}
