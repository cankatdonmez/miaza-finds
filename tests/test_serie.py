"""Serienerfassung und schnelles Ergänzen der Namen (SPEC 6.2)."""
from __future__ import annotations

import io

from PIL import Image

API = "/api/produkte"


def _jpeg():
    puffer = io.BytesIO()
    Image.new("RGB", (800, 600), (120, 100, 80)).save(puffer, "JPEG")
    return puffer.getvalue()


def _kat(client):
    return client.post("/api/kategorien", json={"name": "Stoff", "praefix": "ST"}).json()["id"]


def test_ein_foto_ein_produkt_ohne_namen(client):
    kid = _kat(client)
    nummern = []
    for _ in range(3):
        r = client.post(f"{API}/serie", data={"kategorie_id": kid}, files={"foto": ("a.jpg", _jpeg(), "image/jpeg")})
        assert r.status_code == 201, r.text
        nummern.append(r.json()["inventar_nr"])
    assert [client.get(f"{API}/{n}").json()["code"] for n in nummern] == ["ST-001-001", "ST-002-002", "ST-003-003"]
    p = client.get(f"{API}/{nummern[0]}").json()
    assert p["name"] is None and len(p["fotos"]) == 1 and p["etikett"] == "ungedruckt"
    liste = client.get("/api/bibliothek", params={"status": "fehlend"}).json()
    assert liste["gesamt"] == 3 and liste["zaehler"]["fehlend"] == 3


def test_ohne_gueltiges_foto_kein_produkt(client):
    kid = _kat(client)
    r = client.post(f"{API}/serie", data={"kategorie_id": kid}, files={"foto": ("a.txt", b"nein", "text/plain")})
    assert r.status_code == 422
    assert client.get("/api/bibliothek").json()["gesamt"] == 0


def test_letztes_rueckgaengig_ist_loeschen(client):
    kid = _kat(client)
    nr = client.post(f"{API}/serie", data={"kategorie_id": kid}, files={"foto": ("a.jpg", _jpeg(), "image/jpeg")}).json()["inventar_nr"]
    assert client.delete(f"{API}/{nr}").status_code == 200
    assert client.get("/api/bibliothek").json()["gesamt"] == 0


def test_namen_ergaenzen(client):
    kid = _kat(client)
    nr = client.post(f"{API}/serie", data={"kategorie_id": kid}, files={"foto": ("a.jpg", _jpeg(), "image/jpeg")}).json()["inventar_nr"]
    karte = client.get("/api/bibliothek", params={"status": "fehlend"}).json()["produkte"][0]
    r = client.patch(f"{API}/{nr}", json={"name": "  Leinen  natur ", "version": karte["version"]})
    assert r.status_code == 200 and r.json()["name"] == "Leinen natur"
    assert client.get("/api/bibliothek", params={"status": "fehlend"}).json()["gesamt"] == 0
    assert client.get("/api/bibliothek", params={"q": "leinen"}).json()["gesamt"] == 1
    # alte Version → abgelehnt; leerer Name → abgelehnt
    assert client.patch(f"{API}/{nr}", json={"name": "X", "version": karte["version"]}).status_code == 409
    assert client.patch(f"{API}/{nr}", json={"name": " ", "version": r.json()["version"]}).status_code == 422
