"""Suchtext: Groß/klein und deutsche Sonderzeichen egal (ä/ae, ß/ss, SPEC 6.1)."""
from __future__ import annotations

import unicodedata

_UMSCHRIFT = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def normalisieren(text: str) -> str:
    """„Glänzend Straße“ → „glaenzend strasse“; andere Akzente fallen weg (é → e)."""
    klein = text.casefold().translate(_UMSCHRIFT)
    ohne_akzente = "".join(c for c in unicodedata.normalize("NFKD", klein) if not unicodedata.combining(c))
    return " ".join(ohne_akzente.split())
