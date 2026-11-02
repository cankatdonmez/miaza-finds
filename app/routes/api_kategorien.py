"""/api/kategorien: Kategorien und Filter (SPEC 6.3). Regeln in services/kategorien.py."""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Body, Depends

from ..db import transaction
from ..deps import get_db
from ..services import kategorien

router = APIRouter(prefix="/api/kategorien")


@router.get("")
def liste(db: sqlite3.Connection = Depends(get_db)):
    return {"kategorien": kategorien.liste(db)}


@router.get("/praefix-vorschlag")
def praefix_vorschlag(name: str = "", ausser: int | None = None, db: sqlite3.Connection = Depends(get_db)):
    return {"praefix": kategorien.praefix_vorschlag(db, name, ausser)}


@router.post("", status_code=201)
def anlegen(daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        kid = kategorien.anlegen(db, daten)
    return {"id": kid, "kategorien": kategorien.liste(db)}


@router.put("/{kategorie_id}")
def speichern(kategorie_id: int, daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        ergebnis = kategorien.speichern(db, kategorie_id, daten)
    return {**ergebnis, "kategorien": kategorien.liste(db)}


@router.delete("/{kategorie_id}")
def loeschen(kategorie_id: int, db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        kategorien.loeschen(db, kategorie_id)
    return {"kategorien": kategorien.liste(db)}
