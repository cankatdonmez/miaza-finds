-- Dilim 1: Bibliothek und Erfassung (SPEC 6.1–6.3, 7). Fach/Ort folgt mit Dilim 2 per ALTER TABLE ADD COLUMN.

-- Zähler für Nummern, die nie wiederverwendet werden (SPEC 6.2, 7)
CREATE TABLE zaehler (
  name TEXT PRIMARY KEY,
  wert INTEGER NOT NULL CHECK (wert >= 0)
);
INSERT INTO zaehler (name, wert) VALUES ('inventar', 0);

CREATE TABLE kategorie (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK (length(trim(name)) > 0),
  -- zwei Großbuchstaben, eindeutig (SPEC 6.2)
  praefix TEXT NOT NULL UNIQUE CHECK (length(praefix) = 2 AND praefix GLOB '[A-Z][A-Z]'),
  -- „Sonstiges“ gibt es immer, sie ist nicht löschbar (SPEC 6.3)
  fest INTEGER NOT NULL DEFAULT 0 CHECK (fest IN (0, 1)),
  sortierung INTEGER NOT NULL DEFAULT 0,
  -- nächste laufende Nummer innerhalb der Kategorie (KKK im Code)
  naechste_nr INTEGER NOT NULL DEFAULT 1 CHECK (naechste_nr >= 1),
  version INTEGER NOT NULL DEFAULT 1
);
INSERT INTO kategorie (name, praefix, fest, sortierung) VALUES ('Sonstiges', 'XX', 1, 1000);

CREATE TRIGGER kategorie_fest_nicht_loeschen BEFORE DELETE ON kategorie
WHEN OLD.fest = 1
BEGIN
  SELECT RAISE(ABORT, 'kategorie_fest');
END;

CREATE TRIGGER kategorie_fest_bleibt BEFORE UPDATE OF fest ON kategorie
WHEN OLD.fest <> NEW.fest
BEGIN
  SELECT RAISE(ABORT, 'kategorie_fest');
END;

-- Filter je Kategorie; Reihenfolge = Reihenfolge im Filterbereich (SPEC 6.3)
CREATE TABLE filter (
  id INTEGER PRIMARY KEY,
  kategorie_id INTEGER NOT NULL REFERENCES kategorie(id) ON DELETE CASCADE,
  name TEXT NOT NULL CHECK (length(trim(name)) > 0),
  typ TEXT NOT NULL CHECK (typ IN ('mass', 'einfach', 'mehrfach', 'janein')),
  -- nur bei typ 'mass': mm, cm, m, kg, Stk
  einheit TEXT CHECK (einheit IS NULL OR typ = 'mass'),
  sortierung INTEGER NOT NULL DEFAULT 0,
  UNIQUE (kategorie_id, name)
);
CREATE INDEX filter_kategorie ON filter(kategorie_id, sortierung);

CREATE TABLE filter_option (
  id INTEGER PRIMARY KEY,
  filter_id INTEGER NOT NULL REFERENCES filter(id) ON DELETE CASCADE,
  name TEXT NOT NULL CHECK (length(trim(name)) > 0),
  sortierung INTEGER NOT NULL DEFAULT 0,
  UNIQUE (filter_id, name)
);
CREATE INDEX filter_option_filter ON filter_option(filter_id, sortierung);

-- Produkt: die Inventarnummer ist die bleibende Kennung (QR, SPEC 6.6) und wird aus dem Zähler vergeben.
-- Code = code_praefix-kategorie_nr-inventar_nr, z. B. ST-005-265. code_praefix kann vom Präfix der Kategorie
-- abweichen, wenn beim Kategoriewechsel „Code behalten“ gewählt wurde (SPEC 6.2).
CREATE TABLE produkt (
  inventar_nr INTEGER PRIMARY KEY CHECK (inventar_nr >= 1),
  kategorie_id INTEGER NOT NULL REFERENCES kategorie(id),
  code_praefix TEXT NOT NULL CHECK (length(code_praefix) = 2),
  kategorie_nr INTEGER NOT NULL CHECK (kategorie_nr >= 1),
  art TEXT NOT NULL DEFAULT 'physisch' CHECK (art IN ('physisch', 'digital')),
  -- leer nur aus der Serienerfassung („Fehlende Angaben“, SPEC 6.1/6.2)
  name TEXT CHECK (name IS NULL OR length(trim(name)) > 0),
  marke TEXT,
  abmessungen TEXT,
  link TEXT,
  anzahl INTEGER CHECK (anzahl IS NULL OR anzahl >= 0),
  notiz TEXT,
  etikett TEXT NOT NULL DEFAULT 'ungedruckt' CHECK (etikett IN ('ungedruckt', 'gedruckt', 'neu_drucken')),
  -- kleingeschrieben, ä→ae, ß→ss usw.; wird vom Dienst gepflegt (SPEC 6.1)
  suchtext TEXT NOT NULL DEFAULT '',
  erstellt_am TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  geaendert_am TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  version INTEGER NOT NULL DEFAULT 1,
  UNIQUE (kategorie_id, kategorie_nr)
);
CREATE INDEX produkt_kategorie ON produkt(kategorie_id);
CREATE INDEX produkt_unvollstaendig ON produkt(inventar_nr) WHERE name IS NULL;

