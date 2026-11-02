"""/api/etiketten: Etikettenliste, PDF, „gedruckt“ (SPEC 6.6). Regeln in services/etiketten.py."""
from __future__ import annotations

import io
import socket
import sqlite3
from typing import Any

import segno

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.responses import Response

from ..config import get_settings
from ..db import transaction
from ..deps import get_db
from ..services import etiketten

router = APIRouter()


LOKAL = {"localhost", "127.0.0.1", "::1"}


def _netzadresse() -> str | None:
    # UDP-„Verbindung“ sendet nichts; sie verrät nur, über welche Adresse dieser Rechner ins Netz geht
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
    except OSError:
        return None
    return None if ip.startswith("127.") else ip


def _basis(request: Request) -> str:
    s = get_settings()
    if s.basis_url:
        return s.basis_url.rstrip("/")
    # Auf diesem Rechner über localhost geöffnet: Telefone brauchen die Netzadresse (D-014)
    if s.netz and request.url.hostname in LOKAL and (ip := _netzadresse()):
        port = f":{request.url.port}" if request.url.port else ""
        return f"{request.url.scheme}://{ip}{port}"
    return str(request.base_url).rstrip("/")


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


@router.get("/api/etiketten/qr/{inventar_nr}.svg")
def qr(request: Request, inventar_nr: int):
    # Vorschau auf der Etikettenseite: derselbe Inhalt wie im PDF
    puffer = io.BytesIO()
    segno.make(f"{_basis(request)}/p/{inventar_nr}", error="m").save(puffer, kind="svg", border=0, light="#fff")
    return Response(puffer.getvalue(), media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


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
