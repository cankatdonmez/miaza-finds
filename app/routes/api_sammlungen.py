"""/api/sammlungen: Sammlungen (SPEC 6.8, D-047). Regeln in services/sammlungen.py."""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Body, Depends

from ..db import transaction
from ..deps import get_db
from ..services import sammlungen

router = APIRouter(prefix="/api/sammlungen")


@router.get("")
def liste(produkt: int | None = None, db: sqlite3.Connection = Depends(get_db)):
    return {"sammlungen": sammlungen.liste(db, produkt)}


@router.post("", status_code=201)
def anlegen(daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    """Mit `produkt` legt die neue Sammlung das Produkt gleich hinein (Produktdetail)."""
    produkt = daten.get("produkt")
    with transaction(db):
        sid = sammlungen.anlegen(db, daten.get("name"), daten.get("notiz"))
        if produkt:
            sammlungen.hinzufuegen(db, sid, int(produkt))
    return {"id": sid, "sammlungen": sammlungen.liste(db, produkt)}


@router.get("/{sammlung_id}")
def lesen(sammlung_id: int, db: sqlite3.Connection = Depends(get_db)):
    return sammlungen.lesen(db, sammlung_id)


@router.put("/{sammlung_id}")
def aendern(sammlung_id: int, daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        sammlungen.aendern(db, sammlung_id, daten)
    return sammlungen.lesen(db, sammlung_id)


@router.delete("/{sammlung_id}")
def entfernen(sammlung_id: int, db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        sammlungen.entfernen(db, sammlung_id)
    return {"sammlungen": sammlungen.liste(db)}


@router.post("/{sammlung_id}/zurueck")
def zurueckholen(sammlung_id: int, db: sqlite3.Connection = Depends(get_db)):
    """„Rückgängig“ nach dem Entfernen."""
    with transaction(db):
        sammlungen.zurueckholen(db, sammlung_id)
    return {"sammlungen": sammlungen.liste(db)}


@router.put("/{sammlung_id}/produkte/{inventar_nr}")
def hinzufuegen(sammlung_id: int, inventar_nr: int, db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        sammlungen.hinzufuegen(db, sammlung_id, inventar_nr)
    return {"sammlungen": sammlungen.liste(db, inventar_nr)}


@router.delete("/{sammlung_id}/produkte/{inventar_nr}")
def herausnehmen(sammlung_id: int, inventar_nr: int, db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        sammlungen.herausnehmen(db, sammlung_id, inventar_nr)
    return {"sammlungen": sammlungen.liste(db, inventar_nr)}
