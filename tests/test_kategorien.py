"""Kategorien und Filter über die API (SPEC 6.2, 6.3, D-011)."""
from __future__ import annotations

import pytest

from app.db import connect, transaction
from app.services import nummern

API = "/api/kategorien"


def _kat(client, name):
    return next(k for k in client.get(API).json()["kategorien"] if k["name"] == name)


def _neu(client, name="Fliese", praefix=None):
    r = client.post(API, json={"name": name, "praefix": praefix})
    assert r.status_code == 201, r.text
    return _kat(client, name)


def _speichern(client, kat, **aenderung):
    daten = {"name": kat["name"], "praefix": kat["praefix"], "version": kat["version"], "filter": kat["filter"], **aenderung}
    return client.put(f"{API}/{kat['id']}", json=daten)


def _produkt(app, kat_id, etikett="ungedruckt"):
    conn = connect(app.state.db_path)
    with transaction(conn):
        inv = nummern.naechste_inventar_nr(conn)
        nr = nummern.naechste_kategorie_nr(conn, kat_id)
        praefix = conn.execute("SELECT praefix FROM kategorie WHERE id = ?", (kat_id,)).fetchone()[0]
        conn.execute("INSERT INTO produkt (inventar_nr, kategorie_id, code_praefix, kategorie_nr, name, etikett) "
                     "VALUES (?, ?, ?, ?, 'P', ?)", (inv, kat_id, praefix, nr, etikett))
    conn.close()
    return inv


def test_neu_mit_vorgeschlagenem_praefix(client):
    assert client.get(f"{API}/praefix-vorschlag", params={"name": "Fliese"}).json() == {"praefix": "FL"}
    fl = _neu(client)
    assert fl["praefix"] == "FL" and fl["produkte"] == 0 and fl["filter"] == []
    # FL ist vergeben → nächster Buchstabe aus dem Namen
    assert client.get(f"{API}/praefix-vorschlag", params={"name": "Flachstahl"}).json() == {"praefix": "FA"}
    assert client.get(f"{API}/praefix-vorschlag", params={"name": "Öl"}).json() == {"praefix": "OE"}


def test_sonstiges_steht_am_ende(client):
    _neu(client, "Holz")
    assert [k["name"] for k in client.get(API).json()["kategorien"]] == ["Holz", "Sonstiges"]


@pytest.mark.parametrize("daten, feld", [({"name": " "}, "name"), ({"name": "Holz", "praefix": "H"}, "praefix"),
                                          ({"name": "Holz", "praefix": "XX"}, "praefix"), ({"name": "sonstiges"}, "name")])
def test_eingabefehler_mit_feld(client, daten, feld):
    r = client.post(API, json=daten)
    assert r.status_code == 422 and r.json()["fehler"]["feld"] == feld


def test_praefix_klein_eingegeben_wird_gross(client):
    assert _neu(client, "Holz", "ho")["praefix"] == "HO"


def test_filter_aller_typen_speichern_und_sortieren(client):
    fl = _neu(client)
    filter_ = [
        {"name": "Rutschhemmung", "typ": "einfach", "optionen": [{"name": "R9"}, {"name": "R10"}, {"name": "R11"}]},
        {"name": "Stärke", "typ": "mass", "einheit": "mm"},
        {"name": "Oberfläche", "typ": "mehrfach", "optionen": [{"name": "Matt"}, {"name": "Strukturiert"}]},
        {"name": "Rektifiziert", "typ": "janein"},
    ]
    assert _speichern(client, fl, filter=filter_).status_code == 200
    fl = _kat(client, "Fliese")
    assert [f["name"] for f in fl["filter"]] == ["Rutschhemmung", "Stärke", "Oberfläche", "Rektifiziert"]
    assert [o["name"] for o in fl["filter"][0]["optionen"]] == ["R9", "R10", "R11"]
    assert fl["filter"][1]["einheit"] == "mm" and fl["filter"][3]["optionen"] == []
    # umsortieren, umbenennen, Auswahl ergänzen – Kennungen bleiben
    ids = [f["id"] for f in fl["filter"]]
    neu = list(reversed(fl["filter"]))
    neu[-1] = {**neu[-1], "name": "R-Wert", "optionen": [*neu[-1]["optionen"], {"name": "R12"}]}
    assert _speichern(client, fl, filter=neu).status_code == 200
    fl = _kat(client, "Fliese")
    assert [f["id"] for f in fl["filter"]] == list(reversed(ids))
    assert fl["filter"][-1]["name"] == "R-Wert" and len(fl["filter"][-1]["optionen"]) == 4


