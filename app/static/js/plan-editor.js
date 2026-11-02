// Büroplan bearbeiten (SPEC 6.4, 4.6, 4.8): Räume und Einheiten zeichnen, Unterlage ausrichten. Nur Desktop.
// Alles bleibt im Entwurf, bis „Speichern“; vorher zeigt die Leiste, was es an Produkten und Etiketten ändert.
(function () {
  const { $, $$, esc, icon, t, api, toast, geo } = MF;
  const svg = $("[data-plan-svg]");
  if (!svg) return;
  const NS = "http://www.w3.org/2000/svg";

  let entwurf = null;            // {version, unterlage, unterlage_im_buero, raeume[], einheiten[]}
  let geladen = null;            // letzter Stand vom Server (Fotos, Fächerzahlen)
  let werkzeugName = "auswahl";  // auswahl · raum · einheit · unterlage
  let gewaehlt = null;           // Schlüssel der gewählten Form
  let zaehler = 0;               // für Schlüssel neuer Formen
  let bestaetigen = null;        // Wirkung, die vor dem Speichern bestätigt werden muss
  let speichert = false;

  const formen = $("[data-plan-formen]", svg);
  const ebene = $("[data-plan-ebene]", svg);

  // ---------- Modell ----------
  const raum = (s) => entwurf.raeume.find((r) => r.schluessel === s);
  const einheit = (s) => entwurf.einheiten.find((e) => e.schluessel === s);
  const form = (s) => raum(s) || einheit(s);
  const raumNr = (s) => raum(s)?.nr;
  const code = (e) => `${e.raum ? raumNr(e.raum) : "–"}.${e.nr}`;
  const serverEinheit = (e) => geladen.einheiten.find((x) => x.id === e.id);

  function ausServer(p) {
    geladen = p;
    entwurf = {
      version: p.version, unterlage: p.unterlage, unterlage_im_buero: p.unterlage_im_buero,
      raeume: p.raeume.map((r) => ({ id: r.id, schluessel: "r" + r.id, nr: r.nr, name: r.name, punkte: r.punkte })),
      einheiten: p.einheiten.map((e) => ({ id: e.id, schluessel: "e" + e.id, raum: e.raum_id ? "r" + e.raum_id : null,
                                            nr: e.nr, name: e.name, punkte: e.punkte })),
    };
  }

  // Raum einer Einheit = Raum, in dem ihr Mittelpunkt liegt; bei Wechsel nächste freie Nummer dort (SPEC 6.4)
  function raumZuordnen(e) {
    const m = geo.mitte(e.punkte);
    const r = entwurf.raeume.find((x) => geo.innen(m, x.punkte));
    const neu = r ? r.schluessel : null;
    if (neu === e.raum) return;
    e.raum = neu;
    e.nr = naechsteNr(neu, e);
  }
  function naechsteNr(raumSchluessel, ausser) {
    const belegt = entwurf.einheiten.filter((x) => x !== ausser && x.raum === raumSchluessel).map((x) => x.nr);
    return belegt.length ? Math.max(...belegt) + 1 : 1;
  }
  const alleZuordnen = () => entwurf.einheiten.forEach(raumZuordnen);

  const verlauf = MF.Verlauf(() => entwurf, (s) => { entwurf = s; if (gewaehlt && !form(gewaehlt)) gewaehlt = null; alles(); },
                             { nachAenderung: leiste });

  // ---------- Ansicht und Zeichnen ----------
  function unterlageRahmen(u = entwurf.unterlage) {
    if (!u) return null;
    const w = u.breite * u.massstab, h = u.hoehe * u.massstab;
    const quer = u.drehung === 90 || u.drehung === 270;
    const cx = u.x + w / 2, cy = u.y + h / 2;
    const [vw, vh] = quer ? [h, w] : [w, h];
    return { x: cx - vw / 2, y: cy - vh / 2, w: vw, h: vh };
  }
  const grenzen = () => geo.vereinen([unterlageRahmen(), ...entwurf.raeume.map((r) => geo.rahmen(r.punkte)),
                                      ...entwurf.einheiten.map((e) => geo.rahmen(e.punkte))]) || { x: 0, y: 0, w: 1000, h: 700 };

  const ansicht = MF.Ansicht(svg, {
    grenzen,
    ziehenErlaubt: () => editor.leertaste(),
    nachAenderung: () => { if (entwurf) { zeichnen(); editor.zeichnen(); } },
  });

  const editor = MF.FormenEditor({
    svg, ansicht, ebene, form,
    werkzeug: () => (werkzeugName === "unterlage" ? null : werkzeugName === "auswahl" ? "auswahl" : "zeichnen"),
    auswahl: () => gewaehlt,
    waehlen: (s) => { if (s !== gewaehlt) { gewaehlt = s; panel(); zeichnen(); } },
    merken: () => verlauf.merken(),
    aendern(s, punkte, fertig) {
      form(s).punkte = punkte;
      if (fertig) { if (einheit(s)) raumZuordnen(einheit(s)); else alleZuordnen(); panel(); }
      zeichnen();
      leiste();
    },
    neu(punkte) {
      verlauf.merken();
      const s = "n" + ++zaehler;
      if (werkzeugName === "raum") {
        const nr = entwurf.raeume.length ? Math.max(...entwurf.raeume.map((r) => r.nr)) + 1 : 1;
        entwurf.raeume.push({ id: null, schluessel: s, nr, name: "", punkte });
        alleZuordnen();
      } else {
        const e = { id: null, schluessel: s, raum: undefined, nr: 1, name: "", punkte };
        entwurf.einheiten.push(e);
        raumZuordnen(e);
      }
      gewaehlt = s;
      werkzeug("auswahl");
      alles();
      $("[data-feld=name]", $("[data-plan-panel]"))?.focus();
    },
  });

  function el(name, attr, text) {
    const n = document.createElementNS(NS, name);
    for (const [k, v] of Object.entries(attr)) if (v !== undefined && v !== null) n.setAttribute(k, v);
    if (text !== undefined) n.textContent = text;
    return n;
  }

  function zeichnen() {
    const m = ansicht.massstab();
    const teile = [];
    const u = entwurf.unterlage;
    if (u && $("[data-unterlage-zeigen]").getAttribute("aria-pressed") === "true") {
      const w = u.breite * u.massstab, h = u.hoehe * u.massstab;
      teile.push(el("image", { href: `/media/plan/${u.datei}.png`, x: u.x, y: u.y, width: w, height: h, class: "unterlage" + (werkzeugName === "unterlage" ? " aktiv" : ""),
                               transform: `rotate(${u.drehung} ${u.x + w / 2} ${u.y + h / 2})`, preserveAspectRatio: "none", "data-unterlage": "" }));
    }
    for (const r of entwurf.raeume) {
      teile.push(el("path", { d: geo.pfad(r.punkte), class: "raum" + (r.schluessel === gewaehlt ? " gewaehlt" : ""), "data-form": r.schluessel, "stroke-width": 1.5 * m }));
    }
    for (const e of entwurf.einheiten) {
      teile.push(el("path", { d: geo.pfad(e.punkte), class: "einheit" + (e.schluessel === gewaehlt ? " gewaehlt" : "") + (e.raum ? "" : " ohne-raum"),
                              "data-form": e.schluessel, "stroke-width": 1.5 * m }));
    }
    // Beschriftung: Räume oben links, Einheiten in der Mitte; Schriftgröße folgt dem Zoom
    for (const r of entwurf.raeume) {
      const b = geo.rahmen(r.punkte);
      teile.push(el("text", { x: b.x + 8 * m, y: b.y + 18 * m, class: "raum-text", "font-size": 13 * m }, `${r.nr}${r.name ? " · " + r.name : ""}`));
    }
    for (const e of entwurf.einheiten) {
      const [x, y] = geo.mitte(e.punkte);
      teile.push(el("text", { x, y, class: "einheit-text", "font-size": 12 * m, "text-anchor": "middle", "dominant-baseline": "central" }, code(e)));
    }
    if (u && werkzeugName === "unterlage") {
      const r = unterlageRahmen();
      teile.push(el("rect", { x: r.x, y: r.y, width: r.w, height: r.h, class: "unterlage-rahmen", "stroke-width": 1.5 * m }));
      teile.push(el("rect", { x: r.x + r.w - 7 * m, y: r.y + r.h - 7 * m, width: 14 * m, height: 14 * m, class: "griff", "data-skalieren": "", "stroke-width": 2 * m }));
    }
    formen.replaceChildren(...teile);
  }

  function alles() { zeichnen(); editor.zeichnen(); panel(); leiste(); }

  // ---------- Unterlage ausrichten: ziehen verschiebt, Eckgriff skaliert (Seitenverhältnis bleibt) ----------
  let unterlageZug = null;
  svg.addEventListener("pointerdown", (e) => {
    if (werkzeugName !== "unterlage" || e.button !== 0 || editor.leertaste() || !entwurf.unterlage) return;
    const p = ansicht.punkt(e);
    const skalieren = !!e.target.closest("[data-skalieren]");
    if (!skalieren && !e.target.closest("[data-unterlage]")) return;
    verlauf.merken();
    unterlageZug = { skalieren, start: p, u: { ...entwurf.unterlage }, r: unterlageRahmen() };
    svg.setPointerCapture(e.pointerId);
  });
  svg.addEventListener("pointermove", (e) => {
    if (!unterlageZug) return;
    const p = ansicht.punkt(e);
    const { u, r, start } = unterlageZug;
    if (unterlageZug.skalieren) {
      const k = Math.max((p[0] - r.x) / r.w, (p[1] - r.y) / r.h, 0.05);
      const neu = { ...u, massstab: u.massstab * k };
      // linke obere Ecke des sichtbaren Rahmens bleibt stehen
      const w = u.breite * neu.massstab, h = u.hoehe * neu.massstab;
      const quer = u.drehung === 90 || u.drehung === 270;
      const [vw, vh] = quer ? [h, w] : [w, h];
      neu.x = r.x + vw / 2 - w / 2;
      neu.y = r.y + vh / 2 - h / 2;
      entwurf.unterlage = neu;
    } else {
      entwurf.unterlage = { ...u, x: u.x + p[0] - start[0], y: u.y + p[1] - start[1] };
    }
    zeichnen();
    leiste();
  });
  svg.addEventListener("pointerup", () => { unterlageZug = null; });

  // ---------- Werkzeuge ----------
  function werkzeug(name) {
    werkzeugName = name;
    editor.abbrechen();
    $$("[data-werkzeug]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.werkzeug === name)));
    svg.dataset.werkzeug = name;
    $("[data-plan-hinweis]").textContent = name === "raum" || name === "einheit" ? t("plan.hinweis_zeichnen")
      : name === "unterlage" ? t("plan.hinweis_unterlage") : "";
    $("[data-unterlage-knoepfe]").hidden = name !== "unterlage";
    zeichnen();
    editor.zeichnen();
  }

  document.addEventListener("click", async (e) => {
    const b = e.target.closest("button");
    if (!b || !b.closest("[data-plan]")) return;
    const d = b.dataset;
    if (d.werkzeug) return werkzeug(d.werkzeug);
    if (d.unterlageZeigen !== undefined) {
      b.setAttribute("aria-pressed", String(b.getAttribute("aria-pressed") !== "true"));
      return zeichnen();
    }
    if (d.aktion === "drehen" && entwurf.unterlage) {
      verlauf.merken();
      entwurf.unterlage = { ...entwurf.unterlage, drehung: (entwurf.unterlage.drehung + 90) % 360 };
      return alles();
    }
    if (d.aktion === "unterlage-weg" && entwurf.unterlage) {
      verlauf.merken();
      entwurf.unterlage = null;
      werkzeug("auswahl");
      return alles();
    }
    if (d.aktion === "einpassen") return ansicht.einpassen();
    if (d.aktion === "rueckgaengig") return verlauf.rueckgaengig();
    if (d.aktion === "wiederholen") return verlauf.wiederholen();
    if (d.aktion === "verwerfen") return verwerfen();
    if (d.aktion === "speichern") return speichern();
    if (d.aktion === "loeschen") return loeschen();
    if (d.aktion === "faecher") return faecherOeffnen();
  });

  document.addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea, select") || !gewaehlt || editor.zeichnetGerade()) return;
    if (e.key === "Delete" || e.key === "Backspace") { e.preventDefault(); loeschen(); }
  });
  MF.verlaufTasten(verlauf);

  function loeschen() {
    if (!gewaehlt) return;
    verlauf.merken();
    entwurf.raeume = entwurf.raeume.filter((r) => r.schluessel !== gewaehlt);
    entwurf.einheiten = entwurf.einheiten.filter((x) => x.schluessel !== gewaehlt);
    entwurf.einheiten.forEach((x) => { if (x.raum === gewaehlt) x.raum = undefined; });
    alleZuordnen();
    gewaehlt = null;
    alles();
  }

  // ---------- Panel der Auswahl ----------
  function panel() {
    const p = $("[data-plan-panel]");
    const r = gewaehlt && raum(gewaehlt), e = gewaehlt && einheit(gewaehlt);
    if (!r && !e) {
      const fae = geladen.einheiten.reduce((s, x) => s + x.faecher.length, 0);
      p.innerHTML = `<div class="stack">
        <div class="plan-zahlen">
          <div><span class="num">${entwurf.raeume.length}</span><span class="sub">${esc(t("plan.raeume"))}</span></div>
          <div><span class="num">${entwurf.einheiten.length}</span><span class="sub">${esc(t("plan.einheiten"))}</span></div>
          <div><span class="num">${fae}</span><span class="sub">${esc(t("plan.faecher"))}</span></div>
        </div>
        ${entwurf.einheiten.length || entwurf.raeume.length ? "" : `<p class="sub">${esc(t("plan.leer"))}</p>`}
        <label class="schalter"><input type="checkbox" data-feld="im_buero" ${entwurf.unterlage_im_buero ? "checked" : ""} ${entwurf.unterlage ? "" : "disabled"}>
          <span>${esc(t("plan.unterlage_im_buero"))}</span></label>
      </div>`;
      return;
    }
    if (r) {
      p.innerHTML = `<div class="stack">
        <h2 class="abschnitt">${esc(t("plan.raum"))}</h2>
        <div class="feld-reihe eng">
          <label class="feld"><span>${esc(t("plan.nr"))}</span><input class="eingabe num" data-feld="nr" inputmode="numeric" value="${r.nr}"></label>
          <label class="feld"><span>${esc(t("plan.name"))}</span><input class="eingabe" data-feld="name" maxlength="60" value="${esc(r.name)}"></label>
        </div>
        <button class="linkbtn" type="button" data-aktion="loeschen">${esc(t("plan.raum_loeschen"))}</button>
      </div>`;
      return;
    }
    const s = e.id && serverEinheit(e);
    const n = s ? s.faecher.length : 0;
    p.innerHTML = `<div class="stack">
      <h2 class="abschnitt">${esc(t("plan.einheit"))} <span class="num">${esc(code(e))}</span></h2>
      ${e.raum ? `<div class="sub">${esc(t("plan.im_raum", { name: raum(e.raum).name || raum(e.raum).nr }))}</div>`
               : `<div class="hinweis">${esc(t("plan.ohne_raum"))}</div>`}
      <div class="feld-reihe eng">
        <label class="feld"><span>${esc(t("plan.nr"))}</span><input class="eingabe num" data-feld="nr" inputmode="numeric" value="${e.nr}"></label>
        <label class="feld"><span>${esc(t("plan.name"))}</span><input class="eingabe" data-feld="name" maxlength="60" value="${esc(e.name)}" placeholder="${esc(t("plan.einheit_name_bsp"))}"></label>
      </div>
      ${e.id ? `<div class="plan-foto">${s?.foto ? `<img src="/media/einheiten/${esc(s.foto)}-960.webp" alt="">` : `<span class="leer-bild">${icon("image", 28)}</span>`}</div>
        <label class="btn">${icon("camera", 20)}<span>${esc(t(s?.foto ? "plan.foto_ersetzen" : "plan.foto_waehlen"))}</span>
          <input class="sr-only" type="file" accept="image/*" data-einheit-foto></label>
        <button class="btn" type="button" data-aktion="faecher" ${s?.foto ? "" : "disabled"}>${esc(t("plan.faecher_bearbeiten", { n }))}</button>`
             : `<p class="sub">${esc(t("plan.erst_speichern"))}</p>`}
      <button class="linkbtn" type="button" data-aktion="loeschen">${esc(t("plan.einheit_loeschen"))}</button>
    </div>`;
  }

  // Eingaben im Panel: ein Schritt im Verlauf je Feld-Fokus, nicht je Tastendruck
  let feldGemerkt = null;
  const panelEl = $("[data-plan-panel]");
  panelEl.addEventListener("focusin", (e) => { if (e.target.dataset.feld) feldGemerkt = null; });
  panelEl.addEventListener("input", (e) => {
    const feld = e.target.dataset.feld;
    if (!feld || feld === "im_buero") return;
    const f = form(gewaehlt);
    if (!f) return;
    if (feldGemerkt !== e.target) { verlauf.merken(); feldGemerkt = e.target; }
    if (feld === "nr") {
      const nr = parseInt(e.target.value, 10);
      if (nr >= 1 && nr <= 999) f.nr = nr;
    } else f.name = e.target.value;
    zeichnen();
    leiste();
  });
  panelEl.addEventListener("change", async (e) => {
    if (e.target.dataset.feld === "im_buero") {
      verlauf.merken();
      entwurf.unterlage_im_buero = e.target.checked;
      return leiste();
    }
    if (e.target.matches("[data-einheit-foto]")) {
      const datei = e.target.files[0];
      if (!datei) return;
      const e2 = einheit(gewaehlt);
      try {
        const r = await hochladen(`/api/einheiten/${e2.id}/foto`, "foto", datei);
        Object.assign(serverEinheit(e2), r);
        panel();
      } catch (err) { toast(err.message, { fehler: true }); }
    }
  });

  async function hochladen(url, feld, datei) {
    const fd = new FormData();
    fd.append(feld, datei);
    const res = await fetch(url, { method: "POST", body: fd, credentials: "same-origin" });
    const d = await res.json().catch(() => ({}));
    if (!res.ok) throw new MF.ApiError(d.fehler?.text || t("allg.fehler"), null, res.status);
    return d;
  }

  $("[data-unterlage-datei]").addEventListener("change", async (e) => {
    const datei = e.target.files[0];
    e.target.value = "";
    if (!datei) return;
    toast(t("plan.unterlage_laedt"));
    try {
      const r = await hochladen("/api/plan/unterlage", "datei", datei);
      verlauf.merken();
      // Erste Unterlage: so groß wie die vorhandene Zeichnung, sonst 1000 Einheiten breit
      const g = entwurf.raeume.length || entwurf.einheiten.length ? grenzen() : null;
      const alt = entwurf.unterlage;
      const massstab = alt ? (alt.breite * alt.massstab) / r.breite : (g ? g.w : 1000) / r.breite;
      entwurf.unterlage = { ...r, x: alt?.x ?? g?.x ?? 0, y: alt?.y ?? g?.y ?? 0, massstab, drehung: alt?.drehung ?? 0 };
      $("[data-unterlage-zeigen]").setAttribute("aria-pressed", "true");
      werkzeug("unterlage");
      alles();
      ansicht.einpassen();
    } catch (err) { toast(err.message, { fehler: true }); }
  });

  // ---------- Leiste: Rückgängig · Wiederholen · n Änderungen · Verwerfen · Speichern (SPEC 4.6) ----------
  function leiste() {
    if (!entwurf) return;
    const n = verlauf.geaendert() ? Math.max(verlauf.anzahl(), 1) : 0;
    $("[data-aktion=rueckgaengig]").disabled = !verlauf.kannZurueck();
    $("[data-aktion=wiederholen]").disabled = !verlauf.kannVor();
    $("[data-plan-anzahl]").textContent = n ? t("plan.aenderungen", { n }) : "";
    $("[data-aktion=verwerfen]").disabled = !n;
    $("[data-aktion=speichern]").disabled = !n || speichert;
    if (bestaetigen && JSON.stringify(entwurfFuerServer()) !== bestaetigen.stand) bestaetigen = null;
    $("[data-plan-wirkung]").innerHTML = bestaetigen ? bestaetigen.texte.map((x) => `<div class="hinweis">${esc(x)}</div>`).join("") : "";
    $("[data-aktion=speichern]").textContent = t(bestaetigen ? "plan.trotzdem_speichern" : "plan.speichern");
  }

  const entwurfFuerServer = () => ({
    ...entwurf,
    raeume: entwurf.raeume.map(({ id, schluessel, nr, name, punkte }) => ({ id, schluessel, nr, name, punkte })),
    einheiten: entwurf.einheiten.map(({ id, raum: r, nr, name, punkte }) => ({ id, raum: r || null, nr, name, punkte })),
  });

  async function speichern() {
    if (speichert) return;
    speichert = true;
    leiste();
    try {
      const daten = entwurfFuerServer();
      const stand = JSON.stringify(daten);
      if (!bestaetigen || bestaetigen.stand !== stand) {
        const w = await api("POST", "/api/plan/wirkung", daten);
        const texte = [];
        if (w.einheiten_weg) texte.push(t("plan.wirkung_einheiten", { n: w.einheiten_weg, f: w.faecher_weg }));
        if (w.ohne_platz) texte.push(t("plan.wirkung_ohne_platz", { n: w.ohne_platz }));
        if (w.etiketten_neu) texte.push(t("plan.wirkung_etiketten", { n: w.etiketten_neu }));
        if (texte.length) { bestaetigen = { stand, texte }; return; }
      }
      const r = await api("PUT", "/api/plan", daten);
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
    ausServer(geladen);
    gewaehlt = null;
    bestaetigen = null;
    verlauf.gespeichert();
    alles();
  }

  function faecherOeffnen() {
    const e = einheit(gewaehlt);
    if (verlauf.geaendert()) { toast(t("plan.erst_speichern"), { fehler: true }); return; }
    location.href = `/plan/einheit/${e.id}`;
  }

  window.addEventListener("beforeunload", (e) => { if (entwurf && verlauf.geaendert()) e.preventDefault(); });

  // ---------- Start ----------
  (async () => {
    try {
      ausServer(await api("GET", "/api/plan"));
      verlauf.gespeichert();
      // Nach dem Fach-Editor: die Einheit bleibt gewählt
      const wahl = new URLSearchParams(location.search).get("einheit");
      if (wahl && einheit("e" + wahl)) gewaehlt = "e" + wahl;
      werkzeug("auswahl");
      ansicht.einpassen(false);
      alles();
    } catch (err) { toast(err.message, { fehler: true }); }
  })();
})();
