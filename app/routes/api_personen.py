"""/api/personen: Personen des Büros (SPEC 6.7, D-038). Regeln in services/personen.py."""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Body, Depends

from ..db import transaction
from ..deps import get_db
from ..services import personen

router = APIRouter(prefix="/api/personen")


@router.get("")
def liste(db: sqlite3.Connection = Depends(get_db)):
    return {"personen": personen.liste(db)}


@router.post("", status_code=201)
def anlegen(daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        pid = personen.anlegen(db, daten.get("name"))
    return {"id": pid, "personen": personen.liste(db)}


@router.put("/{person_id}")
def umbenennen(person_id: int, daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        personen.umbenennen(db, person_id, daten.get("name"))
    return {"personen": personen.liste(db)}


@router.delete("/{person_id}")
def entfernen(person_id: int, db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        personen.entfernen(db, person_id)
    return {"personen": personen.liste(db)}


@router.post("/{person_id}/zurueck")
def zurueckholen(person_id: int, db: sqlite3.Connection = Depends(get_db)):
    """„Rückgängig“ nach dem Entfernen."""
    with transaction(db):
        personen.zurueckholen(db, person_id)
    return {"personen": personen.liste(db)}