def test_namen_tauschen_scheitert_nicht_an_eindeutigkeit(client):
    fl = _neu(client)
    _speichern(client, fl, filter=[{"name": "A", "typ": "janein"}, {"name": "B", "typ": "janein"}])
    fl = _kat(client, "Fliese")
    a, b = fl["filter"]
    r = _speichern(client, fl, filter=[{**a, "name": "B"}, {**b, "name": "A"}])
    assert r.status_code == 200, r.text


@pytest.mark.parametrize("filter_, text", [
    ([{"name": "X", "typ": "janein"}, {"name": "x", "typ": "janein"}], "schon"),
    ([{"name": "Stärke", "typ": "mass"}], "Einheit"),
    ([{"name": "Oberfläche", "typ": "mehrfach", "optionen": [{"name": " "}]}], "mindestens eine"),
    ([{"name": "Oberfläche", "typ": "einfach", "optionen": [{"name": "Matt"}, {"name": "matt"}]}], "schon"),
    ([{"name": "Was", "typ": "freitext"}], "Unbekannte"),
])
def test_filterfehler(client, filter_, text):
    r = _speichern(client, _neu(client), filter=filter_)
    assert r.status_code == 422 and text in r.json()["fehler"]["text"]


def test_typ_eines_bestehenden_filters_bleibt(client):
    fl = _neu(client)
    _speichern(client, fl, filter=[{"name": "Rektifiziert", "typ": "janein"}])
    fl = _kat(client, "Fliese")
    r = _speichern(client, fl, filter=[{**fl["filter"][0], "typ": "mass", "einheit": "mm"}])
    assert r.status_code == 422


def test_veraltete_version_wird_abgelehnt(client):
    fl = _neu(client)
    assert _speichern(client, fl, name="Fliesen").status_code == 200
    r = _speichern(client, fl, name="Kacheln")          # noch mit der alten Version
    assert r.status_code == 409 and "anderen Gerät" in r.json()["fehler"]["text"]


def test_nutzung_wird_gezaehlt_und_geloeschte_auswahl_nimmt_werte_mit(client, app):
    fl = _neu(client)
    _speichern(client, fl, filter=[{"name": "Oberfläche", "typ": "mehrfach", "optionen": [{"name": "Matt"}, {"name": "Glänzend"}]}])
    fl = _kat(client, "Fliese")
    f, (matt, glaenzend) = fl["filter"][0], fl["filter"][0]["optionen"]
    inv = _produkt(app, fl["id"])
    conn = connect(app.state.db_path)
    conn.execute("INSERT INTO produkt_wert (produkt_id, filter_id, option_id) VALUES (?, ?, ?)", (inv, f["id"], glaenzend["id"]))
    conn.close()
    fl = _kat(client, "Fliese")
    assert fl["filter"][0]["produkte"] == 1 and [o["produkte"] for o in fl["filter"][0]["optionen"]] == [0, 1]
    _speichern(client, fl, filter=[{**fl["filter"][0], "optionen": [matt]}])
    conn = connect(app.state.db_path)
    assert conn.execute("SELECT count(*) FROM produkt_wert").fetchone()[0] == 0
    conn.close()


def test_praefix_aendern_aendert_codes_und_markiert_gedruckte_etiketten(client, app):
    fl = _neu(client)
    a, b = _produkt(app, fl["id"], "gedruckt"), _produkt(app, fl["id"])
    fl = _kat(client, "Fliese")
    assert fl["codes_mit_praefix"] == 2
    r = _speichern(client, fl, praefix="FI")
    assert r.json()["codes_geaendert"] == 2
    conn = connect(app.state.db_path)
    zeilen = {r[0]: (r[1], r[2]) for r in conn.execute("SELECT inventar_nr, code_praefix, etikett FROM produkt")}
    conn.close()
    assert zeilen == {a: ("FI", "neu_drucken"), b: ("FI", "ungedruckt")}


def test_nur_leere_kategorie_loeschbar(client, app):
    fl, ho = _neu(client), _neu(client, "Holz")
    _produkt(app, fl["id"])
    r = client.delete(f"{API}/{fl['id']}")
    assert r.status_code == 409 and "enthält 1 Produkt und" in r.json()["fehler"]["text"]
    assert client.delete(f"{API}/{ho['id']}").status_code == 200
    sonst = _kat(client, "Sonstiges")
    assert client.delete(f"{API}/{sonst['id']}").status_code == 409
    assert [k["name"] for k in client.get(API).json()["kategorien"]] == ["Fliese", "Sonstiges"]


def test_fremde_seite_kann_nichts_anlegen(client):
    r = client.post(API, json={"name": "Böse"}, headers={"origin": "http://boese.example"})
    assert r.status_code == 403
