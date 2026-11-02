"""Sammelbearbeitung (SPEC 6.2, D-012): viele Produkte auf einmal ändern, mit Vorschau und „Rückgängig“.

Änderungen (dict), jeder Schlüssel ist optional:
  kategorie_id   neue Kategorie; dazu code = "behalten" | "neu"
  marke          neue Marke (nicht leer)
  art            "physisch" | "digital"
  farben_hinzu, farben_weg   Listen aus der Palette
  werte          {filter_id: wert} – nur wenn alle Produkte in derselben Kategorie sind und sie nicht wechselt;
                 None entfernt den Wert dieses Filters

Alle schreibenden Funktionen laufen innerhalb einer Transaktion des Aufrufers.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from ..fehler import Fehler
from ..texte import t
from . import produkte


def _produkte(conn: sqlite3.Connection, ids: list[Any]) -> list[sqlite3.Row]:
    if not ids or not all(isinstance(i, int) for i in ids):
        raise Fehler(t("fehler.sammel_leer"), "produkte")
    zeilen = conn.execute(f"SELECT * FROM produkt WHERE inventar_nr IN ({','.join('?' * len(ids))})", ids).fetchall()
    if len(zeilen) != len(set(ids)):
        raise Fehler(t("fehler.produkt_unbekannt"), "produkte", status=404)
    return zeilen


def vorschau(conn: sqlite3.Connection, ids: list[int], aenderung: dict[str, Any]) -> dict[str, Any]:
    """Was „Anwenden“ bewirken würde – für den Hinweis im Panel, bevor etwas passiert."""
    zeilen = _produkte(conn, ids)
    kategorien = sorted({z["kategorie_id"] for z in zeilen})
    ziel = aenderung.get("kategorie_id")
    wechsel = [z for z in zeilen if ziel and z["kategorie_id"] != ziel]
    codes_neu = werte_weg = 0
    if wechsel:
        produkte_ids = [z["inventar_nr"] for z in wechsel]
        platz = ",".join("?" * len(produkte_ids))
        werte_weg = conn.execute(f"""SELECT count(DISTINCT produkt_id || ':' || filter_id) FROM produkt_wert
                                     WHERE produkt_id IN ({platz}) AND filter_id NOT IN (SELECT id FROM filter WHERE kategorie_id = ?)""",
                                 [*produkte_ids, ziel]).fetchone()[0]
        if aenderung.get("code") == "neu":
            codes_neu = len(wechsel)
        else:
            # Code behalten geht nicht, wenn die Nummer in der Zielkategorie schon vergeben ist
            belegt = {r[0] for r in conn.execute("SELECT kategorie_nr FROM produkt WHERE kategorie_id = ?", (ziel,))}
            codes_neu = sum(1 for z in wechsel if z["kategorie_nr"] in belegt)
    return {"anzahl": len(zeilen), "kategorien": kategorien, "wechsel": len(wechsel), "codes_neu": codes_neu,
            "werte_entfallen": werte_weg}


def _schnappschuss(conn: sqlite3.Connection, z: sqlite3.Row) -> dict[str, Any]:
    inv = z["inventar_nr"]
    return {
        "inventar_nr": inv,
        "felder": {k: z[k] for k in ("kategorie_id", "code_praefix", "kategorie_nr", "marke", "art", "etikett")},
        "farben": [r[0] for r in conn.execute("SELECT farbe FROM produkt_farbe WHERE produkt_id = ?", (inv,))],
        "werte": [tuple(r) for r in conn.execute("SELECT filter_id, option_id, zahl, janein FROM produkt_wert WHERE produkt_id = ?", (inv,))],
    }


def anwenden(conn: sqlite3.Connection, ids: list[int], aenderung: dict[str, Any]) -> list[dict[str, Any]]:
    """Ändert alle Produkte; liefert den vorherigen Stand (für „Rückgängig“) mit der neuen Version je Produkt."""
    zeilen = _produkte(conn, ids)
    ziel = aenderung.get("kategorie_id")
    if ziel is not None and not conn.execute("SELECT 1 FROM kategorie WHERE id = ?", (ziel,)).fetchone():
        raise Fehler(t("fehler.kategorie_unbekannt"), "kategorie_id")
    marke = " ".join(str(aenderung.get("marke") or "").split()) or None
    art = aenderung.get("art")
    if art is not None and art not in produkte.ARTEN:
        raise Fehler(t("fehler.art"), "art")
    hinzu, weg = aenderung.get("farben_hinzu") or [], aenderung.get("farben_weg") or []
    if any(f not in produkte.FARBEN for f in [*hinzu, *weg]):
        raise Fehler(t("fehler.farbe"), "farben")
    werte = aenderung.get("werte") or {}
    if werte and (ziel is not None or len({z["kategorie_id"] for z in zeilen}) != 1):
        raise Fehler(t("fehler.sammel_werte"), "werte")

    vorher = []
    for z in zeilen:
        inv = z["inventar_nr"]
        vorher.append(_schnappschuss(conn, z))
        if ziel is not None and z["kategorie_id"] != ziel:
            produkte.kategorie_wechseln(conn, inv, ziel, neuer_code=aenderung.get("code") == "neu")
        if marke:
            conn.execute("UPDATE produkt SET marke = ? WHERE inventar_nr = ?", (marke, inv))
        if art:
            conn.execute("UPDATE produkt SET art = ? WHERE inventar_nr = ?", (art, inv))
        conn.executemany("INSERT OR IGNORE INTO produkt_farbe (produkt_id, farbe) VALUES (?, ?)", [(inv, f) for f in hinzu])
        conn.executemany("DELETE FROM produkt_farbe WHERE produkt_id = ? AND farbe = ?", [(inv, f) for f in weg])
        if werte:
            _werte_setzen(conn, inv, z["kategorie_id"], werte)
        conn.execute("""UPDATE produkt SET version = version + 1, geaendert_am = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                        WHERE inventar_nr = ?""", (inv,))
        produkte.suchtext_erneuern(conn, inv)
        vorher[-1]["version_danach"] = conn.execute("SELECT version FROM produkt WHERE inventar_nr = ?", (inv,)).fetchone()[0]
    return vorher


def _werte_setzen(conn: sqlite3.Connection, inv: int, kategorie_id: int, werte: dict[str, Any]) -> None:
    """Ersetzt nur die genannten Filter; die übrigen Werte des Produkts bleiben."""
    bisher = produkte._werte_lesen(conn, inv)
    for fid, wert in werte.items():
        bisher[str(fid)] = wert
    produkte.werte_speichern(conn, inv, kategorie_id, bisher)


def rueckgaengig(conn: sqlite3.Connection, vorher: list[dict[str, Any]]) -> dict[str, int]:
    """Stellt den Stand vor dem Anwenden wieder her. Produkte, die inzwischen anders geändert wurden, bleiben."""
    zurueck = uebersprungen = 0
    for s in vorher:
        inv = s["inventar_nr"]
        aktuell = conn.execute("SELECT version FROM produkt WHERE inventar_nr = ?", (inv,)).fetchone()
        if aktuell is None or aktuell[0] != s["version_danach"]:
            uebersprungen += 1
            continue
        conn.execute("SAVEPOINT zurueck")
        try:
            _zuruecksetzen(conn, s)
        except sqlite3.IntegrityError:
            # z. B. alte Nummer inzwischen in der Kategorie vergeben → dieses Produkt bleibt, wie es ist
            conn.execute("ROLLBACK TO zurueck")
            conn.execute("RELEASE zurueck")
            uebersprungen += 1
            continue
        conn.execute("RELEASE zurueck")
        zurueck += 1
    return {"zurueck": zurueck, "uebersprungen": uebersprungen}


def _zuruecksetzen(conn: sqlite3.Connection, s: dict[str, Any]) -> None:
    inv = s["inventar_nr"]
    f = s["felder"]
    conn.execute("""UPDATE produkt SET kategorie_id = :kategorie_id, code_praefix = :code_praefix, kategorie_nr = :kategorie_nr,
                    marke = :marke, art = :art, etikett = :etikett, version = version + 1,
                    geaendert_am = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE inventar_nr = :inv""", {**f, "inv": inv})
    conn.execute("DELETE FROM produkt_farbe WHERE produkt_id = ?", (inv,))
    conn.executemany("INSERT INTO produkt_farbe (produkt_id, farbe) VALUES (?, ?)", [(inv, x) for x in s["farben"]])
    conn.execute("DELETE FROM produkt_wert WHERE produkt_id = ?", (inv,))
    # Werte von inzwischen gelöschten Filtern/Auswahlen fallen weg
    conn.executemany("""INSERT INTO produkt_wert (produkt_id, filter_id, option_id, zahl, janein)
                        SELECT ?, ?, ?, ?, ? WHERE EXISTS (SELECT 1 FROM filter WHERE id = ?)
                        AND (? IS NULL OR EXISTS (SELECT 1 FROM filter_option WHERE id = ?))""",
                     [(inv, w[0], w[1], w[2], w[3], w[0], w[1], w[1]) for w in s["werte"]])
    produkte.suchtext_erneuern(conn, inv)
