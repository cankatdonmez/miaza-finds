"""Systembereich (SPEC 6.13, D-006, D-009, D-010): Anmeldung, Schlüssel, Sicherung, Übernahme, Löschen."""
from __future__ import annotations

import io
import sqlite3
import zipfile

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app

API = "/api/system"
DATEN = {"benutzername": "c.doenmez", "passwort": "sehr-geheim-123", "passwort2": "sehr-geheim-123"}


def _einrichten(client) -> tuple[str, dict]:
    r = client.post(f"{API}/einrichten", json=DATEN)
    assert r.status_code == 200, r.text
    return r.json()["schluessel"], {"x-csrf-token": r.json()["csrf"]}


def _jpeg():
    puffer = io.BytesIO()
    Image.new("RGB", (300, 200), (90, 120, 150)).save(puffer, "JPEG")
    return puffer.getvalue()


def _produkt_mit_foto(client, name="Muster"):
    kid = client.get("/api/kategorien").json()["kategorien"][0]["id"]
    nr = client.post("/api/produkte", json={"name": name, "kategorie_id": kid}).json()["inventar_nr"]
    client.post(f"/api/produkte/{nr}/fotos", files={"foto": ("a.jpg", _jpeg(), "image/jpeg")})
    return nr


def test_einrichten_einmal_und_schluessel_form(client):
    assert client.get(f"{API}/stand").json() == {"eingerichtet": False, "angemeldet": False, "csrf": None, "letzte_sicherung": None}
    schluessel, _ = _einrichten(client)
    assert len(schluessel) == 29 and schluessel.count("-") == 4
    assert client.get(f"{API}/stand").json()["angemeldet"] is True
    assert client.post(f"{API}/einrichten", json=DATEN).status_code == 409


@pytest.mark.parametrize("aenderung, feld", [({"passwort": "kurz", "passwort2": "kurz"}, "passwort"),
                                             ({"passwort2": "anders-als-oben"}, "passwort2"), ({"benutzername": " "}, "benutzername")])
def test_einrichten_prueft_eingaben(client, aenderung, feld):
    r = client.post(f"{API}/einrichten", json={**DATEN, **aenderung})
    assert r.status_code == 422 and r.json()["fehler"]["feld"] == feld


def test_ohne_anmeldung_kein_zugang(client):
    _einrichten(client)
    client.post(f"{API}/abmelden")
    for methode, pfad in (("GET", "/uebersicht"), ("POST", "/sicherung"), ("POST", "/loeschen")):
        assert client.request(methode, API + pfad, json={}).status_code == 401


def test_ohne_csrf_kein_aendern(client):
    _einrichten(client)
    assert client.post(f"{API}/sicherung").status_code == 401


def test_anmelden_und_sperre_nach_fehlversuchen(client):
    _einrichten(client)
    client.post(f"{API}/abmelden")
    for _ in range(5):
        assert client.post(f"{API}/anmelden", json={"benutzername": "c.doenmez", "passwort": "falsch"}).status_code == 401
    r = client.post(f"{API}/anmelden", json={"benutzername": "c.doenmez", "passwort": DATEN["passwort"]})
    assert r.status_code == 429


def test_anmelden_gross_klein_beim_namen_egal(client):
    _einrichten(client)
    client.post(f"{API}/abmelden")
    r = client.post(f"{API}/anmelden", json={"benutzername": "C.Doenmez", "passwort": DATEN["passwort"]})
    assert r.status_code == 200 and client.get(f"{API}/stand").json()["angemeldet"]


