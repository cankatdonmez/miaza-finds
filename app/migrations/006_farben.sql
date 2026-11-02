-- Grundfarben und Farbtöne je Kategorie (D-031)

-- „Farbe“-Filter: ein Mehrfachauswahl-Filter, dessen Auswahlen Farbtöne sind
ALTER TABLE filter ADD COLUMN farbe INTEGER NOT NULL DEFAULT 0 CHECK (farbe IN (0, 1));

-- Farbton: eigene Farbe (#RRGGBB) und die Grundfarbe, zu der er gehört
ALTER TABLE filter_option ADD COLUMN hex TEXT
  CHECK (hex IS NULL OR hex GLOB '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]');
ALTER TABLE filter_option ADD COLUMN grundfarbe TEXT
  CHECK (grundfarbe IS NULL OR grundfarbe IN ('weiss', 'beige', 'braun', 'rot', 'orange', 'gelb', 'gruen', 'blau',
                                              'violett', 'rosa', 'grau', 'schwarz', 'metall', 'mehrfarbig'));

-- Neue Grundfarbenliste: Terracotta wird Orange, Gold wird Metall. Auf produkt_farbe zeigt kein Fremdschlüssel,
-- die Tabelle kann neu angelegt werden.
CREATE TABLE produkt_farbe_neu (
  produkt_id INTEGER NOT NULL REFERENCES produkt(inventar_nr) ON DELETE CASCADE,
  farbe TEXT NOT NULL CHECK (farbe IN ('weiss', 'beige', 'braun', 'rot', 'orange', 'gelb', 'gruen', 'blau',
                                       'violett', 'rosa', 'grau', 'schwarz', 'metall', 'mehrfarbig')),
  PRIMARY KEY (produkt_id, farbe)
);
INSERT OR IGNORE INTO produkt_farbe_neu (produkt_id, farbe)
  SELECT produkt_id, CASE farbe WHEN 'terracotta' THEN 'orange' WHEN 'gold' THEN 'metall' ELSE farbe END FROM produkt_farbe;
DROP TABLE produkt_farbe;
ALTER TABLE produkt_farbe_neu RENAME TO produkt_farbe;
CREATE INDEX produkt_farbe_farbe ON produkt_farbe(farbe);
