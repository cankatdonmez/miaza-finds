"""„Wird bearbeitet“ (SPEC 4.9, D-044): Hinweis im Speicher, wer und seit wann, fällt von selbst weg."""
from __future__ import annotations

import pytest

from app.services import bearbeitung

A = {"art": "produkt", "id": 7, "geraet": "geraet-aaaa"}
B = {"art": "produkt", "id": 7, "geraet": "geraet-bbbb"}


@pytest.fixture
def uhr(monkeypatch):
    zeit = {"s": 1000.0}
    monkeypatch.setattr(bearbeitung, "jetzt", lambda: zeit["s"])
    return zeit


def test_zweites_geraet_sieht_wer_bearbeitet(client, uhr):
    selin = client.post("/api/personen", json={"name": "Selin"}).json()["id"]
    assert client.post("/api/bearbeitung", json={**A, "person_id": selin}).json() == {"frei": True}
    for _ in range(2):                                                                   # Signal alle 2 Minuten
        uhr["s"] += 2 * 60
        client.post("/api/bearbeitung/signal", json={**A, "geaendert": True})
    assert client.post("/api/bearbeitung", json=B).json() == {"frei": False, "wer": "Selin", "minuten": 4}
    assert client.get("/api/bearbeitung", params=B).json()["frei"] is False
    assert client.post("/api/bearbeitung", json=A).json() == {"frei": True}            # gleiches Gerät darf weiter
    # anderer Datensatz ist frei
    assert client.post("/api/bearbeitung", json={**B, "id": 8}).json() == {"frei": True}


def test_ende_und_ohne_person(client, uhr):
    client.post("/api/bearbeitung", json=A)
    assert client.post("/api/bearbeitung", json=B).json()["wer"] is None             # Seite zeigt „Ein anderes Gerät“
    client.post("/api/bearbeitung/ende", json=B)                                         # fremdes Ende zählt nicht
    assert client.get("/api/bearbeitung", params=B).json()["frei"] is False
    assert client.post("/api/bearbeitung/ende", json=A).status_code == 204
    assert client.get("/api/bearbeitung", params=B).json() == {"frei": True}


def test_faellt_von_selbst_weg(client, uhr):
    client.post("/api/bearbeitung", json=A)
    uhr["s"] += 100
    assert client.post("/api/bearbeitung/signal", json={**A, "geaendert": True}).json() == {"frei": True}
    uhr["s"] += bearbeitung.SIGNAL_MAX + 1                                               # Gerät schweigt 2 Minuten
    assert client.get("/api/bearbeitung", params=B).json() == {"frei": True}
    assert client.post("/api/bearbeitung/signal", json=A).json() == {"frei": False, "abgelaufen": True}
    # Signale ohne Änderung halten es nur 15 Minuten
    client.post("/api/bearbeitung", json=A)
    for _ in range(16):
        uhr["s"] += 60
        client.post("/api/bearbeitung/signal", json={**A, "geaendert": False})
    assert client.get("/api/bearbeitung", params=B).json() == {"frei": True}


def test_falsche_angaben(client):
    assert client.post("/api/bearbeitung", json={**A, "art": "sammlung"}).status_code == 422
    assert client.post("/api/bearbeitung", json={**A, "geraet": "kurz"}).status_code == 422
    assert client.post("/api/bearbeitung", json={**A, "id": "7"}).status_code == 422