def test_passwort_vergessen_mit_schluessel(client):
    schluessel, _ = _einrichten(client)
    client.post(f"{API}/abmelden")
    neu = {"passwort": "ganz-neues-pw-1", "passwort2": "ganz-neues-pw-1"}
    assert client.post(f"{API}/vergessen", json={"schluessel": "AAAAA-BBBBB-CCCCC-DDDDD-EEEEE", **neu}).status_code == 401
    # Kleinschreibung und fehlende Bindestriche sind egal
    r = client.post(f"{API}/vergessen", json={"schluessel": schluessel.replace("-", "").lower(), **neu})
    assert r.status_code == 200
    zweiter = r.json()["schluessel"]
    assert zweiter != schluessel
    # alter Schlüssel gilt nicht mehr, neues Passwort schon
    client.post(f"{API}/abmelden")
    assert client.post(f"{API}/vergessen", json={"schluessel": schluessel, **neu}).status_code == 401
    assert client.post(f"{API}/anmelden", json={"benutzername": "c.doenmez", "passwort": neu["passwort"]}).status_code == 200


def test_passwort_aendern_und_schluessel_erneuern(client):
    _, h = _einrichten(client)
    assert client.post(f"{API}/passwort", headers=h, json={"alt": "falsch", "neu": "x" * 12, "neu2": "x" * 12}).status_code == 422
    assert client.post(f"{API}/passwort", headers=h, json={"alt": DATEN["passwort"], "neu": "x" * 12, "neu2": "x" * 12}).status_code == 200
    assert len(client.post(f"{API}/schluessel", headers=h).json()["schluessel"]) == 29


def test_sicherung_erstellen_laden_und_inhalt(client):
    _, h = _einrichten(client)
    _produkt_mit_foto(client)
    r = client.post(f"{API}/sicherung", headers=h).json()
    name = r["name"]
    assert r["sicherungen"][0]["name"] == name
    z = zipfile.ZipFile(io.BytesIO(client.get(f"{API}/sicherung/{name}").content))
    namen = z.namelist()
    assert "finds.db" in namen and "info.json" in namen and sum(n.startswith("media/fotos/") for n in namen) == 3
    assert client.get(f"{API}/sicherung/..%2Ffinds.db").status_code == 404
    assert client.get(f"{API}/stand").json()["letzte_sicherung"] is not None


def test_wiederherstellen_behaelt_verwalter(client, app):
    _, h = _einrichten(client)
    _produkt_mit_foto(client, "Vorher")
    name = client.post(f"{API}/sicherung", headers=h).json()["name"]
    _produkt_mit_foto(client, "Danach")
    client.post(f"{API}/passwort", headers=h, json={"alt": DATEN["passwort"], "neu": "neues-pw-123", "neu2": "neues-pw-123"})
    r = client.post(f"{API}/wiederherstellen", headers=h, json={"name": name})
    assert r.status_code == 200, r.text
    assert r.json()["produkte"] == 1 and r.json()["sicherung_vorher"].startswith("finds-vor-uebernahme-")
    assert [p["name"] for p in client.get("/api/bibliothek").json()["produkte"]] == ["Vorher"]
    assert len(list((app.state.media_dir / "fotos").glob("*"))) == 3
    # das neue Passwort gilt weiter (Verwalter dieser Installation bleibt)
    client.post(f"{API}/abmelden")
    assert client.post(f"{API}/anmelden", json={"benutzername": "c.doenmez", "passwort": "neues-pw-123"}).status_code == 200


def test_umzug_auf_neuen_server(client, tmp_path):
    """Alter Server: Sicherung herunterladen. Neuer Server: einrichten, Datei hochladen (D-009)."""
    _, h = _einrichten(client)
    _produkt_mit_foto(client, "Vom alten Server")
    name = client.post(f"{API}/sicherung", headers=h).json()["name"]
    zip_daten = client.get(f"{API}/sicherung/{name}").content

    neu = create_app(tmp_path / "neu" / "finds.db", tmp_path / "neu" / "media", tmp_path / "neu" / "backups")
    with TestClient(neu, base_url="http://testserver") as c2:
        r = c2.post(f"{API}/einrichten", json={**DATEN, "benutzername": "neu"})
        h2 = {"x-csrf-token": r.json()["csrf"]}
        r = c2.post(f"{API}/uebernehmen", headers=h2, files={"datei": ("alt.zip", zip_daten, "application/zip")})
        assert r.status_code == 200, r.text
        assert [p["name"] for p in c2.get("/api/bibliothek").json()["produkte"]] == ["Vom alten Server"]
        assert c2.get(f"/api/produkte/{c2.get('/api/bibliothek').json()['produkte'][0]['inventar_nr']}").json()["fotos"]
        # weiterhin der Verwalter des neuen Servers
        c2.post(f"{API}/abmelden")
        assert c2.post(f"{API}/anmelden", json={"benutzername": "neu", "passwort": DATEN["passwort"]}).status_code == 200


