"""Sammlungen (D-047): anlegen, Inhalt, Entfernen mit Rückgängig, Löschen des Produkts; Migration 011."""
from __future__ import annotations

from app.db import connect, migrate


def produkt(client, name="Eichendiele"):
    kid = client.get("/api/kategorien").json()["kategorien"][0]["id"]
    return client.post("/api/produkte", json={"name": name, "kategorie_id": kid}).json()["inventar_nr"]


def namen(r):
    return [s["name"] for s in r["sammlungen"]]


def test_anlegen_eindeutig_und_notiz(client):
    r = client.post("/api/sammlungen", json={"name": "  Villa  Sonne ", "notiz": "Kunde A"})
    assert r.status_code == 201 and namen(r.json()) == ["Villa Sonne"]
    assert client.post("/api/sammlungen", json={"name": "villa sonne"}).status_code == 422
    assert client.post("/api/sammlungen", json={"name": " "}).status_code == 422
    assert client.post("/api/sammlungen", json={"name": "x" * 61}).status_code == 422
    sid = r.json()["id"]
    s = client.put(f"/api/sammlungen/{sid}", json={"name": "Villa Mond", "notiz": ""}).json()
    assert s["name"] == "Villa Mond" and s["notiz"] is None


def test_produkte_hinzufuegen_herausnehmen(client):
    nr = produkt(client)
    sid = client.post("/api/sammlungen", json={"name": "A"}).json()["id"]
    r = client.put(f"/api/sammlungen/{sid}/produkte/{nr}").json()
    assert r["sammlungen"][0]["enthalten"] is True and r["sammlungen"][0]["anzahl"] == 1
    client.put(f"/api/sammlungen/{sid}/produkte/{nr}")                    # doppelt ist harmlos
    s = client.get(f"/api/sammlungen/{sid}").json()
    assert s["anzahl"] == 1 and s["produkte"][0]["name"] == "Eichendiele"
    assert client.put(f"/api/sammlungen/{sid}/produkte/999").status_code == 404
    r = client.delete(f"/api/sammlungen/{sid}/produkte/{nr}").json()
    assert r["sammlungen"][0]["enthalten"] is False and r["sammlungen"][0]["anzahl"] == 0


def test_neue_sammlung_mit_produkt(client):
    nr = produkt(client)
    r = client.post("/api/sammlungen", json={"name": "B", "produkt": nr}).json()
    assert r["sammlungen"][0]["enthalten"] is True
    assert client.get(f"/api/sammlungen?produkt={nr}").json()["sammlungen"][0]["enthalten"] is True


def test_entfernen_und_rueckgaengig_mit_inhalt(client):
    nr = produkt(client)
    sid = client.post("/api/sammlungen", json={"name": "A", "produkt": nr}).json()["id"]
    assert client.delete(f"/api/sammlungen/{sid}").json()["sammlungen"] == []
    assert client.get(f"/api/sammlungen/{sid}").status_code == 404
    # Name ist frei, solange die alte entfernt ist; zwei aktive „A“ gibt es nicht
    b = client.post("/api/sammlungen", json={"name": "A"}).json()["id"]
    assert client.post(f"/api/sammlungen/{sid}/zurueck").status_code == 422
    client.delete(f"/api/sammlungen/{b}")
    assert client.post(f"/api/sammlungen/{sid}/zurueck").json()["sammlungen"][0]["anzahl"] == 1


def test_produkt_loeschen_leert_sammlung(client):
    nr = produkt(client)
    sid = client.post("/api/sammlungen", json={"name": "A", "produkt": nr}).json()["id"]
    assert client.delete(f"/api/produkte/{nr}").status_code in (200, 204)
    assert client.get(f"/api/sammlungen/{sid}").json()["anzahl"] == 0


def test_seiten_und_menue(client):
    sid = client.post("/api/sammlungen", json={"name": "Villa"}).json()["id"]
    html = client.get("/sammlungen").text
    assert 'href="/sammlungen" aria-current="page"' in html           # Desktop-Seitenleiste
    leiste = html[html.index('class="leiste"'):]
    assert 'href="/mehr" aria-current="page"' in leiste and 'href="/sammlungen"' not in leiste
    assert 'href="/sammlungen"' in client.get("/mehr").text
    assert '<h1 class="seitentitel">Villa</h1>' in client.get(f"/sammlungen/{sid}").text
    assert client.get("/sammlungen/999").status_code == 404


def test_migration_011(tmp_path):
    conn = connect(tmp_path / "m.db")
    migrate(conn)
    conn.execute("INSERT INTO sammlung (name) VALUES ('A')")
    assert conn.execute("SELECT entfernt_am FROM sammlung").fetchone()[0] is None
    conn.close()
