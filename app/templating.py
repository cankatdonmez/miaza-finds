from __future__ import annotations

import hashlib

from fastapi.templating import Jinja2Templates

from .config import BASE_DIR
from .texte import t
from .version import VERSION

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _asset_version() -> str:
    """Cache-Buster: ändert sich, sobald sich eine statische Datei ändert."""
    h = hashlib.sha256()
    for f in sorted((BASE_DIR / "static").rglob("*")):
        if f.is_file() and f.suffix in {".css", ".js"}:
            h.update(f.read_bytes())
    return h.hexdigest()[:10]


templates.env.globals["asset_v"] = _asset_version()
templates.env.globals["app_version"] = VERSION
templates.env.globals["t"] = t
