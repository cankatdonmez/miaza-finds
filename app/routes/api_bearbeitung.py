"""/api/bearbeitung: Hinweis „Wird bearbeitet“ (SPEC 4.9, D-044). Regeln in services/bearbeitung.py."""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import Response

from ..deps import get_db
from ..services import bearbeitung

router = APIRouter(prefix="/api/bearbeitung")


def _speicher(request: Request) -> dict:
    return request.app.state.bearbeitung


@router.post("")
def beginnen(request: Request, daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    return bearbeitung.beginnen(_speicher(request), db, daten)


@router.post("/signal")
def signal(request: Request, daten: dict[str, Any] = Body(...)):
    return bearbeitung.signal(_speicher(request), daten)


@router.post("/ende", status_code=204)
def ende(request: Request, daten: dict[str, Any] = Body(...)):
    """Auch per sendBeacon beim Verlassen der Seite."""
    bearbeitung.ende(_speicher(request), daten)
    return Response(status_code=204)


@router.get("")
def stand(request: Request, art: str = "", id: int = 0, geraet: str = ""):
    return bearbeitung.stand(_speicher(request), {"art": art, "id": id, "geraet": geraet})
