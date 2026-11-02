"""Verwalter des Systembereichs (SPEC 6.13, D-006, D-010): Einrichtung, Anmeldung, Sicherheitsschlüssel, Sitzung.

Der Rest der App bleibt ohne Anmeldung. Passwort und Schlüssel werden nur als argon2-Hash gespeichert.
"""
from __future__ import annotations

import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from ..fehler import Fehler
from ..texte import t

_ph = PasswordHasher()
PASSWORT_MIN = 10
SITZUNG_MINUTEN = 30
SPERRE_VERSUCHE = 5
SPERRE_MINUTEN = 15
_ZEICHEN = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"     # ohne 0/O und 1/I, gut abzuschreiben


def _jetzt() -> datetime:
    return datetime.now(timezone.utc)


def _iso(d: datetime) -> str:
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def eingerichtet(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT 1 FROM system_verwalter WHERE id = 1").fetchone() is not None


def neuer_schluessel() -> str:
    """Fünf Gruppen à fünf Zeichen (≈ 125 Bit), z. B. K7Q2M-…"""
    return "-".join("".join(secrets.choice(_ZEICHEN) for _ in range(5)) for _ in range(5))


def _schluessel_norm(schluessel: str) -> str:
    return "".join(c for c in str(schluessel or "").upper() if c.isalnum())


def _passwort_pruefen(passwort: str, wiederholung: str) -> None:
    if len(passwort or "") < PASSWORT_MIN:
        raise Fehler(t("fehler.passwort_kurz", n=PASSWORT_MIN), "passwort")
    if passwort != wiederholung:
        raise Fehler(t("fehler.passwort_ungleich"), "passwort2")


def einrichten(conn: sqlite3.Connection, benutzername: str, passwort: str, wiederholung: str) -> str:
    """Erstes Öffnen: Verwalter anlegen. Liefert den Sicherheitsschlüssel (wird nur dieses eine Mal gezeigt)."""
    if eingerichtet(conn):
        raise Fehler(t("fehler.schon_eingerichtet"), status=409)
    name = " ".join(str(benutzername or "").split())
    if not name:
        raise Fehler(t("fehler.name_fehlt"), "benutzername")
    _passwort_pruefen(passwort, wiederholung)
    schluessel = neuer_schluessel()
    conn.execute("INSERT INTO system_verwalter (id, benutzername, passwort_hash, schluessel_hash) VALUES (1, ?, ?, ?)",
                 (name, _ph.hash(passwort), _ph.hash(_schluessel_norm(schluessel))))
    return schluessel


def _gesperrt(conn: sqlite3.Connection) -> bool:
    seit = _iso(_jetzt() - timedelta(minutes=SPERRE_MINUTEN))
    return conn.execute("SELECT count(*) FROM system_fehlversuch WHERE zeit > ?", (seit,)).fetchone()[0] >= SPERRE_VERSUCHE


def _fehlversuch(conn: sqlite3.Connection) -> None:
    conn.execute("INSERT INTO system_fehlversuch (zeit) VALUES (?)", (_iso(_jetzt()),))


def _verwalter(conn: sqlite3.Connection) -> sqlite3.Row:
    v = conn.execute("SELECT * FROM system_verwalter WHERE id = 1").fetchone()
    if v is None:
        raise Fehler(t("fehler.nicht_eingerichtet"), status=409)
    return v


def _stimmt(hash_: str, wert: str) -> bool:
    try:
        return _ph.verify(hash_, wert)
    except (VerificationError, InvalidHashError):
        return False


def anmelden(conn: sqlite3.Connection, benutzername: str, passwort: str) -> tuple[str, str] | None:
    """Liefert (Sitzungskennung, CSRF-Schlüssel). Fehlversuche zählen; nach 5 in 15 Minuten ist gesperrt.

    Aufrufer: eigene Transaktion, die auch bei Fehlschlag committet wird (der Fehlversuch muss bleiben).
    """
    if _gesperrt(conn):
        raise Fehler(t("fehler.gesperrt", n=SPERRE_MINUTEN), status=429)
    v = _verwalter(conn)
    if str(benutzername or "").strip().casefold() != v["benutzername"].casefold() or not _stimmt(v["passwort_hash"], passwort or ""):
        _fehlversuch(conn)
        return None
    conn.execute("DELETE FROM system_fehlversuch")
    return sitzung_anlegen(conn)


def sitzung_anlegen(conn: sqlite3.Connection) -> tuple[str, str]:
    kennung, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
    jetzt = _jetzt()
    conn.execute("DELETE FROM system_sitzung WHERE laeuft_ab < ?", (_iso(jetzt),))
    conn.execute("INSERT INTO system_sitzung (kennung_hash, csrf, erstellt_am, laeuft_ab) VALUES (?, ?, ?, ?)",
                 (_hash(kennung), csrf, _iso(jetzt), _iso(jetzt + timedelta(minutes=SITZUNG_MINUTEN))))
    return kennung, csrf


def _hash(kennung: str) -> str:
    return hashlib.sha256(kennung.encode()).hexdigest()


def sitzung(conn: sqlite3.Connection, kennung: str | None) -> dict | None:
    """Gültige Sitzung → {"csrf": …}; jede Nutzung verlängert sie (30 Minuten ohne Aktivität)."""
    if not kennung:
        return None
    jetzt = _jetzt()
    s = conn.execute("SELECT csrf, laeuft_ab FROM system_sitzung WHERE kennung_hash = ?", (_hash(kennung),)).fetchone()
    if s is None or s["laeuft_ab"] < _iso(jetzt):
        return None
    conn.execute("UPDATE system_sitzung SET laeuft_ab = ? WHERE kennung_hash = ?",
                 (_iso(jetzt + timedelta(minutes=SITZUNG_MINUTEN)), _hash(kennung)))
    return {"csrf": s["csrf"]}


def abmelden(conn: sqlite3.Connection, kennung: str | None) -> None:
    if kennung:
        conn.execute("DELETE FROM system_sitzung WHERE kennung_hash = ?", (_hash(kennung),))


def mit_schluessel_zuruecksetzen(conn: sqlite3.Connection, schluessel: str, passwort: str, wiederholung: str) -> str | None:
    """Passwort vergessen: mit dem Sicherheitsschlüssel neues Passwort. Der Schlüssel gilt danach nicht mehr;
    der neue wird einmal gezeigt (D-010). Alle Sitzungen enden.
    """
    if _gesperrt(conn):
        raise Fehler(t("fehler.gesperrt", n=SPERRE_MINUTEN), status=429)
    v = _verwalter(conn)
    if not _stimmt(v["schluessel_hash"], _schluessel_norm(schluessel)):
        _fehlversuch(conn)
        return None
    _passwort_pruefen(passwort, wiederholung)
    neu = neuer_schluessel()
    conn.execute("UPDATE system_verwalter SET passwort_hash = ?, schluessel_hash = ? WHERE id = 1",
                 (_ph.hash(passwort), _ph.hash(_schluessel_norm(neu))))
    conn.execute("DELETE FROM system_sitzung")
    conn.execute("DELETE FROM system_fehlversuch")
    return neu


def passwort_aendern(conn: sqlite3.Connection, alt: str, neu: str, wiederholung: str) -> None:
    v = _verwalter(conn)
    if not _stimmt(v["passwort_hash"], alt or ""):
        raise Fehler(t("fehler.passwort_falsch"), "alt")
    _passwort_pruefen(neu, wiederholung)
    conn.execute("UPDATE system_verwalter SET passwort_hash = ? WHERE id = 1", (_ph.hash(neu),))


def schluessel_erneuern(conn: sqlite3.Connection) -> str:
    _verwalter(conn)
    neu = neuer_schluessel()
    conn.execute("UPDATE system_verwalter SET schluessel_hash = ? WHERE id = 1", (_ph.hash(_schluessel_norm(neu)),))
    return neu
