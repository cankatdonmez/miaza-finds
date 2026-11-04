"""Grundfarben und Farbtöne je Kategorie (D-031)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.db import connect, migrate

MIGRATIONEN = Path(__file__).parent.parent / "app" / "migrations"


def test_migration_006_ordnet_alte_farben_zu(tmp_path):
    """Terracotta wird Orange, Gold wird Metall; neue Grundfarben sind erlaubt, alte nicht mehr."""
    vor = tmp_path / "vor"
    vor.mkdir()
    for f in sorted(MIGRATIONEN.glob("*.sql")):
        if f.name < "006":
            (vor / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    conn = connect(tmp_path / "m.db")
    migrate(conn, migrations_dir=vor)
    kid = conn.execute("SELECT id FROM kategorie").fetchone()[0]
    for inv in (1, 2):
        conn.execute("INSERT INTO produkt (inventar_nr, kategorie_id, code_praefix, kategorie_nr, name) VALUES (?, ?, 'XX', ?, 'P')",
                     (inv, kid, inv))
    conn.executemany("INSERT INTO produkt_farbe VALUES (?, ?)", [(1, "terracotta"), (1, "beige"), (2, "gold")])
    conn.commit()
    migrate(conn)
    assert sorted(tuple(r) for r in conn.execute("SELECT produkt_id, farbe FROM produkt_farbe")) == [(1, "beige"), (1, "orange"), (2, "metall")]
    conn.execute("INSERT INTO produkt_farbe VALUES (2, 'mehrfarbig')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO produkt_farbe VALUES (2, 'terracotta')")
    conn.close()


def _stoff_mit_toenen(client):
    kat = client.post("/api/kategorien", json={"name": "Stoff", "praefix": "ST"}).json()
    kat = next(k for k in kat["kategorien"] if k["id"] == kat["id"])
    filter_ = [{"id": None, "name": "Farbton", "typ": "farbe", "optionen": [
        {"name": "Weinrot", "hex": "#7B1E2B", "grundfarbe": "rot"},
        {"name": "Burgund", "hex": "#6D1A36", "grundfarbe": "rot"},
        {"name": "Petrol", "grundfarbe": "blau"}]}]
    r = client.put(f"/api/kategorien/{kat['id']}", json={**kat, "filter": filter_})
    assert r.status_code == 200, r.text
    return next(k for k in r.json()["kategorien"] if k["id"] == kat["id"])


def test_farbe_filter_mit_toenen(client):
    kat = _stoff_mit_toenen(client)
    f = kat["filter"][0]
    assert f["typ"] == "mehrfach" and f["farbe"] is True
    assert [(o["name"], o["hex"], o["grundfarbe"]) for o in f["optionen"]] == [
        ("Weinrot", "#7B1E2B", "rot"), ("Burgund", "#6D1A36", "rot"), ("Petrol", None, "blau")]
    # Ton in eine andere Grundfarbe ziehen: gleiche Kennung, neue Grundfarbe
    f["optionen"][2]["grundfarbe"] = "gruen"
    r = client.put(f"/api/kategorien/{kat['id']}", json={**kat, "filter": [f]})
    neu = next(k for k in r.json()["kategorien"] if k["id"] == kat["id"])["filter"][0]["optionen"][2]
    assert neu["id"] == f["optionen"][2]["id"] and neu["grundfarbe"] == "gruen"


@pytest.mark.parametrize("option, text", [
    ({"name": "Weinrot"}, "Grundfarbe"),
    ({"name": "Weinrot", "grundfarbe": "lila"}, "Grundfarbe"),
    ({"name": "Weinrot", "grundfarbe": "rot", "hex": "rot"}, "ungültig"),
])
def test_ton_fehler(client, option, text):
    kat = client.post("/api/kategorien", json={"name": "Stoff", "praefix": "ST"}).json()
    kat = next(k for k in kat["kategorien"] if k["id"] == kat["id"])
    r = client.put(f"/api/kategorien/{kat['id']}", json={**kat, "filter": [{"name": "Farbton", "typ": "farbe", "optionen": [option]}]})
    assert r.status_code == 422 and text in r.json()["fehler"]["text"]


def test_farbfilter_bleibt_farbfilter(client):
    kat = _stoff_mit_toenen(client)
    f = {**kat["filter"][0], "farbe": False}
    r = client.put(f"/api/kategorien/{kat['id']}", json={**kat, "filter": [f]})
    assert r.status_code == 422


def test_grundfarbe_findet_auch_toene(client):
    """„Rot“ findet das rote Produkt und den Stoff mit dem Ton Weinrot, nicht den blauen Stoff."""
    kat = _stoff_mit_toenen(client)
    f = kat["filter"][0]
    weinrot, petrol = f["optionen"][0]["id"], f["optionen"][2]["id"]
    neu = lambda **d: client.post("/api/produkte", json={"kategorie_id": kat["id"], **d}).json()["inventar_nr"]
    a = neu(name="Samt Weinrot", werte={str(f["id"]): [weinrot]})
    b = neu(name="Leinen Petrol", werte={str(f["id"]): [petrol]})
    c = neu(name="Roter Filz", farben=["rot"])
    namen = lambda q: sorted(p["name"] for p in client.get("/api/bibliothek?" + q).json()["produkte"])
    assert namen("farbe=rot") == ["Roter Filz", "Samt Weinrot"]
    assert namen("farbe=blau") == ["Leinen Petrol"]
    assert namen("farbe=rot&farbe=blau") == ["Leinen Petrol", "Roter Filz", "Samt Weinrot"]
    assert namen(f"kategorie={kat['id']}&w{f['id']}={weinrot}") == ["Samt Weinrot"]
    assert a and b and c
