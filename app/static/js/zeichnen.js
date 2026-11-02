// Gemeinsame Bausteine für Plan, Fach-Editor und Büroansicht (SPEC 4.6, 4.8):
// MF.Ansicht (verschieben, zoomen, einpassen), MF.Verlauf (Rückgängig/Wiederholen), MF.geo (Geometrie).
"use strict";

(function () {
  const RUHIG = matchMedia("(prefers-reduced-motion: reduce)");

  // ---------- Geometrie ----------
  const geo = {
    rechteck: (a, b) => {
      const [x1, x2] = [Math.min(a[0], b[0]), Math.max(a[0], b[0])];
      const [y1, y2] = [Math.min(a[1], b[1]), Math.max(a[1], b[1])];
      return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]];
    },
    rahmen(punkte) {
      const xs = punkte.map((p) => p[0]), ys = punkte.map((p) => p[1]);
      const x = Math.min(...xs), y = Math.min(...ys);
      return { x, y, w: Math.max(...xs) - x, h: Math.max(...ys) - y };
    },
    vereinen(rahmen) {
      const r = rahmen.filter(Boolean);
      if (!r.length) return null;
      const x = Math.min(...r.map((a) => a.x)), y = Math.min(...r.map((a) => a.y));
      return { x, y, w: Math.max(...r.map((a) => a.x + a.w)) - x, h: Math.max(...r.map((a) => a.y + a.h)) - y };
    },
    // Schwerpunkt der Fläche; bei entarteten Formen der Mittelwert der Punkte
    mitte(punkte) {
      let a = 0, cx = 0, cy = 0;
      for (let i = 0; i < punkte.length; i++) {
        const [x1, y1] = punkte[i], [x2, y2] = punkte[(i + 1) % punkte.length];
        const k = x1 * y2 - x2 * y1;
        a += k; cx += (x1 + x2) * k; cy += (y1 + y2) * k;
      }
      if (Math.abs(a) < 1e-9) return [punkte.reduce((s, p) => s + p[0], 0) / punkte.length, punkte.reduce((s, p) => s + p[1], 0) / punkte.length];
      return [cx / (3 * a), cy / (3 * a)];
    },
    innen([x, y], punkte) {
      let drin = false;
      for (let i = 0, j = punkte.length - 1; i < punkte.length; j = i++) {
        const [xi, yi] = punkte[i], [xj, yj] = punkte[j];
        if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) drin = !drin;
      }
      return drin;
    },
    pfad: (punkte) => "M" + punkte.map((p) => `${p[0]} ${p[1]}`).join("L") + "Z",
    runden: (punkte) => punkte.map(([x, y]) => [Math.round(x * 100) / 100, Math.round(y * 100) / 100]),
  };

  // ---------- Ansicht: viewBox eines <svg> (SPEC 4.8) ----------
  // grenzen(): Rahmen des Inhalts. Zoom zwischen ganzem Inhalt und etwa 8×; der Inhalt kann nicht aus dem Bild laufen.
  // ziehenErlaubt(e): darf ein Zeiger mit linker Taste/einem Finger die Ansicht verschieben? (Editor: nur mit Leertaste)
  function Ansicht(svg, { grenzen, ziehenErlaubt = () => true, nachAenderung = () => {} }) {
    let vb = { x: 0, y: 0, w: 100, h: 100 };
    let animation = null;
    const zeiger = new Map();
    let geste = null;

    const groesse = () => {
      const r = svg.getBoundingClientRect();
      return { b: Math.max(r.width, 1), h: Math.max(r.height, 1) };
    };
    function setzen(neu) {
      vb = neu;
      svg.setAttribute("viewBox", `${vb.x} ${vb.y} ${vb.w} ${vb.h}`);
      nachAenderung(vb);
    }
    // Rahmen ins Seitenverhältnis des Elements bringen, mit Rand
    function passend(r, rand = 0.06) {
      const { b, h } = groesse();
      let w = r.w * (1 + 2 * rand) || 100, hh = r.h * (1 + 2 * rand) || 100;
      if (w / hh > b / h) hh = (w * h) / b; else w = (hh * b) / h;
      const [cx, cy] = [r.x + r.w / 2, r.y + r.h / 2];
      return { x: cx - w / 2, y: cy - hh / 2, w, h: hh };
    }
    const ganz = () => passend(grenzen() || { x: 0, y: 0, w: 100, h: 100 });
    function begrenzen(n) {
      const g = ganz();
      const w = Math.min(Math.max(n.w, g.w / 8), g.w * 1.5);
      const h = (w * n.h) / n.w;
      const cx = Math.min(Math.max(n.x + n.w / 2, g.x), g.x + g.w);
      const cy = Math.min(Math.max(n.y + n.h / 2, g.y), g.y + g.h);
      return { x: cx - w / 2, y: cy - h / 2, w, h };
    }
    function animieren(ziel, ms = 420) {
      cancelAnimationFrame(animation);
      if (RUHIG.matches) { setzen(ziel); return; }
      const start = { ...vb }, t0 = performance.now();
      const schritt = (t) => {
        const k = Math.min((t - t0) / ms, 1), e = 1 - Math.pow(1 - k, 3);
        setzen({ x: start.x + (ziel.x - start.x) * e, y: start.y + (ziel.y - start.y) * e,
                 w: start.w + (ziel.w - start.w) * e, h: start.h + (ziel.h - start.h) * e });
        if (k < 1) animation = requestAnimationFrame(schritt);
      };
      animation = requestAnimationFrame(schritt);
    }
    function punkt(e) {
      const p = svg.createSVGPoint();
      p.x = e.clientX; p.y = e.clientY;
      const q = p.matrixTransform(svg.getScreenCTM().inverse());
      return [q.x, q.y];
    }
    function zoomen(faktor, um) {
      const n = begrenzen({ w: vb.w * faktor, h: vb.h * faktor, x: 0, y: 0 });
      const k = n.w / vb.w;
      setzen(begrenzen({ x: um[0] - (um[0] - vb.x) * k, y: um[1] - (um[1] - vb.y) * k, w: n.w, h: n.h }));
    }

    svg.addEventListener("wheel", (e) => {
      e.preventDefault();
      cancelAnimationFrame(animation);
      zoomen(Math.exp(e.deltaY * (e.deltaMode === 1 ? 0.05 : 0.0015)), punkt(e));
    }, { passive: false });

    svg.addEventListener("pointerdown", (e) => {
      zeiger.set(e.pointerId, { x: e.clientX, y: e.clientY });
      const mitte = e.button === 1;
      if (zeiger.size === 2) {
        // zwei Finger: immer verschieben und zoomen (auch im Editor, SPEC 4.8)
        const [a, b] = [...zeiger.values()];
        geste = { art: "zwei", abstand: Math.hypot(a.x - b.x, a.y - b.y), mitte: [(a.x + b.x) / 2, (a.y + b.y) / 2], vb: { ...vb } };
        e.stopPropagation();
        return;
      }
      if (mitte || (e.button === 0 && ziehenErlaubt(e))) {
        geste = { art: "eins", start: [e.clientX, e.clientY], vb: { ...vb }, bewegt: false };
        svg.setPointerCapture(e.pointerId);
        if (mitte) e.preventDefault();
      }
    });
    svg.addEventListener("pointermove", (e) => {
      if (!zeiger.has(e.pointerId)) return;
      zeiger.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (!geste) return;
      const { b } = groesse();
      if (geste.art === "eins") {
        const dx = e.clientX - geste.start[0], dy = e.clientY - geste.start[1];
        if (Math.hypot(dx, dy) > 4) geste.bewegt = true;
        if (!geste.bewegt) return;
        const k = geste.vb.w / b;
        setzen(begrenzen({ ...geste.vb, x: geste.vb.x - dx * k, y: geste.vb.y - dy * k }));
      } else if (zeiger.size === 2) {
        const [p, q] = [...zeiger.values()];
        const abstand = Math.hypot(p.x - q.x, p.y - q.y);
        const mitte = [(p.x + q.x) / 2, (p.y + q.y) / 2];
        const k = geste.vb.w / b;
        const r = svg.getBoundingClientRect();
        // Punkt unter der Startmitte bleibt unter den Fingern
        const ux = geste.vb.x + (geste.mitte[0] - r.left) * k, uy = geste.vb.y + (geste.mitte[1] - r.top) * k;
        const f = geste.abstand / Math.max(abstand, 1);
        const w = geste.vb.w * f, h = geste.vb.h * f;
        setzen(begrenzen({ x: ux - (mitte[0] - r.left) * (w / b), y: uy - (mitte[1] - r.top) * (w / b), w, h }));
      }
    });
    const ende = (e) => {
      zeiger.delete(e.pointerId);
      if (zeiger.size === 0) {
        // Ein echter Zug ist kein Klick
        if (geste?.art === "eins" && geste.bewegt) svg.addEventListener("click", (k) => k.stopPropagation(), { capture: true, once: true });
        geste = null;
      }
    };
    svg.addEventListener("pointerup", ende);
    svg.addEventListener("pointercancel", ende);
    svg.addEventListener("dblclick", (e) => { if (ziehenErlaubt(e)) animieren(ganz()); });
    new ResizeObserver(() => setzen(begrenzen(vb))).observe(svg);

    return {
      punkt,
      zieht: () => !!geste && (geste.art === "zwei" || geste.bewegt),
      einpassen: (weich = true) => (weich ? animieren(ganz()) : setzen(ganz())),
      zeigen: (rahmen, rand = 0.25) => animieren(begrenzen(passend(rahmen, rand))),
      massstab: () => vb.w / groesse().b,      // Planeinheiten je Bildschirmpixel (Strichstärken, Griffe)
      zoomen: (f) => zoomen(f, [vb.x + vb.w / 2, vb.y + vb.h / 2]),
    };
  }

  // ---------- Verlauf: Rückgängig / Wiederholen über Schnappschüsse (SPEC 4.6: mindestens 50 Schritte) ----------
  function Verlauf(holen, setzen, { tiefe = 100, nachAenderung = () => {} } = {}) {
    let zurueck = [], vor = [], gespeichert = JSON.stringify(holen());
    const melden = () => nachAenderung();
    return {
      // vor jeder Änderung aufrufen
      merken() { zurueck.push(JSON.stringify(holen())); if (zurueck.length > tiefe) zurueck.shift(); vor = []; },
      rueckgaengig() {
        if (!zurueck.length) return;
        vor.push(JSON.stringify(holen()));
        setzen(JSON.parse(zurueck.pop()));
        melden();
      },
      wiederholen() {
        if (!vor.length) return;
        zurueck.push(JSON.stringify(holen()));
        setzen(JSON.parse(vor.pop()));
        melden();
      },
      kannZurueck: () => zurueck.length > 0,
      kannVor: () => vor.length > 0,
      geaendert: () => JSON.stringify(holen()) !== gespeichert,
      anzahl: () => (JSON.stringify(holen()) === gespeichert ? 0 : zurueck.length),
      gespeichert() { gespeichert = JSON.stringify(holen()); zurueck = []; vor = []; melden(); },
    };
  }

  // Tastenkürzel des Verlaufs (Strg+Z, Strg+Umschalt+Z / Strg+Y), nicht in Eingabefeldern
  function verlaufTasten(verlauf, aktiv = () => true) {
    document.addEventListener("keydown", (e) => {
      if (!aktiv() || !(e.ctrlKey || e.metaKey) || e.target.closest("input, textarea, select")) return;
      const k = e.key.toLowerCase();
      if (k === "z" && !e.shiftKey) { e.preventDefault(); verlauf.rueckgaengig(); }
      else if ((k === "z" && e.shiftKey) || k === "y") { e.preventDefault(); verlauf.wiederholen(); }
    });
  }

  // ---------- Formen zeichnen und bearbeiten ----------
  // Werkzeug „zeichnen“: ziehen = Rechteck, tippen = Polygon Punkt für Punkt (schließen: erster Punkt, Doppelklick, Enter).
  // Werkzeug „auswahl“: Form antippen = wählen und verschieben, Griff ziehen = Ecke verschieben.
  // Die Formen zeichnet der Aufrufer mit data-form="schluessel"; Griffe und Vorschau zeichnet dieser Baustein in `ebene`.
  function FormenEditor({ svg, ansicht, ebene, werkzeug, form, auswahl, waehlen, aendern, merken, neu }) {
    let zug = null;          // laufendes Ziehen
    let polygon = null;      // Punkte des Polygons im Entstehen
    let zeigerPunkt = null;
    let leertaste = false;

    const NS = "http://www.w3.org/2000/svg";
    const el = (name, attr) => {
      const n = document.createElementNS(NS, name);
      for (const [k, v] of Object.entries(attr)) n.setAttribute(k, v);
      return n;
    };

    function zeichnen() {
      ebene.replaceChildren();
      const m = ansicht.massstab();
      if (polygon) {
        const pts = zeigerPunkt ? [...polygon, zeigerPunkt] : polygon;
        ebene.append(el("polyline", { points: pts.map((p) => p.join(",")).join(" "), class: "zeichnen-vorschau", "stroke-width": 2 * m }));
        polygon.forEach((p, i) => ebene.append(el("circle", { cx: p[0], cy: p[1], r: (i === 0 ? 7 : 4) * m, class: "zeichnen-punkt" })));
      }
      if (zug?.art === "rechteck" && zug.bewegt) {
        ebene.append(el("path", { d: geo.pfad(geo.rechteck(zug.start, zug.jetzt)), class: "zeichnen-vorschau", "stroke-width": 2 * m }));
      }
      const s = auswahl();
      const f = s && form(s);
      if (f && werkzeug() === "auswahl") {
        f.punkte.forEach((p, i) => ebene.append(el("circle", { cx: p[0], cy: p[1], r: 6 * m, class: "griff", "data-griff": i, "stroke-width": 2 * m })));
      }
    }

    function polygonSchliessen() {
      if (polygon && polygon.length >= 3) neu(geo.runden(polygon));
      polygon = null;
      zeichnen();
    }

    svg.addEventListener("pointerdown", (e) => {
      if (e.button !== 0 || leertaste || ansicht.zieht()) return;
      const w = werkzeug();
      if (!w) return;
      const p = ansicht.punkt(e);
      if (w === "zeichnen") {
        if (polygon) {
          // Klick nahe am ersten Punkt schließt
          const nah = Math.hypot(p[0] - polygon[0][0], p[1] - polygon[0][1]) < 10 * ansicht.massstab();
          if (nah) polygonSchliessen(); else { polygon.push(p); zeichnen(); }
          return;
        }
        zug = { art: "rechteck", start: p, jetzt: p, bewegt: false, x: e.clientX, y: e.clientY };
        svg.setPointerCapture(e.pointerId);
        return;
      }
      const griff = e.target.closest("[data-griff]");
      if (griff && auswahl()) {
        merken();
        zug = { art: "griff", i: Number(griff.dataset.griff), schluessel: auswahl() };
        svg.setPointerCapture(e.pointerId);
        return;
      }
      const ziel = e.target.closest("[data-form]");
      if (ziel) {
        waehlen(ziel.dataset.form);
        zug = { art: "form", schluessel: ziel.dataset.form, start: p, punkte: form(ziel.dataset.form).punkte, bewegt: false };
        svg.setPointerCapture(e.pointerId);
      } else {
        waehlen(null);
      }
      zeichnen();
    });

    svg.addEventListener("pointermove", (e) => {
      if (ansicht.zieht()) { zug = null; return; }
      const p = ansicht.punkt(e);
      if (polygon) { zeigerPunkt = p; zeichnen(); }
      if (!zug) return;
      if (zug.art === "rechteck") {
        zug.jetzt = p;
        if (Math.hypot(e.clientX - zug.x, e.clientY - zug.y) > 5) zug.bewegt = true;
        zeichnen();
      } else if (zug.art === "griff") {
        const f = form(zug.schluessel);
        const punkte = f.punkte.map((q, i) => (i === zug.i ? p : q));
        aendern(zug.schluessel, punkte);
        zeichnen();
      } else if (zug.art === "form") {
        const dx = p[0] - zug.start[0], dy = p[1] - zug.start[1];
        if (!zug.bewegt && Math.hypot(dx, dy) < 4 * ansicht.massstab()) return;
        if (!zug.bewegt) { merken(); zug.bewegt = true; }
        aendern(zug.schluessel, zug.punkte.map(([x, y]) => [x + dx, y + dy]));
        zeichnen();
      }
    });

    svg.addEventListener("pointerup", () => {
      if (!zug) return;
      const z = zug;
      zug = null;
      if (z.art === "rechteck") {
        if (z.bewegt) {
          const r = geo.rechteck(z.start, z.jetzt);
          if (geo.rahmen(r).w > 0 && geo.rahmen(r).h > 0) neu(geo.runden(r));
        } else {
          polygon = [z.start];       // Tippen ohne Ziehen beginnt ein Polygon
        }
      } else if (z.art !== "form" || z.bewegt) {
        const f = form(z.schluessel);
        if (f) aendern(z.schluessel, geo.runden(f.punkte), true);
      }
      zeichnen();
    });

    svg.addEventListener("dblclick", (e) => {
      if (!polygon) return;
      e.preventDefault();
      // Doppelklick hat schon zwei Punkte gesetzt: den letzten doppelten entfernen
      polygon.pop();
      polygonSchliessen();
    });

    document.addEventListener("keydown", (e) => {
      if (e.target.closest("input, textarea, select")) return;
      if (e.key === " ") { leertaste = true; svg.classList.add("greifen"); if (werkzeug()) e.preventDefault(); }
      if (!polygon) return;
      if (e.key === "Enter") polygonSchliessen();
      if (e.key === "Escape") { polygon = null; zeichnen(); }
      if (e.key === "Backspace") { e.preventDefault(); polygon.pop(); if (!polygon.length) polygon = null; zeichnen(); }
    });
    document.addEventListener("keyup", (e) => { if (e.key === " ") { leertaste = false; svg.classList.remove("greifen"); } });

    return {
      zeichnen,
      abbrechen() { polygon = null; zug = null; zeichnen(); },
      zeichnetGerade: () => !!polygon,
      leertaste: () => leertaste,
    };
  }

  MF.geo = geo;
  MF.FormenEditor = FormenEditor;
  MF.Ansicht = Ansicht;
  MF.Verlauf = Verlauf;
  MF.verlaufTasten = verlaufTasten;
})();
