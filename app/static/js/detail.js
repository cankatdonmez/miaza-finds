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
      <dl class="merkmale">
        ${p.art === "physisch" ? zeile(t("produkt.platz"), p.platz ? platzText(p.platz) : `<span class="sub">${esc(t("status.ohne_platz"))}</span>`) : ""}
        ${zeile(t("produkt.kategorie"), esc(p.kategorie_name))}
        ${zeile(t("produkt.marke"), esc(p.marke))}
        ${zeile(t("produkt.abmessungen"), esc(p.abmessungen))}
        ${zeile(t("produkt.preis"), preis)}
        ${(p.merkmale || []).map((m) => zeile(m.name, esc(m.wert))).join("")}
        ${zeile(t("produkt.anzahl"), p.anzahl != null ? esc(t("produkt.anzahl_wert", { n: p.anzahl })) : "")}
      </dl>
      ${farben ? `<div class="farben">${farben}</div>` : ""}
      ${p.notiz ? `<p class="detail-notiz">${esc(p.notiz)}</p>` : ""}
      <div class="actions">
        ${p.link ? `<a class="btn" href="${esc(p.link)}" target="_blank" rel="noopener noreferrer">${esc(t("produkt.link_oeffnen"))}</a>` : ""}
        ${p.platz ? `<a class="btn" href="/buero?fach=${p.platz.id}&produkt=${p.inventar_nr}">${icon("buero", 20)}<span>${esc(t("produkt.im_buero_zeigen"))}</span></a>` : ""}
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
      const r = await MF.api("PUT", `/api/produkte/${nr}/platz`, { fach_id: m.fach_id });
      MF.einordnen.verlaengern();
      b.outerHTML = `<div class="einordnen-ok">${icon("pin", 20)}<span>${esc(t("einordnen.erledigt", { code: m.code }))}</span></div>`;
      MF.toast(t("einordnen.erledigt", { code: m.code }), {
        rueckgaengig: async () => {
          try { await MF.api("PUT", `/api/produkte/${nr}/platz`, { fach_id: r.vorher }); location.reload(); }
          catch (err) { MF.toast(err.message, { fehler: true }); }
        },
      });
    } catch (err) { b.disabled = false; MF.toast(err.message, { fehler: true }); }
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
