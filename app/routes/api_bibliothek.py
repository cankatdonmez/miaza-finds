"""/api/bibliothek: Suche und Filter (SPEC 6.1). Regeln in services/bibliothek.py."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Request

from ..deps import get_db
from ..services import bibliothek

router = APIRouter(prefix="/api/bibliothek")


@router.get("")
def suchen(request: Request, seite: int = 0, ids: int = 0, db: sqlite3.Connection = Depends(get_db)):
    paare = [(k, v) for k, v in request.query_params.multi_items() if k not in ("seite", "ids")]
    auftrag = bibliothek.auftrag_aus_adresse(db, paare)
    if ids:
        # „Alle auswählen“ der Sammelbearbeitung: nur die Nummern aller Treffer
        return {"ids": bibliothek.alle_nummern(db, auftrag)}
    return {**bibliothek.suchen(db, auftrag, max(seite, 0)), "zaehler": bibliothek.zaehler(db)}
