-- Personen des Büros (SPEC 6.7, D-038): nur ein Name. Entfernte bleiben mit entfernt_am stehen,
-- damit spätere Ausleihen ihren Namen behalten; ein Name ist nur unter den aktiven eindeutig.
CREATE TABLE person (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) BETWEEN 1 AND 60),
    entfernt_am TEXT
);
CREATE UNIQUE INDEX person_name_aktiv ON person (name COLLATE NOCASE) WHERE entfernt_am IS NULL;
