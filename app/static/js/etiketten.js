// Etiketten drucken (SPEC 6.6): auswählen, Bögen ansehen, PDF erstellen; danach „gedruckt“ mit Rückgängig.
(function () {
  const { $, $$, esc, icon, t, api, toast } = MF;
  const liste = $("[data-etk-liste]");
  if (!liste) return;

  let treffer = [];          // Suchergebnis
  let zahlen = {};
  let bogen = null;
  let auswahl = [];          // [{inventar_nr, code, name}] in Druckreihenfolge
  const gewaehlt = (nr) => auswahl.some((p) => p.inventar_nr === nr);
  const name = (p) => p.name || t("produkt.unbenannt", { nr: p.inventar_nr });

  async function laden() {
    const q = $("[data-etk-suche]").value;
    try {
      const r = await api("GET", "/api/etiketten?q=" + encodeURIComponent(q));
      treffer = r.produkte;
      zahlen = r.zahlen;
      bogen = r.bogen;
      const hinweis = $("[data-etk-qr-hinweis]");
      const lokal = /\/\/(localhost|127\.|\[::1\])/.test(r.qr_adresse);
      hinweis.hidden = !lokal;
      hinweis.textContent = lokal ? t("etiketten.qr_lokal", { adresse: r.qr_adresse }) : "";
      zeichnen();
    } catch (err) { toast(err.message, { fehler: true }); }
  }

  function zeichnen() {
    $("[data-etk-vorwahl]").innerHTML = `
      <button class="pill" type="button" data-vorwahl="ungedruckt">${esc(t("etiketten.ungedruckt"))} <span class="num">${zahlen.ungedruckt || 0}</span></button>
      <button class="pill" type="button" data-vorwahl="neu_drucken">${esc(t("etiketten.neu_drucken"))} <span class="num">${zahlen.neu_drucken || 0}</span></button>
      <button class="pill" type="button" data-vorwahl="treffer">${esc(t("etiketten.treffer"))}</button>
      <button class="pill" type="button" data-vorwahl="leeren" ${auswahl.length ? "" : "disabled"}>${esc(t("etiketten.leeren"))}</button>`;
    liste.innerHTML = treffer.map((p) => {
      const an = gewaehlt(p.inventar_nr);
      return `<button class="zeile${an ? " gewaehlt" : ""}" type="button" role="checkbox" aria-checked="${an}" data-etk="${p.inventar_nr}">
        <span class="waehler">${an ? icon("check", 18) : ""}</span>
        <span class="zeile-haupt"><span class="karte-name">${esc(name(p))}</span><span class="karte-sub num">${esc(p.code)}</span></span>
        <span class="etk-zustand etk-${p.etikett}">${esc(t("etiketten.zustand_" + p.etikett))}</span>
      </button>`;
    }).join("") || `<div class="leer">${esc(t("etiketten.leer"))}</div>`;
    zeichneBoegen();
  }

  function zeichneBoegen() {
    const je = bogen.spalten * bogen.zeilen;
    const anzahlBoegen = Math.ceil(auswahl.length / je);
    $("[data-etk-anzahl]").textContent = t(anzahlBoegen === 1 && auswahl.length > 1 ? "etiketten.anzahl_ein_bogen" : "etiketten.anzahl", { n: auswahl.length, b: anzahlBoegen });
    $("[data-etk-pdf]").disabled = !auswahl.length;
    if (!auswahl.length) {
      $("[data-etk-boegen]").innerHTML = `<div class="card leer">${esc(t("etiketten.keine_auswahl"))}</div>`;
      return;
    }
    // Maßstabsgetreu in % der Seite, damit die Vorschau dem Druck entspricht
    const pb = (mm) => (mm / bogen.seite_breite_mm) * 100;
    const ph = (mm) => (mm / bogen.seite_hoehe_mm) * 100;
    const boegen = [];
    for (let b = 0; b < anzahlBoegen; b++) {
      const zellen = auswahl.slice(b * je, (b + 1) * je).map((p, i) => {
        const s = i % bogen.spalten, z = Math.floor(i / bogen.spalten);
        const links = pb(bogen.rand_links_mm + s * (bogen.breite_mm + bogen.abstand_x_mm));
        const oben = ph(bogen.rand_oben_mm + z * (bogen.hoehe_mm + bogen.abstand_y_mm));
        return `<button class="etk-etikett" type="button" data-etk-weg="${p.inventar_nr}" title="${esc(t("etiketten.entfernen", { name: name(p) }))}"
          style="left:${links}%;top:${oben}%;width:${pb(bogen.breite_mm)}%;height:${ph(bogen.hoehe_mm)}%">
          <span class="etk-qr"><img src="/api/etiketten/qr/${p.inventar_nr}.svg" alt=""></span>
          <span class="etk-name">${esc(name(p))}</span>
          <span class="etk-code num">${esc(p.code)}</span></button>`;
      }).join("");
      boegen.push(`<div class="etk-bogen" style="aspect-ratio:${bogen.seite_breite_mm}/${bogen.seite_hoehe_mm}">${zellen}</div>`);
    }
    $("[data-etk-boegen]").innerHTML = boegen.join("");
  }

  let tippen;
  $("[data-etk-suche]").addEventListener("input", () => { clearTimeout(tippen); tippen = setTimeout(laden, 150); });

  document.addEventListener("click", async (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    const d = b.dataset;
    if (d.etk) {
      const nr = Number(d.etk);
      if (gewaehlt(nr)) auswahl = auswahl.filter((p) => p.inventar_nr !== nr);
      else auswahl.push(treffer.find((p) => p.inventar_nr === nr));
      return zeichnen();
    }
    if (d.etkWeg) { auswahl = auswahl.filter((p) => p.inventar_nr !== Number(d.etkWeg)); return zeichnen(); }
    if (d.vorwahl === "leeren") { auswahl = []; return zeichnen(); }
    if (d.vorwahl === "treffer") {
      treffer.forEach((p) => { if (!gewaehlt(p.inventar_nr)) auswahl.push(p); });
      return zeichnen();
    }
    if (d.vorwahl) {
      // Druckreihenfolge aufsteigend nach Inventarnummer: so liegen die Etiketten wie die Produkte im Regal
      const r = await api("GET", "/api/etiketten?zustand=" + d.vorwahl);
      auswahl = r.produkte.sort((a, b2) => a.inventar_nr - b2.inventar_nr);
      return zeichnen();
    }
    if (d.etkPdf !== undefined) return drucken();
  });

  async function drucken() {
    const ids = auswahl.map((p) => p.inventar_nr);
    const adresse = "/api/etiketten/pdf?" + ids.map((i) => "nr=" + i).join("&");
    window.open(adresse, "_blank", "noopener");
    try {
      const { vorher } = await api("POST", "/api/etiketten/gedruckt", { produkte: ids });
      auswahl = [];
      await laden();
      toast(t("etiketten.markiert", { n: ids.length }), {
        rueckgaengig: async () => {
          try { await api("POST", "/api/etiketten/zuruecksetzen", { vorher }); await laden(); } catch (err) { toast(err.message, { fehler: true }); }
        },
      });
    } catch (err) { toast(err.message, { fehler: true }); }
  }

  laden();
})();