def test_uebernahme_aus_kopiertem_ordner(client, app, tmp_path):
    _, h = _einrichten(client)
    _produkt_mit_foto(client, "Aus dem Ordner")
    # „Alter Server“: Datenordner kopieren (data/finds.db + media/)
    kopie = tmp_path / "kopie"
    (kopie / "data").mkdir(parents=True)
    quelle = sqlite3.connect(app.state.db_path)
    ziel = sqlite3.connect(kopie / "data" / "finds.db")
    quelle.backup(ziel)
    quelle.close(), ziel.close()
    import shutil
    shutil.copytree(app.state.media_dir, kopie / "media")
    client.post(f"{API}/loeschen", headers=h, json={"was": "produkte"})
    assert client.get("/api/bibliothek").json()["gesamt"] == 0
    r = client.post(f"{API}/uebernehmen-pfad", headers=h, json={"pfad": str(kopie)})
    assert r.status_code == 200, r.text
    assert [p["name"] for p in client.get("/api/bibliothek").json()["produkte"]] == ["Aus dem Ordner"]
    assert client.post(f"{API}/uebernehmen-pfad", headers=h, json={"pfad": str(tmp_path / "gibtsnicht")}).status_code == 404


def test_ungueltige_datei_wird_abgelehnt(client):
    _, h = _einrichten(client)
    puffer = io.BytesIO()
    with zipfile.ZipFile(puffer, "w") as z:
        z.writestr("../boese.txt", "x")
    r = client.post(f"{API}/uebernehmen", headers=h, files={"datei": ("x.zip", puffer.getvalue(), "application/zip")})
    assert r.status_code == 422
    r = client.post(f"{API}/uebernehmen", headers=h, files={"datei": ("x.zip", b"kein zip", "application/zip")})
    assert r.status_code == 422


def test_sicherung_einer_neueren_version_wird_abgelehnt(client, app, tmp_path):
    _, h = _einrichten(client)
    name = client.post(f"{API}/sicherung", headers=h).json()["name"]
    pfad = app.state.sicherung_dir / name
    with zipfile.ZipFile(pfad) as z:
        z.extract("finds.db", tmp_path)
    conn = sqlite3.connect(tmp_path / "finds.db")
    conn.execute("INSERT INTO schema_migration VALUES ('999_zukunft.sql', datetime('now'))")
    conn.commit(), conn.close()
    r = client.post(f"{API}/uebernehmen-pfad", headers=h, json={"pfad": str(tmp_path)})
    assert r.status_code == 422 and "neueren" in r.json()["fehler"]["text"]


def test_loeschen_produkte_und_alles(client, app):
    _, h = _einrichten(client)
    client.post("/api/kategorien", json={"name": "Holz", "praefix": "HO"})
    nr = _produkt_mit_foto(client)
    w = client.get(f"{API}/uebersicht").json()["wirkung"]
    assert w == {"produkte": 1, "fotos": 1, "kategorien": 1}
    r = client.post(f"{API}/loeschen", headers=h, json={"was": "produkte"}).json()
    assert r["wirkung"] == {"produkte": 0, "fotos": 0, "kategorien": 1} and r["sicherung_vorher"].startswith("finds-vor-loeschen-")
    # Nummern kommen nach „Produkte löschen“ nicht wieder …
    assert _produkt_mit_foto(client) == nr + 1
    # … nach „Alles löschen“ beginnt die Zählung neu
    client.post(f"{API}/loeschen", headers=h, json={"was": "alles"})
    assert [k["name"] for k in client.get("/api/kategorien").json()["kategorien"]] == ["Sonstiges"]
    assert _produkt_mit_foto(client) == 1
