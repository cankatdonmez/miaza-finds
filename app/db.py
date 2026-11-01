"""SQLite-Zugriff: eine Verbindung pro Anfrage, WAL, Fremdschlüssel, Migrationen (wie miaza counts)."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from .config import BASE_DIR
from .texte import t

MIGRATIONS_DIR = BASE_DIR / "migrations"


class DBError(Exception):
    """Fehler aus einer Datenbankregel (Trigger), mit deutschem Klartext."""

    MESSAGES = {
        "kategorie_fest": t("fehler.kategorie_fest"),
        "inventar_unveraenderlich": t("fehler.inventar_unveraenderlich"),
    }

    def __init__(self, code: str):
        self.code = code
        super().__init__(self.MESSAGES.get(code, code))


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


class UpdateFehler(RuntimeError):
    """Update abgebrochen, bevor etwas verändert wurde."""


def sichern(conn: sqlite3.Connection, ziel: Path) -> Path:
    """Konsistente Kopie der laufenden Datenbank (SQLite-Backup-API, auch bei WAL)."""
    ziel.parent.mkdir(parents=True, exist_ok=True)
    dst = sqlite3.connect(ziel)
    try:
        conn.backup(dst)
        ok = dst.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        dst.close()
    if ok != "ok":
        ziel.unlink(missing_ok=True)
        raise UpdateFehler(f"Sicherung {ziel.name} ist fehlerhaft ({ok}).")
    return ziel


def migrate(conn: sqlite3.Connection, sicherung_dir: Path | None = None,
            migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    """Spielt fehlende Migrationen in Dateinamen-Reihenfolge ein.

    Schutzregeln (Daten gehen bei einem Update nie verloren):
    - Kennt die Datenbank Migrationen, die dieser Programmstand nicht hat (ältere Version
      auf neuerer Datenbank), startet das Programm nicht.
    - Vor jedem Update einer bestehenden Datenbank: Integritätsprüfung und vollständige
      Sicherung unter <sicherung_dir>/vor-update-…db. Schlägt eines fehl, wird nichts verändert.
    - Jede Migration läuft in einer Transaktion; ein Fehler rollt sie vollständig zurück.
    """
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migration (name TEXT PRIMARY KEY, angewendet_am TEXT NOT NULL)"
    )
    done = {r["name"] for r in conn.execute("SELECT name FROM schema_migration")}
    bekannt = {f.name for f in migrations_dir.glob("*.sql")}
    unbekannt = sorted(done - bekannt)
    if unbekannt:
        raise UpdateFehler(
            "Die Datenbank stammt von einer neueren Programmversion "
            f"({', '.join(unbekannt)}). Bitte die aktuelle Version installieren; "
            "eine ältere Version darf diese Daten nicht öffnen."
        )
    offen = [f for f in sorted(migrations_dir.glob("*.sql")) if f.name not in done]
    if offen and done and sicherung_dir is not None:
        ok = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if ok != "ok":
            raise UpdateFehler(f"Integritätsprüfung fehlgeschlagen ({ok}). Update nicht ausgeführt.")
        stempel = datetime.now().strftime("%Y%m%d-%H%M%S")
        letzte = max(done).removesuffix(".sql")
        sichern(conn, sicherung_dir / f"vor-update-{stempel}-{letzte}.db")
    applied = []
    for f in offen:
        sql = f.read_text(encoding="utf-8")
        conn.execute("BEGIN IMMEDIATE")
        try:
            # executescript würde die Transaktion beenden; Statements einzeln ausführen.
            for stmt in _split_sql(sql):
                conn.execute(stmt)
            conn.execute(
                "INSERT INTO schema_migration (name, angewendet_am) VALUES (?, datetime('now'))", (f.name,)
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        applied.append(f.name)
    return applied


def _split_sql(sql: str) -> list[str]:
    """Teilt ein Skript in Statements; Trigger-Körper (BEGIN … END;) bleiben ganz."""
    lines = [ln for ln in sql.splitlines() if not ln.strip().startswith("--")]
    stmts, buf = [], []
    for ln in lines:
        buf.append(ln)
        candidate = "\n".join(buf).strip()
        if candidate.endswith(";") and sqlite3.complete_statement(candidate):
            stmts.append(candidate)
            buf = []
    rest = "\n".join(buf).strip()
    if rest:
        stmts.append(rest)
    return stmts


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except sqlite3.IntegrityError as e:
        conn.execute("ROLLBACK")
        msg = str(e)
        for code in DBError.MESSAGES:
            if code in msg:
                raise DBError(code) from e
        raise
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
