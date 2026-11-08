"""Suche nach Fachcode (SPEC 6.1, D-050): ein Wort wie „2.1.3“ passt nur zum Fachcode, vom Anfang, an Segmentgrenzen."""
from __future__ import annotations

from .test_plan import _entwurf, buero, QUADRAT, KLEIN  # noqa: F401  (Fixture)
from .test_system import API, _einrichten


def _treffer(client, q):
    return sorted(p["inventar_nr"] for p in client.get("/api/bibliothek", params={"q": q}).json()["produkte"])


def _produkt(client, kid, name, fach=None, abmessungen=None):
    nr = client.post("/api/produkte", json={"name": name, "kategorie_id": kid, "abmessungen": abmessungen}).json()["inventar_nr"]
    if fach:
        assert client.put(f"/api/produkte/{nr}/platz", json={"fach_id": fach}).status_code == 200
    return nr


def _raster(client, buero):
    """Fächer 2.1.1, 2.1.3, 2.1.30, 2.10.1, 12.1.1 mit je einem Produkt „Eiche“/„Buche“ (siehe unten)."""
    plan = client.get("/api/plan").json()
    raeume = [{"id": r["id"], "schluessel": f"r{r['id']}", "nr": r["nr"], "name": r["name"], "punkte": r["punkte"]} for r in plan["raeume"]]
    raeume += [{"id": None, "schluessel": "x", "nr": 12, "name": "Lager", "punkte": QUADRAT}]
    ents = [{"id": e["id"], "raum": f"r{e['raum_id']}", "nr": e["nr"], "name": e["name"], "punkte": e["punkte"]} for e in plan["einheiten"]]
    ents += [{"id": None, "raum": f"r{raeume[0]['id']}", "nr": 10, "name": "Regal", "punkte": KLEIN},
             {"id": None, "raum": "x", "nr": 1, "name": "Kommode", "punkte": KLEIN}]
    r = client.put("/api/plan", json={**_entwurf(plan), "raeume": raeume, "einheiten": ents})
    assert r.status_code == 200, r.text
    plan = r.json()["plan"]
    code = {e["code"]: e for e in plan["einheiten"]}
    fach = {}
    for ecode, nrs in (("2.1", [3, 30]), ("2.10", [1]), ("12.1", [1])):
        e = code[ecode]
        alt = [{"id": f["id"], "nr": f["nr"], "punkte": f["punkte"]} for f in e["faecher"]]
        neu = [{"id": None, "nr": n, "punkte": KLEIN} for n in nrs]
        r = client.put(f"/api/einheiten/{e['id']}/faecher", json={"version": plan["version"], "faecher": alt + neu})
        assert r.status_code == 200, r.text
        plan = r.json()["plan"]
    for e in plan["einheiten"]:
        for f in e["faecher"]:
            fach[f["code"]] = f["id"]
    return fach


def test_fachcode_ganz_und_einheit_als_praefix(client, buero):
    f = _raster(client, buero)
    n = {c: _produkt(client, buero["kid"], f"P{c}", f[c]) for c in ("2.1.3", "2.1.30", "2.10.1", "12.1.1")}
    n["2.1.1"] = buero["nr"]
    assert _treffer(client, "2.1.3") == [n["2.1.3"]]
    assert _treffer(client, "2.1.1") == [n["2.1.1"]]
    assert _treffer(client, "2.1") == sorted([n["2.1.1"], n["2.1.3"], n["2.1.30"]])
    assert _treffer(client, "2.10") == [n["2.10.1"]]
    assert _treffer(client, "12.1.1") == [n["12.1.1"]]


def test_nur_fachcode_keine_ausmasse(client, buero):
    f = _raster(client, buero)
    mass = _produkt(client, buero["kid"], "Platte", None, "120x60x2.2 cm")
    f22 = _produkt(client, buero["kid"], "Dort", f["2.1.3"])
    assert _treffer(client, "2.2") == [] and mass not in _treffer(client, "2.1.3")
    assert _treffer(client, "2.1.3") == [f22]
    # Wort ohne Code-Form findet den Fachcode nicht
    assert _treffer(client, ".1.3") == [] and _treffer(client, "1.") == []
    assert _treffer(client, "2.1.3.4") == []


def test_mehrere_woerter_und(client, buero):
    f = _raster(client, buero)
    a = _produkt(client, buero["kid"], "Eiche hell", f["2.1.3"])
    _produkt(client, buero["kid"], "Buche", f["2.1.3"])
    _produkt(client, buero["kid"], "Eiche dunkel", f["12.1.1"])
    assert _treffer(client, "Eiche 2.1") == [a] and _treffer(client, "2.1 eiche") == [a]


