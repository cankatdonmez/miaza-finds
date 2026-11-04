"""Bibliothek: Suche und Filter über alle Produkte (SPEC 6.1). Ziel: Antwort unter 200 ms bei einigen tausend Produkten.

Ein Suchauftrag (dict):
  q          freier Text; jedes Wort muss im Suchtext vorkommen
  art        "physisch" | "digital"
  kategorie  Kategorie-ID; erst dann gelten die kategoriespezifischen Filter
  farben     Liste; eine passende Farbe genügt
  marken     Liste; eine passende Marke genügt
  preis_min, preis_max   Cent
  status     "am_platz" | "in_benutzung" | "ausser_haus" | "ohne_platz" | "fehlend"
  werte      {filter_id: [option_id …] | {"min": x, "max": y} | True/False}
Zwischen verschiedenen Filtern gilt UND, innerhalb eines Filters ODER.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from . import entnahme, nummern, produkte
from .suche import normalisieren

SEITE = 120
STATUS = ("am_platz", "in_benutzung", "ausser_haus", "ohne_platz", "fehlend")


OFFEN = "EXISTS (SELECT 1 FROM entnahme e WHERE e.produkt_id = p.inventar_nr AND e.zurueck_am IS NULL{})"


def _status_bedingung(status: str) -> str:
    """Platz über das Fach (Dilim 2), genommen über den offenen Entnahme-Eintrag (D-039)."""
    return {
        "ohne_platz": "p.art = 'physisch' AND p.fach_id IS NULL",
        "fehlend": "p.name IS NULL",
        "am_platz": f"p.art = 'physisch' AND p.fach_id IS NOT NULL AND NOT {OFFEN.format('')}",
        "in_benutzung": "p.art = 'physisch' AND " + OFFEN.format(" AND e.ort = 'buero'"),
        "ausser_haus": "p.art = 'physisch' AND " + OFFEN.format(" AND e.ort = 'ausser_haus'"),
    }[status]


def _bedingungen(auftrag: dict[str, Any], mit_kategorie: bool = True) -> tuple[list[str], list[Any]]:
    wo, args = [], []
    for wort in normalisieren(auftrag.get("q") or "").split():
        wo.append("instr(p.suchtext, ?) > 0")
        args.append(wort)
    if auftrag.get("art") in ("physisch", "digital"):
        wo.append("p.art = ?")
        args.append(auftrag["art"])
    if auftrag.get("farben"):
        # eigene Grundfarben oder Farbtöne, die zu einer der gesuchten Grundfarben gehören (D-031)
        wo.append(f"""(EXISTS (SELECT 1 FROM produkt_farbe pf WHERE pf.produkt_id = p.inventar_nr AND pf.farbe IN ({_platz(auftrag['farben'])}))
                    OR EXISTS (SELECT 1 FROM produkt_wert pw JOIN filter_option fo ON fo.id = pw.option_id
                               WHERE pw.produkt_id = p.inventar_nr AND fo.grundfarbe IN ({_platz(auftrag['farben'])})))""")
        args += auftrag["farben"] * 2
    if auftrag.get("marken"):
        wo.append(f"p.marke IN ({_platz(auftrag['marken'])})")
        args += auftrag["marken"]
    if auftrag.get("preis_min") is not None:
        wo.append("EXISTS (SELECT 1 FROM preis pr WHERE pr.produkt_id = p.inventar_nr AND pr.cent >= ?)")
        args.append(auftrag["preis_min"])
    if auftrag.get("preis_max") is not None:
        wo.append("EXISTS (SELECT 1 FROM preis pr WHERE pr.produkt_id = p.inventar_nr AND pr.cent <= ?)")
        args.append(auftrag["preis_max"])
    if auftrag.get("status") in STATUS:
        wo.append(_status_bedingung(auftrag["status"]))
    if mit_kategorie and auftrag.get("kategorie"):
        wo.append("p.kategorie_id = ?")
        args.append(auftrag["kategorie"])
        for fid, wert in (auftrag.get("werte") or {}).items():
            bed, a = _wert_bedingung(int(fid), wert)
            if bed:
                wo.append(bed)
                args += a
    return wo, args


def _wert_bedingung(fid: int, wert: Any) -> tuple[str | None, list[Any]]:
    basis = "EXISTS (SELECT 1 FROM produkt_wert w WHERE w.produkt_id = p.inventar_nr AND w.filter_id = ?"
    if isinstance(wert, bool):
        return basis + " AND w.janein = ?)", [fid, int(wert)]
    if isinstance(wert, dict):
        teile, a = [], [fid]
        if wert.get("min") is not None:
            teile.append("w.zahl >= ?")
            a.append(wert["min"])
        if wert.get("max") is not None:
            teile.append("w.zahl <= ?")
            a.append(wert["max"])
        if not teile:
            return None, []
        return basis + " AND " + " AND ".join(teile) + ")", a
    if isinstance(wert, list) and wert:
        return basis + f" AND w.option_id IN ({_platz(wert)}))", [fid, *wert]
    return None, []


def auftrag_aus_adresse(conn: sqlite3.Connection, paare: list[tuple[str, str]]) -> dict[str, Any]:
    """Liest den Suchauftrag aus der Adresszeile, z. B. ?q=terrazzo&kategorie=2&farbe=beige&w5=12&w7_min=8&w9=ja.

    Die Filter stehen in der Adresse, damit Zurück, Neuladen und ein geteilter Link dieselbe Ansicht zeigen.
    """
    auftrag: dict[str, Any] = {"farben": [], "marken": [], "werte": {}}
    roh_werte: dict[str, list[str]] = {}
    for k, v in paare:
        v = v.strip()
        if not v:
            continue
        if k in ("q", "art", "status"):
            auftrag[k] = v
        elif k == "kategorie" and v.isdigit():
            auftrag["kategorie"] = int(v)
        elif k == "farbe":
            auftrag["farben"].append(v)
        elif k == "marke":
            auftrag["marken"].append(v)
        elif k in ("preis_min", "preis_max"):
            auftrag[k] = produkte.preis_lesen(v)
        elif k.startswith("w"):
            roh_werte.setdefault(k[1:], []).append(v)
    if auftrag.get("kategorie"):
        typen = {r["id"]: r["typ"] for r in conn.execute("SELECT id, typ FROM filter WHERE kategorie_id = ?", (auftrag["kategorie"],))}
        for schluessel, werte in roh_werte.items():
            fid_text, _, grenze = schluessel.partition("_")
            if not fid_text.isdigit() or int(fid_text) not in typen:
                continue
            fid, typ = int(fid_text), typen[int(fid_text)]
            if typ == "mass" and grenze in ("min", "max"):
                try:
                    auftrag["werte"].setdefault(fid, {})[grenze] = float(werte[0].replace(",", "."))
                except ValueError:
                    pass
            elif typ == "janein" and werte[0] in ("ja", "nein"):
                auftrag["werte"][fid] = werte[0] == "ja"
            elif typ in ("einfach", "mehrfach"):
                auftrag["werte"][fid] = [int(w) for w in werte if w.isdigit()]
    return auftrag


def _platz(liste: list) -> str:
    return ",".join("?" * len(liste))


def suchen(conn: sqlite3.Connection, auftrag: dict[str, Any], seite: int = 0) -> dict[str, Any]:
    wo, args = _bedingungen(auftrag)
    where = ("WHERE " + " AND ".join(wo)) if wo else ""
    # Bei Suche zuerst die genaue Nummer („265“), dann Namen, die mit dem Suchwort beginnen; sonst Neueste zuerst
    q = normalisieren(auftrag.get("q") or "")
    ordnung, oargs = "p.inventar_nr DESC", []
    if q:
        nummer = int(q) if q.isdigit() else -1
        ordnung = "(p.inventar_nr = ?) DESC, (p.suchtext LIKE ?) DESC, p.inventar_nr DESC"
        oargs = [nummer, q.replace("%", "") + "%"]
    gesamt = conn.execute(f"SELECT count(*) FROM produkt p {where}", args).fetchone()[0]
    zeilen = conn.execute(f"""
        SELECT p.inventar_nr, p.code_praefix, p.kategorie_nr, p.name, p.marke, p.art, p.etikett, p.version, k.name AS kategorie,
               pr.cent, pr.einheit, pr.datum AS preis_datum,
               (SELECT f.datei FROM foto f WHERE f.produkt_id = p.inventar_nr ORDER BY f.sortierung, f.id LIMIT 1) AS foto,
               (SELECT e.ort FROM entnahme e WHERE e.produkt_id = p.inventar_nr AND e.zurueck_am IS NULL) AS genommen
        FROM produkt p JOIN kategorie k ON k.id = p.kategorie_id LEFT JOIN preis pr ON pr.produkt_id = p.inventar_nr
        {where} ORDER BY {ordnung} LIMIT ? OFFSET ?""", [*args, *oargs, SEITE, seite * SEITE]).fetchall()
    produkte = [{
        "inventar_nr": z["inventar_nr"], "code": nummern.code(z["code_praefix"], z["kategorie_nr"], z["inventar_nr"]),
        "name": z["name"], "marke": z["marke"], "art": z["art"], "kategorie": z["kategorie"], "etikett": z["etikett"],
        "preis": {"cent": z["cent"], "einheit": z["einheit"], "datum": z["preis_datum"]} if z["cent"] is not None else None,
        "foto": z["foto"], "version": z["version"],
        # nur für den Rozet auf der Karte (D-039): in_benutzung | ausser_haus | None
        "genommen": entnahme.STATUS_NACH_ORT.get(z["genommen"]) if z["art"] == "physisch" else None,
    } for z in zeilen]
    return {"produkte": produkte, "gesamt": gesamt, "seite": seite, "weitere": (seite + 1) * SEITE < gesamt,
            "kategorien": _kategorie_zahlen(conn, auftrag), "marken": _marken(conn)}


def alle_nummern(conn: sqlite3.Connection, auftrag: dict[str, Any]) -> list[int]:
    wo, args = _bedingungen(auftrag)
    where = ("WHERE " + " AND ".join(wo)) if wo else ""
    return [r[0] for r in conn.execute(f"SELECT p.inventar_nr FROM produkt p {where} ORDER BY p.inventar_nr DESC", args)]


def _kategorie_zahlen(conn: sqlite3.Connection, auftrag: dict[str, Any]) -> dict[int, int]:
    """Anzahl je Kategorie unter allen übrigen Filtern (SPEC 6.1, Desktop)."""
    wo, args = _bedingungen(auftrag, mit_kategorie=False)
    where = ("WHERE " + " AND ".join(wo)) if wo else ""
    return {r[0]: r[1] for r in conn.execute(f"SELECT p.kategorie_id, count(*) FROM produkt p {where} GROUP BY p.kategorie_id", args)}


def _marken(conn: sqlite3.Connection) -> list[str]:
    return [r[0] for r in conn.execute("SELECT DISTINCT marke FROM produkt WHERE marke IS NOT NULL ORDER BY marke COLLATE NOCASE")]


def zaehler(conn: sqlite3.Connection) -> dict[str, int]:
    """Statuszeile des Desktops (SPEC 6.1) und Statistik: über den ganzen Bestand."""
    z = {"gesamt": conn.execute("SELECT count(*) FROM produkt").fetchone()[0]}
    for status in STATUS:
        z[status] = conn.execute(f"SELECT count(*) FROM produkt p WHERE {_status_bedingung(status)}").fetchone()[0]
    return z
