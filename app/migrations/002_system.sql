-- Systembereich (SPEC 6.13, D-006, D-010): ein Verwalter mit Passwort und Sicherheitsschlüssel.
-- Gespeichert werden nur Hashes (argon2), nie Passwort oder Schlüssel selbst.

CREATE TABLE system_verwalter (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  benutzername TEXT NOT NULL CHECK (length(trim(benutzername)) > 0),
  passwort_hash TEXT NOT NULL,
  schluessel_hash TEXT NOT NULL,
  erstellt_am TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- Sitzungen nur für den Systembereich; Kennung als Hash, kurze Laufzeit
CREATE TABLE system_sitzung (
  kennung_hash TEXT PRIMARY KEY,
  csrf TEXT NOT NULL,
  erstellt_am TEXT NOT NULL,
  laeuft_ab TEXT NOT NULL
);

-- Fehlversuche bei Anmeldung und Schlüssel (Sperre nach mehreren Versuchen)
CREATE TABLE system_fehlversuch (
  id INTEGER PRIMARY KEY,
  zeit TEXT NOT NULL
);
