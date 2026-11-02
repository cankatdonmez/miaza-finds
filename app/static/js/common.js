/* Gemeinsame Bausteine (wie ZE in miaza counts): DOM, Texte, API, Toast. */
"use strict";

const MF = (() => {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const icon = (name, size = 22) =>
    `<svg class="icon" width="${size}" height="${size}" aria-hidden="true"><use href="#i-${name}"/></svg>`;

  // ---------- Texte (Wörterbuch aus app/texte.py) ----------
  const TEXTE = JSON.parse($("#texte")?.textContent || "{}");
  function t(schluessel, werte) {
    // Einzahl wie in app/texte.py: bei n == 1 der Schlüssel mit „_eins“, wenn es ihn gibt
    if (werte && werte.n === 1 && TEXTE[schluessel + "_eins"] !== undefined) schluessel += "_eins";
    const text = TEXTE[schluessel];
    if (text === undefined) { console.error("Text fehlt:", schluessel); return schluessel; }
    return werte ? text.replace(/\{(\w+)\}/g, (_, k) => String(werte[k] ?? "")) : text;
  }

  // ---------- API ----------
  class ApiError extends Error {
    constructor(text, feld, status) { super(text); this.feld = feld; this.status = status; }
  }

  async function api(method, url, body) {
    const opts = { method, headers: { Accept: "application/json" }, credentials: "same-origin" };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    let res;
    try {
      res = await fetch(url, opts);
    } catch {
      throw new ApiError(t("allg.fehler_netz"));
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const f = data.fehler || {};
      throw new ApiError(f.text || t("allg.fehler"), f.feld, res.status);
    }
    return data;
  }

  // ---------- Toast (SPEC 4.5: kurz, am Rand, bei schnellen Aktionen „Rückgängig“) ----------
  let toastTimer;
  function toast(text, { fehler = false, rueckgaengig } = {}) {
    $(".toast")?.remove();
    const el = document.createElement("div");
    el.className = "toast" + (fehler ? " fehler" : "");
    el.setAttribute("role", fehler ? "alert" : "status");
    el.innerHTML = `<span>${esc(text)}</span>`;
    if (rueckgaengig) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "toast-btn";
      b.textContent = t("allg.rueckgaengig");
      b.addEventListener("click", () => { el.remove(); rueckgaengig(); });
      el.appendChild(b);
    }
    document.body.appendChild(el);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.remove(), fehler ? 5000 : rueckgaengig ? 7000 : 2400);
  }

  // Meldung, die nach einem Seitenwechsel erscheint (z. B. „Gespeichert“ beim Zurück zur Bibliothek)
  // rueckgaengig: {methode, url, daten} – ein API-Aufruf, der die Änderung zurücknimmt; danach wird neu geladen
  function toastNachher(text, rueckgaengig = null) {
    try { sessionStorage.setItem("mf-toast", JSON.stringify({ text, rueckgaengig })); } catch { /* ohne Speicher keine Meldung */ }
  }
  try {
    const wartend = sessionStorage.getItem("mf-toast");
    if (wartend) {
      sessionStorage.removeItem("mf-toast");
      const { text, rueckgaengig: r } = JSON.parse(wartend);
      toast(text, r ? {
        rueckgaengig: async () => {
          try { await api(r.methode, r.url, r.daten); location.reload(); } catch (err) { toast(err.message, { fehler: true }); }
        },
      } : {});
    }
  } catch { /* ohne Speicher keine Meldung */ }

  // Datum 2026-11-01 → 01.11.2026, Cent → 1.234,56 (SPEC 8.1)
  const datum = (iso) => (iso ? iso.split("-").reverse().join(".") : "");
  const euro = (cent) => (cent / 100).toLocaleString("de-AT", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  // ---------- „Hier einordnen“ (D-016): dieses Gerät ordnet 30 Minuten lang in ein Fach ein ----------
  const EINORDNEN = "mf-einordnen";
  const DAUER_MS = 30 * 60 * 1000;
  const einordnen = {
    aktiv() {
      try {
        const m = JSON.parse(localStorage.getItem(EINORDNEN) || "null");
        if (m && m.bis > Date.now()) return m;
        localStorage.removeItem(EINORDNEN);
      } catch { /* ohne Speicher kein Modus */ }
      return null;
    },
    starten(fach) {
      try { localStorage.setItem(EINORDNEN, JSON.stringify({ fach_id: fach.id, code: fach.code, bis: Date.now() + DAUER_MS })); } catch { /* egal */ }
      einordnenLeiste();
    },
    // jede Einordnung verlängert den Modus
    verlaengern() { const m = einordnen.aktiv(); if (m) einordnen.starten({ id: m.fach_id, code: m.code }); },
    beenden() { try { localStorage.removeItem(EINORDNEN); } catch { /* egal */ } einordnenLeiste(); },
  };
  function einordnenLeiste() {
    $(".einordnen-leiste")?.remove();
    const m = einordnen.aktiv();
    const ort = $(".inhalt");
    if (!m || !ort) return;
    const el = document.createElement("div");
    el.className = "einordnen-leiste";
    el.innerHTML = `${icon("pin", 20)}<span>${esc(t("einordnen.leiste", { code: m.code }))}</span>
      <button class="iconbtn" type="button" aria-label="${esc(t("einordnen.beenden"))}" title="${esc(t("einordnen.beenden"))}">${icon("close", 20)}</button>`;
    $("button", el).addEventListener("click", () => einordnen.beenden());
    ort.prepend(el);
  }
  einordnenLeiste();

  // ---------- Foto einer Einheit mit ihren Fächern (Büro; D-026, wie die Demo) ----------
  // Fächer sind unsichtbare Tastflächen; jedes trägt oben links eine Marke „Code · Anzahl“. Das Spotlicht ist ein
  // Rahmen um das Fach (Begrenzungsrechteck, Punkte in % des Fotos), der von Fach zu Fach gleitet: gewählt = dunkel und
  // pulsierend, Zeiger darüber = Vorschau. Nach dem Einsetzen ins DOM MF.fotoBeleben(rahmen) aufrufen.
  const kasten = (punkte) => {
    const xs = punkte.map((p) => p[0]), ys = punkte.map((p) => p[1]);
    return { x: Math.min(...xs), y: Math.min(...ys), w: Math.max(...xs) - Math.min(...xs), h: Math.max(...ys) - Math.min(...ys) };
  };
  const lage = (k) => `left:${k.x}%;top:${k.y}%;width:${k.w}%;height:${k.h}%`;
  let letzterSpot = null;          // dort beginnt die Gleitbewegung beim nächsten Zeichnen

  function fotoMitFaechern(e, gewaehltesFach) {
    if (!e.foto) return `<div class="buero-foto leer"><span class="sub">${esc(t("buero.kein_foto"))}</span></div>`;
    const h = (100 * e.foto_hoehe) / e.foto_breite;
    const pfad = (punkte) => "M" + punkte.map(([x, y]) => `${x} ${(y * h) / 100}`).join("L") + "Z";
    const flaechen = e.faecher.map((f) => `<path d="${pfad(f.punkte)}" class="foto-fach" data-fach="${f.id}"
      data-kasten="${Object.values(kasten(f.punkte)).join(",")}"><title>${esc(f.code)}</title></path>`).join("");
    const marken = e.faecher.map((f) => {
      const k = kasten(f.punkte);
      return `<span class="foto-marke${f.produkte ? "" : " leer"}${f.id === gewaehltesFach ? " gewaehlt" : ""}" data-marke="${f.id}"
        style="left:calc(${k.x}% + 4px);top:calc(${k.y}% + 4px)">${esc(f.code)}${f.produkte ? " · " + f.produkte : ""}</span>`;
    }).join("");
    const sf = gewaehltesFach && e.faecher.find((f) => f.id === gewaehltesFach);
    return `<div class="buero-foto${sf ? " mit-spot" : ""}" style="aspect-ratio:${e.foto_breite}/${e.foto_hoehe}"
        ${sf ? `data-spot="${Object.values(kasten(sf.punkte)).join(",")}"` : ""}>
      <img src="/media/einheiten/${esc(e.foto)}-960.webp" alt="">
      <svg viewBox="0 0 100 ${h}" preserveAspectRatio="none">${flaechen}</svg>
      <div class="foto-spot${sf ? " gewaehlt" : ""}" ${sf ? `data-spot-fach="${sf.id}"` : ""}></div>${marken}</div>`;
  }

  // Spotlicht setzen: von der letzten Lage zur neuen gleiten; Marken außerhalb des Spots treten zurück
  function spotSetzen(rahmen, k, art, fachId) {
    const spot = rahmen.querySelector(".foto-spot");
    spot.className = "foto-spot" + (art ? " " + art : "");
    if (k) { spot.style.cssText = lage(k); letzterSpot = k; }
    rahmen.classList.toggle("mit-spot", !!art);
    rahmen.querySelectorAll("[data-marke]").forEach((m) => m.classList.toggle("im-spot", !!art && Number(m.dataset.marke) === fachId));
  }
  const kastenAus = (s) => { const [x, y, w, h] = s.split(",").map(Number); return { x, y, w, h }; };

  function fotoBeleben(bereich) {
    const rahmen = bereich.querySelector(".buero-foto:not(.leer)");
    if (!rahmen) return;
    const ziel = rahmen.dataset.spot && kastenAus(rahmen.dataset.spot);
    const gewaehlt = ziel ? Number(rahmen.querySelector(".foto-spot").dataset.spotFach) : null;
    if (ziel && letzterSpot) {
      // erst an der alten Stelle zeigen, im nächsten Bild an die neue gleiten
      spotSetzen(rahmen, letzterSpot, "gewaehlt", gewaehlt);
      requestAnimationFrame(() => requestAnimationFrame(() => spotSetzen(rahmen, ziel, "gewaehlt", gewaehlt)));
    } else if (ziel) {
      spotSetzen(rahmen, ziel, "gewaehlt", gewaehlt);
    }
    // Vorschau mit dem Zeiger (nur wo es einen Zeiger gibt), solange kein Fach gewählt ist
    if (ziel || !matchMedia("(hover: hover)").matches) return;
    rahmen.addEventListener("pointerover", (ev) => {
      const f = ev.target.closest("[data-kasten]");
      if (f) spotSetzen(rahmen, kastenAus(f.dataset.kasten), "vorschau", Number(f.dataset.fach));
    });
    rahmen.addEventListener("pointerleave", () => spotSetzen(rahmen, null, "", null));
  }

  return { $, $$, esc, icon, t, api, ApiError, toast, toastNachher, datum, euro, einordnen, fotoMitFaechern, fotoBeleben };
})();
