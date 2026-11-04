-- Sammlungen (SPEC 6.8, D-047): benannte Produktlisten ohne Mengen. Entfernen blendet aus (entfernt_am), damit Rückgängig alles zurückholt.
CREATE TABLE sammlung (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL CHECK (length(trim(name)) > 0),
  notiz TEXT,
  erstellt_am TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  entfernt_am TEXT
);

CREATE TABLE sammlung_produkt (
  sammlung_id INTEGER NOT NULL REFERENCES sammlung(id) ON DELETE CASCADE,
  produkt_id INTEGER NOT NULL REFERENCES produkt(inventar_nr) ON DELETE CASCADE,
  hinzugefuegt_am TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  PRIMARY KEY (sammlung_id, produkt_id)
);
CREATE INDEX sammlung_produkt_produkt ON sammlung_produkt(produkt_id);
