"""Einzelerfassung über die API (SPEC 6.2): Pflichtfeld, Code, Werte, Preis, Kategoriewechsel, Löschen, Fotos."""
from __future__ import annotations

import io
from datetime import date

import pytest
from PIL import Image

from app import zeit
from app.services.produkte import preis_lesen
from app.services.suche import normalisieren

API = "/api/produkte"


@pytest.fixture
def tag(monkeypatch):
    stand = {"heute": date(2026, 11, 1)}
    monkeypatch.setattr(zeit, "heute", lambda: stand["heute"])
    return stand


def _kategorie(client, name, praefix, filter_=None):
    kid = client.post("/api/kategorien", json={"name": name, "praefix": praefix}).json()["id"]
    if filter_:
        k = next(k for k in client.get("/api/kategorien").json()["kategorien"] if k["id"] == kid)
        r = client.put(f"/api/kategorien/{kid}", json={"name": name, "praefix": praefix, "version": k["version"], "filter": filter_})
        assert r.status_code == 200, r.text
    return next(k for k in client.get("/api/kategorien").json()["kategorien"] if k["id"] == kid)


@pytest.fixture
def fliese(client):
    return _kategorie(client, "Fliese", "FL", [
        {"name": "Rutschhemmung", "typ": "einfach", "optionen": [{"name": "R10"}, {"name": "R11"}]},
        {"name": "Stärke", "typ": "mass", "einheit": "mm"},
        {"name": "Oberfläche", "typ": "mehrfach", "optionen": [{"name": "Matt"}, {"name": "Glänzend"}]},
        {"name": "Rektifiziert", "typ": "janein"},
    ])


def _neu(client, kategorie_id, **felder):
    r = client.post(API, json={"name": "Terrazzo", "kategorie_id": kategorie_id, **felder})
    assert r.status_code == 201, r.text
    return r.json()


def _jpeg(breite=1200, hoehe=800, fmt="JPEG"):
    puffer = io.BytesIO()
    Image.new("RGB", (breite, hoehe), (190, 90, 60)).save(puffer, fmt)
    return puffer.getvalue()


def test_kuerzester_weg_nur_name(client, fliese):
    p = _neu(client, fliese["id"])
    assert p["code"] == "FL-001-001" and p["art"] == "physisch" and p["etikett"] == "ungedruckt"
    assert p["farben"] == [] and p["preis"] is None and p["werte"] == {} and p["fotos"] == []


def test_name_ist_pflicht(client, fliese):
    r = client.post(API, json={"name": "  ", "kategorie_id": fliese["id"]})
    assert r.status_code == 422 and r.json()["fehler"]["feld"] == "name"


def test_alle_felder_und_werte(client, fliese, tag):
    f = {x["name"]: x for x in fliese["filter"]}
    r11 = f["Rutschhemmung"]["optionen"][1]["id"]
    matt, glaenzend = (o["id"] for o in f["Oberfläche"]["optionen"])
    p = _neu(client, fliese["id"], marke="Mutina", abmessungen="60 × 120 cm", link="mutina.it/terrazzo", anzahl=3,
             notiz="Muster vom Messestand", farben=["orange", "beige"], preis={"betrag": "1.234,5", "einheit": "m2"},
             werte={str(f["Rutschhemmung"]["id"]): r11, str(f["Stärke"]["id"]): "10,5",
                    str(f["Oberfläche"]["id"]): [matt, glaenzend], str(f["Rektifiziert"]["id"]): True})
    assert p["link"] == "https://mutina.it/terrazzo" and p["anzahl"] == 3
    assert sorted(p["farben"]) == ["beige", "orange"]
    assert p["preis"] == {"cent": 123450, "einheit": "m2", "datum": "2026-11-01"}
    assert p["werte"] == {str(f["Rutschhemmung"]["id"]): r11, str(f["Stärke"]["id"]): 10.5,
                          str(f["Oberfläche"]["id"]): [matt, glaenzend], str(f["Rektifiziert"]["id"]): True}


