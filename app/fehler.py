"""Fachliche Fehler der Dienste. Routen lassen sie durch; main.py macht daraus {"fehler": {"text", "feld"}}."""
from __future__ import annotations


class Fehler(Exception):
    """Eingabe verletzt eine Regel (422) oder passt nicht zum aktuellen Stand (409)."""

    def __init__(self, text: str, feld: str | None = None, status: int = 422):
        super().__init__(text)
        self.text = text
        self.feld = feld
        self.status = status
