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
    assert r["bogen"]["spalten"] * r["bogen"]["zeilen"] == 24       # A4, 3 × 8 (D-033)
    assert [p["name"] for p in client.get("/api/etiketten", params={"q": "FL-021"}).json()["produkte"]] == ["Terrazzo 20"]


def test_bogen_passt_auf_a4():
    b = bogen()
    rechts = b["rand_links_mm"] + b["spalten"] * b["breite_mm"] + (b["spalten"] - 1) * b["abstand_x_mm"]
    unten = b["rand_oben_mm"] + b["zeilen"] * b["hoehe_mm"] + (b["zeilen"] - 1) * b["abstand_y_mm"]
    assert rechts <= b["seite_breite_mm"] and unten <= b["seite_hoehe_mm"]


def test_pdf_boegen_mit_name_und_code(client, produkte):
    mehr = [client.post("/api/produkte", json={"name": f"Extra {i}", "kategorie_id": produkte["kid"]}).json()["inventar_nr"] for i in range(4)]
    r = client.get("/api/etiketten/pdf", params={"nr": produkte["ids"] + mehr})
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    pdf = PdfReader(io.BytesIO(r.content))
    assert len(pdf.pages) == 2                                  # 25 Etiketten, 24 je Bogen
    text = pdf.pages[0].extract_text()
    assert "TERRAZZO" in text and "FL-001-001" in text            # Name in Versalien, ggf. zweizeilig
    # das PDF allein ändert nichts
    assert client.get("/api/etiketten").json()["zahlen"]["ungedruckt"] == 25


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


def test_qr_vorschau_ist_svg(client, produkte):
    r = client.get(f"/api/etiketten/qr/{produkte['ids'][0]}.svg")
    assert r.status_code == 200 and r.headers["content-type"] == "image/svg+xml" and b"<svg" in r.content


def test_qr_adresse_im_netz_statt_localhost(client, monkeypatch):
    from app.routes import api_etiketten
    assert client.get("/api/etiketten").json()["qr_adresse"] == "http://testserver"
    monkeypatch.setenv("MF_NETZ", "1")
    monkeypatch.setattr(api_etiketten, "_netzadresse", lambda: "192.168.1.20")
    lokal = {"host": "localhost:8090"}
    assert client.get("/api/etiketten", headers=lokal).json()["qr_adresse"] == "http://192.168.1.20:8090"
    monkeypatch.setenv("MF_BASIS_URL", "https://finds.example.at/")
    assert client.get("/api/etiketten", headers=lokal).json()["qr_adresse"] == "https://finds.example.at"


def test_fach_etiketten(client):
    from tests.test_plan import KLEIN, QUADRAT, _entwurf
    p = client.put("/api/plan", json=_entwurf(client.get("/api/plan").json(),
                   raeume=[{"id": None, "schluessel": "a", "nr": 2, "punkte": QUADRAT}],
                   einheiten=[{"id": None, "raum": "a", "nr": 2, "name": "Schrank links", "punkte": KLEIN}])).json()["plan"]
    e = p["einheiten"][0]
    p = client.put(f"/api/einheiten/{e['id']}/faecher", json={"version": p["version"], "faecher": [
        {"id": None, "nr": n, "name": "Obere Schublade" if n == 2 else "", "punkte": [[0, 0], [10, 0], [10, 10]]}
        for n in (1, 2, 10)]}).json()["plan"]
    r = client.get("/api/etiketten/faecher").json()
    assert [f["code"] for f in r["faecher"]] == ["2.2.1", "2.2.2", "2.2.10"] and r["zahlen"]["ungedruckt"] == 3
    assert [f["code"] for f in client.get("/api/etiketten/faecher", params={"q": "schrank 2.2.10"}).json()["faecher"]] == ["2.2.10"]
    ids = [f["id"] for f in r["faecher"]]
    pdf = PdfReader(io.BytesIO(client.get("/api/etiketten/faecher/pdf", params={"id": ids}).content))
    text = pdf.pages[0].extract_text()
    # unter dem Code: Name des Fachs, sonst der Einheit (D-020)
    assert "2.2.10" in text and "Schrank links" in text and "Obere Schublade" in text
    assert [f["beschreibung"] for f in r["faecher"]] == ["Schrank links", "Obere Schublade", "Schrank links"]
    vorher = client.post("/api/etiketten/faecher/gedruckt", json={"faecher": ids}).json()["vorher"]
    assert client.get("/api/etiketten/faecher").json()["zahlen"]["ungedruckt"] == 0
    assert client.post("/api/etiketten/faecher/zuruecksetzen", json={"vorher": vorher}).json()["zurueck"] == 3
    assert client.get(f"/api/etiketten/qr/fach/{ids[0]}.svg").status_code == 200
    assert client.get(f"/f/{ids[0]}", follow_redirects=False).headers["location"] == f"/buero?fach={ids[0]}"


