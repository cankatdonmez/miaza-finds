"""Sammelbearbeitung (SPEC 6.2, D-012): Vorschau, Anwenden, Rückgängig."""
from __future__ import annotations

import pytest

from app.db import connect

API = "/api/produkte/sammel"


@pytest.fixture
def lage(client):
    def kat(name, praefix, filter_=None):
        kid = client.post("/api/kategorien", json={"name": name, "praefix": praefix}).json()["id"]
        if filter_:
            k = next(k for k in client.get("/api/kategorien").json()["kategorien"] if k["id"] == kid)
            client.put(f"/api/kategorien/{kid}", json={**k, "filter": filter_})
        return next(k for k in client.get("/api/kategorien").json()["kategorien"] if k["id"] == kid)

    sonst = next(k for k in client.get("/api/kategorien").json()["kategorien"] if k["fest"])
    fliese = kat("Fliese", "FL", [{"name": "Rutschhemmung", "typ": "einfach", "optionen": [{"name": "R10"}, {"name": "R11"}]}])
    stoff = kat("Stoff", "ST", [{"name": "Gewebe", "typ": "einfach", "optionen": [{"name": "Leinen"}]}])
    gewebe = stoff["filter"][0]
    ids = []
    for i in range(3):
        r = client.post("/api/produkte", json={"name": f"Stoff {i}", "kategorie_id": sonst["id"], "farben": ["beige"]})
        ids.append(r.json()["inventar_nr"])
    leinen = client.post("/api/produkte", json={"name": "Leinen natur", "kategorie_id": stoff["id"],
                                                "werte": {str(gewebe["id"]): gewebe["optionen"][0]["id"]}}).json()["inventar_nr"]
    return {"client": client, "ids": ids, "leinen": leinen, "sonst": sonst, "fliese": fliese, "stoff": stoff}


def _p(client, inv):
    return client.get(f"/api/produkte/{inv}").json()


def test_vorschau_sagt_was_passiert(lage):
    c, ziel = lage["client"], lage["fliese"]["id"]
    alle = [*lage["ids"], lage["leinen"]]
    r = c.post(f"{API}/vorschau", json={"produkte": alle, "aenderung": {"kategorie_id": ziel, "code": "neu"}}).json()
    assert r == {"anzahl": 4, "kategorien": sorted([lage["sonst"]["id"], lage["stoff"]["id"]]), "wechsel": 4,
                 "codes_neu": 4, "werte_entfallen": 1}
    # „Code behalten“: nur dort neu, wo die Nummer in der Zielkategorie schon vergeben ist
    r = c.post(f"{API}/vorschau", json={"produkte": alle, "aenderung": {"kategorie_id": ziel, "code": "behalten"}}).json()
    assert r["codes_neu"] == 0


def test_kategorie_wechseln_mit_neuen_codes_und_rueckgaengig(lage, app):
    c, ids, stoff = lage["client"], lage["ids"], lage["stoff"]
    conn = connect(app.state.db_path)
    conn.execute(f"UPDATE produkt SET etikett = 'gedruckt' WHERE inventar_nr = {ids[0]}")
    conn.close()
    vorher = [_p(c, i)["code"] for i in ids]
    r = c.post(API, json={"produkte": ids, "aenderung": {"kategorie_id": stoff["id"], "code": "neu"}}).json()
    assert r["geaendert"] == 3
    danach = [_p(c, i) for i in ids]
    assert {p["kategorie_name"] for p in danach} == {"Stoff"}
    assert [p["code"] for p in danach] == [f"ST-{n:03d}-{i:03d}" for n, i in zip((2, 3, 4), ids)]
    assert danach[0]["etikett"] == "neu_drucken"
    z = c.post(f"{API}/rueckgaengig/{r['rueckgaengig']}").json()
    assert z == {"zurueck": 3, "uebersprungen": 0}
    wieder = [_p(c, i) for i in ids]
    assert [p["code"] for p in wieder] == vorher and wieder[0]["etikett"] == "gedruckt"
    # ein zweites Mal geht nicht
    assert c.post(f"{API}/rueckgaengig/{r['rueckgaengig']}").status_code == 410


def test_rueckgaengig_bringt_filterwerte_zurueck(lage):
    c, leinen = lage["client"], lage["leinen"]
    werte = _p(c, leinen)["werte"]
    r = c.post(API, json={"produkte": [leinen], "aenderung": {"kategorie_id": lage["fliese"]["id"], "code": "behalten"}}).json()
    assert _p(c, leinen)["werte"] == {}
    c.post(f"{API}/rueckgaengig/{r['rueckgaengig']}")
    assert _p(c, leinen)["werte"] == werte


def test_inzwischen_geaenderte_produkte_bleiben(lage):
    c, ids = lage["client"], lage["ids"]
    r = c.post(API, json={"produkte": ids, "aenderung": {"marke": "Kvadrat"}}).json()
    p = _p(c, ids[1])
    c.put(f"/api/produkte/{ids[1]}", json={**p, "name": "Stoff eins"})
    z = c.post(f"{API}/rueckgaengig/{r['rueckgaengig']}").json()
    assert z == {"zurueck": 2, "uebersprungen": 1}
    assert _p(c, ids[1])["marke"] == "Kvadrat" and _p(c, ids[0])["marke"] is None


def test_marke_art_farben(lage):
    c, ids = lage["client"], lage["ids"]
    c.post(API, json={"produkte": ids, "aenderung": {"marke": " Kvadrat ", "art": "digital",
                                                     "farben_hinzu": ["grau"], "farben_weg": ["beige"]}})
    for i in ids:
        p = _p(c, i)
        assert (p["marke"], p["art"], p["farben"]) == ("Kvadrat", "digital", ["grau"])
    treffer = c.get("/api/bibliothek", params={"q": "kvadrat"}).json()["gesamt"]
    assert treffer == 3


def test_filterwerte_nur_in_derselben_kategorie(lage):
    c, fl = lage["client"], lage["fliese"]
    rh = fl["filter"][0]
    a = c.post("/api/produkte", json={"name": "A", "kategorie_id": fl["id"]}).json()["inventar_nr"]
    b = c.post("/api/produkte", json={"name": "B", "kategorie_id": fl["id"],
                                      "werte": {str(rh["id"]): rh["optionen"][0]["id"]}}).json()["inventar_nr"]
    r11 = rh["optionen"][1]["id"]
    assert c.post(API, json={"produkte": [a, b], "aenderung": {"werte": {str(rh["id"]): r11}}}).status_code == 200
    assert _p(c, a)["werte"] == {str(rh["id"]): r11} == _p(c, b)["werte"]
    # gemischte Kategorien → abgelehnt
    r = c.post(API, json={"produkte": [a, lage["leinen"]], "aenderung": {"werte": {str(rh["id"]): r11}}})
    assert r.status_code == 422


@pytest.mark.parametrize("daten", [{"produkte": []}, {"produkte": [999]}, {"produkte": ["1"]},
                                   {"produkte": [1], "aenderung": {"farben_hinzu": ["lila"]}}])
def test_ungueltig(lage, daten):
    assert lage["client"].post(API, json={"aenderung": {}, **daten}).status_code in (404, 422)


def test_alle_treffer_als_nummern(lage):
    c, sonst = lage["client"], lage["sonst"]
    r = c.get("/api/bibliothek", params={"kategorie": sonst["id"], "ids": 1}).json()
    assert sorted(r["ids"]) == sorted(lage["ids"])
