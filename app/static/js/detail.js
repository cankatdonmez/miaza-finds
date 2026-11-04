// Produktdetail (SPEC 6.1): gleicher Inhalt im Seitenpanel (Desktop) und als ganze Seite (Telefon).
// MF.detailHtml(produkt, {kopf}) → HTML; kopf=true zeigt Titel und Knöpfe (im Panel; auf der Seite stehen sie im Seitenkopf).
(function () {
  const { esc, icon, t, datum, euro } = MF;

  function preisText(p) {
    if (!p) return "";
    return `${euro(p.cent)} € ${t("einheit." + p.einheit)}`;
  }

  function zeile(name, wert) {
    return wert ? `<div class="merkmal"><dt>${esc(name)}</dt><dd>${wert}</dd></div>` : "";
  }

  MF.detailHtml = function (p, { kopf = false } = {}) {
    const name = p.name || t("produkt.unbenannt", { nr: p.inventar_nr });
    const fotos = p.fotos || [];
    const bild = fotos.length
      ? `<button class="detail-bild-knopf" type="button" data-bild-voll="${esc(fotos[0].datei)}" aria-label="${esc(t("produkt.bild_voll"))}">
          <img class="detail-bild" src="/media/fotos/${esc(fotos[0].datei)}-960.webp" alt="" data-detail-bild></button>`
      : `<div class="detail-bild leer-bild">${icon("image", 40)}</div>`;
    const kleine = fotos.length > 1 ? `<div class="detail-fotos">${fotos.map((f, i) => `
      <button class="detail-foto" type="button" data-foto-gross="${esc(f.datei)}" aria-pressed="${i === 0}">
        <img src="/media/fotos/${esc(f.datei)}-320.webp" alt=""></button>`).join("")}</div>` : "";
    const farben = (p.farben || []).map((f) => `<span class="farbknopf statisch"><span class="farbpunkt farbe-${f}"></span>${esc(t("farbe." + f))}</span>`).join("");
    const preis = p.preis ? `${esc(preisText(p.preis))} <span class="sub">· ${esc(t("produkt.preis_stand", { datum: datum(p.preis.datum) }))}</span>` : "";
    return `
      ${kopf ? `<div class="panel-kopf">
        <button class="iconbtn" type="button" data-panel-zu aria-label="${esc(t("produkt.schliessen"))}">${icon("close")}</button>
        <span class="spacer"></span>
        <a class="btn" href="/produkt/${p.inventar_nr}/bearbeiten">${esc(t("produkt.bearbeiten"))}</a>
      </div>` : ""}
      ${einordnenKnopf(p)}
      <div class="detail-bildrahmen">${bild}</div>
      ${kleine}
      <div class="detail-titel">
        ${kopf ? `<h2 class="detail-name">${esc(name)}</h2>` : ""}
        <div class="detail-zeile"><span class="num">${esc(p.code)}</span>${p.art === "digital" ? `<span class="badge-digital">${esc(t("produkt.digital"))}</span>` : ""}</div>
      </div>
      ${MF.entnahmeZeile(p)}
      <dl class="merkmale">
        ${p.art === "physisch" ? zeile(t("produkt.platz"), p.platz ? platzText(p.platz) : `<span class="sub">${esc(t("status.ohne_platz"))}</span>`) : ""}
        ${zeile(t("produkt.kategorie"), esc(p.kategorie_name))}
        ${zeile(t("produkt.marke"), esc(p.marke))}
        ${zeile(t("produkt.artikelnummer"), p.artikelnummer ? `<span class="num">${esc(p.artikelnummer)}</span>` : "")}
        ${zeile(t("produkt.abmessungen"), esc(p.abmessungen))}
        ${zeile(t("produkt.preis"), preis)}
        ${(p.merkmale || []).map((m) => zeile(m.name, esc(m.wert))).join("")}
        ${zeile(t("produkt.anzahl"), p.anzahl != null ? esc(t("produkt.anzahl_wert", { n: p.anzahl })) : "")}
      </dl>
      ${farben ? `<div class="farben">${farben}</div>` : ""}
      ${p.notiz ? `<p class="detail-notiz">${esc(p.notiz)}</p>` : ""}
      <section class="sammlungen-feld" data-sammlungen-fuer="${p.inventar_nr}"></section>
      <div class="actions">
        ${p.link ? `<a class="btn" href="${esc(p.link)}" target="_blank" rel="noopener noreferrer">${esc(t("produkt.link_oeffnen"))}</a>` : ""}
        ${p.platz ? `<a class="btn" href="/buero?fach=${p.platz.id}&produkt=${p.inventar_nr}">${icon("buero", 20)}<span>${esc(t("produkt.im_buero_zeigen"))}</span></a>` : ""}
        ${p.art === "physisch" ? `<a class="btn" href="/buero?platzieren=${p.inventar_nr}${p.platz ? "&fach=" + p.platz.id : ""}">${icon("pin", 20)}
          <span>${esc(t(p.platz ? "platz.aendern" : "platz.waehlen"))}</span></a>` : ""}
        ${p.art === "physisch" ? druckliste(p) : ""}
      </div>`;
  };

  // Code, dann Name des Fachs, sonst der Einheit (D-020)
  const platzText = (f) => `<span class="num">${esc(f.code)}</span>${f.name || f.einheit_name ? ` <span class="sub">· ${esc(f.name || f.einheit_name)}</span>` : ""}`;

  // Im Einordnen-Modus (D-016) steht oben ein großer Knopf: ein Tippen und das Produkt liegt im Fach
  function einordnenKnopf(p) {
    const m = MF.einordnen.aktiv();
    if (!m || p.art !== "physisch") return "";
    if (p.platz?.id === m.fach_id) return `<div class="einordnen-ok">${icon("pin", 20)}<span>${esc(t("einordnen.schon", { code: m.code }))}</span></div>`;
    return `<button class="btn primary block einordnen-knopf" type="button" data-einordnen="${p.inventar_nr}">${icon("pin", 20)}<span>${esc(t("einordnen.knopf", { code: m.code }))}</span></button>`;
  }

  document.addEventListener("click", async (e) => {
    const b = e.target.closest("[data-einordnen]");
    if (!b) return;
    const m = MF.einordnen.aktiv();
    if (!m) { b.remove(); return; }
    const nr = Number(b.dataset.einordnen);
    b.disabled = true;
    try {
      // war es genommen, gilt es damit als zurückgelegt (D-043)
      const r = await MF.api("POST", `/api/produkte/${nr}/einordnen`, { fach_id: m.fach_id });
      MF.einordnen.verlaengern();
      const rahmen = b.closest("[data-panel], [data-detail]");
      if (rahmen) rahmen.innerHTML = MF.detailHtml(r.produkt, { kopf: rahmen.matches("[data-panel]") });
      document.dispatchEvent(new CustomEvent("mf:produkt", { detail: r.produkt }));
      MF.toast(t("einordnen.erledigt", { code: m.code }), {
        rueckgaengig: async () => {
          try { await MF.api("POST", `/api/produkte/${nr}/einordnen/zurueck`, r.rueckgaengig); location.reload(); }
          catch (err) { MF.toast(err.message, { fehler: true }); }
        },
      });
    } catch (err) { b.disabled = false; MF.toast(err.message, { fehler: true }); }
  });

  // Sammlungen des Produkts (D-047): Chips der gesetzten, „Zu Sammlung“ klappt die Liste zum Umschalten auf
  const offen = new Set();
  const stand = new Map();

  function sammlungenZeichnen(el) {
    const nr = Number(el.dataset.sammlungenFuer);
    const alle = stand.get(nr) || [];
    const drin = alle.filter((s) => s.enthalten);
    const auf = offen.has(nr);
    el.innerHTML = `
      <h3 class="abschnitt">${esc(t("sammlungen.abschnitt"))}</h3>
      <div class="sammlungen-chips">
        ${drin.map((s) => `<a class="pill" href="/sammlungen/${s.id}">${esc(s.name)}</a>`).join("") || `<span class="sub">${esc(t("sammlungen.keine"))}</span>`}
        <button class="btn" type="button" data-sammlungen-auf aria-expanded="${auf}">${icon("plus", 18)}<span>${esc(t("sammlungen.zu"))}</span></button>
      </div>
      ${auf ? `<div class="sammlungen-wahl">${alle.map((s) => `
        <button class="zeile" type="button" data-sammlung-wahl="${s.id}" aria-pressed="${s.enthalten}">
          <span class="waehler">${s.enthalten ? icon("check", 16) : ""}</span><span class="zeile-haupt"><span class="karte-name">${esc(s.name)}</span></span></button>`).join("")}
        <form class="sammlung-neu" data-sammlung-neu>
          <input class="eingabe" maxlength="60" placeholder="${esc(t("sammlungen.neu"))}" aria-label="${esc(t("sammlungen.neu"))}">
          <button class="iconbtn" type="submit" aria-label="${esc(t("sammlungen.anlegen"))}">${icon("plus", 18)}</button>
        </form></div>` : ""}`;
  }

  async function sammlungenLaden(el) {
    const nr = Number(el.dataset.sammlungenFuer);
    try { stand.set(nr, (await MF.api("GET", `/api/sammlungen?produkt=${nr}`)).sammlungen); sammlungenZeichnen(el); }
    catch (err) { MF.toast(err.message, { fehler: true }); }
  }

  const beobachter = new MutationObserver(() => {
    document.querySelectorAll("[data-sammlungen-fuer]:empty").forEach(sammlungenLaden);
  });
  beobachter.observe(document.documentElement, { childList: true, subtree: true });
  document.querySelectorAll("[data-sammlungen-fuer]:empty").forEach(sammlungenLaden);

  async function umschalten(el, sid, an) {
    const nr = Number(el.dataset.sammlungenFuer);
    const s = (stand.get(nr) || []).find((x) => x.id === sid);
    const setzen = async (ein) => {
      stand.set(nr, (await MF.api(ein ? "PUT" : "DELETE", `/api/sammlungen/${sid}/produkte/${nr}`)).sammlungen);
      sammlungenZeichnen(el);
    };
    try {
      await setzen(an);
      MF.toast(t(an ? "sammlungen.hinzugefuegt" : "sammlungen.herausgenommen", { name: s.name }), {
        rueckgaengig: async () => { try { await setzen(!an); } catch (err) { MF.toast(err.message, { fehler: true }); } },
      });
    } catch (err) { MF.toast(err.message, { fehler: true }); }
  }

  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-sammlungen-fuer]");
    if (!el) return;
    const nr = Number(el.dataset.sammlungenFuer);
    if (e.target.closest("[data-sammlungen-auf]")) {
      if (offen.has(nr)) offen.delete(nr); else offen.add(nr);
      sammlungenZeichnen(el);
      return;
    }
    const w = e.target.closest("[data-sammlung-wahl]");
    if (w) umschalten(el, Number(w.dataset.sammlungWahl), w.getAttribute("aria-pressed") !== "true");
  });

  document.addEventListener("submit", async (e) => {
    const f = e.target.closest("[data-sammlung-neu]");
    if (!f) return;
    e.preventDefault();
    const el = f.closest("[data-sammlungen-fuer]");
    const nr = Number(el.dataset.sammlungenFuer);
    const n = f.querySelector("input").value.trim();
    if (!n) return;
    try {
      const r = await MF.api("POST", "/api/sammlungen", { name: n, produkt: nr });
      stand.set(nr, r.sammlungen);
      sammlungenZeichnen(el);
      MF.toast(t("sammlungen.hinzugefuegt", { name: n }));
    } catch (err) { MF.toast(err.message, { fehler: true }); }
  });

  // Druckliste (SPEC 5): auch am Telefon; gedruckt wird am Desktop
  function druckliste(p) {
    return p.etikett === "gedruckt"
      ? `<button class="btn" type="button" data-druckliste="${p.inventar_nr}">${icon("tag", 20)}<span>${esc(t("etiketten.druckliste"))}</span></button>`
      : `<span class="sub druckliste-ok">${icon("tag", 18)}${esc(t("etiketten.auf_liste"))}</span>`;
  }

  document.addEventListener("click", async (e) => {
    const b = e.target.closest("[data-druckliste]");
    if (!b) return;
    try {
      await MF.api("POST", `/api/produkte/${b.dataset.druckliste}/druckliste`);
      b.outerHTML = druckliste({ etikett: "neu_drucken" });
    } catch (err) { MF.toast(err.message, { fehler: true }); }
  });

  // Kleine Fotos tauschen das große Bild (in Seite und Panel)
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-foto-gross]");
    if (!b) return;
    const rahmen = b.closest("[data-detail], [data-panel]");
    const gross = rahmen?.querySelector("[data-detail-bild]");
    if (gross) {
      gross.src = `/media/fotos/${b.dataset.fotoGross}-960.webp`;
      gross.closest("[data-bild-voll]").dataset.bildVoll = b.dataset.fotoGross;
    }
    rahmen.querySelectorAll("[data-foto-gross]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  });

  // Volle Größe (2400 px) nur auf Wunsch: Tippen aufs große Bild; Tippen oder Esc schließt (D-015)
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-bild-voll]");
    if (!b) return;
    const el = document.createElement("div");
    el.className = "bildansicht";
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-modal", "true");
    el.innerHTML = `<img src="/media/fotos/${esc(b.dataset.bildVoll)}.jpg" alt="">`;
    const zu = () => { el.remove(); document.removeEventListener("keydown", taste); b.focus(); };
    const taste = (ev) => { if (ev.key === "Escape") zu(); };
    el.addEventListener("click", zu);
    document.addEventListener("keydown", taste);
    document.body.appendChild(el);
  });
})();
