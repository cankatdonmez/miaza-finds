// Nehmen und Zurücklegen im Produktdetail (SPEC 6.7, D-039), beim Zurücklegen mit Fach-Bestätigung (D-042). Gilt für Seite und Seitenpanel gleich:
// nach jeder Änderung wird das Detail neu gezeichnet und „mf:produkt“ gemeldet (die Bibliothek lädt ihre Karten neu).
(function () {
  const { esc, icon, t, api, toast, datum } = MF;

  // Status-Zeile im Detail: Rozet in Statusfarbe, bei Entnahme Person, Datum und Notiz
  MF.statusHtml = function (p) {
    const badge = `<span class="status-badge status-${p.status}">${esc(t("status." + p.status))}</span>`;
    const e = p.entnahme;
    if (!e) return badge;
    const wer = [e.person, t("status.seit", { datum: datum(e.genommen_am.slice(0, 10)) })].filter(Boolean).join(" · ");
    return `${badge} <span class="sub">${esc(wer)}</span>${e.notiz ? `<div class="sub">${esc(e.notiz)}</div>` : ""}`;
  };

  // Gleich unter dem Titel, weil es die häufigste Handlung auf der Seite ist: Status und Hauptknopf
  MF.entnahmeZeile = function (p) {
    if (p.art !== "physisch") return "";
    return `<div class="detail-entnahme"><div class="detail-status">${MF.statusHtml(p)}</div>${MF.entnahmeKnopf(p)}</div>`;
  };

  // Hauptknopf: genommen → Zurücklegen, sonst Nehmen
  MF.entnahmeKnopf = function (p) {
    if (p.art !== "physisch") return "";
    return p.entnahme
      ? `<button class="btn primary" type="button" data-zuruecklegen="${p.inventar_nr}" data-fach="${p.platz?.id || ""}" data-fach-code="${esc(p.platz?.code || "")}">${icon("pin", 20)}<span>${esc(t("entnahme.zuruecklegen"))}</span></button>`
      : `<button class="btn primary" type="button" data-nehmen="${p.inventar_nr}">${esc(t("entnahme.nehmen"))}</button>`;
  };

  function neuZeichnen(b, p) {
    const rahmen = b.closest("[data-panel], [data-detail]");
    if (rahmen) rahmen.innerHTML = MF.detailHtml(p, { kopf: rahmen.matches("[data-panel]") });
    document.dispatchEvent(new CustomEvent("mf:produkt", { detail: p }));
  }

  // Formular an der Stelle des Knopfs: Person (die dieses Geräts vorgewählt), Ort, Notiz
  async function formular(b) {
    const nr = Number(b.dataset.nehmen);
    let personen = [];
    try { personen = (await api("GET", "/api/personen")).personen; } catch (err) { toast(err.message, { fehler: true }); return; }
    const ich = MF.geraetPerson();
    let person = personen.some((x) => x.id === ich) ? ich : null;
    let ort = "buero";
    const form = document.createElement("div");
    form.className = "nehmen-form";
    const zeichnen = () => {
      form.innerHTML = `
        ${personen.length ? `<div class="sub" id="nehmen-wer-${nr}">${esc(t("entnahme.person"))}</div>
        <div class="pills" role="group" aria-labelledby="nehmen-wer-${nr}">${personen.map((x) => `
          <button class="pill" type="button" data-wer="${x.id}" aria-pressed="${x.id === person}">${esc(x.name)}</button>`).join("")}</div>` : ""}
        <div class="segs" role="group" aria-label="${esc(t("entnahme.ort"))}">
          <button class="segbtn" type="button" data-ort="buero" aria-pressed="${ort === "buero"}">${esc(t("entnahme.ort_buero"))}</button>
          <button class="segbtn" type="button" data-ort="ausser_haus" aria-pressed="${ort === "ausser_haus"}">${esc(t("entnahme.ort_ausser_haus"))}</button>
        </div>
        <input class="eingabe" data-notiz maxlength="300" placeholder="${esc(t("entnahme.notiz"))}" aria-label="${esc(t("entnahme.notiz"))}" value="${esc(form.querySelector("[data-notiz]")?.value || "")}">
        <div class="actions">
          <button class="btn primary" type="button" data-nehmen-los ${personen.length && !person ? "disabled" : ""}>${esc(t("entnahme.nehmen"))}</button>
          <button class="btn" type="button" data-nehmen-ab>${esc(t("entnahme.abbrechen"))}</button>
        </div>`;
    };
    zeichnen();
    b.replaceWith(form);
    form.addEventListener("click", async (e) => {
      const x = e.target.closest("button");
      if (!x) return;
      if (x.dataset.wer) { person = Number(x.dataset.wer); return zeichnen(); }
      if (x.dataset.ort) { ort = x.dataset.ort; return zeichnen(); }
      if (x.hasAttribute("data-nehmen-ab")) {
        const knopf = document.createElement("div");
        knopf.innerHTML = MF.entnahmeKnopf({ art: "physisch", inventar_nr: nr });
        return form.replaceWith(knopf.firstElementChild);
      }
      if (!x.hasAttribute("data-nehmen-los")) return;
      x.disabled = true;
      try {
        const r = await api("POST", `/api/produkte/${nr}/nehmen`, { person_id: person, ort, notiz: form.querySelector("[data-notiz]").value });
        neuZeichnen(form, r.produkt);
        toast(t("entnahme.genommen", { status: t("status." + r.produkt.status) }), {
          rueckgaengig: async () => {
            try { neuNachRueckgaengig((await api("DELETE", `/api/entnahmen/${r.entnahme}`)).produkt); }
            catch (err) { toast(err.message, { fehler: true }); }
          },
        });
      } catch (err) { x.disabled = false; toast(err.message, { fehler: true }); }
    });
  }

  // Nach „Rückgängig“ ist der Knopf evtl. nicht mehr im Bild: das sichtbare Detail desselben Produkts neu zeichnen
  function neuNachRueckgaengig(p) {
    const ziel = document.querySelector(`[data-nehmen="${p.inventar_nr}"], [data-zuruecklegen="${p.inventar_nr}"], .nehmen-form`);
    if (ziel) neuZeichnen(ziel, p);
    else document.dispatchEvent(new CustomEvent("mf:produkt", { detail: p }));
  }

  // ---------- Zurücklegen ----------
  // daten: {fach_bestaetigt} oder {neuer_fach}; ohne Fach-Abfrage leer. el = Knopf oder Bestätigungsfeld
  async function zuruecklegen(el, nr, daten = {}) {
    try {
      const r = await api("POST", `/api/produkte/${nr}/zuruecklegen`, daten);
      neuZeichnen(el, r.produkt);
      const platzWeg = r.platz_vorher !== (r.produkt.platz?.id ?? null);
      const ok = daten.fach_bestaetigt === true || daten.neuer_fach != null;
      toast(r.produkt.platz ? t("entnahme.zurueckgelegt_fach", { code: r.produkt.platz.code }) : t("entnahme.zurueckgelegt"), {
        rueckgaengig: async () => {
          try {
            const zurueck = await api("POST", `/api/entnahmen/${r.entnahme}/offen`, platzWeg ? { platz: { fach: r.platz_vorher } } : {});
            neuNachRueckgaengig(zurueck.produkt);
          } catch (err) { toast(err.message, { fehler: true }); }
        },
      });
      if (ok) document.querySelector(".toast")?.classList.add("ok");
    } catch (err) {
      if (el.matches("button")) el.disabled = false;
      toast(err.message, { fehler: true });
    }
  }

  let einstellungen = null;     // einmal je Seite; Änderungen in den Einstellungen gelten ab dem nächsten Laden
  async function fachBestaetigen() {
    einstellungen = einstellungen || await api("GET", "/api/einstellungen");
    return einstellungen.fach_bestaetigen;
  }

  // Bestätigungsfeld an der Stelle des Knopfs (D-042): Fach-Etikett scannen oder ohne Scan bestätigen
  async function bestaetigen(b) {
    const nr = Number(b.dataset.zuruecklegen);
    const soll = { id: Number(b.dataset.fach), code: b.dataset.fachCode };
    const feld = document.createElement("div");
    feld.className = "nehmen-form";
    const live = MF.scan.liveMoeglich();
    let stop = null;
    const aus = () => { if (stop) stop(); stop = null; };
    const grund = () => {
      feld.innerHTML = `
        <div class="fach-scan-titel">${esc(t("fach.scannen_titel", { code: soll.code }))}</div>
        ${live ? `<video class="fach-scan-bild" playsinline muted autoplay></video>` : ""}
        <div class="actions">
          ${live ? "" : `<button class="btn primary" type="button" data-f="foto">${icon("camera", 20)}<span>${esc(t("fach.scannen"))}</span></button>`}
          <button class="btn" type="button" data-f="ohne">${esc(t("fach.ohne_scan"))}</button>
          <button class="btn" type="button" data-f="ab">${esc(t("entnahme.abbrechen"))}</button>
        </div>`;
      if (live) {
        MF.scan.kamera(feld.querySelector("video"), gescannt).then((s) => {
          stop = s;
          // Kamera will nicht (abgelehnt, belegt): dann wie ohne HTTPS mit Foto
          if (!s && feld.isConnected) { feld.querySelector("video")?.remove(); feld.querySelector(".actions").insertAdjacentHTML("afterbegin",
            `<button class="btn primary" type="button" data-f="foto">${icon("camera", 20)}<span>${esc(t("fach.scannen"))}</span></button>`); }
        });
      }
    };

    async function gescannt(z) {
      aus();
      if (z.art !== "fach") { toast(t("fach.kein_fach"), { fehler: true }); return grund(); }
      if (z.id === soll.id) return zuruecklegen(feld, nr, { fach_bestaetigt: true });
      // Anderes Fach: sagen, was los ist, und den Menschen entscheiden lassen
      let ist = String(z.id);
      try {
        const plan = await api("GET", "/api/plan");
        ist = plan.einheiten.flatMap((x) => x.faecher).find((f) => f.id === z.id)?.code || ist;
      } catch { /* dann eben die Nummer */ }
      feld.innerHTML = `
        <div class="fach-scan-titel">${esc(t("fach.falsch", { soll: soll.code, ist }))}</div>
        <div class="actions">
          <button class="btn primary" type="button" data-f="hin">${esc(t("fach.hinbringen", { soll: soll.code }))}</button>
          <button class="btn" type="button" data-f="neu" data-neu="${z.id}">${esc(t("fach.neuer_platz", { ist }))}</button>
          <button class="btn" type="button" data-f="ab">${esc(t("entnahme.abbrechen"))}</button>
        </div>`;
    }

    feld.addEventListener("click", (e) => {
      const x = e.target.closest("[data-f]");
      if (!x) return;
      const f = x.dataset.f;
      if (f === "foto") return MF.scan.foto(gescannt);
      aus();
      if (f === "ab") { const k = document.createElement("div"); k.innerHTML = b.outerHTML; const neu = k.firstElementChild; neu.disabled = false; return feld.replaceWith(neu); }
      x.disabled = true;
      if (f === "ohne" || f === "hin") return zuruecklegen(feld, nr, { fach_bestaetigt: false });
      if (f === "neu") return zuruecklegen(feld, nr, { neuer_fach: Number(x.dataset.neu) });
    });
    grund();
    b.replaceWith(feld);
  }

  document.addEventListener("click", async (e) => {
    const nehmen = e.target.closest("[data-nehmen]");
    if (nehmen) return formular(nehmen);
    const zurueck = e.target.closest("[data-zuruecklegen]");
    if (!zurueck) return;
    zurueck.disabled = true;
    let abfragen = false;
    try { abfragen = Boolean(zurueck.dataset.fach) && await fachBestaetigen(); } catch { abfragen = false; }
    if (abfragen) return bestaetigen(zurueck);
    zuruecklegen(zurueck, Number(zurueck.dataset.zuruecklegen));
  });
})();
