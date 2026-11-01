"""Seitengerüste. Die Daten kommen per JSON-API; hier nur das Grundgerüst."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..templating import templates
from ..version import VERSION

router = APIRouter()


@router.get("/")
def start(request: Request):
    return templates.TemplateResponse(request, "start.html", {})


@router.get("/api/stand")
def stand():
    """Programmstand, z. B. für den Start-Test und spätere Betriebsprüfung."""
    return {"version": VERSION}
