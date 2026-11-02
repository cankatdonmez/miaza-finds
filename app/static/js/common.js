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
  function toastNachher(text) {
    try { sessionStorage.setItem("mf-toast", text); } catch { /* ohne Speicher keine Meldung */ }
  }
  try {
    const wartend = sessionStorage.getItem("mf-toast");
    if (wartend) { sessionStorage.removeItem("mf-toast"); toast(wartend); }
  } catch { /* ohne Speicher keine Meldung */ }

  // Datum 2026-11-01 → 01.11.2026, Cent → 1.234,56 (SPEC 8.1)
  const datum = (iso) => (iso ? iso.split("-").reverse().join(".") : "");
  const euro = (cent) => (cent / 100).toLocaleString("de-AT", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return { $, $$, esc, icon, t, api, ApiError, toast, toastNachher, datum, euro };
})();
