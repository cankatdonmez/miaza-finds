"""/api/etiketten: Etikettenliste, PDF, „gedruckt“ (SPEC 6.6). Regeln in services/etiketten.py."""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.responses import Response

from ..config import get_settings
from ..db import transaction
from ..deps import get_db
from ..services import etiketten

router = APIRouter()


def _basis(request: Request) -> str:
    return (get_settings().basis_url or str(request.base_url)).rstrip("/")


@router.get("/api/etiketten")
def liste(request: Request, q: str = "", zustand: str | None = None, db: sqlite3.Connection = Depends(get_db)):
    # Adresse im QR mitschicken: zeigt sie auf diesen Rechner (localhost), warnt die Seite vor dem Druck
    return {"produkte": etiketten.liste(db, q, zustand), "zahlen": etiketten.zahlen(db), "bogen": etiketten.bogen(),
            "qr_adresse": _basis(request)}


@router.get("/api/etiketten/pdf")
def pdf(request: Request, nr: list[int] = Query(...), db: sqlite3.Connection = Depends(get_db)):
    inhalt = etiketten.pdf(db, nr, _basis(request))
    return Response(inhalt, media_type="application/pdf",
                    headers={"Content-Disposition": 'inline; filename="miaza-etiketten.pdf"', "Cache-Control": "no-store"})


@router.post("/api/etiketten/gedruckt")
def gedruckt(daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        return {"vorher": etiketten.als_gedruckt(db, daten.get("produkte") or [])}


@router.post("/api/etiketten/zuruecksetzen")
def zuruecksetzen(daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        return {"zurueck": etiketten.zuruecksetzen(db, daten.get("vorher") or [])}


@router.post("/api/produkte/{inventar_nr}/druckliste")
def auf_druckliste(inventar_nr: int, db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        return {"etikett": etiketten.auf_druckliste(db, inventar_nr)}
