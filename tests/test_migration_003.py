"""Migration 003 (Büro): Plan, Räume, Einheiten, Fächer und Platz des Produkts (SPEC 6.4, 7)."""
from __future__ import annotations

import sqlite3

import pytest

from app.db import connect, migrate


@pytest.fixture
def db(tmp_path):
    conn = connect(tmp_path / "m.db")
    migrate(conn)
    yield conn
    conn.close()


def _einheit_mit_fach(db):
    rid = db.execute("INSERT INTO raum (nr, punkte) VALUES (2, '[]') RETURNING id").fetchone()[0]
    eid = db.execute("INSERT INTO einheit (raum_id, nr, punkte) VALUES (?, 1, '[]') RETURNING id", (rid,)).fetchone()[0]
    fid = db.execute("INSERT INTO fach (einheit_id, nr, punkte) VALUES (?, 1, '[]') RETURNING id", (eid,)).fetchone()[0]
    db.execute("INSERT INTO produkt (inventar_nr, kategorie_id, code_praefix, kategorie_nr, name, fach_id) "
               "VALUES (1, 1, 'XX', 1, 'P', ?)", (fid,))
    return rid, eid, fid


def test_genau_ein_plan(db):
    assert db.execute("SELECT count(*), max(version) FROM plan").fetchone()[:] == (1, 1)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO plan (id) VALUES (2)")


def test_einheit_geloescht_produkt_ohne_platz(db):
    _, eid, _ = _einheit_mit_fach(db)
    db.execute("DELETE FROM einheit WHERE id = ?", (eid,))
    assert db.execute("SELECT fach_id FROM produkt").fetchone()[0] is None
    assert db.execute("SELECT count(*) FROM fach").fetchone()[0] == 0


def test_fach_kennung_wird_nie_wiederverwendet(db):
    _, eid, fid = _einheit_mit_fach(db)
    db.execute("DELETE FROM fach WHERE id = ?", (fid,))
    neu = db.execute("INSERT INTO fach (einheit_id, nr, punkte) VALUES (?, 1, '[]') RETURNING id", (eid,)).fetchone()[0]
    assert neu > fid


def test_einheitsnummer_je_raum_eindeutig_ausser_ohne_raum(db):
    rid, _, _ = _einheit_mit_fach(db)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO einheit (raum_id, nr, punkte) VALUES (?, 1, '[]')", (rid,))
    db.execute("INSERT INTO einheit (raum_id, nr, punkte) VALUES (NULL, 1, '[]')")
    db.execute("INSERT INTO einheit (raum_id, nr, punkte) VALUES (NULL, 1, '[]')")
