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
    "einstellungen.reiter_kategorien": "Kategorien & Filter",
    "einstellungen.reiter_allgemein": "Allgemein",
    # Kategorien und Filter (SPEC 6.3)
    "kat.neu": "Neue Kategorie",
    "kat.name": "Name",
    "kat.praefix": "Präfix",
    "kat.produkt_eins": "1 Produkt",
    "kat.produkte": "{n} Produkte",
    "kat.filter": "Filter",
    "kat.filter_neu": "Filter hinzufügen",
    "kat.filter_name": "Name des Filters",
    "kat.typ_mass": "Maß",
    "kat.typ_einfach": "Einfachauswahl",
    "kat.typ_mehrfach": "Mehrfachauswahl",
    "kat.typ_janein": "Ja / Nein",
    "kat.beispiel_mass": "z. B. Stärke 8–12 mm",
    "kat.beispiel_einfach": "z. B. R9 oder R10",
    "kat.beispiel_mehrfach": "z. B. Matt und Strukturiert",
    "kat.beispiel_janein": "z. B. Rektifiziert",
    "kat.einheit": "Einheit",
    "kat.auswahl": "Auswahl",
    "kat.auswahl_neu": "Auswahl hinzufügen",
    "kat.nach_oben": "Nach oben",
    "kat.nach_unten": "Nach unten",
    "kat.filter_entfernen": "Filter entfernen",
    "kat.auswahl_entfernen": "„{name}“ entfernen",
    "kat.speichern": "Speichern",
    "kat.verwerfen": "Verwerfen",
    "kat.loeschen": "Kategorie löschen",
    "kat.gespeichert": "Gespeichert",
    "kat.geloescht": "„{name}“ gelöscht",
    "kat.hinweis_codes": "{n} Codes ändern sich; gedruckte Etiketten kommen auf die Druckliste.",
    "kat.hinweis_filter": "Filter „{name}“ entfällt bei {n} Produkten.",
    "kat.hinweis_auswahl": "Auswahl „{name}“ entfällt bei {n} Produkten.",
    "kat.ungespeichert": "Die Änderungen sind noch nicht gespeichert. Verwerfen?",
    "kat.waehlen": "Links eine Kategorie wählen.",
    # Allgemein
    "allg.rueckgaengig": "Rückgängig",
    "allg.fehler_netz": "Keine Verbindung zum Server. Bitte erneut versuchen.",
    "allg.fehler": "Das hat nicht geklappt. Bitte erneut versuchen.",
    # Fehlerseiten
    "fehler.404": "Diese Seite gibt es nicht.",
    "fehler.zur_startseite": "Zur Bibliothek",
    # Fehlermeldungen der Dienste
    "fehler.veraltet": "Das wurde inzwischen an einem anderen Gerät geändert. Bitte neu laden.",
    "fehler.name_fehlt": "Bitte einen Namen eingeben.",
    "fehler.name_zu_lang": "Der Name ist zu lang (höchstens 60 Zeichen).",
    "fehler.kategorie_name_vergeben": "Diese Kategorie gibt es schon.",
    "fehler.praefix_form": "Das Präfix besteht aus zwei Buchstaben, z. B. FL.",
    "fehler.praefix_vergeben": "Dieses Präfix hat schon die Kategorie „{name}“.",
    "fehler.kategorie_unbekannt": "Diese Kategorie gibt es nicht mehr.",
    "fehler.kategorie_fest": "„Sonstiges“ gibt es immer und kann nicht gelöscht werden.",
    "fehler.inventar_unveraenderlich": "Die Inventarnummer eines Produkts ändert sich nie.",
    "fehler.kategorie_nicht_leer": "Die Kategorie enthält {n} Produkte und kann nicht gelöscht werden.",
    "fehler.filter_name_doppelt": "Den Filter „{name}“ gibt es in dieser Kategorie schon.",
    "fehler.filter_typ": "Unbekannte Filterart.",
    "fehler.filter_typ_fest": "Die Art eines bestehenden Filters lässt sich nicht ändern.",
    "fehler.filter_einheit": "Bitte eine Einheit wählen.",
    "fehler.filter_optionen_fehlen": "Der Filter „{name}“ braucht mindestens eine Auswahl.",
    "fehler.option_doppelt": "Die Auswahl „{name}“ gibt es in diesem Filter schon.",
}


def t(schluessel: str, **werte) -> str:
    text = DE[schluessel]
    return text.format(**werte) if werte else text
