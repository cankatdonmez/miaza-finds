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

  return { $, $$, esc, icon, t, api, ApiError, toast };
})();
