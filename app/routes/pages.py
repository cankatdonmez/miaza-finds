"""Seitengerüste. Die Daten kommen per JSON-API; hier nur das Grundgerüst."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from ..deps import get_db
from ..fehler import Fehler
from ..services import produkte
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


def _seite(request: Request, seite: str, titel_schluessel: str | None, vorlage: str | None = None,
           titel: str | None = None, **extra):
    return templates.TemplateResponse(request, f"{vorlage or seite}.html", {
        "seite": seite, "titel": titel or t(titel_schluessel), "menue_desktop": MENUE_DESKTOP,
        "menue_telefon": MENUE_TELEFON, "mehr_seiten": MEHR_SEITEN, **extra,
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


@router.get("/produkt/neu")
def produkt_neu(request: Request):
    return _seite(request, "bibliothek", "produkt.neu_titel", vorlage="produkt", inventar_nr=None)


@router.get("/produkt/{inventar_nr}")
def produkt(request: Request, inventar_nr: int, db: sqlite3.Connection = Depends(get_db)):
    try:
        p = produkte.lesen(db, inventar_nr)
    except Fehler:
        raise HTTPException(404) from None
    return _seite(request, "bibliothek", None, vorlage="produkt", titel=p["name"] or p["code"], inventar_nr=inventar_nr)


@router.get("/p/{inventar_nr}")
def qr_link(inventar_nr: int):
    """Bleibender Link auf dem Etikett (SPEC 6.6): nur die Inventarnummer, nie der Ort."""
    return RedirectResponse(f"/produkt/{inventar_nr}", status_code=303)


@router.get("/api/stand")
def stand():
    """Programmstand, z. B. für den Start-Test und spätere Betriebsprüfung."""
    return {"version": VERSION}
