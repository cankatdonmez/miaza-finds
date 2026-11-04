-- Entnahme-Eintrag („Çıkış kaydı“, SPEC 6.7, D-039). Offen = zurueck_am IS NULL; daraus kommt der Status des Produkts.
-- fach_bestaetigt: beim Zurücklegen mit Fach-QR bestätigt (1), ohne Scan (0), noch nicht zurück oder ohne Abfrage (NULL).
CREATE TABLE entnahme (
    id INTEGER PRIMARY KEY,
    produkt_id INTEGER NOT NULL REFERENCES produkt(inventar_nr) ON DELETE CASCADE,
    person_id INTEGER REFERENCES person(id),
    ort TEXT NOT NULL CHECK (ort IN ('buero', 'ausser_haus')),
    notiz TEXT,
    genommen_am TEXT NOT NULL,
    zurueck_am TEXT,
    fach_bestaetigt INTEGER CHECK (fach_bestaetigt IN (0, 1))
);
CREATE UNIQUE INDEX entnahme_offen ON entnahme (produkt_id) WHERE zurueck_am IS NULL;
CREATE INDEX entnahme_produkt ON entnahme (produkt_id, genommen_am);
