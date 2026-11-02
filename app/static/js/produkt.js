// Produkt erfassen und bearbeiten (SPEC 6.2). Kürzester Weg: Foto, Name, Speichern; der Rest kann später kommen.
(function () {
  const { $, $$, esc, icon, t, api, toast, toastNachher, datum } = MF;
  const form = $("[data-produktform]");
  if (!form) return;

  const FARBEN = ["weiss", "beige", "braun", "terracotta", "gold", "rosa", "gruen", "blau", "grau", "schwarz"];
  const EINHEITEN = ["m2", "m", "stueck", "paket"];
  const LETZTE = "mf-letzte-kategorie";
  const inventarNr = Number(form.dataset.inventarNr) || null;
  // Nach Speichern/Abbrechen: bestehendes Produkt → seine Detailseite, neues → Bibliothek
  const zurueck = inventarNr ? `/produkt/${inventarNr}` : "/bibliothek";

  let kategorien = [];
  let original = null;       // gespeicherter Stand (null = neu)
  let p = null;              // Formularzustand
  // Fotos sind bis „Speichern“ Entwurf (D-028): neue werden danach hochgeladen, entfernte danach gelöscht
  let neueFotos = [];        // {datei, url}
  let wegFotos = new Set();  // Kennungen gespeicherter Fotos, die beim Speichern gelöscht werden
  let speichert = false;

  // Telefon: Kamera-App über „capture“. Desktop ignoriert „capture“ → eigene Kamera, nur wenn es eine gibt (D-014)
  const TELEFON = matchMedia("(pointer: coarse)").matches;
  let kameraDa = false;

  const kopie = (o) => JSON.parse(JSON.stringify(o));
  const kategorie = (id) => kategorien.find((k) => k.id === id);
  const letzteKategorie = () => { try { return Number(localStorage.getItem(LETZTE)); } catch { return 0; } };

  function daten() {
    return {
      name: p.name, art: p.art, kategorie_id: p.kategorie_id, marke: p.marke, abmessungen: p.abmessungen,
      link: p.link, anzahl: p.anzahl === "" ? null : p.anzahl, notiz: p.notiz, farben: p.farben,
      preis: p.preis.betrag.trim() ? p.preis : null, werte: p.werte, code: p.code, version: p.version,
    };
  }
  const geaendert = () => neueFotos.length > 0 || wegFotos.size > 0 || JSON.stringify(daten()) !== JSON.stringify(original);

  // ---------- Laden ----------
  async function laden() {
    kategorien = (await api("GET", "/api/kategorien")).kategorien;
    if (inventarNr) {
      const r = await api("GET", "/api/produkte/" + inventarNr);
      p = {
        ...r, marke: r.marke || "", abmessungen: r.abmessungen || "", link: r.link || "", notiz: r.notiz || "",
        name: r.name || "", anzahl: r.anzahl ?? "", code: "behalten", code_alt: r.code,
        preis: r.preis ? { betrag: MF.euro(r.preis.cent), einheit: r.preis.einheit, datum: r.preis.datum }
                       : { betrag: "", einheit: "m2" },
      };
    } else {
      const k = kategorie(letzteKategorie()) || kategorien.find((x) => x.fest) || kategorien[0];
      p = { name: "", art: "physisch", kategorie_id: k.id, marke: "", abmessungen: "", link: "", anzahl: "",
            notiz: "", farben: [], preis: { betrag: "", einheit: "m2" }, werte: {}, fotos: [], code: "behalten", version: null };
    }
    original = daten();
    zeichnen();
    if (!inventarNr) $("[data-feld=name]", form).focus();
  }

  // ---------- Zeichnen ----------
  function zeichnen() {
    const k = kategorie(p.kategorie_id);
    const gewechselt = original && inventarNr && p.kategorie_id !== original.kategorie_id;
    form.innerHTML = `
      <section class="card stack">
        <div class="fotos" data-fotos>${zeichneFotos()}</div>
        <div class="foto-knoepfe">
          ${TELEFON ? `<label class="btn">${icon("camera", 20)}<span>${esc(t("produkt.foto_aufnehmen"))}</span>
            <input class="sr-only" type="file" accept="image/*" capture="environment" data-foto-eingabe></label>`
          : `<button class="btn" type="button" data-aktion="kamera" ${kameraDa ? "" : "hidden"}>${icon("camera", 20)}<span>${esc(t("produkt.foto_aufnehmen"))}</span></button>`}
          <label class="btn">${icon("image", 20)}<span>${esc(t("produkt.bild_waehlen"))}</span>
            <input class="sr-only" type="file" accept="image/jpeg,image/png,image/webp" multiple data-foto-eingabe></label>
        </div>
      </section>

      <section class="card stack">
        <div class="segs" role="group">
          ${["physisch", "digital"].map((a) => `<button class="segbtn" type="button" data-art="${a}" aria-pressed="${p.art === a}">${esc(t("produkt.art_" + a))}</button>`).join("")}
        </div>
        <label class="feld"><span>${esc(t("produkt.name"))}</span>
          <input class="eingabe" data-feld="name" value="${esc(p.name)}" maxlength="120" autocomplete="off" required></label>
        <label class="feld"><span>${esc(t("produkt.kategorie"))}</span>
          <select class="eingabe" data-feld="kategorie_id">
            ${kategorien.map((x) => `<option value="${x.id}" ${x.id === p.kategorie_id ? "selected" : ""}>${esc(x.name)}</option>`).join("")}
          </select></label>
        ${gewechselt ? `
          <div class="segs" role="group">
            <button class="segbtn" type="button" data-code="behalten" aria-pressed="${p.code === "behalten"}">${esc(t("produkt.code_behalten", { code: p.code_alt || "" }))}</button>
            <button class="segbtn" type="button" data-code="neu" aria-pressed="${p.code === "neu"}">${esc(t("produkt.code_neu", { praefix: k.praefix }))}</button>
          </div>
          ${Object.keys(p.werte_alt || {}).length ? `<div class="hinweis">${esc(t("produkt.werte_entfallen"))}</div>` : ""}` : ""}
        ${k.filter.map(zeichneFilter).join("")}
      </section>

      <section class="card stack">
        <div class="feld-reihe">
          <label class="feld"><span>${esc(t("produkt.marke"))}</span><input class="eingabe" data-feld="marke" value="${esc(p.marke)}" maxlength="80"></label>
          <label class="feld"><span>${esc(t("produkt.abmessungen"))}</span><input class="eingabe" data-feld="abmessungen" value="${esc(p.abmessungen)}" maxlength="80"></label>
        </div>
        <div class="feld-reihe">
          <label class="feld"><span>${esc(t("produkt.preis"))}</span>
            <span class="preis-zeile"><input class="eingabe num" data-feld="betrag" value="${esc(p.preis.betrag)}" inputmode="decimal" placeholder="0,00">
              <span class="preis-euro">€</span>
              <select class="eingabe" data-feld="einheit" aria-label="${esc(t("produkt.preis_einheit"))}">
                ${EINHEITEN.map((e) => `<option value="${e}" ${e === p.preis.einheit ? "selected" : ""}>${esc(t("einheit." + e))}</option>`).join("")}
              </select></span>
            ${p.preis.datum ? `<span class="sub">${esc(t("produkt.preis_stand", { datum: datum(p.preis.datum) }))}</span>` : ""}
          </label>
          <label class="feld"><span>${esc(t("produkt.anzahl"))}</span><input class="eingabe num" data-feld="anzahl" value="${esc(p.anzahl)}" inputmode="numeric"></label>
        </div>
        <label class="feld"><span>${esc(t("produkt.link"))}</span><input class="eingabe" data-feld="link" value="${esc(p.link)}" inputmode="url" maxlength="500"></label>
        <div class="feld"><span>${esc(t("produkt.farben"))}</span>
          <div class="farben">${FARBEN.map((f) => `
            <button class="farbknopf" type="button" data-farbe="${f}" aria-pressed="${p.farben.includes(f)}" title="${esc(t("farbe." + f))}">
              <span class="farbpunkt farbe-${f}"></span><span>${esc(t("farbe." + f))}</span></button>`).join("")}</div>
        </div>
        <label class="feld"><span>${esc(t("produkt.notiz"))}</span><textarea class="eingabe notiz" data-feld="notiz" rows="3" maxlength="2000">${esc(p.notiz)}</textarea></label>
      </section>

      ${inventarNr ? `<div class="produkt-fuss"><span class="num sub">${esc(p.code_alt || "")}</span><button class="linkbtn" type="button" data-aktion="loeschen">${esc(t("produkt.loeschen"))}</button></div>` : ""}

      <div class="formleiste">
        <a class="btn" href="${zurueck}" data-aktion="abbrechen">${esc(t("produkt.abbrechen"))}</a>
        <button class="btn primary" type="submit">${esc(t("produkt.speichern"))}</button>
      </div>`;
  }

  function zeichneFotos() {
    const gespeichert = (p.fotos || []).filter((f) => !wegFotos.has(f.id)).map((f) => `
      <figure class="foto"><img src="/media/fotos/${esc(f.datei)}-320.webp" alt="" loading="lazy">
        <button class="foto-x" type="button" data-foto-weg="${f.id}" aria-label="${esc(t("produkt.foto_entfernen"))}">${icon("close", 18)}</button></figure>`);
    const wartend = neueFotos.map((f, i) => `
      <figure class="foto"><img src="${f.url}" alt="">
        <button class="foto-x" type="button" data-foto-neu-weg="${i}" aria-label="${esc(t("produkt.foto_entfernen"))}">${icon("close", 18)}</button>
        <button class="foto-x foto-zuschnitt" type="button" data-foto-neu-zuschnitt="${i}" aria-label="${esc(t("zuschnitt.titel"))}" title="${esc(t("zuschnitt.titel"))}">${icon("zuschnitt", 18)}</button></figure>`);
    return [...gespeichert, ...wartend].join("");
  }

  function zeichneFilter(f) {
    const wert = p.werte[f.id];
    const kopf = `<span>${esc(f.name)}</span>`;
    if (f.typ === "mass") {
      return `<label class="feld">${kopf}<span class="mass-zeile">
        <input class="eingabe num" data-wert="${f.id}" value="${esc(wert ?? "")}" inputmode="decimal">
        <span class="sub">${esc(f.einheit)}</span></span></label>`;
    }
    let knoepfe;
    if (f.typ === "janein") {
      knoepfe = [[true, t("produkt.ja")], [false, t("produkt.nein")]].map(([w, text]) =>
        `<button class="pill" type="button" data-janein="${f.id}" data-w="${w}" aria-pressed="${wert === w}">${esc(text)}</button>`).join("");
    } else {
      const gewaehlt = f.typ === "mehrfach" ? (wert || []) : (wert ? [wert] : []);
      knoepfe = f.optionen.map((o) =>
        `<button class="pill" type="button" data-option="${f.id}" data-o="${o.id}" aria-pressed="${gewaehlt.includes(o.id)}">${esc(o.name)}</button>`).join("");
    }
    return `<div class="feld">${kopf}<div class="pills">${knoepfe}</div></div>`;
  }

  // ---------- Eingaben ----------
  form.addEventListener("input", (e) => {
    const el = e.target;
    if (el.dataset.wert) { p.werte[el.dataset.wert] = el.value.trim() === "" ? null : el.value; return; }
    const feld = el.dataset.feld;
    if (!feld) return;
    if (feld === "betrag" || feld === "einheit") p.preis[feld] = el.value;
    else if (feld === "kategorie_id") return;    // „change“ zeichnet neu
    else p[feld] = el.value;
  });

  form.addEventListener("change", (e) => {
    const el = e.target;
    if (el.dataset.feld === "kategorie_id") {
      if (!p.werte_alt) p.werte_alt = original?.werte || {};
      p.kategorie_id = Number(el.value);
      p.werte = {};                          // Filter der neuen Kategorie beginnen leer
      if (inventarNr && p.kategorie_id === original.kategorie_id) p.werte = kopie(original.werte);
      zeichnen();
    }
    if (el.matches("[data-foto-eingabe]")) {
      fotosHinzu([...el.files]);
      el.value = "";
    }
  });

  form.addEventListener("click", async (e) => {
    const b = e.target.closest("button, a");
    if (!b) return;
    if (b.dataset.art) { p.art = b.dataset.art; $$("[data-art]", form).forEach((x) => x.setAttribute("aria-pressed", String(x === b))); return; }
    if (b.dataset.code) { p.code = b.dataset.code; $$("[data-code]", form).forEach((x) => x.setAttribute("aria-pressed", String(x === b))); return; }
    if (b.dataset.farbe) {
      const f = b.dataset.farbe;
      p.farben = p.farben.includes(f) ? p.farben.filter((x) => x !== f) : [...p.farben, f];
      b.setAttribute("aria-pressed", String(p.farben.includes(f)));
      return;
    }
    if (b.dataset.option) {
      const fid = b.dataset.option, oid = Number(b.dataset.o);
      const f = kategorie(p.kategorie_id).filter.find((x) => String(x.id) === fid);
      if (f.typ === "mehrfach") {
        const liste = p.werte[fid] || [];
        p.werte[fid] = liste.includes(oid) ? liste.filter((x) => x !== oid) : [...liste, oid];
      } else {
        p.werte[fid] = p.werte[fid] === oid ? null : oid;     // nochmal tippen = abwählen
      }
      zeichneFilterNeu();
      return;
    }
    if (b.dataset.janein) {
      const w = b.dataset.w === "true";
      p.werte[b.dataset.janein] = p.werte[b.dataset.janein] === w ? null : w;
      zeichneFilterNeu();
      return;
    }
    if (b.dataset.fotoNeuZuschnitt !== undefined) {
      const f = neueFotos[Number(b.dataset.fotoNeuZuschnitt)];
      const z = await MF.zuschneiden(f.datei);
      if (z && z !== f.datei) {
        URL.revokeObjectURL(f.url);
        Object.assign(f, { datei: z, url: URL.createObjectURL(z) });
        $("[data-fotos]", form).innerHTML = zeichneFotos();
      }
      return;
    }
    if (b.dataset.fotoNeuWeg !== undefined) {
      URL.revokeObjectURL(neueFotos[Number(b.dataset.fotoNeuWeg)].url);
      neueFotos.splice(Number(b.dataset.fotoNeuWeg), 1);
      $("[data-fotos]", form).innerHTML = zeichneFotos();
      return;
    }
    if (b.dataset.fotoWeg) {
      wegFotos.add(Number(b.dataset.fotoWeg));
      $("[data-fotos]", form).innerHTML = zeichneFotos();
      return;
    }
    if (b.dataset.aktion === "kamera") { kameraOeffnen(); return; }
    if (b.dataset.aktion === "loeschen") { await loeschen(); return; }
    if (b.dataset.aktion === "abbrechen" && geaendert()) {
      if (!window.confirm(t("allg.ungespeichert"))) { e.preventDefault(); return; }
      original = daten();      // bewusst verworfen: kein zweiter Hinweis beim Verlassen
      neueFotos = [];
      wegFotos.clear();
    }
  });

  // Nur die Auswahlknöpfe neu setzen, ohne Fokus und Eingaben zu verlieren
  function zeichneFilterNeu() {
    $$("[data-option]", form).forEach((b) => {
      const w = p.werte[b.dataset.option];
      const oid = Number(b.dataset.o);
      b.setAttribute("aria-pressed", String(Array.isArray(w) ? w.includes(oid) : w === oid));
    });
    $$("[data-janein]", form).forEach((b) => b.setAttribute("aria-pressed", String(p.werte[b.dataset.janein] === (b.dataset.w === "true"))));
  }

  // ---------- Fotos: zwei Wege, am Desktop auch Ziehen und Einfügen (SPEC 4.5) ----------
  async function fotosHinzu(dateien) {
    // Manche Kameras liefern keinen Dateityp; ob es ein Bild ist, prüft der Server
    let bilder = dateien.filter((f) => !f.type || f.type.startsWith("image/"));
    if (!bilder.length) return;
    // Ein einzelnes Foto gleich zuschneiden (D-027); bei mehreren nicht, das hielte zu lange auf
    if (bilder.length === 1) {
      const z = await MF.zuschneiden(bilder[0]);
      if (!z) return;
      bilder = [z];
    }
    neueFotos.push(...bilder.map((f) => ({ datei: f, url: URL.createObjectURL(f) })));
    $("[data-fotos]", form).innerHTML = zeichneFotos();
  }

  async function hochladen(nr, datei) {
    const fd = new FormData();
    fd.append("foto", datei);
    const res = await fetch(`/api/produkte/${nr}/fotos`, { method: "POST", body: fd, credentials: "same-origin" });
    const d = await res.json().catch(() => ({}));
    if (!res.ok) throw new MF.ApiError(d.fehler?.text || t("allg.fehler"), null, res.status);
    return d;
  }

  // ---------- Kamera am Desktop (nur sichere Verbindung: localhost oder HTTPS, SPEC 8.2) ----------
  async function kameraPruefen() {
    if (TELEFON || !navigator.mediaDevices?.getUserMedia) return;
    try {
      kameraDa = (await navigator.mediaDevices.enumerateDevices()).some((d) => d.kind === "videoinput");
    } catch { kameraDa = false; }
    const b = $("[data-aktion=kamera]", form);
    if (b) b.hidden = !kameraDa;
  }

  // Mehrere Kameras (Laptop, USB, virtuell): Auswahl im Kamerafenster, gemerkt auf diesem Gerät
  const KAMERA = "mf-kamera";
  async function kameraStrom(id) {
    const video = { width: { ideal: 1920 }, height: { ideal: 1440 } };
    if (id) {
      try { return await navigator.mediaDevices.getUserMedia({ video: { ...video, deviceId: { exact: id } } }); } catch { /* abgesteckt → Standard */ }
    }
    return navigator.mediaDevices.getUserMedia({ video });
  }

  async function kameraOeffnen() {
    let gemerkt = null;
    try { gemerkt = localStorage.getItem(KAMERA); } catch { /* ohne Speicher Standardkamera */ }
    let strom;
    try { strom = await kameraStrom(gemerkt); } catch { toast(t("produkt.kamera_fehler"), { fehler: true }); return; }
    // Namen der Kameras kennt der Browser erst nach der Erlaubnis
    const kameras = (await navigator.mediaDevices.enumerateDevices()).filter((d) => d.kind === "videoinput");
    const aktiv = () => strom.getVideoTracks()[0]?.getSettings().deviceId;
    const el = document.createElement("div");
    el.className = "kamera";
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-modal", "true");
    el.innerHTML = `<video autoplay playsinline muted></video>
      <div class="kamera-knoepfe">
        ${kameras.length > 1 ? `<select class="eingabe kamera-wahl" data-k="wahl" aria-label="${esc(t("produkt.kamera_wahl"))}">
          ${kameras.map((k, i) => `<option value="${esc(k.deviceId)}" ${k.deviceId === aktiv() ? "selected" : ""}>${esc(k.label || t("produkt.kamera_n", { n: i + 1 }))}</option>`).join("")}
        </select>` : ""}
        <button class="btn" type="button" data-k="zu">${esc(t("produkt.abbrechen"))}</button>
        <button class="btn primary" type="button" data-k="ausloesen">${icon("camera", 20)}<span>${esc(t("produkt.kamera_ausloesen"))}</span></button>
      </div>`;
    const video = $("video", el);
    video.srcObject = strom;
    const stoppen = () => strom.getTracks().forEach((s) => s.stop());
    const zu = () => { stoppen(); el.remove(); document.removeEventListener("keydown", taste); };
    const taste = (e) => { if (e.key === "Escape") zu(); };
    document.addEventListener("keydown", taste);
    el.addEventListener("change", async (e) => {
      if (e.target.dataset.k !== "wahl") return;
      stoppen();
      try {
        strom = await kameraStrom(e.target.value);
        video.srcObject = strom;
        try { localStorage.setItem(KAMERA, e.target.value); } catch { /* egal */ }
      } catch { toast(t("produkt.kamera_fehler"), { fehler: true }); }
    });
    el.addEventListener("click", (e) => {
      const k = e.target.closest("[data-k]")?.dataset.k;
      if (k === "zu") zu();
      if (k === "ausloesen" && video.videoWidth) {
        const c = document.createElement("canvas");
        c.width = video.videoWidth;
        c.height = video.videoHeight;
        c.getContext("2d").drawImage(video, 0, 0);
        c.toBlob((blob) => { if (blob) fotosHinzu([new File([blob], "kamera.jpg", { type: "image/jpeg" })]); }, "image/jpeg", 0.92);
        zu();
      }
    });
    document.body.appendChild(el);
    $("[data-k=ausloesen]", el).focus();
  }

  document.addEventListener("dragover", (e) => { if (e.dataTransfer?.types.includes("Files")) e.preventDefault(); });
  document.addEventListener("drop", (e) => {
    if (!e.dataTransfer?.files.length) return;
    e.preventDefault();
    fotosHinzu([...e.dataTransfer.files]);
  });
  document.addEventListener("paste", (e) => {
    const dateien = [...(e.clipboardData?.files || [])];
    if (dateien.length) { e.preventDefault(); fotosHinzu(dateien); }
  });

  // ---------- Speichern, Löschen ----------
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (speichert) return;
    speichert = true;
    const knopf = $("[type=submit]", form);
    knopf.disabled = true;
    try {
      const r = inventarNr ? await api("PUT", "/api/produkte/" + inventarNr, daten())
                           : await api("POST", "/api/produkte", daten());
      try { localStorage.setItem(LETZTE, String(p.kategorie_id)); } catch { /* egal */ }
      for (const id of wegFotos) {
        try { await api("DELETE", `/api/produkte/${r.inventar_nr}/fotos/${id}`); } catch (err) { toast(err.message, { fehler: true }); }
      }
      wegFotos.clear();
      if (neueFotos.length) {
        toast(t("produkt.fotos_laden"));
        for (const f of neueFotos) {
          try { await hochladen(r.inventar_nr, f.datei); } catch (err) { toast(err.message, { fehler: true }); }
        }
        neueFotos = [];
      }
      original = daten();      // kein „nicht gespeichert“-Hinweis beim Verlassen
      toastNachher(t("produkt.gespeichert", { code: r.code }));
      location.href = zurueck;
    } catch (err) {
      toast(err.message, { fehler: true });
      if (err.feld) $(`[data-feld="${err.feld}"]`, form)?.focus();
    } finally {
      speichert = false;
      knopf.disabled = false;
    }
  });

  // Endgültig und ohne Rückgängig → hier fragt die App ausdrücklich nach (SPEC 6.2, Produkt löschen)
  async function loeschen() {
    if (!window.confirm(t("produkt.loeschen_frage", { code: p.code_alt, nr: inventarNr }))) return;
    try {
      await api("DELETE", "/api/produkte/" + inventarNr);
      original = daten();
      neueFotos = [];
      toastNachher(t("produkt.geloescht", { code: p.code_alt }));
      location.href = "/bibliothek";
    } catch (err) { toast(err.message, { fehler: true }); }
  }

  window.addEventListener("beforeunload", (e) => { if (p && geaendert()) e.preventDefault(); });

  laden().then(kameraPruefen).catch((err) => toast(err.message, { fehler: true }));
})();