def test_merkmale_zum_anzeigen(client, fliese):
    f = {x["name"]: x for x in fliese["filter"]}
    p = _neu(client, fliese["id"], werte={str(f["Stärke"]["id"]): "10,5", str(f["Rektifiziert"]["id"]): False,
                                          str(f["Oberfläche"]["id"]): [o["id"] for o in f["Oberfläche"]["optionen"]]})
    assert p["merkmale"] == [{"name": "Stärke", "wert": "10,5 mm"}, {"name": "Oberfläche", "wert": "Matt, Glänzend"},
                             {"name": "Rektifiziert", "wert": "Nein"}]
    assert client.get(f"/produkt/{p['inventar_nr']}/bearbeiten").status_code == 200


@pytest.mark.parametrize("text, cent", [("36,50", 3650), ("1.234,56", 123456), ("10", 1000), ("0,5", 50), ("12 €", 1200)])
def test_preis_deutsch(text, cent):
    assert preis_lesen(text) == cent


@pytest.mark.parametrize("text", ["36.50", "abc", "1,234", "-3"])
def test_preis_falsch(text):
    with pytest.raises(Exception):
        preis_lesen(text)


def test_preisdatum_nur_bei_aenderung(client, fliese, tag):
    p = _neu(client, fliese["id"], preis={"betrag": "20", "einheit": "m2"})
    tag["heute"] = date(2026, 12, 5)
    p = client.put(f"{API}/{p['inventar_nr']}", json={**p, "kategorie_id": fliese["id"], "preis": {"betrag": "20,00", "einheit": "m2"}}).json()
    assert p["preis"]["datum"] == "2026-11-01"
    p = client.put(f"{API}/{p['inventar_nr']}", json={**p, "kategorie_id": fliese["id"], "preis": {"betrag": "22", "einheit": "m2"}}).json()
    assert p["preis"] == {"cent": 2200, "einheit": "m2", "datum": "2026-12-05"}
    p = client.put(f"{API}/{p['inventar_nr']}", json={**p, "kategorie_id": fliese["id"], "preis": None}).json()
    assert p["preis"] is None


@pytest.mark.parametrize("feld, wert", [("farben", ["lila"]), ("anzahl", -1), ("anzahl", "drei"), ("art", "virtuell"),
                                        ("preis", {"betrag": "5", "einheit": "kiste"})])
def test_ungueltige_felder(client, fliese, feld, wert):
    r = client.post(API, json={"name": "X", "kategorie_id": fliese["id"], feld: wert})
    assert r.status_code == 422


def test_werte_werden_geprueft(client, fliese):
    f = {x["name"]: x for x in fliese["filter"]}
    fremd = _kategorie(client, "Holz", "HO", [{"name": "Holzart", "typ": "einfach", "optionen": [{"name": "Eiche"}]}])
    faelle = [
        {str(f["Stärke"]["id"]): "dick"},
        {str(f["Rutschhemmung"]["id"]): [o["id"] for o in f["Rutschhemmung"]["optionen"]]},
        {str(f["Rutschhemmung"]["id"]): fremd["filter"][0]["optionen"][0]["id"]},
        {str(fremd["filter"][0]["id"]): fremd["filter"][0]["optionen"][0]["id"]},
    ]
    for werte in faelle:
        r = client.post(API, json={"name": "X", "kategorie_id": fliese["id"], "werte": werte})
        assert r.status_code == 422, werte


def test_veraltete_version(client, fliese):
    p = _neu(client, fliese["id"])
    assert client.put(f"{API}/{p['inventar_nr']}", json={**p, "name": "A"}).status_code == 200
    assert client.put(f"{API}/{p['inventar_nr']}", json={**p, "name": "B"}).status_code == 409


def test_kategoriewechsel_code_behalten_oder_neu(client, fliese, app):
    holz = _kategorie(client, "Holz", "HO")
    f = fliese["filter"][0]
    a = _neu(client, fliese["id"], werte={str(f["id"]): f["optionen"][0]["id"]})
    b = _neu(client, fliese["id"])
    # Das Formular schickt nach dem Wechsel die (leeren) Werte der neuen Kategorie; ohne „werte“ entfallen die alten trotzdem
    daten = {k: v for k, v in a.items() if k != "werte"}
    a = client.put(f"{API}/{a['inventar_nr']}", json={**daten, "kategorie_id": holz["id"], "code": "behalten"}).json()
    assert a["code"] == "FL-001-001" and a["kategorie_name"] == "Holz" and a["werte"] == {}
    from app.db import connect
    conn = connect(app.state.db_path)
    conn.execute("UPDATE produkt SET etikett = 'gedruckt' WHERE inventar_nr = ?", (b["inventar_nr"],))
    conn.close()
    b = client.get(f"{API}/{b['inventar_nr']}").json()
    b = client.put(f"{API}/{b['inventar_nr']}", json={**b, "kategorie_id": holz["id"], "code": "neu"}).json()
    # Holz-Nummer 1 trägt schon das verschobene Produkt a → nächste freie ist 2
    assert b["code"] == "HO-002-002" and b["etikett"] == "neu_drucken"
    # ein neues Holz-Produkt überspringt belegte Nummern
    assert _neu(client, holz["id"])["code"] == "HO-003-003"


