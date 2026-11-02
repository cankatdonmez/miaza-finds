-- Farbe des Raums: eine der sechs Pastellfarben (D-024, THEMA.md); bestehende Räume der Reihe nach
ALTER TABLE raum ADD COLUMN farbe INTEGER NOT NULL DEFAULT 1 CHECK (farbe BETWEEN 1 AND 6);
UPDATE raum SET farbe = ((nr - 1) % 6) + 1;
