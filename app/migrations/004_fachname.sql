-- Name des Fachs, frei und optional wie bei der Einheit („Obere Schublade“; D-020)
ALTER TABLE fach ADD COLUMN name TEXT NOT NULL DEFAULT '';
