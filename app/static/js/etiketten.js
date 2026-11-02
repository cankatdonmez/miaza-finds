// Etiketten drucken (SPEC 6.6): Produkte oder Fächer auswählen, Bögen ansehen, PDF erstellen;
// danach „gedruckt“ mit Rückgängig. Beide Arten nutzen dasselbe Papier und denselben Ablauf.
(function () {
  const { $, $$, esc, t, api, toast } = MF;
  const liste = $("[data-etk-liste]");
  if (!liste) return;

  // Was sich je Art unterscheidet
  const ARTEN = {
    produkte: {
      liste: "/api/etiketten", feld: "produkte", pdf: (ids) => "/api/etiketten/pdf?" + ids.map((i) => "nr=" + i).join("&"),
      gedruckt: "/api/etiketten/gedruckt", zurueck: "/api/etiketten/zuruecksetzen", sende: "produkte",
      id: (x) => x.inventar_nr, qr: (x) => `/api/etiketten/qr/${x.inventar_nr}.svg`,
      name: (x) => x.name || t("produkt.unbenannt", { nr: x.inventar_nr }), sub: (x) => x.code,
      sortieren: (a, b) => a.inventar_nr - b.inventar_nr,
    },
    faecher: {
      liste: "/api/etiketten/faecher", feld: "faecher", pdf: (ids) => "/api/etiketten/faecher/pdf?" + ids.map((i) => "id=" + i).join("&"),
      gedruckt: "/api/etiketten/faecher/gedruckt", zurueck: "/api/etiketten/faecher/zuruecksetzen", sende: "faecher",
      id: (x) => x.id, qr: (x) => `/api/etiketten/qr/fach/${x.id}.svg`,
      name: (x) => x.code, sub: (x) => x.beschreibung,
      // Reihenfolge wie im Regal: nach Code
      sortieren: (a, b) => a.code.localeCompare(b.code, "de", { numeric: true }),
    },
  };
  let art = "produkte";
  const A = () => ARTEN[art];

  let treffer = [];
  let zahlen = {};
  let bogen = null;
  let auswahl = [];          // Einträge in Druckreihenfolge
  const gewaehlt = (id) => auswahl.some((x) => A().id(x) === id);

  async function laden() {
    const q = $("[data-etk-suche]").value;
    try {
      const r = await api("GET", A().liste + "?q=" + encodeURIComponent(q));
      treffer = r[A().feld];
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
    $$("[data-etk-art]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.etkArt === art)));
    $("[data-etk-vorwahl]").innerHTML = `
      <button class="pill" type="button" data-vorwahl="ungedruckt">${esc(t("etiketten.ungedruckt"))} <span class="num">${zahlen.ungedruckt || 0}</span></button>
      <button class="pill" type="button" data-vorwahl="neu_drucken">${esc(t("etiketten.neu_drucken"))} <span class="num">${zahlen.neu_drucken || 0}</span></button>
      <button class="pill" type="button" data-vorwahl="treffer">${esc(t("etiketten.treffer"))}</button>
      <button class="pill" type="button" data-vorwahl="leeren" ${auswahl.length ? "" : "disabled"}>${esc(t("etiketten.leeren"))}</button>`;
    liste.innerHTML = treffer.map((x) => {
      const id = A().id(x), an = gewaehlt(id);
      return `<button class="zeile${an ? " gewaehlt" : ""}" type="button" role="checkbox" aria-checked="${an}" data-etk="${id}">
        <span class="waehler">${an ? MF.icon("check", 18) : ""}</span>
        <span class="zeile-haupt"><span class="karte-name${art === "faecher" ? " num" : ""}">${esc(A().name(x))}</span><span class="karte-sub${art === "produkte" ? " num" : ""}">${esc(A().sub(x))}</span></span>
        <span class="etk-zustand etk-${x.etikett}">${esc(t("etiketten.zustand_" + x.etikett))}</span>
      </button>`;
    }).join("") || `<div class="leer">${esc(t(art === "faecher" ? "etiketten.leer_faecher" : "etiketten.leer"))}</div>`;
    zeichneBoegen();
  }

  function zeichneBoegen() {
    const je = bogen.spalten * bogen.zeilen;
    const anzahlBoegen = Math.ceil(auswahl.length / je);
    $("[data-etk-anzahl]").textContent = t(anzahlBoegen === 1 && auswahl.length > 1 ? "etiketten.anzahl_ein_bogen" : "etiketten.anzahl", { n: auswahl.length, b: anzahlBoegen });
    $("[data-etk-pdf]").disabled = !auswahl.length;
    if (!auswahl.length) {
      $("[data-etk-boegen]").innerHTML = `<div class="card leer">${esc(t(art === "faecher" ? "etiketten.keine_auswahl_faecher" : "etiketten.keine_auswahl"))}</div>`;
      return;
    }
    // Maßstabsgetreu in % der Seite, damit die Vorschau dem Druck entspricht
    const pb = (mm) => (mm / bogen.seite_breite_mm) * 100;
    const ph = (mm) => (mm / bogen.seite_hoehe_mm) * 100;
    const boegen = [];
    for (let b = 0; b < anzahlBoegen; b++) {
      const zellen = auswahl.slice(b * je, (b + 1) * je).map((x, i) => {
        const s = i % bogen.spalten, z = Math.floor(i / bogen.spalten);
        const links = pb(bogen.rand_links_mm + s * (bogen.breite_mm + bogen.abstand_x_mm));
        const oben = ph(bogen.rand_oben_mm + z * (bogen.hoehe_mm + bogen.abstand_y_mm));
        const text = art === "faecher"
          ? `<span class="etk-fachcode num">${esc(x.code)}</span><span class="etk-code">${esc(x.beschreibung)}</span>`
          : `<span class="etk-name">${esc(A().name(x))}</span><span class="etk-code num">${esc(x.code)}</span>`;
        return `<button class="etk-etikett" type="button" data-etk-weg="${A().id(x)}" title="${esc(t("etiketten.entfernen", { name: A().name(x) }))}"
          style="left:${links}%;top:${oben}%;width:${pb(bogen.breite_mm)}%;height:${ph(bogen.hoehe_mm)}%">
          <span class="etk-qr"><img src="${A().qr(x)}" alt=""></span>${text}</button>`;
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
    if (d.etkArt && d.etkArt !== art) {
      art = d.etkArt;
      auswahl = [];
      $("[data-etk-suche]").value = "";
      return laden();
    }
    if (d.etk) {
      const id = Number(d.etk);
      if (gewaehlt(id)) auswahl = auswahl.filter((x) => A().id(x) !== id);
      else auswahl.push(treffer.find((x) => A().id(x) === id));
      return zeichnen();
    }
    if (d.etkWeg) { auswahl = auswahl.filter((x) => A().id(x) !== Number(d.etkWeg)); return zeichnen(); }
    if (d.vorwahl === "leeren") { auswahl = []; return zeichnen(); }
    if (d.vorwahl === "treffer") {
      treffer.forEach((x) => { if (!gewaehlt(A().id(x))) auswahl.push(x); });
      return zeichnen();
    }
    if (d.vorwahl) {
      // Druckreihenfolge wie im Regal (Produkte nach Inventarnummer, Fächer nach Code)
      const r = await api("GET", A().liste + "?zustand=" + d.vorwahl);
      auswahl = r[A().feld].sort(A().sortieren);
      return zeichnen();
    }
    if (d.etkPdf !== undefined) return drucken();
  });

  async function drucken() {
    const a = A();
    const ids = auswahl.map(a.id);
    window.open(a.pdf(ids), "_blank", "noopener");
    try {
      const { vorher } = await api("POST", a.gedruckt, { [a.sende]: ids });
      auswahl = [];
      await laden();
      toast(t("etiketten.markiert", { n: ids.length }), {
        rueckgaengig: async () => {
          try { await api("POST", a.zurueck, { vorher }); await laden(); } catch (err) { toast(err.message, { fehler: true }); }
        },
      });
    } catch (err) { toast(err.message, { fehler: true }); }
  }

  // Fach-Etiketten direkt öffnen (aus dem Plan-Editor: ?art=faecher)
  if (new URLSearchParams(location.search).get("art") === "faecher") art = "faecher";
  laden();
})();
