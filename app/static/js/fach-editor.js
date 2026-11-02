// Fächer einer Einheit auf ihrem Foto zeichnen (SPEC 6.4, 4.6). Nur Desktop.
// Zeichenfläche: Fotobreite = 100 Einheiten, Höhe im Seitenverhältnis; gespeichert wird in Prozent (0–100).
(function () {
  const { $, $$, esc, icon, t, api, toast, geo } = MF;
  const svg = $("[data-fach-svg]");
  if (!svg) return;
  const NS = "http://www.w3.org/2000/svg";
  const einheitId = Number(svg.dataset.einheit);

  let plan = null, einheit = null;
  let faecher = [];              // [{id, schluessel, nr, name, punkte}] in Zeichenkoordinaten
  let werkzeugName = "auswahl";
  let gewaehlt = null;
  let zaehler = 0;
  let bestaetigen = null;
  let speichert = false;
  const H = () => (einheit?.foto ? (100 * einheit.foto_hoehe) / einheit.foto_breite : 75);

  const formen = $("[data-fach-formen]", svg);
  const ebene = $("[data-fach-ebene]", svg);
  const fach = (s) => faecher.find((f) => f.schluessel === s);
  const gespeichertesFach = (id) => einheit.faecher.find((f) => f.id === id);

  const zuZeichnung = (punkte) => punkte.map(([x, y]) => [x, (y * H()) / 100]);
  const zuProzent = (punkte) => punkte.map(([x, y]) => [Math.min(Math.max(x, 0), 100), Math.min(Math.max((y * 100) / H(), 0), 100)]);

  function ausServer(p) {
    plan = p;
    einheit = p.einheiten.find((e) => e.id === einheitId);
    if (!einheit) { location.href = "/plan"; return; }
    faecher = einheit.faecher.map((f) => ({ id: f.id, schluessel: "f" + f.id, nr: f.nr, name: f.name, punkte: zuZeichnung(f.punkte) }));
    $("[data-fach-titel]").textContent = t("fach.titel", { code: einheit.code }) + (einheit.name ? " · " + einheit.name : "");
  }

  const verlauf = MF.Verlauf(() => faecher, (s) => { faecher = s; if (gewaehlt && !fach(gewaehlt)) gewaehlt = null; alles(); },
                             { nachAenderung: leiste });
  const ansicht = MF.Ansicht(svg, {
    grenzen: () => ({ x: 0, y: 0, w: 100, h: H() }),
    ziehenErlaubt: () => editor.leertaste(),
    nachAenderung: () => { if (einheit) { zeichnen(); editor.zeichnen(); } },
  });
  const editor = MF.FormenEditor({
    svg, ansicht, ebene, form: fach,
    werkzeug: () => (werkzeugName === "fach" ? "zeichnen" : "auswahl"),
    auswahl: () => gewaehlt,
    waehlen: (s) => { if (s !== gewaehlt) { gewaehlt = s; panel(); zeichnen(); } },
    merken: () => verlauf.merken(),
    aendern(s, punkte) { fach(s).punkte = punkte; zeichnen(); leiste(); },
    neu(punkte) {
      verlauf.merken();
      const s = "n" + ++zaehler;
      faecher.push({ id: null, schluessel: s, nr: faecher.length ? Math.max(...faecher.map((f) => f.nr)) + 1 : 1, name: "", punkte });
      gewaehlt = s;
      werkzeug("auswahl");
      alles();
    },
  });

  function el(name, attr, text) {
    const n = document.createElementNS(NS, name);
    for (const [k, v] of Object.entries(attr)) n.setAttribute(k, v);
    if (text !== undefined) n.textContent = text;
    return n;
  }

  function zeichnen() {
    const m = ansicht.massstab();
    const teile = [];
    if (einheit.foto) teile.push(el("image", { href: `/media/einheiten/${einheit.foto}.jpg`, x: 0, y: 0, width: 100, height: H(), preserveAspectRatio: "none" }));
    else teile.push(el("rect", { x: 0, y: 0, width: 100, height: H(), class: "fach-leer" }));
    for (const f of faecher) {
      teile.push(el("path", { d: geo.pfad(f.punkte), class: "fach" + (f.schluessel === gewaehlt ? " gewaehlt" : ""), "data-form": f.schluessel, "stroke-width": 2 * m }));
    }
    for (const f of faecher) {
      const [x, y] = geo.mitte(f.punkte);
      teile.push(el("text", { x, y, class: "fach-text", "font-size": 14 * m, "text-anchor": "middle", "dominant-baseline": "central", "stroke-width": 3 * m }, `${einheit.code}.${f.nr}`));
    }
    formen.replaceChildren(...teile);
  }
  function alles() { zeichnen(); editor.zeichnen(); panel(); leiste(); }

  function werkzeug(name) {
    werkzeugName = name;
    editor.abbrechen();
    $$("[data-werkzeug]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.werkzeug === name)));
    svg.dataset.werkzeug = name;
    $("[data-fach-hinweis]").textContent = name === "fach" ? t("plan.hinweis_zeichnen") : "";
    editor.zeichnen();
  }

  // Neu nummerieren (SPEC 6.4): von links nach rechts, von oben nach unten; Zeilen über die Höhe der Fächer
  function neuNummerieren() {
    if (!faecher.length) return;
    verlauf.merken();
    const info = faecher.map((f) => ({ f, m: geo.mitte(f.punkte), h: geo.rahmen(f.punkte).h }));
    const toleranz = Math.max(Math.min(...info.map((i) => i.h)) / 2, 0.5);
    info.sort((a, b) => a.m[1] - b.m[1]);
    const zeilen = [];
    for (const i of info) {
      const z = zeilen.find((r) => Math.abs(r[0].m[1] - i.m[1]) < toleranz);
      if (z) z.push(i); else zeilen.push([i]);
    }
    let nr = 1;
    zeilen.forEach((z) => z.sort((a, b) => a.m[0] - b.m[0]).forEach((i) => { i.f.nr = nr++; }));
    alles();
  }

  function loeschen() {
    if (!gewaehlt) return;
    verlauf.merken();
    faecher = faecher.filter((f) => f.schluessel !== gewaehlt);
    gewaehlt = null;
    alles();
  }

  // ---------- Panel ----------
  function panel() {
    const p = $("[data-fach-panel]");
    const f = gewaehlt && fach(gewaehlt);
    const fotoKnopf = `<label class="btn">${icon("camera", 20)}<span>${esc(t(einheit.foto ? "plan.foto_ersetzen" : "plan.foto_waehlen"))}</span>
      <input class="sr-only" type="file" accept="image/*" data-einheit-foto></label>`;
    if (!f) {
      p.innerHTML = `<div class="stack">
        <div class="sub">${esc(t("fach.anzahl", { n: faecher.length }))}</div>
        ${einheit.foto ? "" : `<p class="sub">${esc(t("fach.erst_foto"))}</p>`}
        ${fotoKnopf}
        <button class="btn" type="button" data-aktion="nummerieren" ${faecher.length > 1 ? "" : "disabled"}>${esc(t("fach.nummerieren"))}</button>
      </div>`;
      return;
    }
    const n = f.id ? gespeichertesFach(f.id)?.produkte || 0 : 0;
    p.innerHTML = `<div class="stack">
      <h2 class="abschnitt">${esc(t("fach.fach"))} <span class="num">${esc(einheit.code)}.${f.nr}</span></h2>
      <label class="feld"><span>${esc(t("plan.nr"))}</span><input class="eingabe num" data-feld="nr" inputmode="numeric" value="${f.nr}"></label>
      <label class="feld"><span>${esc(t("plan.name"))}</span><input class="eingabe" data-feld="name" maxlength="60"
        placeholder="${esc(t("fach.name_bsp"))}" value="${esc(f.name)}"></label>
      <div class="sub">${esc(t("fach.produkte", { n }))}</div>
      <button class="linkbtn" type="button" data-aktion="loeschen">${esc(t("fach.loeschen"))}</button>
    </div>`;
  }

  let feldGemerkt = null;
  const panelEl = $("[data-fach-panel]");
  panelEl.addEventListener("input", (e) => {
    if (e.target.dataset.feld === "name") {
      if (feldGemerkt !== e.target) { verlauf.merken(); feldGemerkt = e.target; }
      fach(gewaehlt).name = e.target.value;
      return leiste();
    }
    if (e.target.dataset.feld !== "nr") return;
    const nr = parseInt(e.target.value, 10);
    if (!(nr >= 1 && nr <= 999)) return;
    if (feldGemerkt !== e.target) { verlauf.merken(); feldGemerkt = e.target; }
    fach(gewaehlt).nr = nr;
    zeichnen();
    leiste();
  });
  panelEl.addEventListener("change", async (e) => {
    if (!e.target.matches("[data-einheit-foto]")) return;
    const datei = e.target.files[0];
    if (!datei) return;
    const fd = new FormData();
    fd.append("foto", datei);
    try {
      const res = await fetch(`/api/einheiten/${einheitId}/foto`, { method: "POST", body: fd, credentials: "same-origin" });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(d.fehler?.text || t("allg.fehler"));
      // Fächer bleiben in Prozent: auf das neue Seitenverhältnis umrechnen
      const prozent = faecher.map((f) => zuProzent(f.punkte));
      Object.assign(einheit, d);
      faecher.forEach((f, i) => { f.punkte = zuZeichnung(prozent[i]); });
      ansicht.einpassen(false);
      alles();
    } catch (err) { toast(err.message, { fehler: true }); }
  });

  document.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b || !b.closest("[data-fach]")) return;
    const d = b.dataset;
    if (d.werkzeug) return werkzeug(d.werkzeug);
    if (d.aktion === "nummerieren") return neuNummerieren();
    if (d.aktion === "loeschen") return loeschen();
    if (d.aktion === "einpassen") return ansicht.einpassen();
    if (d.aktion === "rueckgaengig") return verlauf.rueckgaengig();
    if (d.aktion === "wiederholen") return verlauf.wiederholen();
    if (d.aktion === "verwerfen") return verwerfen();
    if (d.aktion === "speichern") return speichern();
  });
  document.addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea, select") || !gewaehlt || editor.zeichnetGerade()) return;
    if (e.key === "Delete" || e.key === "Backspace") { e.preventDefault(); loeschen(); }
  });
  MF.verlaufTasten(verlauf);

  // ---------- Leiste und Speichern ----------
  // wie der Server: Leerraum zusammengezogen
  const namen = (s) => s.split(/\s+/).filter(Boolean).join(" ");
  const fuerServer = () => faecher.map((f) => ({ id: f.id, nr: f.nr, name: namen(f.name), punkte: geo.runden(zuProzent(f.punkte)) }));

  // Wirkung vor dem Speichern (SPEC 4.6): aus dem geladenen Stand berechenbar
  function wirkung() {
    const bleiben = new Set(faecher.map((f) => f.id).filter(Boolean));
    const weg = einheit.faecher.filter((f) => !bleiben.has(f.id));
    const neuDruck = faecher.filter((f) => {
      const alt = f.id && gespeichertesFach(f.id);
      return alt && alt.etikett === "gedruckt" && (alt.nr !== f.nr || alt.name !== namen(f.name));
    });
    const texte = [];
    const ohne = weg.reduce((s, f) => s + f.produkte, 0);
    if (ohne) texte.push(t("plan.wirkung_ohne_platz", { n: ohne }));
    if (neuDruck.length) texte.push(t("plan.wirkung_etiketten", { n: neuDruck.length }));
    const doppelt = new Set(faecher.map((f) => f.nr)).size !== faecher.length;
    return { texte, doppelt };
  }

  function leiste() {
    if (!einheit) return;
    const n = verlauf.geaendert() ? Math.max(verlauf.anzahl(), 1) : 0;
    $("[data-aktion=rueckgaengig]").disabled = !verlauf.kannZurueck();
    $("[data-aktion=wiederholen]").disabled = !verlauf.kannVor();
    $("[data-fach-anzahl]").textContent = n ? t("plan.aenderungen", { n }) : "";
    $("[data-aktion=verwerfen]").disabled = !n;
    const w = wirkung();
    $("[data-aktion=speichern]").disabled = !n || speichert || w.doppelt;
    if (bestaetigen && bestaetigen !== JSON.stringify(fuerServer())) bestaetigen = null;
    const hinweise = w.doppelt ? [t("fehler.fach_nr_doppelt")] : bestaetigen ? w.texte : [];
    $("[data-fach-wirkung]").innerHTML = hinweise.map((x) => `<div class="hinweis">${esc(x)}</div>`).join("");
    $("[data-aktion=speichern]").textContent = t(bestaetigen ? "plan.trotzdem_speichern" : "plan.speichern");
  }

  async function speichern() {
    const daten = fuerServer();
    const stand = JSON.stringify(daten);
    if (!bestaetigen && wirkung().texte.length) { bestaetigen = stand; return leiste(); }
    speichert = true;
    leiste();
    try {
      const r = await api("PUT", `/api/einheiten/${einheitId}/faecher`, { version: plan.version, faecher: daten });
      bestaetigen = null;
      ausServer(r.plan);
      gewaehlt = null;
      verlauf.gespeichert();
      toast(t("plan.gespeichert"));
      alles();
    } catch (err) {
      toast(err.message, { fehler: true });
    } finally {
      speichert = false;
      leiste();
    }
  }

  function verwerfen() {
    if (verlauf.geaendert() && !window.confirm(t("plan.verwerfen_frage", { n: Math.max(verlauf.anzahl(), 1) }))) return;
    ausServer(plan);
    gewaehlt = null;
    bestaetigen = null;
    verlauf.gespeichert();
    alles();
  }

  window.addEventListener("beforeunload", (e) => { if (einheit && verlauf.geaendert()) e.preventDefault(); });

  (async () => {
    try {
      ausServer(await api("GET", "/api/plan"));
      verlauf.gespeichert();
      werkzeug(einheit.foto ? "auswahl" : "auswahl");
      ansicht.einpassen(false);
      alles();
    } catch (err) { toast(err.message, { fehler: true }); }
  })();
})();
