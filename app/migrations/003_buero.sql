-- Dilim 2: Büro – Plan, Räume, Einheiten, Fächer; Platz des Produkts (SPEC 6.4, 7, D-017)

-- Genau ein Plan. Räume, Einheiten und Fächer gehören zu seiner Version (SPEC 7): jedes Speichern erhöht sie.
-- Unterlage: Bild in media/plan/, Lage in Planeinheiten (x, y = linke obere Ecke), Maßstab = Planeinheiten je Bildpixel.
CREATE TABLE plan (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  version INTEGER NOT NULL DEFAULT 1,
  unterlage TEXT,
  unterlage_breite INTEGER,
  unterlage_hoehe INTEGER,
  unterlage_x REAL NOT NULL DEFAULT 0,
  unterlage_y REAL NOT NULL DEFAULT 0,
  unterlage_massstab REAL NOT NULL DEFAULT 1 CHECK (unterlage_massstab > 0),
  unterlage_drehung INTEGER NOT NULL DEFAULT 0 CHECK (unterlage_drehung IN (0, 90, 180, 270)),
  unterlage_im_buero INTEGER NOT NULL DEFAULT 0 CHECK (unterlage_im_buero IN (0, 1))
);
INSERT INTO plan (id) VALUES (1);

-- Punkte als JSON [[x, y], …] in Planeinheiten; die Raumnummer ist die erste Stelle der Codes (2.2.5)
CREATE TABLE raum (
  id INTEGER PRIMARY KEY,
  nr INTEGER NOT NULL UNIQUE CHECK (nr >= 1),
  name TEXT NOT NULL DEFAULT '',
  punkte TEXT NOT NULL
);

-- Einheit außerhalb jedes Raums: raum_id NULL, wird markiert (SPEC 6.4)
CREATE TABLE einheit (
  id INTEGER PRIMARY KEY,
  raum_id INTEGER REFERENCES raum(id) ON DELETE SET NULL,
  nr INTEGER NOT NULL CHECK (nr >= 1),
  name TEXT NOT NULL DEFAULT '',
  punkte TEXT NOT NULL,
  foto TEXT,
  foto_breite INTEGER,
  foto_hoehe INTEGER
);
CREATE UNIQUE INDEX einheit_nr ON einheit(raum_id, nr) WHERE raum_id IS NOT NULL;

-- AUTOINCREMENT: die Kennung steht im QR des Fach-Etiketts und wird nie wiederverwendet (SPEC 6.6).
-- Punkte in Prozent des Einheitsfotos (0–100), damit ein neues Foto gleicher Ansicht passt.
CREATE TABLE fach (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  einheit_id INTEGER NOT NULL REFERENCES einheit(id) ON DELETE CASCADE,
  nr INTEGER NOT NULL CHECK (nr >= 1),
  punkte TEXT NOT NULL,
  etikett TEXT NOT NULL DEFAULT 'ungedruckt' CHECK (etikett IN ('ungedruckt', 'gedruckt', 'neu_drucken')),
  UNIQUE (einheit_id, nr)
);

-- Platz des Produkts über die bleibende Fach-Kennung; gelöschtes Fach → Produkt „Ohne Platz“ (SPEC 6.4, 7)
ALTER TABLE produkt ADD COLUMN fach_id INTEGER REFERENCES fach(id) ON DELETE SET NULL;
CREATE INDEX produkt_fach ON produkt(fach_id);
