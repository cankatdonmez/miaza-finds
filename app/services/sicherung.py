"""Sicherung, Wiederherstellung, Datenübernahme und Sammellöschung (SPEC 6.13, 8.4, D-009).

Eine Sicherung ist eine ZIP-Datei: finds.db (konsistente Kopie), media/… (alle Fotos), info.json.
Dieselbe Datei dient zum Herunterladen, zum Wiederherstellen und zum Umzug auf einen neuen Server.
Vor jedem Schritt, der Daten ersetzt oder löscht, entsteht automatisch eine Sicherung.
"""
from __future__ import annotations

import json
import re
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from ..db import MIGRATIONS_DIR, connect, migrate, sichern
from ..fehler import Fehler
from ..texte import t
from ..version import VERSION

NAME_MUSTER = re.compile(r"^finds-[a-z-]+-\d{8}-\d{6}(-\d+)?\.zip$")
VERWALTER_TABELLEN = ("system_verwalter", "system_sitzung", "system_fehlversuch")


# ---------- Sichern ----------

def erstellen(db_path: Path, media_dir: Path, ziel_dir: Path, anlass: str = "manuell") -> Path:
    ziel_dir.mkdir(parents=True, exist_ok=True)
    stempel = datetime.now().strftime("%Y%m%d-%H%M%S")
    ziel = ziel_dir / f"finds-{anlass}-{stempel}.zip"
    n = 1
    while ziel.exists():
        ziel = ziel_dir / f"finds-{anlass}-{stempel}-{n}.zip"
        n += 1
    with tempfile.TemporaryDirectory() as tmp:
        kopie = Path(tmp) / "finds.db"
        conn = connect(db_path)
        try:
            sichern(conn, kopie)
            info = {"programm": "miaza finds", "version": VERSION, "erstellt": datetime.now().isoformat(timespec="seconds"),
                    "produkte": conn.execute("SELECT count(*) FROM produkt").fetchone()[0],
                    "migrationen": [r[0] for r in conn.execute("SELECT name FROM schema_migration ORDER BY name")]}
        finally:
            conn.close()
        with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(kopie, "finds.db")
            z.writestr("info.json", json.dumps(info, ensure_ascii=False, indent=2))
            if media_dir.exists():
                for datei in sorted(media_dir.rglob("*")):
                    if datei.is_file():
                        # Fotos sind schon komprimiert; nicht noch einmal packen
                        z.write(datei, "media/" + datei.relative_to(media_dir).as_posix(), compress_type=zipfile.ZIP_STORED)
    return ziel


