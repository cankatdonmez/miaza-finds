"""Migration 005: Farbe des Raums (D-024)."""
from __future__ import annotations

import sqlite3

import pytest

from app.db import connect, migrate


def test_raumfarbe(tmp_path):
    conn = connect(tmp_path / "m.db")
    migrate(conn)
    conn.execute("INSERT INTO raum (nr, punkte) VALUES (7, '[]')")
    assert conn.execute("SELECT farbe FROM raum").fetchone()[0] == 1
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE raum SET farbe = 7")
    conn.close()
