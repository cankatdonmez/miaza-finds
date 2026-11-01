"""Bibliothek: Suche, Filter, Zahlen und Tempo (SPEC 6.1, 8.1)."""
from __future__ import annotations

import time

import pytest

from app.db import connect, transaction
from app.services import produkte

API = "/api/bibliothek"


@pytest.fixture
def bestand(client):
    """Fliese mit Filtern, Holz ohne; fünf Produkte mit unterschiedlichen Merkmalen."""
    kid = client.post("/api/kategorien", json={"name": "Fliese", "praefix": "FL"}).json()["id"]
    k = next(k for k in client.get("/api/kategorien").json()["kategorien"] if k["id"] == kid)
    client.put(f"/api/kategorien/{kid}", json={**k, "filter": [
        {"name": "Rutschhemmung", "typ": "einfach", "optionen": [{"name": "R10"}, {"name": "R11"}]},
        {"name": "Stärke", "typ": "mass", "einheit": "mm"},
        {"name": "Oberfläche", "typ": "mehrfach", "optionen": [{"name": "Matt"}, {"name": "Strukturiert"}]},
        {"name": "Rektifiziert", "typ": "janein"},
    ]})
    fl = next(k for k in client.get("/api/kategorien").json()["kategorien"] if k["id"] == kid)
    f = {x["name"]: x for x in fl["filter"]}
    o = {opt["name"]: opt["id"] for x in fl["filter"] for opt in x["optionen"]}
    ho = client.post("/api/kategorien", json={"name": "Holz", "praefix": "HO"}).json()["id"]

    def neu(**d):
        r = client.post("/api/produkte", json=d)
        assert r.status_code == 201, r.text
        return r.json()["inventar_nr"]

    ids = {
        "terrazzo": neu(name="Terrazzo Rosso", kategorie_id=kid, marke="Mutina", farben=["terracotta"],
                        preis={"betrag": "48,90", "einheit": "m2"},
                        werte={str(f["Rutschhemmung"]["id"]): o["R10"], str(f["Stärke"]["id"]): 10,
                               str(f["Oberfläche"]["id"]): [o["Matt"]], str(f["Rektifiziert"]["id"]): True}),
        "feinstein": neu(name="Feinsteinzeug Grau", kategorie_id=kid, marke="Marazzi", farben=["grau"],
                         preis={"betrag": "29", "einheit": "m2"},
                         werte={str(f["Rutschhemmung"]["id"]): o["R11"], str(f["Stärke"]["id"]): 20,
                                str(f["Oberfläche"]["id"]): [o["Matt"], o["Strukturiert"]], str(f["Rektifiziert"]["id"]): False}),
        "eiche": neu(name="Eiche geölt", kategorie_id=ho, marke="Mafi", farben=["braun", "beige"],
                     preis={"betrag": "95", "einheit": "m2"}),
        "katalog": neu(name="Glänzende Fliesen Katalog", kategorie_id=kid, art="digital"),
    }
    return {"client": client, "ids": ids, "f": f, "o": o, "fliese": kid, "holz": ho}


def _namen(client, **params):
    r = client.get(API, params=params)
    assert r.status_code == 200, r.text
    return [p["name"] for p in r.json()["produkte"]]


def test_ohne_filter_neueste_zuerst(bestand):
    assert _namen(bestand["client"]) == ["Glänzende Fliesen Katalog", "Eiche geölt", "Feinsteinzeug Grau", "Terrazzo Rosso"]


@pytest.mark.parametrize("q, erwartet", [
    ("terrazzo", ["Terrazzo Rosso"]),
    ("glaenzende", ["Glänzende Fliesen Katalog"]),
    ("GLÄNZENDE", ["Glänzende Fliesen Katalog"]),
    ("eiche oel", ["Eiche geölt"]),          # Wortteile genügen
    ("eiche terrazzo", []),                 # jedes Wort muss passen
    ("eiche geoelt", ["Eiche geölt"]),
    ("r11", ["Feinsteinzeug Grau"]),
    ("marazzi", ["Feinsteinzeug Grau"]),
    ("FL-002", ["Feinsteinzeug Grau"]),
])
def test_suche(bestand, q, erwartet):
    assert _namen(bestand["client"], q=q) == erwartet


def test_nummer_allein_findet_das_produkt_zuerst(bestand, app):
    c = bestand["client"]
    inv = bestand["ids"]["eiche"]
    assert _namen(c, q=str(inv))[0] == "Eiche geölt"