CREATE TRIGGER produkt_inventar_unveraenderlich BEFORE UPDATE OF inventar_nr ON produkt
WHEN OLD.inventar_nr <> NEW.inventar_nr
BEGIN
  SELECT RAISE(ABORT, 'inventar_unveraenderlich');
END;

-- Werte der kategoriespezifischen Filter. mass: zahl · einfach/mehrfach: option_id (mehrfach = mehrere Zeilen) · janein: janein
CREATE TABLE produkt_wert (
  id INTEGER PRIMARY KEY,
  produkt_id INTEGER NOT NULL REFERENCES produkt(inventar_nr) ON DELETE CASCADE,
  filter_id INTEGER NOT NULL REFERENCES filter(id) ON DELETE CASCADE,
  option_id INTEGER REFERENCES filter_option(id) ON DELETE CASCADE,
  zahl REAL,
  janein INTEGER CHECK (janein IS NULL OR janein IN (0, 1)),
  CHECK ((option_id IS NOT NULL) + (zahl IS NOT NULL) + (janein IS NOT NULL) = 1)
);
CREATE UNIQUE INDEX produkt_wert_option ON produkt_wert(produkt_id, filter_id, option_id) WHERE option_id IS NOT NULL;
CREATE UNIQUE INDEX produkt_wert_einzeln ON produkt_wert(produkt_id, filter_id) WHERE option_id IS NULL;
CREATE INDEX produkt_wert_filter ON produkt_wert(filter_id, option_id);

-- Farben aus der festen Palette (SPEC 6.2)
CREATE TABLE produkt_farbe (
  produkt_id INTEGER NOT NULL REFERENCES produkt(inventar_nr) ON DELETE CASCADE,
  farbe TEXT NOT NULL CHECK (farbe IN ('weiss', 'beige', 'braun', 'terracotta', 'gold', 'rosa', 'gruen', 'blau', 'grau', 'schwarz')),
  PRIMARY KEY (produkt_id, farbe)
);
CREATE INDEX produkt_farbe_farbe ON produkt_farbe(farbe);

-- Preis in Cent mit Einheit und Datum. In v1 ein Preis je Produkt (eindeutiger Index, für die Preisgeschichte in v2 entfernbar).
CREATE TABLE preis (
  id INTEGER PRIMARY KEY,
  produkt_id INTEGER NOT NULL REFERENCES produkt(inventar_nr) ON DELETE CASCADE,
  cent INTEGER NOT NULL CHECK (cent >= 0),
  einheit TEXT NOT NULL CHECK (einheit IN ('m2', 'm', 'stueck', 'paket')),
  waehrung TEXT NOT NULL DEFAULT 'EUR',
  datum TEXT NOT NULL
);
CREATE UNIQUE INDEX preis_je_produkt ON preis(produkt_id);

-- Fotos: Originaldatei und Vorschaugrößen liegen in media/, hier nur der Dateiname
CREATE TABLE foto (
  id INTEGER PRIMARY KEY,
  produkt_id INTEGER NOT NULL REFERENCES produkt(inventar_nr) ON DELETE CASCADE,
  datei TEXT NOT NULL UNIQUE,
  breite INTEGER NOT NULL CHECK (breite > 0),
  hoehe INTEGER NOT NULL CHECK (hoehe > 0),
  sortierung INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX foto_produkt ON foto(produkt_id, sortierung);
