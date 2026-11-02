"""Büroplan über die API: Räume, Einheiten, Fächer, Unterlage, Platz (SPEC 6.4–6.7, D-016)."""
from __future__ import annotations

import io

import pytest
from PIL import Image
from reportlab.pdfgen import canvas

QUADRAT = [[0, 0], [100, 0], [100, 100], [0, 100]]
KLEIN = [[10, 10], [30, 10], [30, 30], [10, 30]]


def _entwurf(plan, **aenderung):
    """Entwurf aus dem geladenen Plan (wie der Editor ihn schickt)."""
    raeume = [{**r, "schluessel": f"r{r['id']}"} for r in plan["raeume"]]
    einheiten = [{"id": e["id"], "raum": f"r{e['raum_id']}" if e["raum_id"] else None, "nr": e["nr"],
                  "name": e["name"], "punkte": e["punkte"]} for e in plan["einheiten"]]
    return {"version": plan["version"], "unterlage": plan["unterlage"], "unterlage_im_buero": plan["unterlage_im_buero"],
            "raeume": raeume, "einheiten": einheiten, **aenderung}


@pytest.fixture
def buero(client):
    """Raum 2 mit Einheit 2.1 (zwei Fächer) und einem Produkt in 2.1.1."""
    plan = client.get("/api/plan").json()
    r = client.put("/api/plan", json=_entwurf(plan, raeume=[{"id": None, "schluessel": "a", "nr": 2, "name": "Atelier", "punkte": QUADRAT}],
                                              einheiten=[{"id": None, "raum": "a", "nr": 1, "name": "Schrank links", "punkte": KLEIN}]))
    assert r.status_code == 200, r.text
    plan = r.json()["plan"]
    e = plan["einheiten"][0]
    r = client.put(f"/api/einheiten/{e['id']}/faecher", json={"version": plan["version"], "faecher": [
        {"id": None, "nr": 1, "punkte": [[0, 0], [50, 0], [50, 50], [0, 50]]},
        {"id": None, "nr": 2, "punkte": [[50, 0], [100, 0], [100, 50], [50, 50]]}]})
    assert r.status_code == 200, r.text
    plan = r.json()["plan"]
    kid = client.post("/api/kategorien", json={"name": "Fliese", "praefix": "FL"}).json()["id"]
    nr = client.post("/api/produkte", json={"name": "Terrazzo", "kategorie_id": kid}).json()["inventar_nr"]
    fach1 = plan["einheiten"][0]["faecher"][0]
    assert client.put(f"/api/produkte/{nr}/platz", json={"fach_id": fach1["id"]}).status_code == 200
    return {"plan": client.get("/api/plan").json(), "nr": nr, "fach": fach1["id"], "kid": kid}


def test_leerer_plan(client):
    p = client.get("/api/plan").json()
    assert p["version"] == 1 and p["raeume"] == [] and p["einheiten"] == [] and p["unterlage"] is None


def test_codes_und_zaehlung(client, buero):
    e = buero["plan"]["einheiten"][0]
    assert e["code"] == "2.1" and e["name"] == "Schrank links" and e["produkte"] == 1
    assert [f["code"] for f in e["faecher"]] == ["2.1.1", "2.1.2"]
    f = client.get(f"/api/faecher/{buero['fach']}").json()
    assert f["code"] == "2.1.1" and f["raum_name"] == "Atelier" and [p["name"] for p in f["produkte"]] == ["Terrazzo"]
    assert f["produkte"][0]["code"] == "FL-001-001"


def test_veraltete_version(client, buero):
    alt = buero["plan"]
    assert client.put("/api/plan", json=_entwurf(alt)).status_code == 200
    r = client.put("/api/plan", json=_entwurf(alt))
    assert r.status_code == 409 and "geändert" in r.json()["fehler"]["text"]


def test_wirkung_und_loeschen_macht_ohne_platz(client, buero):
    entwurf = _entwurf(buero["plan"], einheiten=[])
    assert client.post("/api/plan/wirkung", json=entwurf).json() == {"einheiten_weg": 1, "faecher_weg": 2, "ohne_platz": 1, "etiketten_neu": 0}
    assert client.put("/api/plan", json=entwurf).status_code == 200
    assert client.get("/api/plan").json()["ohne_platz"] == 1
    assert client.get(f"/api/faecher/{buero['fach']}").status_code == 404


def test_raumnummer_aendern_markiert_gedruckte_fach_etiketten(client, buero, app):
    from app.db import connect
    conn = connect(app.state.db_path)
    conn.execute("UPDATE fach SET etikett = 'gedruckt'")
    conn.close()
    entwurf = _entwurf(buero["plan"])
    entwurf["raeume"][0]["nr"] = 3
    assert client.post("/api/plan/wirkung", json=entwurf).json()["etiketten_neu"] == 2
    p = client.put("/api/plan", json=entwurf).json()["plan"]
    assert [f["code"] for f in p["einheiten"][0]["faecher"]] == ["3.1.1", "3.1.2"]
    assert {f["etikett"] for f in p["einheiten"][0]["faecher"]} == {"neu_drucken"}
    # das Produkt bleibt im selben Fach, nur der Code ist neu
    assert client.get(f"/api/faecher/{buero['fach']}").json()["code"] == "3.1.1"