def test_einheit_ohne_raum(client, buero):
    plan = client.get("/api/plan").json()
    ents = [{"id": e["id"], "raum": f"r{e['raum_id']}", "nr": e["nr"], "name": e["name"], "punkte": e["punkte"]} for e in plan["einheiten"]]
    ents.append({"id": None, "raum": None, "nr": 1, "name": "Lose", "punkte": KLEIN})
    plan = client.put("/api/plan", json={**_entwurf(plan), "einheiten": ents}).json()["plan"]
    lose = next(e for e in plan["einheiten"] if e["raum_id"] is None)
    plan = client.put(f"/api/einheiten/{lose['id']}/faecher", json={"version": plan["version"], "faecher": [
        {"id": None, "nr": 3, "punkte": KLEIN}]}).json()["plan"]
    fid = next(e for e in plan["einheiten"] if e["raum_id"] is None)["faecher"][0]["id"]
    nr = _produkt(client, buero["kid"], "Lose Ware", fid)
    for q in ("1.3", "1.1.3", "–.1.3"):
        assert nr not in _treffer(client, q)
    assert _treffer(client, "Lose") == [nr]


def test_umziehen_und_umnummerieren(client, buero):
    nr, plan = buero["nr"], buero["plan"]
    e = plan["einheiten"][0]
    f1, f2 = (f["id"] for f in e["faecher"])
    client.put(f"/api/produkte/{nr}/platz", json={"fach_id": f2})
    assert _treffer(client, "2.1.2") == [nr] and _treffer(client, "2.1.1") == []
    r = client.put(f"/api/einheiten/{e['id']}/faecher", json={"version": plan["version"], "faecher": [
        {"id": f1, "nr": 5, "punkte": e["faecher"][0]["punkte"]}, {"id": f2, "nr": 6, "punkte": e["faecher"][1]["punkte"]}]})
    assert r.status_code == 200
    assert _treffer(client, "2.1.6") == [nr] and _treffer(client, "2.1.2") == []
    client.put(f"/api/produkte/{nr}/platz", json={"fach_id": None})
    assert _treffer(client, "2.1.6") == []


def test_plan_loeschen_und_geladene_sicherung_sofort(client, buero):
    nr = buero["nr"]
    _, h = _einrichten(client)
    assert _treffer(client, "2.1.1") == [nr]
    name = client.post(f"{API}/sicherung", headers=h).json()["name"]       # Sicherung mit Fach
    assert client.post(f"{API}/loeschen", headers=h, json={"teile": ["plan"]}).status_code == 200
    assert _treffer(client, "2.1.1") == [] and _treffer(client, "Terrazzo") == [nr]
    assert client.post(f"{API}/wiederherstellen", headers=h, json={"name": name}).status_code == 200
    assert _treffer(client, "2.1.1") == [nr]
    # Stand ohne Fächer wiederherstellen: Sicherung nach dem Löschen
    client.post(f"{API}/loeschen", headers=h, json={"teile": ["plan"]})
    leer = client.post(f"{API}/sicherung", headers=h).json()["name"]
    client.post(f"{API}/wiederherstellen", headers=h, json={"name": name})
    assert _treffer(client, "2.1.1") == [nr]
    client.post(f"{API}/wiederherstellen", headers=h, json={"name": leer})
    assert _treffer(client, "2.1.1") == [] and _treffer(client, "Terrazzo") == [nr]


def test_einzelne_zahl_ist_kein_fachcode(client, buero):
    assert buero["nr"] == 1 and _treffer(client, "2") == []       # Raum 2, Produkt 1: „2“ ist nur Text


def test_karte_platz_in_liste(client, buero):
    """Karte am Desktop (SPEC 6.1): Fach-ID und -Code in der Liste; ohne Platz und digital: None."""
    ohne = _produkt(client, buero["kid"], "Ohne")
    dig = client.post("/api/produkte", json={"name": "Datei", "kategorie_id": buero["kid"], "art": "digital"})
    liste = {p["inventar_nr"]: p for p in client.get("/api/bibliothek").json()["produkte"]}
    assert liste[buero["nr"]]["platz"] == {"id": buero["fach"], "code": "2.1.1"}
    assert liste[ohne]["platz"] is None
    if dig.status_code == 201:
        assert liste[dig.json()["inventar_nr"]]["platz"] is None


def test_karte_platz_nach_umzug_und_ohne_raum(client, buero):
    f = _raster(client, buero)
    nr = _produkt(client, buero["kid"], "Kommodenstück", f["12.1.1"])
    p = {x["inventar_nr"]: x for x in client.get("/api/bibliothek").json()["produkte"]}
    assert p[nr]["platz"]["code"] == "12.1.1"
    assert client.put(f"/api/produkte/{nr}/platz", json={"fach_id": f["2.1.3"]}).status_code == 200
    p = {x["inventar_nr"]: x for x in client.get("/api/bibliothek").json()["produkte"]}
    assert p[nr]["platz"]["code"] == "2.1.3" and p[nr]["platz"]["id"] == f["2.1.3"]


def test_karte_platz_frontend_nur_hover(client):
    js = client.get("/static/js/bibliothek.js").text
    assert "/buero?fach=${p.platz.id}&produkt=${p.inventar_nr}" in js and "data-platz-href" in js
    css = client.get("/static/css/app.css").text
    i = css.index(".karte-platz{display:none")
    assert "@media (hover:hover)" in css[i:i + 700] and "visibility:hidden" in css[i:i + 700]
