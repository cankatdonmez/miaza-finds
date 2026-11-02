"""Anfrage-Abhängigkeiten: Datenbank."""
from __future__ import annotations

import sqlite3
from typing import Iterator

from fastapi import Request

from .db import connect


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    conn = connect(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()
