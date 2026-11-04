-- Einstellungen des ganzen Büros (SPEC 6.11), nicht des Geräts. Fehlt ein Schlüssel, gilt der Standard aus
-- services/einstellungen.py; so braucht ein neuer Schalter keine Migration.
CREATE TABLE einstellung (
    schluessel TEXT PRIMARY KEY,
    wert TEXT NOT NULL
);