def test_raeume_tauschen_nummern(client, buero):
    p = client.put("/api/plan", json=_entwurf(buero["plan"], raeume=[*_entwurf(buero["plan"])["raeume"],
                   {"id": None, "schluessel": "b", "nr": 3, "name": "Küche", "punkte": QUADRAT}])).json()["plan"]
    entwurf = _entwurf(p)
    entwurf["raeume"][0]["nr"], entwurf["raeume"][1]["nr"] = 3, 2
    r = client.put("/api/plan", json=entwurf)
    assert r.status_code == 200, r.text


@pytest.mark.parametrize("aenderung, text", [
    ({"raeume": [{"id": None, "schluessel": "a", "nr": 1, "punkte": QUADRAT}, {"id": None, "schluessel": "b", "nr": 1, "punkte": QUADRAT}]}, "dieselbe Nummer"),
    ({"raeume": [{"id": None, "schluessel": "a", "nr": 0, "punkte": QUADRAT}]}, "1 bis 999"),
    ({"raeume": [{"id": None, "schluessel": "a", "nr": 1, "punkte": [[0, 0], [1, 1]]}]}, "ungültig"),
    ({"einheiten": [{"id": None, "raum": "gibtsnicht", "nr": 1, "punkte": KLEIN}]}, "ungültig"),
])
def test_entwurf_fehler(client, aenderung, text):
    r = client.put("/api/plan", json=_entwurf(client.get("/api/plan").json(), **aenderung))
    assert r.status_code == 422 and text in r.json()["fehler"]["text"]


def test_einheit_ohne_raum(client):
    p = client.put("/api/plan", json=_entwurf(client.get("/api/plan").json(),
                   einheiten=[{"id": None, "raum": None, "nr": 1, "punkte": KLEIN}, {"id": None, "raum": None, "nr": 1, "punkte": KLEIN}])).json()["plan"]
    assert [e["code"] for e in p["einheiten"]] == ["–.1", "–.1"]


def test_faecher_umnummerieren_und_loeschen(client, buero, app):
    from app.db import connect
    conn = connect(app.state.db_path)
    conn.execute("UPDATE fach SET etikett = 'gedruckt'")
    conn.close()
    e = buero["plan"]["einheiten"][0]
    f1, f2 = e["faecher"]
    r = client.put(f"/api/einheiten/{e['id']}/faecher", json={"version": buero["plan"]["version"], "faecher": [
        {"id": f1["id"], "nr": 2, "punkte": f1["punkte"]}, {"id": f2["id"], "nr": 1, "punkte": f2["punkte"]}]})
    assert r.status_code == 200 and r.json()["wirkung"]["etiketten_neu"] == 2
    p = r.json()["plan"]
    r = client.put(f"/api/einheiten/{e['id']}/faecher", json={"version": p["version"], "faecher": []})
    assert r.json()["wirkung"] == {"faecher_weg": 2, "ohne_platz": 1, "etiketten_neu": 0}



def test_fach_name(client, buero, app):
    """Name des Fachs (D-020): gespeichert, im Fach und im Produktdetail; Änderung auf gedrucktem Etikett → neu drucken."""
    e = buero["plan"]["einheiten"][0]
    f1, f2 = e["faecher"]
    faecher = lambda name: [{"id": f1["id"], "nr": 1, "name": name, "punkte": f1["punkte"]},
                            {"id": f2["id"], "nr": 2, "punkte": f2["punkte"]}]
    r = client.put(f"/api/einheiten/{e['id']}/faecher", json={"version": buero["plan"]["version"], "faecher": faecher("  Obere   Schublade ")})
    assert r.status_code == 200 and r.json()["wirkung"]["etiketten_neu"] == 0
    p = r.json()["plan"]
    assert [f["name"] for f in p["einheiten"][0]["faecher"]] == ["Obere Schublade", ""]
    assert client.get(f"/api/faecher/{f1['id']}").json()["name"] == "Obere Schublade"
    from app.db import connect
    conn = connect(app.state.db_path)
    conn.execute("UPDATE fach SET etikett = 'gedruckt'")
    conn.close()
    r = client.put(f"/api/einheiten/{e['id']}/faecher", json={"version": p["version"], "faecher": faecher("Linke Tür")})
    assert r.json()["wirkung"]["etiketten_neu"] == 1
    assert [f["etikett"] for f in r.json()["plan"]["einheiten"][0]["faecher"]] == ["neu_drucken", "gedruckt"]
    zu_lang = client.put(f"/api/einheiten/{e['id']}/faecher", json={"version": r.json()["plan"]["version"], "faecher": faecher("x" * 61)})
    assert zu_lang.status_code == 422

