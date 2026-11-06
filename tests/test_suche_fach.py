"""Suche nach Fachcode (SPEC 6.1): „2.1.2“ findet die Produkte dieses Fachs."""
from __future__ import annotations

from .test_plan import _entwurf, buero  # noqa: F401  (Fixture)


def _treffer(client, q):
    return [p["inventar_nr"] for p in client.get("/api/bibliothek", params={"q": q}).json()["produkte"]]


def _faecher(buero):
    return [f["id"] for f in buero["plan"]["einheiten"][0]["faecher"]]


def test_fachcode_und_einheitscode_finden_produkt(client, buero):
    assert _treffer(client, "2.1.1") == [buero["nr"]]
    assert _treffer(client, "2.1") == [buero["nr"]]
    assert _treffer(client, "2.1.2") == []


def test_umziehen_ueber_platz_einordnen_zuruecklegen_sammel(client, buero):
    nr, (f1, f2) = buero["nr"], _faecher(buero)
    client.put(f"/api/produkte/{nr}/platz", json={"fach_id": f2})
    assert _treffer(client, "2.1.2") == [nr] and _treffer(client, "2.1.1") == []
    client.post(f"/api/produkte/{nr}/nehmen", json={})
    client.post(f"/api/produkte/{nr}/zuruecklegen", json={"neuer_fach": f1})
    assert _treffer(client, "2.1.1") == [nr] and _treffer(client, "2.1.2") == []
    assert client.post(f"/api/produkte/{nr}/einordnen", json={"fach_id": f2}).status_code == 200
    assert _treffer(client, "2.1.2") == [nr] and _treffer(client, "2.1.1") == []
    r = client.post("/api/produkte/sammel", json={"produkte": [nr], "aenderung": {"platz": f1}}).json()
    assert _treffer(client, "2.1.1") == [nr] and _treffer(client, "2.1.2") == []
    client.post(f"/api/produkte/sammel/rueckgaengig/{r['rueckgaengig']}")
    assert _treffer(client, "2.1.2") == [nr] and _treffer(client, "2.1.1") == []
    client.put(f"/api/produkte/{nr}/platz", json={"fach_id": None})
    assert _treffer(client, "2.1.2") == []


def test_umnummerieren_erneuert_suchtext(client, buero):
    nr, (f1, f2) = buero["nr"], _faecher(buero)
    e = buero["plan"]["einheiten"][0]
    r = client.put(f"/api/einheiten/{e['id']}/faecher", json={"version": buero["plan"]["version"], "faecher": [
        {"id": f1, "nr": 5, "punkte": e["faecher"][0]["punkte"]}, {"id": f2, "nr": 6, "punkte": e["faecher"][1]["punkte"]}]})
    assert r.status_code == 200
    assert _treffer(client, "2.1.5") == [nr] and _treffer(client, "2.1.1") == []
    plan = r.json()["plan"]
    raum = {**plan["raeume"][0], "nr": 7, "schluessel": "r"}
    ents = [{"id": x["id"], "raum": "r", "nr": x["nr"], "name": x["name"], "punkte": x["punkte"]} for x in plan["einheiten"]]
    assert client.put("/api/plan", json=_entwurf(plan, raeume=[raum], einheiten=ents)).status_code == 200
    assert _treffer(client, "7.1.5") == [nr] and _treffer(client, "2.1.5") == []
    # Fach weg → Produkt ohne Platz, Code nicht mehr auffindbar
    plan = client.get("/api/plan").json()
    client.put(f"/api/einheiten/{plan['einheiten'][0]['id']}/faecher", json={"version": plan["version"], "faecher": []})
    assert _treffer(client, "7.1.5") == []


def test_ohne_platz_und_alter_suchtext(client, buero, app):
    from app.db import connect
    from app.main import create_app
    kid = buero["kid"]
    frei = client.post("/api/produkte", json={"name": "Eiche", "kategorie_id": kid}).json()["inventar_nr"]
    conn = connect(app.state.db_path)
    vorher = conn.execute("SELECT suchtext FROM produkt WHERE inventar_nr = ?", (frei,)).fetchone()[0]
    conn.execute("UPDATE produkt SET suchtext = 'terrazzo' WHERE inventar_nr = ?", (buero["nr"],))
    conn.commit()
    conn.close()
    assert _treffer(client, "2.1.1") == []
    create_app(db_path=app.state.db_path, media_dir=app.state.media_dir, sicherung_dir=app.state.sicherung_dir)
    assert _treffer(client, "2.1.1") == [buero["nr"]]
    conn = connect(app.state.db_path)
    assert conn.execute("SELECT suchtext FROM produkt WHERE inventar_nr = ?", (frei,)).fetchone()[0] == vorher
