"""Nehmen und Zurücklegen (SPEC 6.7, D-039): Status aus dem Entnahme-Eintrag, Rückgängig, Filter; Migration 009."""
from __future__ import annotations

import sqlite3

import pytest

from app.db import connect, migrate


@pytest.fixture
def ware(client):
    kid = client.post("/api/kategorien", json={"name": "Fliese", "praefix": "FL"}).json()["id"]
    nr = client.post("/api/produkte", json={"name": "Terrazzo", "kategorie_id": kid}).json()["inventar_nr"]
    digital = client.post("/api/produkte", json={"name": "Katalog", "kategorie_id": kid, "art": "digital"}).json()["inventar_nr"]
    selin = client.post("/api/personen", json={"name": "Selin"}).json()["id"]
    return {"nr": nr, "digital": digital, "selin": selin}


def status_liste(client, status):
    return [p["inventar_nr"] for p in client.get("/api/bibliothek", params={"status": status}).json()["produkte"]]


def test_nehmen_und_zuruecklegen(client, ware):
    nr = ware["nr"]
    assert client.get(f"/api/produkte/{nr}").json()["status"] == "ohne_platz"
    r = client.post(f"/api/produkte/{nr}/nehmen", json={"person_id": ware["selin"], "ort": "ausser_haus", "notiz": " Baustelle  Mayer "})
    assert r.status_code == 201
    p = r.json()["produkt"]
    assert p["status"] == "ausser_haus" and p["entnahme"]["person"] == "Selin" and p["entnahme"]["notiz"] == "Baustelle Mayer"
    assert status_liste(client, "ausser_haus") == [nr] and status_liste(client, "in_benutzung") == []
    karte = client.get("/api/bibliothek").json()["produkte"]
    assert {k["inventar_nr"]: k["genommen"] for k in karte} == {nr: "ausser_haus", ware["digital"]: None}
    # zweimal nehmen geht nicht
    assert client.post(f"/api/produkte/{nr}/nehmen", json={}).status_code == 409
    r = client.post(f"/api/produkte/{nr}/zuruecklegen")
    assert r.json()["produkt"]["status"] == "ohne_platz" and r.json()["produkt"]["entnahme"] is None
    assert client.post(f"/api/produkte/{nr}/zuruecklegen").status_code == 409


def test_rueckgaengig(client, ware):
    nr = ware["nr"]
    eid = client.post(f"/api/produkte/{nr}/nehmen", json={}).json()["entnahme"]
    assert client.get(f"/api/produkte/{nr}").json()["status"] == "in_benutzung"        # ohne Person, im Büro
    assert client.delete(f"/api/entnahmen/{eid}").json()["produkt"]["entnahme"] is None
    eid = client.post(f"/api/produkte/{nr}/nehmen", json={"ort": "buero"}).json()["entnahme"]
    client.post(f"/api/produkte/{nr}/zuruecklegen")
    assert client.delete(f"/api/entnahmen/{eid}").status_code == 409                   # schon zurück: Nehmen bleibt
    assert client.post(f"/api/entnahmen/{eid}/offen").json()["produkt"]["status"] == "in_benutzung"
    # Zurücklegen-Rückgängig geht nicht mehr, wenn schon neu genommen wurde
    client.post(f"/api/produkte/{nr}/zuruecklegen")
    client.post(f"/api/produkte/{nr}/nehmen", json={})
    assert client.post(f"/api/entnahmen/{eid}/offen").status_code == 409


def test_am_platz_und_falsche_eingaben(client, ware, tmp_path):
    nr = ware["nr"]
    assert client.post(f"/api/produkte/{ware['digital']}/nehmen", json={}).status_code == 422
    assert client.post(f"/api/produkte/{nr}/nehmen", json={"ort": "keller"}).status_code == 422
    assert client.post(f"/api/produkte/{nr}/nehmen", json={"person_id": 999}).status_code == 422
    client.delete(f"/api/personen/{ware['selin']}")
    assert client.post(f"/api/produkte/{nr}/nehmen", json={"person_id": ware["selin"]}).status_code == 422   # entfernt
    assert client.post("/api/produkte/999/nehmen", json={}).status_code == 404
    # Mit Fach: am Platz, solange nicht genommen
    conn = connect(tmp_path / "test.db")              # dieselbe Datei wie die App (conftest)
    conn.execute("INSERT INTO einheit (nr, punkte) VALUES (1, '[]')")
    conn.execute("INSERT INTO fach (einheit_id, nr, punkte) VALUES (1, 1, '[]')")
    conn.execute("UPDATE produkt SET fach_id = 1 WHERE inventar_nr = ?", (nr,))
    conn.commit()
    conn.close()
    assert status_liste(client, "am_platz") == [nr]
    client.post(f"/api/produkte/{nr}/nehmen", json={})
    assert status_liste(client, "am_platz") == [] and status_liste(client, "in_benutzung") == [nr]


def test_produkt_loeschen_nimmt_eintraege_mit(client, ware):
    nr = ware["nr"]
    client.post(f"/api/produkte/{nr}/nehmen", json={})
    assert client.delete(f"/api/produkte/{nr}").status_code == 200


