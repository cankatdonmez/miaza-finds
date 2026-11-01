"""Produktetiketten (SPEC 6.6): Liste, PDF nach Bogendefinition, gedruckt + Rückgängig, Druckliste."""
from __future__ import annotations

import io

import pytest
from pypdf import PdfReader

from app.db import connect
from app.services.etiketten import bogen


@pytest.fixture
def produkte(client):
    kid = client.post("/api/kategorien", json={"name": "Fliese", "praefix": "FL"}).json()["id"]
    ids = [client.post("/api/produkte", json={"name": f"Terrazzo {i}", "kategorie_id": kid}).json()["inventar_nr"] for i in range(21)]
    digital = client.post("/api/produkte", json={"name": "Katalog", "kategorie_id": kid, "art": "digital"}).json()["inventar_nr"]
    return {"ids": ids, "digital": digital, "kid": kid}


def test_liste_ohne_digitale_und_mit_zahlen(client, produkte):
    r = client.get("/api/etiketten").json()
    assert len(r["produkte"]) == 21 and produkte["digital"] not in {p["inventar_nr"] for p in r["produkte"]}
    assert r["zahlen"] == {"ungedruckt": 21, "neu_drucken": 0}
    assert r["bogen"]["spalten"] * r["bogen"]["zeilen"] == 20
    assert [p["name"] for p in client.get("/api/etiketten", params={"q": "FL-021"}).json()["produkte"]] == ["Terrazzo 20"]


def test_bogen_passt_auf_a4():
    b = bogen()
    breite = b["rand_links_mm"] * 2 + b["spalten"] * b["breite_mm"] + (b["spalten"] - 1) * b["abstand_x_mm"]
    hoehe = b["rand_oben_mm"] * 2 + b["zeilen"] * b["hoehe_mm"] + (b["zeilen"] - 1) * b["abstand_y_mm"]
    assert breite <= b["seite_breite_mm"] and hoehe <= b["seite_hoehe_mm"]


def test_pdf_zwei_boegen_mit_name_und_code(client, produkte):
    r = client.get("/api/etiketten/pdf", params={"nr": produkte["ids"]})
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    pdf = PdfReader(io.BytesIO(r.content))
    assert len(pdf.pages) == 2
    text = pdf.pages[0].extract_text()
    assert "Terrazzo 0" in text and "FL-001-001" in text
    # das PDF allein ändert nichts
    assert client.get("/api/etiketten").json()["zahlen"]["ungedruckt"] == 21


def test_langer_name_wird_gekuerzt(client, produkte):
    nr = client.post("/api/produkte", json={"name": "Sehr langer Produktname " * 4, "kategorie_id": produkte["kid"]}).json()["inventar_nr"]
    text = PdfReader(io.BytesIO(client.get("/api/etiketten/pdf", params={"nr": [nr]}).content)).pages[0].extract_text()
    assert "…" in text


def test_gedruckt_und_rueckgaengig(client, produkte, app):
    ids = produkte["ids"][:3]
    conn = connect(app.state.db_path)
    conn.execute("UPDATE produkt SET etikett = 'neu_drucken' WHERE inventar_nr = ?", (ids[0],))
    conn.close()
    vorher = client.post("/api/etiketten/gedruckt", json={"produkte": ids}).json()["vorher"]
    assert {v["etikett"] for v in vorher} == {"neu_drucken", "ungedruckt"}
    assert client.get("/api/etiketten", params={"zustand": "gedruckt"}).json()["produkte"].__len__() == 3
    assert client.post("/api/etiketten/zuruecksetzen", json={"vorher": vorher}).json() == {"zurueck": 3}
    assert client.get("/api/etiketten").json()["zahlen"] == {"ungedruckt": 20, "neu_drucken": 1}


def test_auf_die_druckliste(client, produkte):
    nr = produkte["ids"][0]
    assert client.post(f"/api/produkte/{nr}/druckliste").json() == {"etikett": "ungedruckt"}
    client.post("/api/etiketten/gedruckt", json={"produkte": [nr]})
    assert client.post(f"/api/produkte/{nr}/druckliste").json() == {"etikett": "neu_drucken"}


def test_unbekannte_nummer(client, produkte):
    assert client.get("/api/etiketten/pdf", params={"nr": [9999]}).status_code == 404
