"""Migration 001 (Bibliothek): Grundbestand, Datenbankregeln und Nummernvergabe (SPEC 6.2, 6.3, 7)."""
from __future__ import annotations

import sqlite3

import pytest

from app.db import DBError, connect, migrate, transaction
from app.services import nummern


@pytest.fixture
def db(tmp_path):
    conn = connect(tmp_path / "m.db")
    migrate(conn)
    yield conn
    conn.close()


def _kategorie(db, name="Fliese", praefix="FL"):
    return db.execute("INSERT INTO kategorie (name, praefix) VALUES (?, ?) RETURNING id", (name, praefix)).fetchone()[0]


def _produkt(db, kat_id, name="Testfliese"):
    with transaction(db):
        inv = nummern.naechste_inventar_nr(db)
        nr = nummern.naechste_kategorie_nr(db, kat_id)
        praefix = db.execute("SELECT praefix FROM kategorie WHERE id = ?", (kat_id,)).fetchone()[0]
        db.execute("INSERT INTO produkt (inventar_nr, kategorie_id, code_praefix, kategorie_nr, name) VALUES (?, ?, ?, ?, ?)",
                   (inv, kat_id, praefix, nr, name))
    return inv


def test_sonstiges_gibt_es_von_anfang_an(db):
    zeile = db.execute("SELECT name, praefix, fest FROM kategorie").fetchall()
    assert [tuple(z) for z in zeile] == [("Sonstiges", "XX", 1)]


def test_sonstiges_ist_nicht_loeschbar(db):
    with pytest.raises(DBError, match="Sonstiges"):
        with transaction(db):
            db.execute("DELETE FROM kategorie WHERE fest = 1")
    with pytest.raises(DBError):
        with transaction(db):
            db.execute("UPDATE kategorie SET fest = 0")


@pytest.mark.parametrize("praefix", ["F", "FLI", "fl", "F1"])
def test_praefix_zwei_grossbuchstaben(db, praefix):
    with pytest.raises(sqlite3.IntegrityError):
        _kategorie(db, praefix=praefix)


def test_praefix_und_name_eindeutig(db):
    _kategorie(db)
    with pytest.raises(sqlite3.IntegrityError):
        _kategorie(db, name="Holz", praefix="FL")
    with pytest.raises(sqlite3.IntegrityError):
        _kategorie(db, name="fliese", praefix="HO")


def test_codes_und_nummern(db):
    fl, st = _kategorie(db), _kategorie(db, "Stoff", "ST")
    a, b, c = _produkt(db, fl), _produkt(db, st), _produkt(db, fl)
    assert (a, b, c) == (1, 2, 3)
    zeilen = db.execute("SELECT code_praefix, kategorie_nr, inventar_nr FROM produkt ORDER BY inventar_nr").fetchall()
    assert [nummern.code(*z) for z in zeilen] == ["FL-001-001", "ST-001-002", "FL-002-003"]
    assert nummern.code("ST", 5, 1265) == "ST-005-1265"


def test_geloeschte_nummern_kommen_nie_wieder(db):
    fl = _kategorie(db)
    _produkt(db, fl)
    letzte = _produkt(db, fl)
    db.execute("DELETE FROM produkt WHERE inventar_nr = ?", (letzte,))
    neu = _produkt(db, fl)
    assert neu == letzte + 1
    assert db.execute("SELECT kategorie_nr FROM produkt WHERE inventar_nr = ?", (neu,)).fetchone()[0] == 3


def test_inventarnummer_unveraenderlich(db):
    inv = _produkt(db, _kategorie(db))
    with pytest.raises(DBError, match="Inventarnummer"):
        with transaction(db):
            db.execute("UPDATE produkt SET inventar_nr = 99 WHERE inventar_nr = ?", (inv,))


def test_name_darf_fehlen_aber_nicht_leer_sein(db):
    fl = _kategorie(db)
    _produkt(db, fl, name=None)
    with pytest.raises(sqlite3.IntegrityError):
        _produkt(db, fl, name="   ")
    assert db.execute("SELECT count(*) FROM produkt WHERE name IS NULL").fetchone()[0] == 1


def test_produkt_loeschen_nimmt_abhaengiges_mit(db):
    fl = _kategorie(db)
    f = db.execute("INSERT INTO filter (kategorie_id, name, typ) VALUES (?, 'Oberfläche', 'mehrfach') RETURNING id", (fl,)).fetchone()[0]
    opt = db.execute("INSERT INTO filter_option (filter_id, name) VALUES (?, 'Matt') RETURNING id", (f,)).fetchone()[0]
    inv = _produkt(db, fl)
    db.execute("INSERT INTO produkt_wert (produkt_id, filter_id, option_id) VALUES (?, ?, ?)", (inv, f, opt))
    db.execute("INSERT INTO produkt_farbe VALUES (?, 'terracotta')", (inv,))
    db.execute("INSERT INTO preis (produkt_id, cent, einheit, datum) VALUES (?, 3650, 'm2', '2026-11-01')", (inv,))
    db.execute("INSERT INTO foto (produkt_id, datei, breite, hoehe) VALUES (?, 'a.jpg', 800, 600)", (inv,))
    db.execute("DELETE FROM produkt WHERE inventar_nr = ?", (inv,))
    for tabelle in ("produkt_wert", "produkt_farbe", "preis", "foto"):
        assert db.execute(f"SELECT count(*) FROM {tabelle}").fetchone()[0] == 0, tabelle


def test_werte_je_filtertyp(db):
    fl = _kategorie(db)
    inv = _produkt(db, fl)
    mass = db.execute("INSERT INTO filter (kategorie_id, name, typ, einheit) VALUES (?, 'Stärke', 'mass', 'mm') RETURNING id", (fl,)).fetchone()[0]
    db.execute("INSERT INTO produkt_wert (produkt_id, filter_id, zahl) VALUES (?, ?, 10)", (inv, mass))
    # ein Maß-Wert je Filter
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO produkt_wert (produkt_id, filter_id, zahl) VALUES (?, ?, 12)", (inv, mass))
    # genau eine Art von Wert je Zeile
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO produkt_wert (produkt_id, filter_id) VALUES (?, ?)", (inv, mass))
    # Einheit nur bei Maß
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO filter (kategorie_id, name, typ, einheit) VALUES (?, 'R-Wert', 'einfach', 'mm')", (fl,))


def test_farbe_nur_aus_palette_und_preis_einmal(db):
    inv = _produkt(db, _kategorie(db))
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO produkt_farbe VALUES (?, 'lila')", (inv,))
    db.execute("INSERT INTO preis (produkt_id, cent, einheit, datum) VALUES (?, 100, 'stueck', '2026-11-01')", (inv,))
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO preis (produkt_id, cent, einheit, datum) VALUES (?, 200, 'stueck', '2026-11-02')", (inv,))


def test_kategorie_mit_produkten_nicht_direkt_loeschbar(db):
    """Produkte wandern vorher nach „Sonstiges“ (SPEC 6.3); ohne das verhindert der Fremdschlüssel den Verlust."""
    fl = _kategorie(db)
    _produkt(db, fl)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("DELETE FROM kategorie WHERE id = ?", (fl,))
