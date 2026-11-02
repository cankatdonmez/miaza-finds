// Bibliothek (SPEC 6.1): eine Suche, Filter, Raster/Liste, Statuszeile, Detail im Panel.
// Der Zustand steht in der Adresszeile (Zurück, Neuladen und geteilte Links zeigen dieselbe Ansicht).
(function () {
  const { $, $$, esc, icon, t, api, toast, euro } = MF;
  const ergebnis = $("[data-ergebnis]");
  if (!ergebnis) return;

  const FARBEN = ["weiss", "beige", "braun", "terracotta", "gold", "rosa", "gruen", "blau", "grau", "schwarz"];
  const STATUS = ["am_platz", "in_benutzung", "ausser_haus", "ohne_platz", "fehlend"];
  const breit = window.matchMedia("(min-width: 900px)");

  let kategorien = [];
  let antwort = null;
  let seite = 0;
  let abfrage = 0;            // nur die letzte Antwort zählt
  let ansicht = "raster";
  try { ansicht = localStorage.getItem("mf-ansicht") || "raster"; } catch { /* Standard */ }
  let auswahl = null;         // Set der Inventarnummern, solange „Auswählen“ läuft (Sammelbearbeitung, D-012)
  // Bei „Fehlende Angaben“ immer Liste: Namen nacheinander eintippen (SPEC 6.2, Serienerfassung Schritt 4)
  const ergaenzen = () => zustand.status === "fehlend" && !auswahl;
  const sichtbar = () => (auswahl || ergaenzen() ? "liste" : ansicht);

  // ---------- Zustand <-> Adresse ----------
  let zustand = ausAdresse();

  function ausAdresse() {
    const a = new URLSearchParams(location.search);
    const werte = {};
    for (const [k, v] of a) {
      const m = k.match(/^w(\d+)(_min|_max)?$/);
      if (!m) continue;
      const fid = m[1];
      if (m[2]) { werte[fid] = { ...(werte[fid] || {}), [m[2].slice(1)]: v }; }
      else if (v === "ja" || v === "nein") werte[fid] = v;
      else werte[fid] = [...(werte[fid] || []), Number(v)];
    }
    return {
      q: a.get("q") || "", art: a.get("art") || "", kategorie: Number(a.get("kategorie")) || null,
      status: a.get("status") || "", farben: a.getAll("farbe"), marken: a.getAll("marke"),
      preis_min: a.get("preis_min") || "", preis_max: a.get("preis_max") || "", werte,
    };
  }

  function alsParameter() {
    const a = new URLSearchParams();
    if (zustand.q.trim()) a.set("q", zustand.q.trim());
    if (zustand.art) a.set("art", zustand.art);
    if (zustand.kategorie) a.set("kategorie", zustand.kategorie);
    if (zustand.status) a.set("status", zustand.status);
    zustand.farben.forEach((f) => a.append("farbe", f));
    zustand.marken.forEach((m) => a.append("marke", m));
    if (zustand.preis_min) a.set("preis_min", zustand.preis_min);
    if (zustand.preis_max) a.set("preis_max", zustand.preis_max);
    if (zustand.kategorie) {
      for (const [fid, w] of Object.entries(zustand.werte)) {
        if (Array.isArray(w)) w.forEach((o) => a.append("w" + fid, o));
        else if (typeof w === "string") a.set("w" + fid, w);
        else if (w) { if (w.min) a.set(`w${fid}_min`, w.min); if (w.max) a.set(`w${fid}_max`, w.max); }
      }
    }
    return a;
  }

  function aktiveFilter() {
    const w = Object.values(zustand.werte).filter((x) => (Array.isArray(x) ? x.length : typeof x === "string" ? x : x && (x.min || x.max))).length;
    return (zustand.kategorie ? 1 : 0) + (zustand.status ? 1 : 0) + zustand.farben.length + zustand.marken.length +
      (zustand.preis_min || zustand.preis_max ? 1 : 0) + (zustand.kategorie ? w : 0);
  }

  // ---------- Laden ----------
  async function laden({ weiter = false } = {}) {
    const nr = ++abfrage;
    seite = weiter ? seite + 1 : 0;
    const a = alsParameter();
    history.replaceState(null, "", a.toString() ? "?" + a : location.pathname);
    if (seite) a.set("seite", seite);
    try {
      const r = await api("GET", "/api/bibliothek?" + a);
      if (nr !== abfrage) return;
      if (weiter) r.produkte = [...antwort.produkte, ...r.produkte];
      antwort = r;
      zeichnen();
    } catch (err) { toast(err.message, { fehler: true }); }
  }

  // ---------- Zeichnen ----------
  function zeichnen() {
    $$("[data-art]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.art === zustand.art)));
    $$("[data-ansicht]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.ansicht === ansicht)));
    zeichneFilter();
    zeichneChips();
    zeichneStatuszeile();
    zeichneErgebnis();
    zeichneAuswahlleiste();
    const n = aktiveFilter();
    const zahl = $("[data-filterzahl]");
    zahl.hidden = !n;
    zahl.textContent = n;
    $("[data-filter-schliessen]").textContent = t("bibliothek.filter_zeigen", { n: antwort.gesamt });
  }

  function zeichneErgebnis() {
    // Leeres Ergebnis ohne Listenrahmen: die Karte „Keine Treffer“ steht allein (kein Rahmen im Rahmen)
    ergebnis.className = "ergebnis" + (antwort.produkte.length ? " " + sichtbar() : "");
    if (!antwort.produkte.length) {
      const leererBestand = antwort.zaehler.gesamt === 0;
      ergebnis.innerHTML = `<div class="card leer stack">
        <div>${esc(t(leererBestand ? "bibliothek.leer" : "bibliothek.keine_treffer"))}</div>
        ${leererBestand ? `<div><a class="btn primary" href="/produkt/neu">${icon("plus", 20)}<span>${esc(t("menue.neues_produkt"))}</span></a></div>`
                        : `<div><button class="btn" type="button" data-zuruecksetzen>${esc(t("bibliothek.zuruecksetzen"))}</button></div>`}
      </div>`;
    } else {
      ergebnis.innerHTML = antwort.produkte.map(sichtbar() === "liste" ? zeile : karte).join("");
    }
    namenLeiste.hidden = !(ergaenzen() && antwort.produkte.length);
    $("[data-mehr]").hidden = !antwort.weitere;
  }

  const name = (p) => p.name || t("produkt.unbenannt", { nr: p.inventar_nr });
  const preis = (p) => (p.preis ? `${euro(p.preis.cent)} € ${t("einheit." + p.preis.einheit)}` : "");
  // Schärfe nach Bildschirm (D-015): der Browser nimmt 320 oder 960 px je nach Breite und Pixeldichte
  const KARTE = "(min-width: 900px) 260px, 50vw";
  const srcset = (f) => `/media/fotos/${esc(f)}-320.webp 320w, /media/fotos/${esc(f)}-960.webp 960w`;
  const bild = (p, cls) => p.foto
    ? `<img class="${cls}" src="/media/fotos/${esc(p.foto)}-320.webp" srcset="${srcset(p.foto)}" sizes="${cls === "karte-img" ? KARTE : "48px"}" alt="" loading="lazy">`
    : `<span class="${cls} leer-bild">${icon("image", 28)}</span>`;
  const digital = (p) => (p.art === "digital" ? `<span class="badge-digital">${esc(t("produkt.digital"))}</span>` : "");

  function karte(p) {
    return `<a class="karte" href="/produkt/${p.inventar_nr}" data-produkt="${p.inventar_nr}">
      <span class="karte-bild">${bild(p, "karte-img")}${digital(p)}</span>
      <span class="karte-text">
        <span class="karte-name">${esc(name(p))}</span>
        <span class="karte-sub">${esc([p.marke, p.kategorie].filter(Boolean).join(" · "))}</span>
        ${p.preis ? `<span class="karte-preis num">${esc(preis(p))}</span>` : ""}
      </span></a>`;
  }

  function ergaenzZeile(p) {
    return `<div class="zeile" data-ergaenzen="${p.inventar_nr}">
      ${bild(p, "zeile-img")}
      <span class="zeile-haupt">
        <input class="eingabe" data-name-fuer="${p.inventar_nr}" data-version="${p.version}" data-gespeichert="${esc(p.name || "")}" value="${esc(p.name || "")}"
          placeholder="${esc(t("produkt.unbenannt", { nr: p.inventar_nr }))}" aria-label="${esc(t("serie.name", { code: p.code }))}" enterkeyhint="next" maxlength="120">
        <span class="karte-sub num">${esc(p.code)} · ${esc(p.kategorie)}</span>
      </span>
      <a class="iconbtn" href="/produkt/${p.inventar_nr}/bearbeiten" aria-label="${esc(t("produkt.bearbeiten"))}">${icon("right", 20)}</a>
    </div>`;
  }

  function zeile(p) {
    if (ergaenzen()) return ergaenzZeile(p);
    const an = auswahl?.has(p.inventar_nr);
    return `<a class="zeile${an ? " gewaehlt" : ""}" href="/produkt/${p.inventar_nr}" data-produkt="${p.inventar_nr}" ${auswahl ? `role="checkbox" aria-checked="${an}"` : ""}>
      ${auswahl ? `<span class="waehler">${an ? icon("check", 18) : ""}</span>` : ""}
      ${bild(p, "zeile-img")}
      <span class="zeile-haupt"><span class="karte-name">${esc(name(p))}</span><span class="karte-sub num">${esc(p.code)}</span></span>
      <span class="zeile-spalte nur-desktop">${esc(p.kategorie)}</span>
      <span class="zeile-spalte nur-desktop">${esc(p.marke || "")}</span>
      <span class="zeile-preis num">${esc(preis(p))}</span>
      ${digital(p)}</a>`;
  }

  function zeichneAuswahlleiste() {
    const leiste = $("[data-auswahlleiste]");
    leiste.hidden = !auswahl;
    $("[data-auswahl-start]").hidden = !!auswahl;
    if (!auswahl) return;
    leiste.innerHTML = `
      <span class="auswahl-zahl">${esc(t("sammel.ausgewaehlt", { n: auswahl.size }))}</span>
      ${antwort.gesamt > auswahl.size ? `<button class="linkbtn" type="button" data-auswahl-alle>${esc(t("sammel.alle", { n: antwort.gesamt }))}</button>` : ""}
      ${auswahl.size ? `<button class="linkbtn" type="button" data-auswahl-keine>${esc(t("sammel.keine"))}</button>` : ""}
      <span class="spacer"></span>
      <button class="btn" type="button" data-auswahl-ende>${esc(t("sammel.fertig"))}</button>
      <button class="btn primary" type="button" data-auswahl-bearbeiten ${auswahl.size ? "" : "disabled"}>${esc(t("sammel.bearbeiten"))}</button>`;
  }

  function auswahlEnde() {
    auswahl = null;
    zeichneErgebnis();
    zeichneAuswahlleiste();
  }

  function zeichneStatuszeile() {
    const z = antwort.zaehler;
    const teile = [`<button class="linkbtn leise" type="button" data-status-setzen="">${esc(t("bibliothek.zeile_gesamt", { n: z.gesamt }))}</button>`];
    for (const s of ["ausser_haus", "ohne_platz", "fehlend"]) {
      if (z[s]) teile.push(`<button class="linkbtn leise" type="button" data-status-setzen="${s}">${esc(t("bibliothek.zeile_" + s, { n: z[s] }))}</button>`);
    }
    $("[data-statuszeile]").innerHTML = teile.join(`<span aria-hidden="true">·</span>`);
  }

  function filterHtml() {
    const k = kategorien.find((x) => x.id === zustand.kategorie);
    const zahlen = antwort?.kategorien || {};
    const kat = `<section class="fgruppe"><h3 class="abschnitt">${esc(t("produkt.kategorie"))}</h3>
      <div class="flinks">
        <button class="flink" type="button" data-kategorie="" aria-pressed="${!zustand.kategorie}">${esc(t("bibliothek.alle"))}</button>
        ${kategorien.map((x) => `<button class="flink" type="button" data-kategorie="${x.id}" aria-pressed="${x.id === zustand.kategorie}">
          <span>${esc(x.name)}</span><span class="num sub">${zahlen[x.id] || 0}</span></button>`).join("")}
      </div></section>`;
    const z = antwort?.zaehler || {};
    const status = STATUS.filter((s) => z[s] || zustand.status === s);
    const stat = status.length ? `<section class="fgruppe"><h3 class="abschnitt">${esc(t("bibliothek.status"))}</h3><div class="pills">
      ${status.map((s) => `<button class="pill" type="button" data-status="${s}" aria-pressed="${zustand.status === s}">${esc(t("status." + s))} <span class="num">${z[s] || 0}</span></button>`).join("")}
      </div></section>` : "";
    const eigene = k ? k.filter.map(filterGruppe).join("") : "";
    const farbe = `<section class="fgruppe"><h3 class="abschnitt">${esc(t("bibliothek.farbe"))}</h3><div class="farben">
      ${FARBEN.map((f) => `<button class="farbknopf" type="button" data-farbe="${f}" aria-pressed="${zustand.farben.includes(f)}">
        <span class="farbpunkt farbe-${f}"></span><span>${esc(t("farbe." + f))}</span></button>`).join("")}</div></section>`;
    const marken = antwort?.marken || [];
    const marke = marken.length ? `<section class="fgruppe"><h3 class="abschnitt">${esc(t("bibliothek.marke"))}</h3><div class="pills">
      ${marken.map((m) => `<button class="pill" type="button" data-marke="${esc(m)}" aria-pressed="${zustand.marken.includes(m)}">${esc(m)}</button>`).join("")}
      </div></section>` : "";
    const preisG = `<section class="fgruppe"><h3 class="abschnitt">${esc(t("bibliothek.preis"))}</h3><div class="von-bis">
      <input class="eingabe num" data-preis="preis_min" value="${esc(zustand.preis_min)}" inputmode="decimal" placeholder="${esc(t("bibliothek.preis_von"))}" aria-label="${esc(t("bibliothek.preis_von"))}">
      <span class="sub">–</span>
      <input class="eingabe num" data-preis="preis_max" value="${esc(zustand.preis_max)}" inputmode="decimal" placeholder="${esc(t("bibliothek.preis_bis"))}" aria-label="${esc(t("bibliothek.preis_bis"))}">
      </div></section>`;
    return kat + stat + eigene + farbe + marke + preisG;
  }

  function filterGruppe(f) {
    const w = zustand.werte[f.id];
    let inhalt;
    if (f.typ === "mass") {
      inhalt = `<div class="von-bis">
        <input class="eingabe num" data-mass="${f.id}" data-grenze="min" value="${esc(w?.min || "")}" inputmode="decimal" placeholder="${esc(t("bibliothek.preis_von"))}" aria-label="${esc(f.name)} ${esc(t("bibliothek.preis_von"))}">
        <span class="sub">–</span>
        <input class="eingabe num" data-mass="${f.id}" data-grenze="max" value="${esc(w?.max || "")}" inputmode="decimal" placeholder="${esc(t("bibliothek.preis_bis"))}" aria-label="${esc(f.name)} ${esc(t("bibliothek.preis_bis"))}">
        <span class="sub">${esc(f.einheit)}</span></div>`;
    } else if (f.typ === "janein") {
      inhalt = `<div class="pills">${[["", t("bibliothek.egal")], ["ja", t("produkt.ja")], ["nein", t("produkt.nein")]].map(([v, text]) =>
        `<button class="pill" type="button" data-janein="${f.id}" data-v="${v}" aria-pressed="${(w || "") === v}">${esc(text)}</button>`).join("")}</div>`;
    } else {
      inhalt = `<div class="pills">${f.optionen.map((o) =>
        `<button class="pill" type="button" data-option="${f.id}" data-o="${o.id}" aria-pressed="${(w || []).includes(o.id)}">${esc(o.name)}</button>`).join("")}</div>`;
    }
    return `<section class="fgruppe"><h3 class="abschnitt">${esc(f.name)}</h3>${inhalt}</section>`;
  }

  function zeichneFilter() {
    const html = filterHtml();
    const fokus = document.activeElement?.dataset;
    const ziel = breit.matches ? $("[data-filterspalte]") : $("[data-filterblatt-inhalt]");
    // Preis- und Maßfelder nicht während der Eingabe neu zeichnen (Fokus bliebe sonst nicht erhalten)
    if (fokus && (fokus.preis || fokus.mass) && ziel.contains(document.activeElement)) return;
    ziel.innerHTML = html;
  }

  function zeichneChips() {
    const chips = [];
    const chip = (text, aktion) => chips.push(`<span class="chip">${esc(text)}<button class="chip-x" type="button" data-weg="${esc(aktion)}" aria-label="${esc(t("bibliothek.entfernen", { name: text }))}">×</button></span>`);
    const k = kategorien.find((x) => x.id === zustand.kategorie);
    if (k) chip(k.name, "kategorie");
    if (zustand.status) chip(t("status." + zustand.status), "status");
    if (k) {
      for (const f of k.filter) {
        const w = zustand.werte[f.id];
        if (!w) continue;
        if (Array.isArray(w)) w.forEach((o) => { const opt = f.optionen.find((x) => x.id === o); if (opt) chip(opt.name, `option:${f.id}:${o}`); });
        else if (typeof w === "string") chip(`${f.name}: ${t("produkt." + w)}`, `wert:${f.id}`);
        else if (w.min || w.max) chip(`${f.name} ${w.min || "…"}–${w.max || "…"} ${f.einheit}`, `wert:${f.id}`);
      }
    }
    zustand.farben.forEach((f) => chip(t("farbe." + f), `farbe:${f}`));
    zustand.marken.forEach((m) => chip(m, `marke:${m}`));
    if (zustand.preis_min || zustand.preis_max) chip(`${zustand.preis_min || "…"}–${zustand.preis_max || "…"} €`, "preis");
    $("[data-chips]").innerHTML = chips.join("");
  }

  // ---------- Eingaben ----------
  let tippen;
  $("[data-suche]").value = zustand.q;
  $("[data-suche]").addEventListener("input", (e) => {
    zustand.q = e.target.value;
    clearTimeout(tippen);
    tippen = setTimeout(laden, 150);
  });

  function umschalten(liste, wert) { return liste.includes(wert) ? liste.filter((x) => x !== wert) : [...liste, wert]; }

  document.addEventListener("click", async (e) => {
    const b = e.target.closest("button, a");
    if (!b) return;
    const d = b.dataset;
    if (d.art !== undefined && b.closest(".art-wahl")) { zustand.art = d.art; return laden(); }
    if (d.ansicht) {
      ansicht = d.ansicht;
      try { localStorage.setItem("mf-ansicht", ansicht); } catch { /* egal */ }
      return zeichnen();
    }
    if (d.kategorie !== undefined && b.classList.contains("flink")) {
      zustand.kategorie = Number(d.kategorie) || null;
      zustand.werte = {};
      return laden();
    }
    if (d.status) { zustand.status = zustand.status === d.status ? "" : d.status; return laden(); }
    if (d.statusSetzen !== undefined) { zustand.status = d.statusSetzen; return laden(); }
    if (d.farbe && b.closest("[data-filterspalte], [data-filterblatt]")) { zustand.farben = umschalten(zustand.farben, d.farbe); return laden(); }
    if (d.marke) { zustand.marken = umschalten(zustand.marken, d.marke); return laden(); }
    if (d.option) { zustand.werte[d.option] = umschalten(zustand.werte[d.option] || [], Number(d.o)); return laden(); }
    if (d.janein) { zustand.werte[d.janein] = d.v; return laden(); }
    if (d.weg) { entfernen(d.weg); return laden(); }
    if (d.zuruecksetzen !== undefined) {
      zustand = { ...zustand, art: "", kategorie: null, status: "", farben: [], marken: [], preis_min: "", preis_max: "", werte: {}, q: "" };
      $("[data-suche]").value = "";
      return laden();
    }
    if (d.mehr !== undefined) return laden({ weiter: true });
    if (d.filterOeffnen !== undefined) { $("[data-filterblatt]").hidden = false; return zeichneFilter(); }
    if (d.filterSchliessen !== undefined) { $("[data-filterblatt]").hidden = true; return; }
    if (d.panelZu !== undefined) { panelZu(); return; }
    if (d.auswahlStart !== undefined) { panelZu(); auswahl = new Set(); return zeichnen(); }
    if (d.auswahlEnde !== undefined) return auswahlEnde();
    if (d.auswahlKeine !== undefined) { auswahl.clear(); zeichneErgebnis(); return zeichneAuswahlleiste(); }
    if (d.auswahlAlle !== undefined) {
      try {
        const r = await api("GET", "/api/bibliothek?ids=1&" + alsParameter());
        r.ids.forEach((i) => auswahl.add(i));
      } catch (err) { toast(err.message, { fehler: true }); }
      zeichneErgebnis();
      return zeichneAuswahlleiste();
    }
    if (d.auswahlBearbeiten !== undefined) {
      window.dispatchEvent(new CustomEvent("mf:sammel", { detail: { ids: [...auswahl], kategorien } }));
      return;
    }
    if (d.produkt && auswahl) {
      e.preventDefault();
      const nr = Number(d.produkt);
      if (auswahl.has(nr)) auswahl.delete(nr); else auswahl.add(nr);
      zeichneErgebnis();
      return zeichneAuswahlleiste();
    }
    if (d.produkt && breit.matches && !e.ctrlKey && !e.metaKey) { e.preventDefault(); panelAuf(Number(d.produkt)); }
  });

  // Klick auf den abgedunkelten Rand schließt das Filterblatt
  $("[data-filterblatt]").addEventListener("click", (e) => { if (e.target === e.currentTarget) e.currentTarget.hidden = true; });

  let zahlTimer;
  document.addEventListener("input", (e) => {
    const d = e.target.dataset;
    if (!d.preis && !d.mass) return;
    if (d.preis) zustand[d.preis] = e.target.value.trim();
    if (d.mass) zustand.werte[d.mass] = { ...(zustand.werte[d.mass] || {}), [d.grenze]: e.target.value.trim() };
    clearTimeout(zahlTimer);
    zahlTimer = setTimeout(laden, 400);
  });

  function entfernen(was) {
    const [art, a, b] = was.split(":");
    if (art === "kategorie") { zustand.kategorie = null; zustand.werte = {}; }
    else if (art === "status") zustand.status = "";
    else if (art === "farbe") zustand.farben = zustand.farben.filter((x) => x !== a);
    else if (art === "marke") zustand.marken = zustand.marken.filter((x) => x !== was.slice(6));
    else if (art === "preis") { zustand.preis_min = ""; zustand.preis_max = ""; }
    else if (art === "option") zustand.werte[a] = (zustand.werte[a] || []).filter((x) => x !== Number(b));
    else if (art === "wert") delete zustand.werte[a];
  }

  // ---------- Detailpanel (Desktop) ----------
  const panel = $("[data-panel]");
  async function panelAuf(nr) {
    try {
      const p = await api("GET", "/api/produkte/" + nr);
      panel.innerHTML = MF.detailHtml(p, { kopf: true });
      panel.hidden = false;
      $$("[data-produkt]").forEach((x) => x.classList.toggle("gewaehlt", Number(x.dataset.produkt) === nr));
    } catch (err) { toast(err.message, { fehler: true }); }
  }
  function panelZu() {
    panel.hidden = true;
    $$(".gewaehlt").forEach((x) => x.classList.remove("gewaehlt"));
  }
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (!panel.hidden) panelZu();
    $("[data-filterblatt]").hidden = true;
  });
  breit.addEventListener("change", () => { panelZu(); $("[data-filterblatt]").hidden = true; if (antwort) zeichneFilter(); });

  // Nach der Sammelbearbeitung (sammel.js): Auswahl beenden und neu laden
  window.addEventListener("mf:sammel-fertig", () => { auswahl = null; laden(); });
  // Nach der Serienerfassung (serie.js): gleich die Produkte mit fehlenden Angaben zeigen
  window.addEventListener("mf:serie-fertig", () => {
    zustand = { ...zustand, q: "", art: "", kategorie: null, farben: [], marken: [], preis_min: "", preis_max: "", werte: {}, status: "fehlend" };
    $("[data-suche]").value = "";
    laden();
  });

  // ---------- Namen nach der Serie (D-028) ----------
  // Enter speichert dieses Feld und springt weiter; „Speichern“ unter der Liste speichert alle geänderten auf einmal
  const namenLeiste = document.createElement("div");
  namenLeiste.className = "formleiste";
  namenLeiste.hidden = true;
  namenLeiste.innerHTML = `<span class="sub" data-namen-zahl></span>
    <button class="btn primary" type="button" data-namen-speichern>${esc(t("produkt.speichern"))}</button>`;
  ergebnis.after(namenLeiste);

  const offeneNamen = () => $$("[data-name-fuer]").filter((f) => f.value.trim() && f.value.trim() !== f.dataset.gespeichert);
  function namenZahl() {
    const n = offeneNamen().length;
    $("[data-namen-zahl]", namenLeiste).textContent = n ? t("serie.namen_offen", { n }) : "";
  }
  async function nameSpeichern(feld) {
    const name = feld.value.trim();
    if (!name || name === feld.dataset.gespeichert) return true;
    try {
      const r = await api("PATCH", "/api/produkte/" + feld.dataset.nameFuer, { name, version: Number(feld.dataset.version) });
      feld.dataset.version = r.version;
      feld.dataset.gespeichert = name;
      feld.closest(".zeile").classList.add("erledigt");
      return true;
    } catch (err) {
      toast(err.message, { fehler: true });
      return false;
    } finally { namenZahl(); }
  }
  document.addEventListener("input", (e) => { if (e.target.closest?.("[data-name-fuer]")) namenZahl(); });
  document.addEventListener("keydown", async (e) => {
    const feld = e.target.closest?.("[data-name-fuer]");
    if (!feld || e.key !== "Enter") return;
    e.preventDefault();
    const alle = $$("[data-name-fuer]");
    const naechstes = alle[alle.indexOf(feld) + 1];
    // Sofort weiter, damit schnelles Tippen nicht im alten Feld landet; gespeichert wird im Hintergrund
    if (naechstes) naechstes.focus();
    else feld.blur();
    if (!(await nameSpeichern(feld))) feld.focus();
  });
  namenLeiste.addEventListener("click", async (e) => {
    if (!e.target.closest("[data-namen-speichern]")) return;
    const offen = offeneNamen();
    if (!offen.length) return toast(t("serie.namen_keine"));
    let ok = 0;
    for (const f of offen) if (await nameSpeichern(f)) ok += 1;
    if (ok) toast(t("serie.namen_gespeichert", { n: ok }));
  });
  window.addEventListener("beforeunload", (e) => { if (offeneNamen().length) e.preventDefault(); });

  // ---------- Start ----------
  api("GET", "/api/kategorien")
    .then((r) => { kategorien = r.kategorien; return laden(); })
    .catch((err) => toast(err.message, { fehler: true }));
})();
