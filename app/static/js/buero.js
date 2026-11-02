// Büro (SPEC 6.5): Plan → Einheit → Fach → Produkte. Telefon und Desktop.
// Zustand in der Adresse (?einheit=…&fach=…&produkt=…), damit Zurück, Neuladen und Links („Im Büro zeigen“) passen.
// Kartenbögen und Fächer-Fächer kommen nach dem „Tekrar bak“ (D-017); bis dahin Liste.
(function () {
  const { $, esc, icon, t, api, toast, geo } = MF;
  const svg = $("[data-buero-svg]");
  if (!svg) return;
  const NS = "http://www.w3.org/2000/svg";
  const panel = $("[data-buero-panel]");

  let plan = null;
  let zustand = { einheit: null, fach: null, produkt: null };
  let fachInhalt = null;         // {code, produkte[]} des gewählten Fachs

  const einheit = (id) => plan.einheiten.find((e) => e.id === id);
  const einheitVonFach = (fid) => plan.einheiten.find((e) => e.faecher.some((f) => f.id === fid));

  function unterlageRahmen(u) {
    const w = u.breite * u.massstab, h = u.hoehe * u.massstab;
    const quer = u.drehung === 90 || u.drehung === 270;
    const [vw, vh] = quer ? [h, w] : [w, h];
    return { x: u.x + w / 2 - vw / 2, y: u.y + h / 2 - vh / 2, w: vw, h: vh };
  }
  const zeigtUnterlage = () => plan.unterlage && plan.unterlage_im_buero;
  const grenzen = () => geo.vereinen([zeigtUnterlage() ? unterlageRahmen(plan.unterlage) : null,
                                      ...plan.raeume.map((r) => geo.rahmen(r.punkte)), ...plan.einheiten.map((e) => geo.rahmen(e.punkte))]);

  const ansicht = MF.Ansicht(svg, { grenzen: () => grenzen() || { x: 0, y: 0, w: 1000, h: 700 }, nachAenderung: () => plan && zeichnen() });

  function el(name, attr, text) {
    const n = document.createElementNS(NS, name);
    for (const [k, v] of Object.entries(attr)) n.setAttribute(k, v);
    if (text !== undefined) n.textContent = text;
    return n;
  }

  function zeichnen() {
    const m = ansicht.massstab();
    const teile = [];
    if (zeigtUnterlage()) {
      const u = plan.unterlage, w = u.breite * u.massstab, h = u.hoehe * u.massstab;
      teile.push(el("image", { href: `/media/plan/${u.datei}.png`, x: u.x, y: u.y, width: w, height: h, class: "unterlage",
                               transform: `rotate(${u.drehung} ${u.x + w / 2} ${u.y + h / 2})`, preserveAspectRatio: "none" }));
    }
    for (const r of plan.raeume) teile.push(el("path", { d: geo.pfad(r.punkte), class: "raum ansicht-raum", "stroke-width": 1.5 * m }));
    for (const e of plan.einheiten) {
      teile.push(el("path", { d: geo.pfad(e.punkte), class: "einheit" + (e.id === zustand.einheit ? " gewaehlt" : ""),
                              "data-einheit": e.id, "stroke-width": (e.id === zustand.einheit ? 2.5 : 1.5) * m }));
    }
    for (const r of plan.raeume) {
      const b = geo.rahmen(r.punkte);
      teile.push(el("text", { x: b.x + 8 * m, y: b.y + 18 * m, class: "raum-text", "font-size": 13 * m }, r.name || String(r.nr)));
    }
    for (const e of plan.einheiten) {
      const [x, y] = geo.mitte(e.punkte);
      teile.push(el("text", { x, y, class: "einheit-text", "font-size": 12 * m, "text-anchor": "middle", "dominant-baseline": "central" }, e.code));
    }
    svg.replaceChildren(...teile);
  }

  // ---------- Panel ----------
  function fotoMitFaechern(e, gewaehltesFach) {
    if (!e.foto) return `<div class="buero-foto leer"><span class="sub">${esc(t("buero.kein_foto"))}</span></div>`;
    const h = (100 * e.foto_hoehe) / e.foto_breite;
    const pfade = e.faecher.map((f) => {
      const d = geo.pfad(f.punkte.map(([x, y]) => [x, (y * h) / 100]));
      return `<path d="${d}" class="fach${f.id === gewaehltesFach ? " gewaehlt" : ""}" data-fach="${f.id}"></path>`;
    }).join("");
    // Spotlicht (SPEC 4.7): außer dem gewählten Fach wird alles abgedunkelt
    const sf = gewaehltesFach && e.faecher.find((f) => f.id === gewaehltesFach);
    const spot = sf ? `<path class="spot" fill-rule="evenodd" d="M0 0H100V${h}H0Z ${geo.pfad(sf.punkte.map(([x, y]) => [x, (y * h) / 100]))}"></path>` : "";
    return `<div class="buero-foto" style="aspect-ratio:${e.foto_breite}/${e.foto_hoehe}">
      <img src="/media/einheiten/${esc(e.foto)}-960.webp" alt="">
      <svg viewBox="0 0 100 ${h}" preserveAspectRatio="none">${pfade}${spot}</svg></div>`;
  }

  function zeichnePanel() {
    const e = zustand.einheit && einheit(zustand.einheit);
    if (!e) {
      const leer = !plan.einheiten.length;
      const gruppen = [...plan.raeume.map((r) => ({ name: r.name || String(r.nr), einheiten: plan.einheiten.filter((e) => e.raum_id === r.id) })),
                       { name: t("plan.ohne_raum"), einheiten: plan.einheiten.filter((e) => !e.raum_id) }].filter((g) => g.einheiten.length);
      panel.innerHTML = `<div class="stack">
        <p class="sub">${esc(t(leer ? "buero.leer" : "buero.waehlen"))}</p>
        ${gruppen.map((g) => `<div class="fachliste"><h2 class="abschnitt">${esc(g.name)}</h2>${g.einheiten.map((e) => `
          <button class="zeile" type="button" data-einheit="${e.id}"><span class="zeile-haupt"><span class="num">${esc(e.code)}</span>
            ${e.name ? `<span class="karte-sub">${esc(e.name)}</span>` : ""}</span><span class="sub">${esc(t("buero.produkte", { n: e.produkte }))}</span>${icon("right", 18)}</button>`).join("")}</div>`).join("")}
        ${plan.ohne_platz ? `<a class="linkbtn" href="/bibliothek?status=ohne_platz">${esc(t("buero.ohne_platz", { n: plan.ohne_platz }))}</a>` : ""}
        <a class="linkbtn nur-desktop" href="/plan">${esc(t("buero.plan_bearbeiten"))}</a>
      </div>`;
      return;
    }
    const kopf = `<div class="buero-kopf"><h2 class="abschnitt"><span class="num">${esc(e.code)}</span>${e.name ? " · " + esc(e.name) : ""}</h2>
      <button class="iconbtn" type="button" data-aktion="schliessen" aria-label="${esc(t("produkt.schliessen"))}">${icon("close")}</button></div>`;
    if (!zustand.fach) {
      panel.innerHTML = `<div class="stack">${kopf}${fotoMitFaechern(e, null)}
        <label class="btn">${icon("camera", 20)}<span>${esc(t(e.foto ? "plan.foto_ersetzen" : "plan.foto_waehlen"))}</span>
          <input class="sr-only" type="file" accept="image/*" data-einheit-foto></label>
        ${e.faecher.length ? `<div class="fachliste">${e.faecher.map((f) => `
          <button class="zeile" type="button" data-fach="${f.id}"><span class="zeile-haupt"><span class="num">${esc(f.code)}</span></span>
            <span class="sub">${esc(t("buero.produkte", { n: f.produkte }))}</span>${icon("right", 18)}</button>`).join("")}</div>`
          : `<p class="sub">${esc(t("buero.faecher_leer"))}</p>`}
      </div>`;
      return;
    }
    const f = e.faecher.find((x) => x.id === zustand.fach);
    const produkte = fachInhalt?.produkte || [];
    panel.innerHTML = `<div class="stack">${kopf}${fotoMitFaechern(e, zustand.fach)}
      <div class="buero-kopf"><button class="linkbtn" type="button" data-aktion="zurueck">${esc(t("buero.zurueck_einheit"))}</button>
        <span class="spacer"></span><span class="num buero-fachcode">${esc(f.code)}</span></div>
      <button class="btn block" type="button" data-aktion="einordnen">${icon("pin", 20)}<span>${esc(t("einordnen.hier"))}</span></button>
      ${produkte.length ? `<div class="fachliste">${produkte.map((p) => `
        <a class="zeile${p.inventar_nr === zustand.produkt ? " gesucht" : ""}" href="/produkt/${p.inventar_nr}">
          ${p.foto ? `<img class="zeile-img" src="/media/fotos/${esc(p.foto)}-320.webp" alt="" loading="lazy">` : `<span class="zeile-img leer-bild">${icon("image", 20)}</span>`}
          <span class="zeile-haupt"><span class="karte-name">${esc(p.name || t("produkt.unbenannt", { nr: p.inventar_nr }))}</span><span class="karte-sub num">${esc(p.code)}</span></span>
          ${icon("right", 18)}</a>`).join("")}</div>`
        : `<p class="sub">${esc(t("buero.fach_leer"))}</p>`}
    </div>`;
  }

  // ---------- Zustand ----------
  async function setzen(neu, { weich = true } = {}) {
    zustand = { ...zustand, ...neu };
    const q = new URLSearchParams();
    if (zustand.einheit) q.set("einheit", zustand.einheit);
    if (zustand.fach) q.set("fach", zustand.fach);
    if (zustand.produkt) q.set("produkt", zustand.produkt);
    history.replaceState(null, "", location.pathname + (q.toString() ? "?" + q : ""));
    fachInhalt = null;
    if (zustand.fach) {
      try { fachInhalt = await api("GET", "/api/faecher/" + zustand.fach); } catch (err) { toast(err.message, { fehler: true }); }
    }
    zeichnen();
    zeichnePanel();
    const e = zustand.einheit && einheit(zustand.einheit);
    if (e) ansicht.zeigen(geo.rahmen(e.punkte), 0.8);
    else if (weich) ansicht.einpassen();
  }

  svg.addEventListener("click", (e) => {
    const z = e.target.closest("[data-einheit]");
    if (z) setzen({ einheit: Number(z.dataset.einheit), fach: null, produkt: null });
  });
  panel.addEventListener("change", async (e) => {
    if (!e.target.matches("[data-einheit-foto]") || !e.target.files[0]) return;
    const fd = new FormData();
    fd.append("foto", e.target.files[0]);
    toast(t("produkt.fotos_laden"));
    try {
      const res = await fetch(`/api/einheiten/${zustand.einheit}/foto`, { method: "POST", body: fd, credentials: "same-origin" });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(d.fehler?.text || t("allg.fehler"));
      Object.assign(einheit(zustand.einheit), d);
      zeichnePanel();
    } catch (err) { toast(err.message, { fehler: true }); }
  });

  panel.addEventListener("click", (e) => {
    const z = e.target.closest("button[data-einheit]");
    if (z) return setzen({ einheit: Number(z.dataset.einheit), fach: null, produkt: null });
    const f = e.target.closest("[data-fach]");
    if (f) return setzen({ fach: Number(f.dataset.fach) });
    const b = e.target.closest("[data-aktion]");
    if (!b) return;
    if (b.dataset.aktion === "schliessen") setzen({ einheit: null, fach: null, produkt: null });
    if (b.dataset.aktion === "zurueck") setzen({ fach: null, produkt: null });
    if (b.dataset.aktion === "einordnen") {
      MF.einordnen.starten({ id: zustand.fach, code: fachInhalt?.code });
      toast(t("einordnen.gestartet", { code: fachInhalt?.code }));
    }
  });

  (async () => {
    try {
      plan = await api("GET", "/api/plan");
      const q = new URLSearchParams(location.search);
      const fach = Number(q.get("fach")) || null;
      const e = fach ? einheitVonFach(fach) : einheit(Number(q.get("einheit")));
      ansicht.einpassen(false);
      await setzen({ einheit: e?.id || null, fach: e && fach ? fach : null, produkt: Number(q.get("produkt")) || null }, { weich: false });
    } catch (err) { toast(err.message, { fehler: true }); }
  })();
})();
