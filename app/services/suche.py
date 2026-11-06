"""Suchtext: Groß/klein und deutsche Sonderzeichen egal (ä/ae, ß/ss, SPEC 6.1)."""
from __future__ import annotations

import re
import unicodedata

_UMSCHRIFT = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def normalisieren(text: str) -> str:
    """„Glänzend Straße“ → „glaenzend strasse“; andere Akzente fallen weg (é → e)."""
    klein = text.casefold().translate(_UMSCHRIFT)
    ohne_akzente = "".join(c for c in unicodedata.normalize("NFKD", klein) if not unicodedata.combining(c))
    return " ".join(ohne_akzente.split())


_FACHCODE = re.compile(r"[0-9]+\.[0-9]+(\.[0-9]+)?")


def wort_bedingung(wort: str) -> tuple[str, list[str]]:
    """Bedingung für ein normalisiertes Suchwort (SPEC 6.1, D-050). Ein Wort wie „2.1“ oder „2.1.3“ passt nur zum
    Fachcode, vom Anfang und an Segmentgrenzen; jedes andere Wort sucht im Suchtext und findet keinen Fachcode."""
    if _FACHCODE.fullmatch(wort):
        code = "(r.nr || '.' || e.nr || '.' || f.nr)"
        return (f"EXISTS (SELECT 1 FROM fach f JOIN einheit e ON e.id = f.einheit_id JOIN raum r ON r.id = e.raum_id "
                f"WHERE f.id = p.fach_id AND ({code} = ? OR {code} LIKE ?))", [wort, wort + ".%"])
    return "instr(p.suchtext, ?) > 0", [wort]