def test_art_farbe_marke_preis(bestand):
    c = bestand["client"]
    assert _namen(c, art="digital") == ["Glänzende Fliesen Katalog"]
    assert sorted(_namen(c, farbe=["grau", "beige"])) == ["Eiche geölt", "Feinsteinzeug Grau"]
    assert _namen(c, marke=["Mutina"]) == ["Terrazzo Rosso"]
    assert sorted(_namen(c, preis_min="30", preis_max="100")) == ["Eiche geölt", "Terrazzo Rosso"]


def test_kategoriefilter_oder_innerhalb_und_zwischen(bestand):
    c, f, o = bestand["client"], bestand["f"], bestand["o"]
    kat = {"kategorie": bestand["fliese"]}
    rh, st, ob, rk = (f[n]["id"] for n in ("Rutschhemmung", "Stärke", "Oberfläche", "Rektifiziert"))
    assert sorted(_namen(c, **kat, **{f"w{rh}": [o["R10"], o["R11"]]})) == ["Feinsteinzeug Grau", "Terrazzo Rosso"]
    assert _namen(c, **kat, **{f"w{rh}": o["R10"], f"w{ob}": o["Matt"]}) == ["Terrazzo Rosso"]
    assert _namen(c, **kat, **{f"w{ob}": o["Strukturiert"]}) == ["Feinsteinzeug Grau"]
    assert _namen(c, **kat, **{f"w{st}_min": "12"}) == ["Feinsteinzeug Grau"]
    assert _namen(c, **kat, **{f"w{st}_min": "8", f"w{st}_max": "12,5"}) == ["Terrazzo Rosso"]
    assert _namen(c, **kat, **{f"w{rk}": "nein"}) == ["Feinsteinzeug Grau"]


def test_filter_einer_anderen_kategorie_werden_ignoriert(bestand):
    c, f, o = bestand["client"], bestand["f"], bestand["o"]
    rh = f["Rutschhemmung"]["id"]
    assert _namen(c, kategorie=bestand["holz"], **{f"w{rh}": o["R10"]}) == ["Eiche geölt"]


def test_status_und_zaehler(bestand):
    c = bestand["client"]
    with transaction(conn := connect(c.app.state.db_path)):
        produkte.anlegen(conn, {"kategorie_id": bestand["holz"]}, name_pflicht=False)
    conn.close()
    r = c.get(API).json()
    assert r["zaehler"] == {"gesamt": 5, "am_platz": 0, "in_benutzung": 0, "ausser_haus": 0, "ohne_platz": 4, "fehlend": 1}
    assert _namen(c, status="fehlend") == [None]
    assert "Glänzende Fliesen Katalog" not in _namen(c, status="ohne_platz")


def test_kategoriezahlen_unter_den_uebrigen_filtern(bestand):
    c = bestand["client"]
    r = c.get(API, params={"kategorie": bestand["holz"], "art": "physisch"}).json()
    assert r["kategorien"] == {str(bestand["fliese"]): 2, str(bestand["holz"]): 1}
    assert r["marken"] == ["Mafi", "Marazzi", "Mutina"]


def test_karte_mit_code_preis_und_foto(bestand):
    karte = bestand["client"].get(API, params={"q": "terrazzo"}).json()["produkte"][0]
    assert karte["code"] == "FL-001-001" and karte["kategorie"] == "Fliese" and karte["foto"] is None
    assert karte["preis"]["cent"] == 4890 and karte["preis"]["einheit"] == "m2"


def test_falscher_preis_in_der_adresse(bestand):
    assert bestand["client"].get(API, params={"preis_min": "viel"}).status_code == 422


def test_seiten_und_tempo_bei_3000_produkten(client, app):
    conn = connect(app.state.db_path)
    kid = conn.execute("SELECT id FROM kategorie").fetchone()[0]
    with transaction(conn):
        for i in range(3000):
            inv = produkte.anlegen(conn, {"name": f"Muster {i} {'Eiche' if i % 7 == 0 else 'Stein'}", "kategorie_id": kid,
                                          "marke": f"Marke {i % 40}", "farben": ["grau"] if i % 3 else ["beige"],
                                          "preis": {"betrag": str(10 + i % 90), "einheit": "m2"}})
    conn.close()
    client.get(API)              # warm
    start = time.perf_counter()
    r = client.get(API, params={"q": "eiche", "farbe": "beige", "preis_max": "80"})
    dauer = time.perf_counter() - start
    daten = r.json()
    assert daten["gesamt"] > 0 and len(daten["produkte"]) <= 120
    assert dauer < 0.2, f"Suche dauerte {dauer * 1000:.0f} ms"
    erste = client.get(API).json()
    assert erste["weitere"] and len(erste["produkte"]) == 120
    zweite = client.get(API, params={"seite": 1}).json()
    assert not {p["inventar_nr"] for p in zweite["produkte"]} & {p["inventar_nr"] for p in erste["produkte"]}
