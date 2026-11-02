// Einstellungen › Kategorien & Filter (SPEC 6.3, D-011). Einfaches Formular: Speichern / Verwerfen, kein Rückgängig-Stapel.
(function () {
  const { $, $$, esc, icon, t, api, toast } = MF;
  const liste = $("[data-katliste]");
  const editor = $("[data-kat-editor]");
  if (!liste) return;

  const TYPEN = ["mass", "einfach", "mehrfach", "janein", "farbe"];
  // Startfarbe eines neuen Tons: die Grundfarbe selbst (aus den Token)
  const grundHex = (g) => getComputedStyle(document.documentElement).getPropertyValue("--farbe-" + g).trim() || "#888888";
  const EINHEITEN = ["mm", "cm", "m", "kg", "Stk"];

  let kategorien = [];
  let original = null;     // Kategorie wie gespeichert (null = neue Kategorie)
  let entwurf = null;      // bearbeitete Kopie
  let praefixVonHand = false;
  let typwahlOffen = false;

  const kopie = (o) => JSON.parse(JSON.stringify(o));
  const anzahl = (n) => t("kat.produkte", { n });
  const vergleichbar = (k) => JSON.stringify({
    name: k.name.trim(), praefix: k.praefix.trim().toUpperCase(),
    filter: k.filter.map((f) => ({ id: f.id, name: f.name.trim(), einheit: f.einheit || null,
      optionen: f.optionen.map((o) => ({ id: o.id, name: o.name.trim() })) })),
  });
  const geaendert = () => entwurf && (!original || vergleichbar(entwurf) !== vergleichbar(original)
    || entwurf.filter.some((f) => f.neu?.trim()));

  // ---------- Laden und Liste ----------
  async function laden(auswahl) {
    kategorien = (await api("GET", "/api/kategorien")).kategorien;
    zeichneListe();
    if (auswahl !== undefined) oeffnen(auswahl);
  }

  function zeichneListe() {
    const aktiv = entwurf && (original ? original.id : "neu");
    liste.innerHTML = kategorien.map((k) => `
      <button class="katlink" type="button" data-kat="${k.id}" ${k.id === aktiv ? 'aria-current="true"' : ""}>
        <span class="katlink-name">${esc(k.name)}</span>
        <span class="katlink-info num">${esc(k.praefix)} · ${k.produkte}</span>
      </button>`).join("");
  }

  function oeffnen(id) {
    if (id === null) { original = null; entwurf = null; zeichneEditor(); zeichneListe(); return; }
    original = id === "neu" ? null : kopie(kategorien.find((k) => k.id === id));
    entwurf = original ? kopie(original) : { name: "", praefix: "", filter: [], produkte: 0, fest: false };
    praefixVonHand = !!original;
    typwahlOffen = false;
    zeichneListe();
    zeichneEditor();
    if (!original) $("[data-feld=name]", editor).focus();
  }

  // Wechseln verwirft ungespeicherte Änderungen sofort; „Rückgängig“ holt sie zurück (D-029)
  function wechseln(ziel) {
    if (geaendert()) {
      const zurueck = { id: original ? original.id : "neu", entwurf: kopie(entwurf), praefixVonHand };
      toast(t("plan.verworfen"), {
        rueckgaengig: () => {
          oeffnen(zurueck.id);
          entwurf = zurueck.entwurf;
          praefixVonHand = zurueck.praefixVonHand;
          zeichneListe();
          zeichneEditor();
        },
      });
    }
    oeffnen(ziel);
  }

  liste.addEventListener("click", (e) => {
    const b = e.target.closest("[data-kat]");
    if (b) wechseln(Number(b.dataset.kat));
  });
  $("[data-kat-neu]").addEventListener("click", () => wechseln("neu"));
  window.addEventListener("beforeunload", (e) => { if (geaendert()) e.preventDefault(); });

  // ---------- Editor ----------
  function zeichneEditor() {
    if (!entwurf) { editor.innerHTML = `<div class="card leer">${esc(t("kat.waehlen"))}</div>`; return; }
    const loeschbar = original && !original.fest && original.produkte === 0;
    editor.innerHTML = `
      <div class="card stack">
        <div class="kat-kopf">
          <label class="feld feld-gross"><span>${esc(t("kat.name"))}</span>
            <input class="eingabe" data-feld="name" value="${esc(entwurf.name)}" maxlength="60" autocomplete="off"></label>
          <label class="feld feld-praefix"><span>${esc(t("kat.praefix"))}</span>
            <input class="eingabe num" data-feld="praefix" value="${esc(entwurf.praefix)}" maxlength="2" autocomplete="off"></label>
        </div>
        ${original ? `<div class="sub num">${esc(anzahl(original.produkte))}</div>` : ""}
        <h2 class="abschnitt">${esc(t("kat.filter"))}</h2>
        <div class="stack" data-filterliste>${entwurf.filter.map(zeichneFilter).join("")}</div>
        ${typwahlOffen ? zeichneTypwahl() : `<div><button class="btn" type="button" data-aktion="filter-neu">${icon("plus", 20)}<span>${esc(t("kat.filter_neu"))}</span></button></div>`}
        ${loeschbar ? `<div class="kat-fuss"><button class="linkbtn" type="button" data-aktion="loeschen">${esc(t("kat.loeschen"))}</button></div>` : ""}
      </div>
      <div class="speicherleiste" data-speicherleiste hidden>
        <div class="speicher-hinweise" data-hinweise></div>
        <div class="speicher-knoepfe">
          <button class="btn" type="button" data-aktion="verwerfen">${esc(t("kat.verwerfen"))}</button>
          <button class="btn primary" type="button" data-aktion="speichern">${esc(t("kat.speichern"))}</button>
        </div>
      </div>`;
    zeichneLeiste();
  }

  function zeichneFilter(f, i) {
    const letzter = i === entwurf.filter.length - 1;
    let inhalt = "";
    if (f.typ === "mass") {
      inhalt = `<label class="feld feld-einheit"><span>${esc(t("kat.einheit"))}</span>
        <select class="eingabe" data-feld="einheit" data-i="${i}">
          ${EINHEITEN.map((e) => `<option ${e === f.einheit ? "selected" : ""}>${e}</option>`).join("")}</select></label>`;
    } else if (f.farbe) {
      inhalt = zeichneFarbkasten(f, i);
    } else if (f.typ === "einfach" || f.typ === "mehrfach") {
      inhalt = `<div class="optionen">
        ${f.optionen.map((o, j) => `<span class="option">
            <input class="option-name" data-feld="option" data-i="${i}" data-j="${j}" value="${esc(o.name)}" size="${Math.max(3, o.name.length)}" aria-label="${esc(t("kat.auswahl"))}">
            ${o.produkte ? `<span class="option-n num">${o.produkte}</span>` : ""}
            <button class="option-x" type="button" data-aktion="option-weg" data-i="${i}" data-j="${j}" aria-label="${esc(t("kat.auswahl_entfernen", { name: o.name }))}">×</button>
          </span>`).join("")}
        <span class="option-neu-zeile">
          <input class="eingabe option-neu" data-feld="option-neu" data-i="${i}" value="${esc(f.neu || "")}" placeholder="${esc(t("kat.auswahl_neu"))}">
          <button class="iconbtn" type="button" data-aktion="option-neu" data-i="${i}" ${f.neu?.trim() ? "" : "disabled"} aria-label="${esc(t("kat.auswahl_neu"))}">${icon("plus", 18)}</button>
        </span>
      </div>`;
    }
    return `<div class="filterkarte">
      <div class="filterkopf">
        <input class="eingabe filter-name" data-feld="filtername" data-i="${i}" value="${esc(f.name)}" placeholder="${esc(t("kat.filter_name"))}" maxlength="60">
        <span class="typ-chip">${esc(t("kat.typ_" + (f.farbe ? "farbe" : f.typ)))}</span>
        <button class="iconbtn" type="button" data-aktion="hoch" data-i="${i}" ${i === 0 ? "disabled" : ""} aria-label="${esc(t("kat.nach_oben"))}">${icon("up", 20)}</button>
        <button class="iconbtn" type="button" data-aktion="runter" data-i="${i}" ${letzter ? "disabled" : ""} aria-label="${esc(t("kat.nach_unten"))}">${icon("down", 20)}</button>
        <button class="iconbtn" type="button" data-aktion="filter-weg" data-i="${i}" aria-label="${esc(t("kat.filter_entfernen"))}">${icon("close", 20)}</button>
      </div>
      ${inhalt}
    </div>`;
  }

  // Farbkasten (D-031): je Grundfarbe ein Kasten, die Töne liegen darin; ziehen = andere Grundfarbe
  function zeichneFarbkasten(f, i) {
    return `<div class="farbkasten">${MF.GRUNDFARBEN.map((g) => {
      const toene = f.optionen.map((o, j) => ({ o, j })).filter(({ o }) => o.grundfarbe === g);
      const name = t("farbe." + g);
      return `<div class="farbfach" data-grund="${g}" data-i="${i}">
        <div class="farbfach-kopf"><span class="farbpunkt klein farbe-${g}"></span><span>${esc(name)}</span>
          <button class="iconbtn" type="button" data-aktion="ton-neu" data-i="${i}" data-grund="${g}" aria-label="${esc(t("kat.ton_neu", { farbe: name }))}" title="${esc(t("kat.ton_neu", { farbe: name }))}">${icon("plus", 18)}</button></div>
        ${toene.map(({ o, j }) => `<span class="ton" data-i="${i}" data-j="${j}">
          <span class="ton-griff" draggable="true" title="${esc(t("kat.ton_ziehen"))}" aria-label="${esc(t("kat.ton_ziehen"))}">${icon("griff", 18)}</span>
          <input class="ton-farbe" type="color" data-feld="ton-hex" data-i="${i}" data-j="${j}" value="${esc(o.hex || grundHex(g))}" aria-label="${esc(t("kat.ton_farbe"))}">
          <input class="option-name" data-feld="option" data-i="${i}" data-j="${j}" value="${esc(o.name)}" placeholder="${esc(t("kat.ton_name"))}" aria-label="${esc(t("kat.ton_name"))}">
          ${o.produkte ? `<span class="option-n num">${o.produkte}</span>` : ""}
          <button class="option-x" type="button" data-aktion="option-weg" data-i="${i}" data-j="${j}" aria-label="${esc(t("kat.auswahl_entfernen", { name: o.name }))}">×</button>
        </span>`).join("")}
      </div>`;
    }).join("")}</div>`;
  }

  function zeichneTypwahl() {
    return `<div class="typwahl">${TYPEN.map((typ) => `
      <button class="typknopf" type="button" data-aktion="typ" data-typ="${typ}">
        <span class="typknopf-name">${esc(t("kat.typ_" + typ))}</span>
        <span class="sub">${esc(t("kat.beispiel_" + typ))}</span>
      </button>`).join("")}</div>`;
  }

  // Hinweise vor dem Speichern: was an Produkten verloren geht oder sich ändert (SPEC 3.6)
  function hinweise() {
    if (!original) return [];
    const h = [];
    const praefix = entwurf.praefix.trim().toUpperCase();
    if (praefix !== original.praefix && original.codes_mit_praefix) h.push(t("kat.hinweis_codes", { n: original.codes_mit_praefix }));
    for (const f of original.filter) {
      const neu = entwurf.filter.find((x) => x.id === f.id);
      if (!neu) { if (f.produkte) h.push(t("kat.hinweis_filter", { name: f.name, n: f.produkte })); continue; }
      for (const o of f.optionen) {
        if (o.produkte && !neu.optionen.some((x) => x.id === o.id)) h.push(t("kat.hinweis_auswahl", { name: o.name, n: o.produkte }));
      }
    }
    return h;
  }

  function zeichneLeiste() {
    const leiste = $("[data-speicherleiste]", editor);
    if (!leiste) return;
    leiste.hidden = !geaendert();
    $("[data-hinweise]", leiste).innerHTML = hinweise().map((h) => `<div class="hinweis">${esc(h)}</div>`).join("");
  }

  // ---------- Eingaben ----------
  editor.addEventListener("input", async (e) => {
    const el = e.target;
    const i = Number(el.dataset.i);
    switch (el.dataset.feld) {
      case "name":
        entwurf.name = el.value;
        if (!praefixVonHand) {
          const r = await api("GET", "/api/kategorien/praefix-vorschlag?name=" + encodeURIComponent(el.value));
          if (!praefixVonHand && entwurf.name === el.value) {
            entwurf.praefix = el.value.trim() ? r.praefix : "";
            $("[data-feld=praefix]", editor).value = entwurf.praefix;
          }
        }
        break;
      case "praefix":
        el.value = el.value.toUpperCase().replace(/[^A-Z]/g, "");
        entwurf.praefix = el.value;
        praefixVonHand = true;
        break;
      case "filtername": entwurf.filter[i].name = el.value; break;
      case "einheit": entwurf.filter[i].einheit = el.value; break;
      case "option": entwurf.filter[i].optionen[Number(el.dataset.j)].name = el.value; break;
      case "ton-hex": entwurf.filter[i].optionen[Number(el.dataset.j)].hex = el.value; break;
      case "option-neu":
        entwurf.filter[i].neu = el.value;
        $(`[data-aktion=option-neu][data-i="${i}"]`, editor).disabled = !el.value.trim();
        break;
    }
    zeichneLeiste();
  });

  editor.addEventListener("keydown", (e) => {
    const el = e.target;
    if (el.dataset.feld !== "option-neu" || e.key !== "Enter") return;
    e.preventDefault();
    optionHinzu(Number(el.dataset.i));
  });

  // Enter oder „+“: Option übernehmen, Fokus bleibt für die nächste
  function optionHinzu(i) {
    const f = entwurf.filter[i];
    if (!uebernehmen(f)) return;
    zeichneEditor();
    $(`[data-feld=option-neu][data-i="${i}"]`, editor).focus();
  }
  function uebernehmen(f) {
    const name = (f.neu || "").trim();
    delete f.neu;
    if (name) f.optionen.push({ id: null, name, produkte: 0 });
    return !!name;
  }

  editor.addEventListener("click", async (e) => {
    const b = e.target.closest("[data-aktion]");
    if (!b) return;
    const i = Number(b.dataset.i);
    const fl = entwurf.filter;
    switch (b.dataset.aktion) {
      case "filter-neu": typwahlOffen = true; zeichneEditor(); return;
      case "typ": {
        const typ = b.dataset.typ;
        // „Farbe“ ist eine Mehrfachauswahl mit Farbtönen (D-031)
        // Ein neuer Farbfilter beginnt mit einem Ton je Grundfarbe, benannt wie sie (D-032); umbenennen nach Bedarf
        const toene = typ === "farbe"
          ? MF.GRUNDFARBEN.map((g) => ({ id: null, name: t("farbe." + g), hex: g === "mehrfarbig" ? null : grundHex(g), grundfarbe: g, produkte: 0 })) : [];
        fl.push({ id: null, name: typ === "farbe" ? t("kat.farbton") : "", typ: typ === "farbe" ? "mehrfach" : typ, farbe: typ === "farbe",
                  einheit: typ === "mass" ? "mm" : null, optionen: toene, produkte: 0 });
        typwahlOffen = false;
        zeichneEditor();
        $(`[data-feld=filtername][data-i="${fl.length - 1}"]`, editor).focus();
        return;
      }
      case "hoch": [fl[i - 1], fl[i]] = [fl[i], fl[i - 1]]; break;
      case "runter": [fl[i], fl[i + 1]] = [fl[i + 1], fl[i]]; break;
      case "filter-weg": fl.splice(i, 1); break;
      case "option-weg": fl[i].optionen.splice(Number(b.dataset.j), 1); break;
      case "option-neu": optionHinzu(i); return;
      case "ton-neu": {
        const g = b.dataset.grund;
        fl[i].optionen.push({ id: null, name: "", hex: grundHex(g), grundfarbe: g, produkte: 0 });
        zeichneEditor();
        $(`.ton [data-feld=option][data-i="${i}"][data-j="${fl[i].optionen.length - 1}"]`, editor)?.focus();
        return;
      }
      case "verwerfen": oeffnen(original ? original.id : null); return;
      case "speichern": await speichern(b); return;
      case "loeschen": await loeschen(); return;
      default: return;
    }
    zeichneEditor();
  });

  async function speichern(knopf) {
    knopf.disabled = true;
    entwurf.filter.forEach(uebernehmen);     // noch nicht übernommene Eingabe geht nicht verloren
    try {
      if (!original) {
        // Erst anlegen; scheitert danach das Speichern der Filter, bleibt die Kategorie bestehen und wird bearbeitet
        const r = await api("POST", "/api/kategorien", { name: entwurf.name, praefix: entwurf.praefix });
        kategorien = r.kategorien;
        original = kopie(kategorien.find((k) => k.id === r.id));
        zeichneListe();
      }
      const r = await api("PUT", "/api/kategorien/" + original.id, { ...entwurf, version: original.version });
      kategorien = r.kategorien;
      toast(t("kat.gespeichert"));
      oeffnen(original.id);
    } catch (err) {
      toast(err.message, { fehler: true });
      if (err.status === 409) await laden(original?.id ?? null);
    } finally {
      knopf.disabled = false;
    }
  }

  // Nur leere Kategorien (D-011). Statt einer Rückfrage: „Rückgängig“ legt sie mit ihren Filtern neu an.
  async function loeschen() {
    const weg = kopie(original);
    try {
      await api("DELETE", "/api/kategorien/" + weg.id);
    } catch (err) { toast(err.message, { fehler: true }); return; }
    entwurf = null;
    original = null;
    await laden(null);
    toast(t("kat.geloescht", { name: weg.name }), {
      rueckgaengig: async () => {
        try {
          const { id } = await api("POST", "/api/kategorien", { name: weg.name, praefix: weg.praefix });
          const filter = weg.filter.map((f) => ({ ...f, id: null, optionen: f.optionen.map((o) => ({ name: o.name, hex: o.hex, grundfarbe: o.grundfarbe })) }));
          await api("PUT", "/api/kategorien/" + id, { name: weg.name, praefix: weg.praefix, version: 1, filter });
          await laden(id);
        } catch (err) { toast(err.message, { fehler: true }); }
      },
    });
  }

  // Ton in einen anderen Kasten ziehen: neue Grundfarbe, gleicher Ton (Kennung bleibt)
  let gezogen = null;
  editor.addEventListener("dragstart", (e) => {
    const ton = e.target.closest?.(".ton-griff")?.closest(".ton");
    if (!ton) return;
    gezogen = { i: Number(ton.dataset.i), j: Number(ton.dataset.j) };
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", ton.dataset.j);
    e.dataTransfer.setDragImage(ton, 16, 22);
  });
  editor.addEventListener("dragover", (e) => {
    const fach = e.target.closest?.(".farbfach");
    if (!gezogen || !fach || Number(fach.dataset.i) !== gezogen.i) return;
    e.preventDefault();
    $$(".farbfach.ueber", editor).forEach((x) => x !== fach && x.classList.remove("ueber"));
    fach.classList.add("ueber");
  });
  editor.addEventListener("drop", (e) => {
    const fach = e.target.closest?.(".farbfach");
    if (!gezogen || !fach) return;
    e.preventDefault();
    entwurf.filter[gezogen.i].optionen[gezogen.j].grundfarbe = fach.dataset.grund;
    gezogen = null;
    zeichneEditor();
  });
  editor.addEventListener("dragend", () => { gezogen = null; $$(".farbfach.ueber", editor).forEach((x) => x.classList.remove("ueber")); });

  laden().catch((err) => toast(err.message, { fehler: true }));
})();
