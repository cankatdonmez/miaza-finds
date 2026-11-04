"""Einstiegspunkt: `uvicorn --factory app.main:create_app`."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
# Starlette-Klasse, damit auch unbekannte Pfade (vom Router ausgelöst) hier landen
from starlette.exceptions import HTTPException

from .config import BASE_DIR, get_settings
from .db import DBError, connect, migrate
from .fehler import Fehler
from .routes import api_bearbeitung, api_bibliothek, api_einstellungen, api_entnahme, api_etiketten, api_kategorien, api_personen, api_plan, api_produkte, api_system, pages
from .templating import templates

SICHERE_METHODEN = {"GET", "HEAD", "OPTIONS"}


def fremde_herkunft(request: Request) -> bool:
    """Ändernde Anfrage von einer fremden Seite? (D-007: Schutz gegen CSRF ohne Anmeldung)

    Browser senden bei ändernden Anfragen `Origin` bzw. `Sec-Fetch-Site`; fehlen beide, kommt die
    Anfrage nicht aus einem Browser (Skript, Test) und kann keine fremde Seite sein.
    """
    if request.method in SICHERE_METHODEN:
        return False
    origin = request.headers.get("origin")
    if origin:
        return urlsplit(origin).netloc != request.headers.get("host", "")
    return request.headers.get("sec-fetch-site") in {"cross-site", "same-site"}


def create_app(db_path: Path | None = None, media_dir: Path | None = None,
               sicherung_dir: Path | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="miaza finds", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.db_path = db_path or settings.db_path
    app.state.media_dir = media_dir or settings.media_dir
    app.state.sicherung_dir = sicherung_dir or settings.backup_dir
    app.state.media_dir.mkdir(parents=True, exist_ok=True)
    app.state.bearbeitung = {}       # „Wird bearbeitet“: nur im Speicher (SPEC 7, D-044)
    app.state.sammel_vorher = {}     # Stand vor einer Sammelbearbeitung, für „Rückgängig“ (D-012)

    conn = connect(app.state.db_path)
    try:
        migrate(conn, app.state.sicherung_dir)
    finally:
        conn.close()

    @app.middleware("http")
    async def schutz_und_kopfzeilen(request: Request, call_next):
        if fremde_herkunft(request):
            return JSONResponse({"fehler": {"text": "Anfrage von einer fremden Seite abgelehnt."}}, status_code=403)
        resp = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; font-src 'self'; frame-ancestors 'none'; form-action 'self'; connect-src 'self'",
        )
        if request.url.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.exception_handler(HTTPException)
    async def _http(request: Request, exc: HTTPException):
        if request.url.path.startswith("/api/"):
            detail = exc.detail if isinstance(exc.detail, dict) else {"text": str(exc.detail)}
            return JSONResponse({"fehler": detail}, status_code=exc.status_code)
        if exc.status_code == 404:
            return templates.TemplateResponse(request, "404.html", {}, status_code=404)
        return JSONResponse({"fehler": {"text": str(exc.detail)}}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        return JSONResponse({"fehler": {"text": "Die Eingabe ist unvollständig oder ungültig."}}, status_code=422)

    @app.exception_handler(Fehler)
    async def _fehler(_: Request, exc: Fehler):
        return JSONResponse({"fehler": {"text": exc.text, "feld": exc.feld}}, status_code=exc.status)

    @app.exception_handler(DBError)
    async def _dberr(_: Request, exc: DBError):
        return JSONResponse({"fehler": {"text": str(exc)}}, status_code=409)

    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
    app.mount("/media", StaticFiles(directory=str(app.state.media_dir)), name="media")
    app.include_router(api_bibliothek.router)
    app.include_router(api_etiketten.router)
    app.include_router(api_kategorien.router)
    app.include_router(api_personen.router)
    app.include_router(api_entnahme.router)
    app.include_router(api_einstellungen.router)
    app.include_router(api_bearbeitung.router)
    app.include_router(api_plan.router)
    app.include_router(api_produkte.router)
    app.include_router(api_system.router)
    app.include_router(pages.router)
    return app
