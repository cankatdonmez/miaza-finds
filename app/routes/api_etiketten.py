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


@router.get("/api/etiketten/faecher")
def fach_liste(request: Request, q: str = "", zustand: str | None = None, db: sqlite3.Connection = Depends(get_db)):
    return {"faecher": etiketten.fach_liste(db, q, zustand), "zahlen": etiketten.fach_zahlen(db), "bogen": etiketten.bogen(),
            "qr_adresse": _basis(request)}


@router.get("/api/etiketten/faecher/pdf")
def fach_pdf(request: Request, id: list[int] = Query(...), db: sqlite3.Connection = Depends(get_db)):
    inhalt = etiketten.fach_pdf(db, id, _basis(request))
    return Response(inhalt, media_type="application/pdf",
                    headers={"Content-Disposition": 'inline; filename="miaza-fach-etiketten.pdf"', "Cache-Control": "no-store"})


@router.post("/api/etiketten/faecher/gedruckt")
def faecher_gedruckt(daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        return {"vorher": etiketten.faecher_als_gedruckt(db, daten.get("faecher") or [])}


@router.post("/api/etiketten/faecher/zuruecksetzen")
def faecher_zuruecksetzen(daten: dict[str, Any] = Body(...), db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        return {"zurueck": etiketten.faecher_zuruecksetzen(db, daten.get("vorher") or [])}


@router.get("/api/etiketten/vorschau/{inventar_nr}.png")
def vorschau(inventar_nr: int, request: Request, db: sqlite3.Connection = Depends(get_db)):
    """Ein Produktetikett als Bild, genau wie gedruckt (Vorschau der Etikettenseite)."""
    return Response(etiketten.vorschau(db, inventar_nr, _basis(request)), media_type="image/png",
                    headers={"Cache-Control": "no-cache"})


@router.get("/api/etiketten/vorschau/fach/{fach_id}.png")
def fach_vorschau(fach_id: int, request: Request, db: sqlite3.Connection = Depends(get_db)):
    return Response(etiketten.fach_vorschau(db, fach_id, _basis(request)), media_type="image/png",
                    headers={"Cache-Control": "no-cache"})


@router.get("/api/etiketten/qr/fach/{fach_id}.svg")
def fach_qr(request: Request, fach_id: int):
    puffer = io.BytesIO()
    segno.make(f"{_basis(request)}/f/{fach_id}", error="m").save(puffer, kind="svg", border=0, light="#fff")
    return Response(puffer.getvalue(), media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


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
