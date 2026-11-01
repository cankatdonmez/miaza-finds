"""Seitengerüste. Die Daten kommen per JSON-API; hier nur das Grundgerüst."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from ..templating import templates
from ..texte import t
from ..version import VERSION

router = APIRouter()

# (Ziel, Textschlüssel, Symbol). Nur, was in diesem Dilim schon funktioniert; Ofis, Scannen und Sammlungen
# kommen mit ihren Dilims dazu (SPEC 4.5). Etiketten-Druck gibt es nur am Desktop (SPEC 5).
MENUE_DESKTOP = [("bibliothek", "menue.bibliothek", "grid"), ("etiketten", "menue.etiketten", "tag"),
                 ("einstellungen", "menue.einstellungen", "settings")]
MENUE_TELEFON = [("bibliothek", "menue.bibliothek", "grid"), ("mehr", "menue.mehr", "more")]
# Seiten, die am Telefon unter „Mehr“ liegen
MEHR_SEITEN = {"mehr", "einstellungen"}


def _seite(request: Request, seite: str, titel_schluessel: str):
    return templates.TemplateResponse(request, f"{seite}.html", {
        "seite": seite, "titel": t(titel_schluessel), "menue_desktop": MENUE_DESKTOP,
        "menue_telefon": MENUE_TELEFON, "mehr_seiten": MEHR_SEITEN,
    })


@router.get("/")
def start():
    return RedirectResponse("/bibliothek", status_code=303)


@router.get("/bibliothek")
def bibliothek(request: Request):
    return _seite(request, "bibliothek", "bibliothek.titel")


@router.get("/etiketten")
def etiketten(request: Request):
    return _seite(request, "etiketten", "etiketten.titel")


@router.get("/einstellungen")
def einstellungen(request: Request):
    return _seite(request, "einstellungen", "einstellungen.titel")


@router.get("/mehr")
def mehr(request: Request):
    return _seite(request, "mehr", "mehr.titel")


@router.get("/api/stand")
def stand():
    """Programmstand, z. B. für den Start-Test und spätere Betriebsprüfung."""
    return {"version": VERSION}
