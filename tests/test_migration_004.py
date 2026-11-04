"""Migration 004: Name des Fachs (D-020)."""
from __future__ import annotations

from app.db import connect, migrate


def test_fach_hat_leeren_namen(tmp_path):
    conn = connect(tmp_path / "m.db")
    migrate(conn)
    rid = conn.execute("INSERT INTO raum (nr, punkte) VALUES (1, '[]') RETURNING id").fetchone()[0]
    eid = conn.execute("INSERT INTO einheit (raum_id, nr, punkte) VALUES (?, 1, '[]') RETURNING id", (rid,)).fetchone()[0]
    conn.execute("INSERT INTO fach (einheit_id, nr, punkte) VALUES (?, 1, '[]')", (eid,))
    assert conn.execute("SELECT name FROM fach").fetchone()[0] == ""
    conn.close()
