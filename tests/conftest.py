from __future__ import annotations

import sys

# Kein __pycache__ im Drive-Ordner (D-008); muss vor dem Import der App stehen
sys.dont_write_bytecode = True

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402


@pytest.fixture
def app(tmp_path):
    return create_app(tmp_path / "test.db", tmp_path / "media", tmp_path / "backups")


@pytest.fixture
def client(app):
    with TestClient(app, base_url="http://testserver") as c:
        yield c
