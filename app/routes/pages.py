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
MENUE_DESKTOP = [("bibliothek", "menue.bibliothek", "grid"), ("buero", "menue.buero", "buero"),
                 ("etiketten", "menue.etiketten", "tag"), ("einstellungen", "menue.einstellungen", "settings")]
MENUE_TELEFON = [("bibliothek", "menue.bibliothek", "grid"), ("buero", "menue.buero", "buero"), ("mehr", "menue.mehr", "more")]
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


@router.get("/buero")
def buero(request: Request):
    return _seite(request, "buero", "buero.titel")


@router.get("/f/{fach_id}")
def fach_link(fach_id: int):
    """Bleibender Link auf dem Fach-Etikett (SPEC 6.6): die Kennung des Fachs, nie sein Code."""
    return RedirectResponse(f"/buero?fach={fach_id}", status_code=303)


@router.get("/plan")
def plan_bearbeiten(request: Request):
    """Büroplan bearbeiten (SPEC 6.4): nur Desktop, erreichbar über Einstellungen › Büroplan."""
    return _seite(request, "einstellungen", "plan.titel", vorlage="plan")


@router.get("/plan/einheit/{einheit_id}")
def faecher_bearbeiten(request: Request, einheit_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Fächer einer Einheit auf ihrem Foto (SPEC 6.4): nur Desktop."""
    if db.execute("SELECT 1 FROM einheit WHERE id = ?", (einheit_id,)).fetchone() is None:
        raise HTTPException(404)
    return _seite(request, "einstellungen", "plan.titel", vorlage="fach", einheit_id=einheit_id)


@router.get("/mehr")
def mehr(request: Request):
    return _seite(request, "mehr", "mehr.titel")


@router.get("/system")
def system(request: Request):
    """Systembereich (SPEC 6.13): nicht im Menü, nur über Einstellungen erreichbar."""
    return _seite(request, "einstellungen", "system.titel", vorlage="system")


@router.get("/produkt/neu")
def produkt_neu(request: Request):
    return _seite(request, "bibliothek", "produkt.neu_titel", vorlage="produkt", inventar_nr=None)


def _produkt_oder_404(db: sqlite3.Connection, inventar_nr: int) -> dict:
    try:
        return produkte.lesen(db, inventar_nr)
    except Fehler:
        raise HTTPException(404) from None


@router.get("/produkt/{inventar_nr}")
def produkt(request: Request, inventar_nr: int, db: sqlite3.Connection = Depends(get_db)):
    """Detail; am Telefon als ganze Seite, am Desktop öffnet die Bibliothek dasselbe im Seitenpanel (SPEC 6.1)."""
    p = _produkt_oder_404(db, inventar_nr)
    return _seite(request, "bibliothek", None, vorlage="detail", titel=p["name"] or t("produkt.unbenannt", nr=inventar_nr),
                  inventar_nr=inventar_nr)


@router.get("/produkt/{inventar_nr}/bearbeiten")
def produkt_bearbeiten(request: Request, inventar_nr: int, db: sqlite3.Connection = Depends(get_db)):
    p = _produkt_oder_404(db, inventar_nr)
    return _seite(request, "bibliothek", None, vorlage="produkt", titel=p["name"] or t("produkt.unbenannt", nr=inventar_nr),
                  inventar_nr=inventar_nr)


@router.get("/p/{inventar_nr}")
def qr_link(inventar_nr: int):
    """Bleibender Link auf dem Etikett (SPEC 6.6): nur die Inventarnummer, nie der Ort."""
    return RedirectResponse(f"/produkt/{inventar_nr}", status_code=303)


@router.get("/api/stand")
def stand():
    """Programmstand, z. B. für den Start-Test und spätere Betriebsprüfung."""
    return {"version": VERSION}