def test_etikett_nach_vorlage_und_neu_drucken(client):
    """D-033: Name in Versalien, Marke, Artikelnummer, Maße, Merkmale mit „ | “; geänderter Inhalt → neu drucken."""
    kat = client.post("/api/kategorien", json={"name": "Wandfliese", "praefix": "WF"}).json()
    kat = next(k for k in kat["kategorien"] if k["id"] == kat["id"])
    kat = next(k for k in client.put(f"/api/kategorien/{kat['id']}", json={**kat, "filter": [
        {"name": "Art", "typ": "einfach", "optionen": [{"name": "Wandfliese"}]},
        {"name": "Rutschhemmung", "typ": "einfach", "optionen": [{"name": "R9"}]},
        {"name": "Rektifiziert", "typ": "janein"}]}).json()["kategorien"] if k["id"] == kat["id"])
    f = {x["name"]: x for x in kat["filter"]}
    p = client.post("/api/produkte", json={
        "name": "Bumpy Beige", "kategorie_id": kat["id"], "marke": "Seramiksan", "artikelnummer": "851102",
        "abmessungen": "B10 * L30 * D9", "werte": {str(f["Art"]["id"]): f["Art"]["optionen"][0]["id"],
                                                   str(f["Rutschhemmung"]["id"]): f["Rutschhemmung"]["optionen"][0]["id"],
                                                   str(f["Rektifiziert"]["id"]): False}}).json()
    nr = p["inventar_nr"]
    eintrag = next(x for x in client.get("/api/etiketten").json()["produkte"] if x["inventar_nr"] == nr)
    assert eintrag["info"] == ["Seramiksan", "851102", "B10 * L30 * D9", "Wandfliese | R9"]
    text = PdfReader(io.BytesIO(client.get("/api/etiketten/pdf", params={"nr": [nr]}).content)).pages[0].extract_text()
    for teil in ("BUMPY", "BEIGE", "SERAMIKSAN", "851102", "WANDFLIESE | R9", "WF-001-"):
        assert teil in text
    assert client.get("/api/produkte?q=851102").status_code in (200, 404, 405)
    client.post("/api/etiketten/gedruckt", json={"produkte": [nr]})
    p = client.get(f"/api/produkte/{nr}").json()
    daten = {k: p[k] for k in ("name", "art", "kategorie_id", "marke", "artikelnummer", "abmessungen", "link", "anzahl",
                               "notiz", "farben", "werte", "version")}
    # Notiz steht nicht auf dem Etikett: bleibt gedruckt
    p = client.put(f"/api/produkte/{nr}", json={**daten, "notiz": "nur intern"}).json()
    assert p["etikett"] == "gedruckt"
    p = client.put(f"/api/produkte/{nr}", json={**daten, "notiz": "nur intern", "version": p["version"], "artikelnummer": "851103"}).json()
    assert p["etikett"] == "neu_drucken"


def test_langes_wort_bleibt_im_etikett(client, produkte):
    """Ein einzelnes langes Wort wird kleiner gesetzt, notfalls gekürzt – nie über den Rand (D-033)."""
    from app.services import etiketten
    from reportlab.pdfbase import pdfmetrics
    etiketten._schriften()
    nr = client.post("/api/produkte", json={"name": "Feinsteinzeugfliesenplattenmuster", "kategorie_id": produkte["kid"]}).json()["inventar_nr"]
    text = PdfReader(io.BytesIO(client.get("/api/etiketten/pdf", params={"nr": [nr]}).content)).pages[0].extract_text()
    zeile = text.splitlines()[0]
    b = etiketten.bogen()
    breite_pt = (b["breite_mm"] - etiketten.TEXT_LINKS - etiketten.TEXT_RAND_RECHTS) / 25.4 * 72
    assert pdfmetrics.stringWidth(zeile, "Figtree-SemiBold", etiketten.NAME_MIN_PT) <= breite_pt + 0.5


def test_etikett_mittig_mit_rand(client, produkte):
    """D-034: Inhalt waagerecht und senkrecht mittig, überall mindestens 3 mm Rand; „miaza“ steht drauf."""
    import pypdfium2 as pdfium
    from app.services import etiketten
    r = client.get("/api/etiketten/pdf", params={"nr": produkte["ids"][:1]})
    assert "miaza" in PdfReader(io.BytesIO(r.content)).pages[0].extract_text()
    k = 6
    bild = pdfium.PdfDocument(r.content)[0].render(scale=k).to_pil().convert("L")
    b = etiketten.bogen()
    pt = lambda v: v / 25.4 * 72 * k
    zelle = bild.crop((int(pt(b["rand_links_mm"])), int(pt(b["rand_oben_mm"])),
                       int(pt(b["rand_links_mm"] + b["breite_mm"])), int(pt(b["rand_oben_mm"] + b["hoehe_mm"]))))
    px, (w, h) = zelle.load(), zelle.size
    dunkel = [(x, y) for x in range(w) for y in range(h) if px[x, y] < 128]
    mm_ = lambda p: p / k / 72 * 25.4
    links, rechts = mm_(min(x for x, _ in dunkel)), mm_(w - max(x for x, _ in dunkel))
    oben, unten = mm_(min(y for _, y in dunkel)), mm_(h - max(y for _, y in dunkel))
    assert min(links, rechts, oben, unten) >= 3
    assert abs(links - rechts) < 1 and abs(oben - unten) < 1