def test_fach_punkte_in_prozent(client, buero):
    e = buero["plan"]["einheiten"][0]
    r = client.put(f"/api/einheiten/{e['id']}/faecher", json={"version": buero["plan"]["version"], "faecher": [
        {"id": None, "nr": 1, "punkte": [[0, 0], [150, 0], [150, 50]]}]})
    assert r.status_code == 422


def test_platz_setzen_und_entfernen(client, buero):
    nr = buero["nr"]
    r = client.put(f"/api/produkte/{nr}/platz", json={"fach_id": None}).json()
    assert r["vorher"] == buero["fach"] and r["fach"] is None
    assert client.put(f"/api/produkte/{nr}/platz", json={"fach_id": 9999}).status_code == 404
    digital = client.post("/api/produkte", json={"name": "Katalog", "kategorie_id": buero["kid"], "art": "digital"}).json()["inventar_nr"]
    assert client.put(f"/api/produkte/{digital}/platz", json={"fach_id": buero["fach"]}).status_code == 422


def _png(b=40, h=20):
    puffer = io.BytesIO()
    Image.new("RGB", (b, h), "white").save(puffer, "PNG")
    return puffer.getvalue()


def test_unterlage_bild_und_pdf(client):
    r = client.post("/api/plan/unterlage", files={"datei": ("plan.png", _png(), "image/png")})
    assert r.status_code == 201 and (r.json()["breite"], r.json()["hoehe"]) == (40, 20)
    puffer = io.BytesIO()
    c = canvas.Canvas(puffer, pagesize=(842, 595))
    c.rect(100, 100, 400, 300)
    c.save()
    r = client.post("/api/plan/unterlage", files={"datei": ("plan.pdf", puffer.getvalue(), "application/pdf")})
    assert r.status_code == 201 and r.json()["breite"] > r.json()["hoehe"]
    u = {**r.json(), "x": 0, "y": 0, "massstab": 0.5, "drehung": 90}
    p = client.put("/api/plan", json=_entwurf(client.get("/api/plan").json(), unterlage=u)).json()["plan"]
    assert p["unterlage"]["datei"] == u["datei"] and p["unterlage"]["drehung"] == 90
    assert client.get(f"/media/plan/{u['datei']}.png").status_code == 200


def test_unterlage_falsches_format(client):
    r = client.post("/api/plan/unterlage", files={"datei": ("plan.txt", b"hallo", "text/plain")})
    assert r.status_code == 422


def test_einheit_foto(client, buero):
    e = buero["plan"]["einheiten"][0]
    r = client.post(f"/api/einheiten/{e['id']}/foto", files={"foto": ("s.png", _png(300, 400), "image/png")})
    assert r.status_code == 201 and (r.json()["foto_breite"], r.json()["foto_hoehe"]) == (300, 400)
    assert client.get(f"/media/einheiten/{r.json()['foto']}-960.webp").status_code == 200
    # Fächer bleiben beim neuen Foto
    assert len(client.get("/api/plan").json()["einheiten"][0]["faecher"]) == 2


def test_status_filter_nach_platz(client, buero):
    z = client.get("/api/bibliothek", params={"status": "am_platz"}).json()
    assert [p["inventar_nr"] for p in z["produkte"]] == [buero["nr"]]
    assert client.get("/api/bibliothek", params={"status": "ohne_platz"}).json()["gesamt"] == 0
    assert client.get(f"/api/produkte/{buero['nr']}").json()["platz"]["code"] == "2.1.1"


def test_sammel_platz_und_rueckgaengig(client, buero):
    nr2 = client.post("/api/produkte", json={"name": "Eiche", "kategorie_id": buero["kid"]}).json()["inventar_nr"]
    digital = client.post("/api/produkte", json={"name": "Katalog", "kategorie_id": buero["kid"], "art": "digital"}).json()["inventar_nr"]
    fach2 = buero["plan"]["einheiten"][0]["faecher"][1]["id"]
    r = client.post("/api/produkte/sammel", json={"produkte": [buero["nr"], nr2, digital], "aenderung": {"platz": fach2}}).json()
    platz = lambda n: (client.get(f"/api/produkte/{n}").json()["platz"] or {}).get("code")
    assert (platz(buero["nr"]), platz(nr2), platz(digital)) == ("2.1.2", "2.1.2", None)
    client.post(f"/api/produkte/sammel/rueckgaengig/{r['rueckgaengig']}")
    assert (platz(buero["nr"]), platz(nr2)) == ("2.1.1", None)
    assert client.post("/api/produkte/sammel", json={"produkte": [nr2], "aenderung": {"platz": 9999}}).status_code == 422
