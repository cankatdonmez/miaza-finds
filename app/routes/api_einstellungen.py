"""/api/einstellungen: Schalter des ganzen Büros (SPEC 6.11). Regeln in services/einstellungen.py."""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Body, Depends

from ..db import transaction
from ..deps import get_db
from ..services import einstellungen

router = APIRouter(prefix="/api/einstellungen")


@router.get("")
def lesen(db: sqlite3.Connection = Depends(get_db)):
    return einstellungen.lesen(db)


@router.put("")
def aendern(daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        return einstellungen.aendern(db, daten)