def test_migration_009(tmp_path):
    conn = connect(tmp_path / "m.db")
    migrate(conn)
    conn.execute("INSERT INTO kategorie (name, praefix) VALUES ('K', 'KK')")
    conn.execute("INSERT INTO produkt (inventar_nr, kategorie_id, code_praefix, kategorie_nr, name, suchtext) VALUES (1, 2, 'KK', 1, 'x', 'x')")
    conn.execute("INSERT INTO entnahme (produkt_id, ort, genommen_am) VALUES (1, 'buero', '2026-11-04T10:00:00')")
    with pytest.raises(sqlite3.IntegrityError):          # nur ein offener Eintrag je Produkt
        conn.execute("INSERT INTO entnahme (produkt_id, ort, genommen_am) VALUES (1, 'buero', '2026-11-04T11:00:00')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO entnahme (produkt_id, ort, genommen_am, zurueck_am) VALUES (1, 'keller', 'a', 'b')")
    conn.close()


@pytest.fixture
def mit_faechern(client, ware, tmp_path):
    """Zwei Fächer; das Produkt liegt in Fach 1."""
    conn = connect(tmp_path / "test.db")
    conn.execute("INSERT INTO einheit (nr, punkte) VALUES (1, '[]')")
    conn.executemany("INSERT INTO fach (einheit_id, nr, punkte) VALUES (1, ?, '[]')", [(1,), (2,)])
    conn.execute("UPDATE produkt SET fach_id = 1 WHERE inventar_nr = ?", (ware["nr"],))
    conn.commit()
    def bestaetigt(eid):
        return conn.execute("SELECT fach_bestaetigt FROM entnahme WHERE id = ?", (eid,)).fetchone()[0]
    yield {**ware, "bestaetigt": bestaetigt}
    conn.close()


def test_fach_bestaetigen(client, mit_faechern):
    """D-042: gescannt → bestätigt; ohne Scan → unbestätigt; keine Abfrage → leer."""
    nr, bestaetigt = mit_faechern["nr"], mit_faechern["bestaetigt"]
    for daten, erwartet in (({"fach_bestaetigt": True}, 1), ({"fach_bestaetigt": False}, 0), ({}, None)):
        client.post(f"/api/produkte/{nr}/nehmen", json={})
        r = client.post(f"/api/produkte/{nr}/zuruecklegen", json=daten).json()
        assert bestaetigt(r["entnahme"]) == erwartet and r["produkt"]["status"] == "am_platz" and r["platz_vorher"] == 1


def test_neuer_platz_beim_zuruecklegen_und_rueckgaengig(client, mit_faechern):
    nr = mit_faechern["nr"]
    client.post(f"/api/produkte/{nr}/nehmen", json={})
    r = client.post(f"/api/produkte/{nr}/zuruecklegen", json={"neuer_fach": 2}).json()
    assert r["produkt"]["platz"]["id"] == 2 and mit_faechern["bestaetigt"](r["entnahme"]) == 1
    p = client.post(f"/api/entnahmen/{r['entnahme']}/offen", json={"platz": {"fach": r["platz_vorher"]}}).json()["produkt"]
    assert p["platz"]["id"] == 1 and p["status"] == "in_benutzung"
    assert client.post(f"/api/produkte/{nr}/zuruecklegen", json={"neuer_fach": 99}).status_code == 404
    assert client.get(f"/api/produkte/{nr}").json()["status"] == "in_benutzung"        # nichts halb gespeichert


def test_einstellung_fach_bestaetigen(client, tmp_path):
    assert client.get("/api/einstellungen").json() == {"fach_bestaetigen": True}            # Standard
    assert client.put("/api/einstellungen", json={"fach_bestaetigen": False}).json() == {"fach_bestaetigen": False}
    assert client.get("/api/einstellungen").json()["fach_bestaetigen"] is False
    assert client.put("/api/einstellungen", json={"gibt_es_nicht": True}).status_code == 422
    assert client.put("/api/einstellungen", json={"fach_bestaetigen": "ja"}).status_code == 422


def test_einordnen_und_rueckgaengig(client, mit_faechern):
    """D-043: Einordnen setzt den Platz; ein genommenes Produkt gilt damit als zurückgelegt (bestätigt)."""
    nr = mit_faechern["nr"]
    r = client.post(f"/api/produkte/{nr}/einordnen", json={"fach_id": 2}).json()
    assert r["produkt"]["platz"]["id"] == 2 and r["rueckgaengig"] == {"vorher": 1, "entnahme": None}
    client.post(f"/api/produkte/{nr}/einordnen/zurueck", json=r["rueckgaengig"])
    assert client.get(f"/api/produkte/{nr}").json()["platz"]["id"] == 1
    # genommen → einordnen → zurück am Platz, bestätigt; Rückgängig: wieder genommen und alter Platz
    eid = client.post(f"/api/produkte/{nr}/nehmen", json={}).json()["entnahme"]
    r = client.post(f"/api/produkte/{nr}/einordnen", json={"fach_id": 2}).json()
    assert r["produkt"]["status"] == "am_platz" and r["rueckgaengig"]["entnahme"] == eid and mit_faechern["bestaetigt"](eid) == 1
    p = client.post(f"/api/produkte/{nr}/einordnen/zurueck", json=r["rueckgaengig"]).json()["produkt"]
    assert p["status"] == "in_benutzung" and p["platz"]["id"] == 1
    assert client.post(f"/api/produkte/{nr}/einordnen", json={"fach_id": 99}).status_code == 404
    assert client.post(f"/api/produkte/{mit_faechern['digital']}/einordnen", json={"fach_id": 1}).status_code == 422