def liste(ziel_dir: Path) -> list[dict[str, Any]]:
    if not ziel_dir.exists():
        return []
    dateien = [p for p in ziel_dir.glob("finds-*.zip") if NAME_MUSTER.match(p.name)]
    return [{"name": p.name, "groesse": p.stat().st_size,
             "zeit": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")}
            for p in sorted(dateien, key=lambda p: p.stat().st_mtime, reverse=True)]


def datei(ziel_dir: Path, name: str) -> Path:
    """Nur Dateien aus dem Sicherungsordner, keine fremden Pfade."""
    if not NAME_MUSTER.match(name or "") or not (ziel_dir / name).is_file():
        raise Fehler(t("fehler.sicherung_unbekannt"), status=404)
    return ziel_dir / name


# ---------- Wiederherstellen / Übernehmen ----------

def _auspacken(quelle: Path, tmp: Path) -> tuple[Path, Path | None]:
    """ZIP oder kopierter Datenordner → (finds.db, media-Ordner oder None)."""
    if quelle.is_file() and zipfile.is_zipfile(quelle):
        with zipfile.ZipFile(quelle) as z:
            for name in z.namelist():
                teile = Path(name).parts
                if name.startswith(("/", "\\")) or ".." in teile or (teile[0] not in ("finds.db", "info.json", "media")):
                    raise Fehler(t("fehler.sicherung_ungueltig"), "datei")
            if "finds.db" not in z.namelist():
                raise Fehler(t("fehler.sicherung_ungueltig"), "datei")
            z.extractall(tmp)
        media = tmp / "media"
        return tmp / "finds.db", media if media.is_dir() else None
    if quelle.is_dir():
        # Kopierter Ordner: finds.db direkt oder in data/, Fotos in media/ daneben oder eine Ebene höher
        for db in (quelle / "finds.db", quelle / "data" / "finds.db"):
            if db.is_file():
                for media in (quelle / "media", db.parent / "media", db.parent.parent / "media"):
                    if media.is_dir():
                        return db, media
                return db, None
    raise Fehler(t("fehler.sicherung_ungueltig"), "datei")


def _pruefen(db: Path) -> dict[str, Any]:
    try:
        conn = sqlite3.connect(db)
        ok = conn.execute("PRAGMA integrity_check").fetchone()[0]
        namen = {r[0] for r in conn.execute("SELECT name FROM schema_migration")}
        produkte = conn.execute("SELECT count(*) FROM produkt").fetchone()[0]
        conn.close()
    except sqlite3.DatabaseError:
        raise Fehler(t("fehler.sicherung_ungueltig"), "datei") from None
    if ok != "ok":
        raise Fehler(t("fehler.sicherung_ungueltig"), "datei")
    if namen - {f.name for f in MIGRATIONS_DIR.glob("*.sql")}:
        raise Fehler(t("fehler.sicherung_neuer"), "datei")
    return {"produkte": produkte}


def einspielen(db_path: Path, media_dir: Path, sicherung_dir: Path, quelle: Path) -> dict[str, Any]:
    """Ersetzt alle Daten durch die Quelle (Sicherung oder kopierter Ordner eines alten Servers, D-009).

    Vorher automatische Sicherung. Der Verwalter dieser Installation (Passwort, Schlüssel) bleibt.
    """
    with tempfile.TemporaryDirectory() as tmp:
        db, media = _auspacken(quelle, Path(tmp))
        info = _pruefen(db)
        vorher = erstellen(db_path, media_dir, sicherung_dir, "vor-uebernahme")

        live = connect(db_path)
        try:
            verwalter = {tab: [tuple(r) for r in live.execute(f"SELECT * FROM {tab}")] for tab in VERWALTER_TABELLEN}
            quelle_conn = sqlite3.connect(db)
            try:
                quelle_conn.backup(live)          # ersetzt den Inhalt in einem Zug
            finally:
                quelle_conn.close()
            migrate(live, sicherung_dir)          # ältere Programmversion → auf den heutigen Stand
            live.execute("BEGIN IMMEDIATE")
            for tab, zeilen in verwalter.items():
                live.execute(f"DELETE FROM {tab}")
                if zeilen:
                    live.executemany(f"INSERT INTO {tab} VALUES ({','.join('?' * len(zeilen[0]))})", zeilen)
            live.execute("COMMIT")
        finally:
            live.close()

        fotos = _media_ersetzen(media_dir, media)
    return {"produkte": info["produkte"], "fotos": fotos, "sicherung_vorher": vorher.name}


def _media_ersetzen(media_dir: Path, neu: Path | None) -> int:
    if media_dir.exists():
        for kind in media_dir.iterdir():
            shutil.rmtree(kind) if kind.is_dir() else kind.unlink()
    media_dir.mkdir(parents=True, exist_ok=True)
    if neu is None:
        return 0
    shutil.copytree(neu, media_dir, dirs_exist_ok=True)
    return sum(1 for p in (media_dir / "fotos").glob("*.jpg")) if (media_dir / "fotos").exists() else 0


# ---------- Löschen ----------

# Teile, die einzeln gelöscht werden können (D-025)
TEILE = ("produkte", "kategorien", "plan", "nummern")


def wirkung(conn: sqlite3.Connection) -> dict[str, int]:
    """Was die Löschung je Teil trifft – steht vor dem Klick da (SPEC 6.13)."""
    zahl = lambda sql: conn.execute(sql).fetchone()[0]
    return {"produkte": zahl("SELECT count(*) FROM produkt"), "fotos": zahl("SELECT count(*) FROM foto"),
            "kategorien": zahl("SELECT count(*) FROM kategorie WHERE fest = 0"),
            "raeume": zahl("SELECT count(*) FROM raum"), "einheiten": zahl("SELECT count(*) FROM einheit"),
            "faecher": zahl("SELECT count(*) FROM fach")}


def teile_pruefen(teile: Any) -> set[str]:
    """Kategorien gibt es nur mit ihren Produkten; Nummern neu nur, wenn nichts mehr auf sie verweist."""
    if not isinstance(teile, list) or not teile or any(x not in TEILE for x in teile):
        raise Fehler(t("fehler.art"), "teile")
    gewaehlt = set(teile)
    if "kategorien" in gewaehlt:
        gewaehlt.add("produkte")
    if "nummern" in gewaehlt and not {"produkte", "plan"} <= gewaehlt:
        raise Fehler(t("fehler.nummern_nur_mit"), "teile")
    return gewaehlt


def loeschen(conn: sqlite3.Connection, media_dir: Path, teile: set[str]) -> None:
    """Gewählte Teile löschen (D-025). Vorher gedruckte Etiketten werden bei „nummern“ ungültig – das sagt die Oberfläche."""
    if "produkte" in teile:
        conn.execute("DELETE FROM produkt")
        shutil.rmtree(media_dir / "fotos", ignore_errors=True)
    if "kategorien" in teile:
        conn.execute("DELETE FROM filter")
        conn.execute("DELETE FROM kategorie WHERE fest = 0")
    if "plan" in teile:
        # Einheiten nehmen ihre Fächer mit; Produkte werden „Ohne Platz“ (ON DELETE SET NULL)
        conn.execute("DELETE FROM einheit")
        conn.execute("DELETE FROM raum")
        conn.execute("""UPDATE plan SET version = version + 1, unterlage = NULL, unterlage_breite = NULL, unterlage_hoehe = NULL,
                        unterlage_x = 0, unterlage_y = 0, unterlage_massstab = 1, unterlage_drehung = 0, unterlage_im_buero = 0""")
        shutil.rmtree(media_dir / "plan", ignore_errors=True)
        shutil.rmtree(media_dir / "einheiten", ignore_errors=True)
    if "nummern" in teile:
        conn.execute("UPDATE kategorie SET naechste_nr = 1, version = version + 1")
        conn.execute("UPDATE zaehler SET wert = 0")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'fach'")