def test_suchtext_normalisiert(client, fliese, app):
    f = fliese["filter"][0]
    p = _neu(client, fliese["id"], name="Glänzende Straße", marke="Ceramiche", werte={str(f["id"]): f["optionen"][1]["id"]})
    from app.db import connect
    conn = connect(app.state.db_path)
    text = conn.execute("SELECT suchtext FROM produkt WHERE inventar_nr = ?", (p["inventar_nr"],)).fetchone()[0]
    conn.close()
    for wort in ("glaenzende", "strasse", "ceramiche", "fl-001-001", "r11", "fliese"):
        assert wort in text
    assert normalisieren("Café ÄÖÜß") == "cafe aeoeuess"


def test_loeschen_nummer_kommt_nicht_wieder(client, fliese):
    p = _neu(client, fliese["id"])
    assert client.delete(f"{API}/{p['inventar_nr']}").status_code == 200
    assert client.get(f"{API}/{p['inventar_nr']}").status_code == 404
    assert _neu(client, fliese["id"])["inventar_nr"] == p["inventar_nr"] + 1


def test_foto_mit_vorschauen_und_loeschen(client, fliese, app):
    p = _neu(client, fliese["id"])
    r = client.post(f"{API}/{p['inventar_nr']}/fotos", files={"foto": ("a.jpg", _jpeg(3000, 2000), "image/jpeg")})
    assert r.status_code == 201, r.text
    foto = r.json()
    assert (foto["breite"], foto["hoehe"]) == (2400, 1600)
    ordner = app.state.media_dir / "fotos"
    namen = sorted(x.name for x in ordner.iterdir())
    assert namen == sorted([f"{foto['datei']}.jpg", f"{foto['datei']}-320.webp", f"{foto['datei']}-960.webp"])
    assert client.get(f"/media/fotos/{foto['datei']}-320.webp").status_code == 200
    assert client.get(f"{API}/{p['inventar_nr']}").json()["fotos"][0]["id"] == foto["id"]
    assert client.delete(f"{API}/{p['inventar_nr']}/fotos/{foto['id']}").status_code == 200
    assert list(ordner.iterdir()) == []


def test_png_mit_transparenz_und_falsches_format(client, fliese):
    p = _neu(client, fliese["id"])
    puffer = io.BytesIO()
    Image.new("RGBA", (40, 30), (0, 0, 0, 0)).save(puffer, "PNG")
    assert client.post(f"{API}/{p['inventar_nr']}/fotos", files={"foto": ("a.png", puffer.getvalue(), "image/png")}).status_code == 201
    r = client.post(f"{API}/{p['inventar_nr']}/fotos", files={"foto": ("a.txt", b"kein Bild", "text/plain")})
    assert r.status_code == 422 and "Bildformat" in r.json()["fehler"]["text"]


def test_produkt_loeschen_entfernt_fotodateien(client, fliese, app):
    p = _neu(client, fliese["id"])
    client.post(f"{API}/{p['inventar_nr']}/fotos", files={"foto": ("a.jpg", _jpeg(), "image/jpeg")})
    client.delete(f"{API}/{p['inventar_nr']}")
    assert list((app.state.media_dir / "fotos").iterdir()) == []


def test_kategorie_umbenennen_erneuert_suchtext(client, fliese, app):
    p = _neu(client, fliese["id"])
    k = next(k for k in client.get("/api/kategorien").json()["kategorien"] if k["id"] == fliese["id"])
    client.put(f"/api/kategorien/{k['id']}", json={**k, "name": "Keramik"})
    from app.db import connect
    conn = connect(app.state.db_path)
    assert "keramik" in conn.execute("SELECT suchtext FROM produkt WHERE inventar_nr = ?", (p["inventar_nr"],)).fetchone()[0]
    conn.close()
