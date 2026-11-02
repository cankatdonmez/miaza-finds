"""Produktfotos: der Server erzeugt die Vorschaugrößen selbst (SPEC 6.2, 8.1).

Dateien in media/fotos/: <name>.jpg (höchstens 2400 px, für die Detailansicht) und <name>-<px>.webp (Vorschau).
In der Datenbank steht nur <name>.
"""
from __future__ import annotations

import io
import sqlite3
import uuid
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from ..fehler import Fehler
from ..texte import t

MAX_BYTES = 25 * 1024 * 1024
GROESSE_GROSS = 2400
VORSCHAU = (320, 960)
FORMATE = {"JPEG", "PNG", "WEBP", "MPO"}


def ordner(media_dir: Path) -> Path:
    o = media_dir / "fotos"
    o.mkdir(parents=True, exist_ok=True)
    return o


def dateien_von(media_dir: Path, name: str) -> list[Path]:
    o = ordner(media_dir)
    return [o / f"{name}.jpg", *(o / f"{name}-{px}.webp" for px in VORSCHAU)]


def speichern(conn: sqlite3.Connection, media_dir: Path, inventar_nr: int, daten: bytes) -> dict:
    """Prüft und speichert ein Bild; die Datenbankzeile entsteht in der Transaktion des Aufrufers."""
    if conn.execute("SELECT 1 FROM produkt WHERE inventar_nr = ?", (inventar_nr,)).fetchone() is None:
        raise Fehler(t("fehler.produkt_unbekannt"), status=404)
    if len(daten) > MAX_BYTES:
        raise Fehler(t("fehler.bild_gross"), "foto")
    try:
        bild = Image.open(io.BytesIO(daten))
        if bild.format not in FORMATE:
            raise Fehler(t("fehler.bild_format"), "foto")
        bild = ImageOps.exif_transpose(bild)       # Handyfotos richtig herum
        bild.load()
    except (UnidentifiedImageError, OSError):
        raise Fehler(t("fehler.bild_format"), "foto") from None
    if bild.mode not in ("RGB", "L"):
        hintergrund = Image.new("RGB", bild.size, "white")
        hintergrund.paste(bild.convert("RGBA"), mask=bild.convert("RGBA").getchannel("A"))
        bild = hintergrund
    elif bild.mode == "L":
        bild = bild.convert("RGB")

    name = uuid.uuid4().hex
    gross, *vorschauen = dateien_von(media_dir, name)
    kopie = bild.copy()
    kopie.thumbnail((GROESSE_GROSS, GROESSE_GROSS), Image.Resampling.LANCZOS)
    kopie.save(gross, "JPEG", quality=88, optimize=True)
    for px, ziel in zip(VORSCHAU, vorschauen):
        v = bild.copy()
        v.thumbnail((px, px), Image.Resampling.LANCZOS)
        v.save(ziel, "WEBP", quality=80)

    try:
        sortierung = conn.execute("SELECT coalesce(max(sortierung), -1) + 1 FROM foto WHERE produkt_id = ?",
                                  (inventar_nr,)).fetchone()[0]
        fid = conn.execute("INSERT INTO foto (produkt_id, datei, breite, hoehe, sortierung) VALUES (?, ?, ?, ?, ?) RETURNING id",
                           (inventar_nr, name, kopie.width, kopie.height, sortierung)).fetchone()[0]
    except Exception:
        dateien_entfernen(media_dir, [name])     # keine verwaisten Dateien
        raise
    return {"id": fid, "datei": name, "breite": kopie.width, "hoehe": kopie.height}


def loeschen(conn: sqlite3.Connection, inventar_nr: int, foto_id: int) -> str:
    """Entfernt die Zeile; liefert den Dateinamen, den der Aufrufer nach dem Commit löscht."""
    zeile = conn.execute("SELECT datei FROM foto WHERE id = ? AND produkt_id = ?", (foto_id, inventar_nr)).fetchone()
    if zeile is None:
        raise Fehler(t("fehler.foto_unbekannt"), status=404)
    conn.execute("DELETE FROM foto WHERE id = ?", (foto_id,))
    return zeile[0]


def dateien_entfernen(media_dir: Path, namen: list[str]) -> None:
    for name in namen:
        for p in dateien_von(media_dir, name):
            p.unlink(missing_ok=True)
