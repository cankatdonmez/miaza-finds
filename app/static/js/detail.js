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
      ? `<img class="detail-bild" src="/media/fotos/${esc(fotos[0].datei)}.jpg" alt="" data-detail-bild>`
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
      <div class="detail-bildrahmen">${bild}</div>
      ${kleine}
      <div class="detail-titel">
        ${kopf ? `<h2 class="detail-name">${esc(name)}</h2>` : ""}
        <div class="detail-zeile"><span class="num">${esc(p.code)}</span>${p.art === "digital" ? `<span class="badge-digital">${esc(t("produkt.digital"))}</span>` : ""}</div>
      </div>
      <dl class="merkmale">
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
        ${p.art === "physisch" ? druckliste(p) : ""}
      </div>`;
  };

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
    if (gross) gross.src = `/media/fotos/${b.dataset.fotoGross}.jpg`;
    rahmen.querySelectorAll("[data-foto-gross]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  });
})();
