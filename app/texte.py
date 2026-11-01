"""Alle Oberflächentexte an einer Stelle (SPEC 8.1, DESIGN-PRINCIPLES 7). Begriffe nach SPEC 4.10.

Schlüssel sind Punkt-Namen nach Bereich. Ein unbekannter Schlüssel ist ein Programmfehler (KeyError),
damit kein Text stillschweigend fehlt; die Seitentests decken das ab.
"""
from __future__ import annotations

DE: dict[str, str] = {
    # Marke (SPEC 4.1)
    "marke.verb": "finds",
    # Menü (SPEC 4.5); Name „Bibliothek“ vorläufig (SPEC 4.10, offene Frage 5)
    "menue.bibliothek": "Bibliothek",
    "menue.etiketten": "Etiketten",
    "menue.einstellungen": "Einstellungen",
    "menue.mehr": "Mehr",
    "menue.neues_produkt": "Neues Produkt",
    "menue.haupt": "Hauptmenü",
    # Seiten
    "bibliothek.titel": "Bibliothek",
    "bibliothek.leer": "Noch keine Produkte.",
    "etiketten.titel": "Etiketten",
    "etiketten.leer": "Noch keine Etiketten zum Drucken.",
    "einstellungen.titel": "Einstellungen",
    "einstellungen.dieses_geraet": "Dieses Gerät",
    "einstellungen.darstellung": "Darstellung",
    "darstellung.system": "System",
    "darstellung.hell": "Hell",
    "darstellung.dunkel": "Dunkel",
    "mehr.titel": "Mehr",
    # Fehlerseiten
    "fehler.404": "Diese Seite gibt es nicht.",
    "fehler.zur_startseite": "Zur Bibliothek",
}


def t(schluessel: str) -> str:
    return DE[schluessel]
