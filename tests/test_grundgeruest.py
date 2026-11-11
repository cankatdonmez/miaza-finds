"""Grundgerüst: Start, Kopfzeilen, Herkunftsprüfung (D-007), Migrationsschutz."""
from __future__ import annotations

import pytest

from app.db import UpdateFehler, connect, migrate
from app.main import create_app
from app.version import VERSION


def test_start_und_stand(client):
    r = client.get("/")
    assert r.status_code == 200 and r.url.path == "/bibliothek" and f"v{VERSION}" in r.text
    assert client.get("/api/stand").json() == {"version": VERSION}


def test_sicherheitskopfzeilen(client):
    r = client.get("/")
    assert r.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in r.headers["content-security-policy"]
    assert client.get("/api/stand").headers["cache-control"] == "no-store"


def test_404_als_seite_und_als_json(client):
    assert client.get("/gibt-es-nicht").status_code == 404
    r = client.get("/api/gibt-es-nicht")
    assert r.status_code == 404 and "fehler" in r.json()


@pytest.mark.parametrize("kopf", [{"origin": "http://boese.example"}, {"sec-fetch-site": "cross-site"}])
def test_fremde_seite_darf_nichts_aendern(client, kopf):
    r = client.post("/api/stand", headers=kopf)
    assert r.status_code == 403 and "fremden Seite" in r.json()["fehler"]["text"]


@pytest.mark.parametrize("kopf", [{"origin": "http://testserver"}, {"sec-fetch-site": "same-origin"}, {}])
def test_eigene_seite_wird_durchgelassen(client, kopf):
    # 405: die Route kennt kein POST – entscheidend ist, dass die Herkunftsprüfung nicht abgelehnt hat
    assert client.post("/api/stand", headers=kopf).status_code == 405


def test_lesen_von_fremder_seite_bleibt_erlaubt(client):
    assert client.get("/api/stand", headers={"origin": "http://boese.example"}).status_code == 200


def _migrationen(ordner, *namen):
    ordner.mkdir(exist_ok=True)
    for i, n in enumerate(namen):
        (ordner / n).write_text(f"CREATE TABLE t{i} (id INTEGER PRIMARY KEY);", encoding="utf-8")
    return ordner


def test_update_legt_vorher_sicherung_an(tmp_path):
    mig = _migrationen(tmp_path / "mig", "001_a.sql")
    conn = connect(tmp_path / "x.db")
    assert migrate(conn, tmp_path / "sich", mig) == ["001_a.sql"]
    assert not (tmp_path / "sich").exists()          # neue Datenbank: nichts zu sichern
    _migrationen(mig, "001_a.sql", "002_b.sql")
    assert migrate(conn, tmp_path / "sich", mig) == ["002_b.sql"]
    assert [p.name.startswith("vor-update-") for p in (tmp_path / "sich").iterdir()] == [True]
    conn.close()


def test_aeltere_version_oeffnet_neuere_datenbank_nicht(tmp_path):
    mig = _migrationen(tmp_path / "mig", "001_a.sql")
    conn = connect(tmp_path / "x.db")
    conn.execute("CREATE TABLE schema_migration (name TEXT PRIMARY KEY, angewendet_am TEXT NOT NULL)")
    conn.execute("INSERT INTO schema_migration VALUES ('999_zukunft.sql', datetime('now'))")
    with pytest.raises(UpdateFehler, match="neueren Programmversion"):
        migrate(conn, tmp_path / "sich", mig)
    conn.close()


def test_fehlerhafte_migration_rollt_zurueck(tmp_path):
    mig = tmp_path / "mig"
    mig.mkdir()
    (mig / "001_kaputt.sql").write_text("CREATE TABLE gut (id INTEGER);\nKEIN SQL;", encoding="utf-8")
    conn = connect(tmp_path / "x.db")
    with pytest.raises(Exception):
        migrate(conn, None, mig)
    assert conn.execute("SELECT count(*) FROM sqlite_master WHERE name = 'gut'").fetchone()[0] == 0
    conn.close()


def test_daten_landen_in_den_angegebenen_ordnern(tmp_path):
    create_app(tmp_path / "d" / "f.db", tmp_path / "m", tmp_path / "b")
    assert (tmp_path / "d" / "f.db").exists() and (tmp_path / "m").is_dir()


def test_auftakt_markup_und_regeln(client):
    """SPEC 4.1: Markenbild liegt im Seitenkopf, ist ohne JS verborgen, begrenzt auf 700 ms, hält nichts auf."""
    from pathlib import Path
    app_dir = Path(__file__).parent.parent / "app"
    html = client.get("/bibliothek").text
    assert 'id="auftakt"' in html and 'aria-hidden="true"' in html
    css = (app_dir / "static/css/app.css").read_text(encoding="utf-8")
    assert ".auftakt{display:none}" in css                      # ohne JS nie sichtbar
    assert "animation:auftakt-aus .7s" in css                   # K1: höchstens 700 ms
    js = (app_dir / "static/js/theme.js").read_text(encoding="utf-8")
    assert 'sessionStorage.getItem("mf-auftakt")' in js         # K2: nur einmal je Sitzung
    assert "setTimeout(weg, 700)" in js and 'addEventListener("pointerdown"' in js  # K1/K3
    assert js.count("try {") >= 2 and "catch (e)" in js         # Speicherfehler ohne Absturz
