"""Personen des Büros (D-038): anlegen, umbenennen, entfernen mit Rückgängig; Migration 008."""
from __future__ import annotations

import sqlite3

import pytest

from app.db import connect, migrate


def namen(r):
    return [p["name"] for p in r["personen"]]


def test_anlegen_sortiert_und_eindeutig(client):
    client.post("/api/personen", json={"name": "  Selin  "})
    r = client.post("/api/personen", json={"name": "cankat"}).json()
    assert namen(r) == ["cankat", "Selin"]                      # alphabetisch, Leerzeichen gekürzt
    doppelt = client.post("/api/personen", json={"name": "SELIN"})
    assert doppelt.status_code == 422 and "gibt es schon" in doppelt.json()["fehler"]["text"]
    assert client.post("/api/personen", json={"name": " "}).status_code == 422
    assert client.post("/api/personen", json={"name": "x" * 61}).status_code == 422


def test_umbenennen(client):
    a = client.post("/api/personen", json={"name": "Selin"}).json()["id"]
    client.post("/api/personen", json={"name": "Can"})
    assert namen(client.put(f"/api/personen/{a}", json={"name": "Selin K."}).json()) == ["Can", "Selin K."]
    assert client.put(f"/api/personen/{a}", json={"name": "can"}).status_code == 422
    assert client.put("/api/personen/999", json={"name": "X"}).status_code == 404


def test_entfernen_und_rueckgaengig(client):
    a = client.post("/api/personen", json={"name": "Selin"}).json()["id"]
    assert namen(client.delete(f"/api/personen/{a}").json()) == []
    # Name ist wieder frei, solange die alte Person entfernt ist
    b = client.post("/api/personen", json={"name": "Selin"}).json()["id"]
    assert client.post(f"/api/personen/{a}/zurueck").status_code == 422      # zwei aktive „Selin“ gibt es nicht
    client.delete(f"/api/personen/{b}")
    assert namen(client.post(f"/api/personen/{a}/zurueck").json()) == ["Selin"]


def test_migration_008(tmp_path):
    conn = connect(tmp_path / "m.db")
    migrate(conn)
    conn.execute("INSERT INTO person (name) VALUES ('Selin')")
    conn.execute("INSERT INTO person (name, entfernt_am) VALUES ('selin', '2026-11-04')")   # entfernte zählen nicht
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO person (name) VALUES ('SELIN')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO person (name) VALUES ('  ')")
    conn.close()
