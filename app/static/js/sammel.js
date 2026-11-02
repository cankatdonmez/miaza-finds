// Sammelbearbeitung im Seitenpanel der Bibliothek (SPEC 6.2, D-012).
// Kein Bestätigungsfenster: die Wirkung steht im Panel, nach „Anwenden“ gibt es einige Sekunden „Rückgängig“.
(function () {
  const { $, $$, esc, icon, t, api, toast } = MF;
  const panel = $("[data-panel]");
  if (!panel) return;

  const FARBEN = ["weiss", "beige", "braun", "terracotta", "gold", "rosa", "gruen", "blau", "grau", "schwarz"];
  let ids = [];
  let kategorien = [];
  let quelle = [];            // Kategorien der ausgewählten Produkte (aus der Vorschau)
  let a = {};                 // gewünschte Änderung
  let vorschauNr = 0;

  window.addEventListener("mf:sammel", async (e) => {
    ids = e.detail.ids;
    kategorien = e.detail.kategorien;
    a = { kategorie_id: null, code: "behalten", marke: "", art: "", farben_hinzu: [], farben_weg: [], werte: {} };
    const v = await vorschau();
    if (!v) return;
    quelle = v.kategorien;
    zeichnen(v);
    panel.hidden = false;
  });

  function aenderung() {
    const d = {};
    if (a.kategorie_id) { d.kategorie_id = a.kategorie_id; d.code = a.code; }
    if (a.marke.trim()) d.marke = a.marke.trim();
    if (a.art) d.art = a.art;
    if (a.farben_hinzu.length) d.farben_hinzu = a.farben_hinzu;
    if (a.farben_weg.length) d.farben_weg = a.farben_weg;
    const werte = Object.fromEntries(Object.entries(a.werte).filter(([, w]) => w !== undefined));
    if (Object.keys(werte).length && !a.kategorie_id) d.werte = werte;
    return d;
  }

  async function vorschau() {
    const nr = ++vorschauNr;
    try {
      const v = await api("POST", "/api/produkte/sammel/vorschau", { produkte: ids, aenderung: aenderung() });
      return nr === vorschauNr ? v : null;
    } catch (err) { toast(err.message, { fehler: true }); return null; }
  }

  // Filterwerte nur, wenn alle aus einer Kategorie sind und sie bleibt (SPEC 6.2)
  const eineKategorie = () => (quelle.length === 1 && !a.kategorie_id ? kategorien.find((k) => k.id === quelle[0]) : null);

  function zeichnen(v) {
    const k = eineKategorie();
    panel.innerHTML = `
      <div class="panel-kopf">
        <button class="iconbtn" type="button" data-panel-zu aria-label="${esc(t("produkt.schliessen"))}">${icon("close")}</button>
        <h2 class="detail-name">${esc(t("sammel.titel", { n: ids.length }))}</h2>
      </div>
      <label class="feld"><span>${esc(t("produkt.kategorie"))}</span>
        <select class="eingabe" data-s-kategorie>
          <option value="">${esc(t("sammel.unveraendert"))}</option>
          ${kategorien.map((x) => `<option value="${x.id}" ${x.id === a.kategorie_id ? "selected" : ""}>${esc(x.name)}</option>`).join("")}
        </select></label>
      ${a.kategorie_id ? `<div class="segs" role="group">
        <button class="segbtn" type="button" data-s-code="behalten" aria-pressed="${a.code === "behalten"}">${esc(t("sammel.code_behalten"))}</button>
        <button class="segbtn" type="button" data-s-code="neu" aria-pressed="${a.code === "neu"}">${esc(t("sammel.code_neu"))}</button>
      </div>` : ""}
      <label class="feld"><span>${esc(t("produkt.marke"))}</span>
        <input class="eingabe" data-s-marke value="${esc(a.marke)}" placeholder="${esc(t("sammel.unveraendert"))}" maxlength="80"></label>
      <div class="feld"><span>${esc(t("sammel.art"))}</span>
        <div class="segs" role="group">
          ${[["", t("sammel.unveraendert")], ["physisch", t("produkt.art_physisch")], ["digital", t("produkt.art_digital")]].map(([w, text]) =>
            `<button class="segbtn" type="button" data-s-art="${w}" aria-pressed="${a.art === w}">${esc(text)}</button>`).join("")}
        </div></div>
      ${farbGruppe("farben_hinzu", t("sammel.farben_hinzu"))}
      ${farbGruppe("farben_weg", t("sammel.farben_weg"))}
      ${k ? k.filter.map(filterGruppe).join("") : (quelle.length > 1 ? `<p class="sub">${esc(t("sammel.werte_nur_eine"))}</p>` : "")}
      <div class="speicherleiste">
        <div class="speicher-hinweise" data-s-hinweise>${hinweise(v)}</div>
        <div class="speicher-knoepfe"><button class="btn primary" type="button" data-s-anwenden ${Object.keys(aenderung()).length ? "" : "disabled"}>${esc(t("sammel.anwenden"))}</button></div>
      </div>`;
  }

  function farbGruppe(feld, titel) {
    return `<div class="feld"><span>${esc(titel)}</span><div class="farben">${FARBEN.map((f) => `
      <button class="farbknopf" type="button" data-s-farbe="${f}" data-s-feld="${feld}" aria-pressed="${a[feld].includes(f)}">
        <span class="farbpunkt farbe-${f}"></span><span>${esc(t("farbe." + f))}</span></button>`).join("")}</div></div>`;
  }

  function filterGruppe(f) {
    // Nur einfache Werte setzen: eine Auswahl, Ja/Nein; Maße und Mehrfachauswahl bleiben der Einzelbearbeitung
    const w = a.werte[f.id];
    let knoepfe;
    if (f.typ === "janein") {
      knoepfe = [[true, t("produkt.ja")], [false, t("produkt.nein")]].map(([v, text]) =>
        `<button class="pill" type="button" data-s-wert="${f.id}" data-s-v="${v}" aria-pressed="${w === v}">${esc(text)}</button>`).join("");
    } else if (f.typ === "einfach") {
      knoepfe = f.optionen.map((o) =>
        `<button class="pill" type="button" data-s-wert="${f.id}" data-s-v="${o.id}" aria-pressed="${w === o.id}">${esc(o.name)}</button>`).join("");
    } else {
      return "";
    }
    return `<div class="feld"><span>${esc(f.name)}</span><div class="pills">${knoepfe}</div></div>`;
  }

  function hinweise(v) {
    if (!v) return "";
    const teile = [];
    if (v.wechsel) teile.push(t("sammel.hinweis_wechsel", { n: v.wechsel, kategorie: kategorien.find((k) => k.id === a.kategorie_id)?.name || "" }));
    if (v.codes_neu) teile.push(t("sammel.hinweis_codes", { n: v.codes_neu }));
    if (v.werte_entfallen) teile.push(t("sammel.hinweis_werte", { n: v.werte_entfallen }));
    return teile.length ? `<div class="hinweis">${esc(teile.join(" · "))}</div>` : "";
  }

  async function neu() {
    const v = await vorschau();
    if (v) zeichnen(v);
  }

  panel.addEventListener("change", (e) => {
    if (e.target.matches("[data-s-kategorie]")) {
      a.kategorie_id = Number(e.target.value) || null;
      a.werte = {};
      neu();
    }
  });

  panel.addEventListener("input", (e) => {
    if (!e.target.matches("[data-s-marke]")) return;
    a.marke = e.target.value;
    $("[data-s-anwenden]", panel).disabled = !Object.keys(aenderung()).length;
  });

  panel.addEventListener("click", async (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    const d = b.dataset;
    if (d.sCode) { a.code = d.sCode; return neu(); }
    if (d.sArt !== undefined) { a.art = d.sArt; return neu(); }
    if (d.sFarbe) {
      const liste = a[d.sFeld];
      a[d.sFeld] = liste.includes(d.sFarbe) ? liste.filter((x) => x !== d.sFarbe) : [...liste, d.sFarbe];
      // dieselbe Farbe kann nicht zugleich hinzukommen und wegfallen
      const anders = d.sFeld === "farben_hinzu" ? "farben_weg" : "farben_hinzu";
      a[anders] = a[anders].filter((x) => x !== d.sFarbe);
      return neu();
    }
    if (d.sWert) {
      const v = d.sV === "true" ? true : d.sV === "false" ? false : Number(d.sV);
      a.werte[d.sWert] = a.werte[d.sWert] === v ? undefined : v;
      return neu();
    }
    if (d.sAnwenden !== undefined) return anwenden(b);
  });

  async function anwenden(knopf) {
    knopf.disabled = true;
    try {
      const r = await api("POST", "/api/produkte/sammel", { produkte: ids, aenderung: aenderung() });
      panel.hidden = true;
      window.dispatchEvent(new CustomEvent("mf:sammel-fertig"));
      toast(t("sammel.erledigt", { n: r.geaendert }), {
        rueckgaengig: async () => {
          try {
            const z = await api("POST", `/api/produkte/sammel/rueckgaengig/${r.rueckgaengig}`);
            toast(z.uebersprungen ? t("sammel.teilweise", { n: z.uebersprungen }) : t("sammel.zurueck"));
            window.dispatchEvent(new CustomEvent("mf:sammel-fertig"));
          } catch (err) { toast(err.message, { fehler: true }); }
        },
      });
    } catch (err) {
      toast(err.message, { fehler: true });
      knopf.disabled = false;
    }
  }
})();
