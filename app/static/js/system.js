// Systembereich (SPEC 6.13, D-006, D-009, D-010). Folgenschwere Schritte: Wirkung zuerst lesen, dann „Ja, ausführen“;
// vor jedem ersetzenden oder löschenden Schritt sichert der Server automatisch.
(function () {
  const { $, esc, t, toast, datum } = MF;
  const ziel = $("[data-system]");
  if (!ziel) return;

  let csrf = null;
  let offen = null;           // welche Rückfrage gerade offen ist

  async function sapi(method, url, body, formular = false) {
    const opts = { method, credentials: "same-origin", headers: { Accept: "application/json" } };
    if (csrf) opts.headers["X-CSRF-Token"] = csrf;
    if (formular) opts.body = body;
    else if (body !== undefined) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
    let res;
    try { res = await fetch(url, opts); } catch { throw new MF.ApiError(t("allg.fehler_netz")); }
    const d = await res.json().catch(() => ({}));
    if (res.status === 401 && url !== "/api/system/anmelden" && url !== "/api/system/vergessen") { csrf = null; start(); }
    if (!res.ok) throw new MF.ApiError(d.fehler?.text || t("allg.fehler"), d.fehler?.feld, res.status);
    return d;
  }

  const zeit = (iso) => (iso ? `${datum(iso.slice(0, 10))} ${iso.slice(11, 16)}` : "");
  const groesse = (b) => (b > 1e6 ? `${(b / 1e6).toLocaleString("de-AT", { maximumFractionDigits: 1 })} MB` : `${Math.ceil(b / 1e3)} kB`);
  const feld = (name, text, typ = "text", auto = "off") =>
    `<label class="feld"><span>${esc(text)}</span><input class="eingabe" name="${name}" type="${typ}" autocomplete="${auto}"></label>`;

  async function start() {
    const s = await sapi("GET", "/api/system/stand");
    csrf = s.csrf;
    if (!s.eingerichtet) return zeigeEinrichten();
    if (!s.angemeldet) return zeigeAnmelden();
    return zeigeBereich();
  }

  // ---------- Einrichten, Anmelden, Passwort vergessen ----------
  function formular(titel, felder, knopf, beiAbsenden, fuss = "") {
    ziel.innerHTML = `<form class="card stack system-form" data-form>
      <h2 class="detail-name">${esc(titel)}</h2>${felder}
      <button class="btn primary" type="submit">${esc(knopf)}</button>${fuss}</form>`;
    const f = $("[data-form]", ziel);
    f.querySelector("input")?.focus();
    f.addEventListener("submit", async (e) => {
      e.preventDefault();
      const daten = Object.fromEntries(new FormData(f));
      try { await beiAbsenden(daten); } catch (err) {
        toast(err.message, { fehler: true });
        if (err.feld) f.querySelector(`[name="${err.feld}"]`)?.focus();
      }
    });
  }

  function zeigeEinrichten() {
    formular(t("system.einrichten"),
      feld("benutzername", t("system.benutzername"), "text", "username") + feld("passwort", t("system.passwort"), "password", "new-password") +
      feld("passwort2", t("system.passwort2"), "password", "new-password"),
      t("system.einrichten"), async (d) => {
        const r = await sapi("POST", "/api/system/einrichten", d);
        csrf = r.csrf;
        zeigeSchluessel(r.schluessel);
      });
  }

  function zeigeAnmelden() {
    formular(t("system.titel"),
      feld("benutzername", t("system.benutzername"), "text", "username") + feld("passwort", t("system.passwort"), "password", "current-password"),
      t("system.anmelden"), async (d) => {
        csrf = (await sapi("POST", "/api/system/anmelden", d)).csrf;
        zeigeBereich();
      }, `<button class="linkbtn" type="button" data-vergessen>${esc(t("system.vergessen"))}</button>`);
    $("[data-vergessen]", ziel).addEventListener("click", zeigeVergessen);
  }

  function zeigeVergessen() {
    formular(t("system.neues_passwort"),
      feld("schluessel", t("system.schluessel")) + feld("passwort", t("system.passwort_neu"), "password", "new-password") +
      feld("passwort2", t("system.passwort2"), "password", "new-password"),
      t("system.neues_passwort"), async (d) => {
        const r = await sapi("POST", "/api/system/vergessen", d);
        csrf = r.csrf;
        zeigeSchluessel(r.schluessel);
      }, `<button class="linkbtn" type="button" data-zurueck>${esc(t("system.zurueck_anmelden"))}</button>`);
    $("[data-zurueck]", ziel).addEventListener("click", zeigeAnmelden);
  }

  // Schlüssel nur einmal zeigen; erst nach „aufbewahrt“ geht es weiter (D-010)
  function zeigeSchluessel(schluessel) {
    ziel.innerHTML = `<div class="card stack system-form">
      <h2 class="detail-name">${esc(t("system.schluessel_titel"))}</h2>
      <p class="sub">${esc(t("system.schluessel_text"))}</p>
      <div class="schluessel num" data-schluessel>${esc(schluessel)}</div>
      <div class="actions">
        <button class="btn" type="button" data-drucken>${esc(t("system.schluessel_drucken"))}</button>
        <button class="btn" type="button" data-datei>${esc(t("system.schluessel_datei"))}</button>
      </div>
      <label class="pruefzeile"><input type="checkbox" data-ok> <span>${esc(t("system.schluessel_ok"))}</span></label>
      <button class="btn primary" type="button" data-weiter disabled>${esc(t("system.weiter"))}</button>
    </div>`;
    $("[data-drucken]", ziel).addEventListener("click", () => window.print());
    $("[data-datei]", ziel).addEventListener("click", () => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([`miaza finds – ${t("system.schluessel")}\n\n${schluessel}\n`], { type: "text/plain" }));
      a.download = "miaza-finds-sicherheitsschluessel.txt";
      a.click();
      URL.revokeObjectURL(a.href);
    });
    $("[data-ok]", ziel).addEventListener("change", (e) => { $("[data-weiter]", ziel).disabled = !e.target.checked; });
    $("[data-weiter]", ziel).addEventListener("click", zeigeBereich);
  }

  // ---------- Bereich ----------
  async function zeigeBereich() {
    let u;
    try { u = await sapi("GET", "/api/system/uebersicht"); } catch (err) { return toast(err.message, { fehler: true }); }
    const w = u.wirkung;
    const sich = u.sicherungen;
    ziel.innerHTML = `
      <section class="card stack">
        <h2 class="abschnitt">${esc(t("system.sicherung"))}</h2>
        <div class="bar">
          <span class="sub">${esc(sich.length ? t("system.letzte", { zeit: zeit(sich[0].zeit) }) : t("system.keine_sicherung"))}</span>
          <span class="spacer"></span>
          <button class="btn primary" type="button" data-aktion="sichern">${esc(t("system.jetzt_sichern"))}</button>
        </div>
        ${sich.length ? `<div class="sicherungen">${sich.map((s) => `
          <div class="sicherung-zeile">
            <span class="zeile-haupt"><span class="num">${esc(zeit(s.zeit))}</span><span class="karte-sub num">${esc(s.name)} · ${esc(groesse(s.groesse))}</span></span>
            <a class="btn" href="/api/system/sicherung/${encodeURIComponent(s.name)}" download>${esc(t("system.herunterladen"))}</a>
            <button class="btn" type="button" data-frage="wiederherstellen:${esc(s.name)}">${esc(t("system.wiederherstellen"))}</button>
          </div>
          ${rueckfrage(`wiederherstellen:${s.name}`, t("system.wirkung_wiederherstellen", { zeit: zeit(s.zeit) }))}`).join("")}</div>` : ""}
        <p class="sub">${esc(t("system.ordner", { ordner: u.ordner }))}</p>
      </section>

      <section class="card stack">
        <h2 class="abschnitt">${esc(t("system.uebernehmen"))}</h2>
        <label class="feld"><span>${esc(t("system.uebernehmen_datei"))}</span><input class="eingabe datei-eingabe" type="file" accept=".zip,application/zip" data-uebernahme-datei></label>
        <label class="feld"><span>${esc(t("system.uebernehmen_pfad"))}</span><input class="eingabe" data-uebernahme-pfad autocomplete="off"></label>
        <div><button class="btn" type="button" data-frage="uebernehmen">${esc(t("system.uebernehmen_los"))}</button></div>
        ${rueckfrage("uebernehmen", t("system.wirkung_uebernehmen"))}
      </section>

      <section class="card stack">
        <h2 class="abschnitt">${esc(t("system.loeschen"))}</h2>
        <div class="actions">
          <button class="btn" type="button" data-frage="produkte">${esc(t("system.produkte_loeschen"))}</button>
          <button class="btn" type="button" data-frage="alles">${esc(t("system.alles_loeschen"))}</button>
        </div>
        ${rueckfrage("produkte", t("system.wirkung_produkte", w))}
        ${rueckfrage("alles", t("system.wirkung_alles", w))}
      </section>

      <section class="card stack">
        <h2 class="abschnitt">${esc(t("system.sicherheit"))}</h2>
        <form class="stack" data-pw-form>
          ${feld("alt", t("system.passwort_alt"), "password", "current-password")}
          ${feld("neu", t("system.passwort_neu"), "password", "new-password")}
          ${feld("neu2", t("system.passwort2"), "password", "new-password")}
          <div><button class="btn" type="submit">${esc(t("system.passwort_aendern"))}</button></div>
        </form>
        <div><button class="btn" type="button" data-frage="schluessel">${esc(t("system.schluessel_erneuern"))}</button></div>
        ${rueckfrage("schluessel", t("system.wirkung_schluessel"))}
      </section>

      <div><button class="btn" type="button" data-aktion="abmelden">${esc(t("system.abmelden"))}</button></div>`;
    offen = null;
  }

  // Wirkung lesen, dann bestätigen – nur hier, weil diese Schritte nicht rückgängig zu machen sind (SPEC 6.13)
  function rueckfrage(name, text) {
    return `<div class="rueckfrage" data-rueckfrage="${esc(name)}" hidden>
      <p>${esc(text)}</p>
      <div class="actions"><button class="btn" type="button" data-aktion="nein">${esc(t("system.abbrechen"))}</button>
      <button class="btn primary" type="button" data-ja="${esc(name)}">${esc(t("system.ja"))}</button></div></div>`;
  }

  ziel.addEventListener("click", async (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    const d = b.dataset;
    if (d.frage) {
      offen = d.frage;
      ziel.querySelectorAll("[data-rueckfrage]").forEach((x) => { x.hidden = x.dataset.rueckfrage !== offen; });
      return;
    }
    if (d.aktion === "nein") { ziel.querySelectorAll("[data-rueckfrage]").forEach((x) => { x.hidden = true; }); return; }
    if (d.aktion === "abmelden") { await sapi("POST", "/api/system/abmelden"); csrf = null; return zeigeAnmelden(); }
    try {
      if (d.aktion === "sichern") {
        b.disabled = true;
        const r = await sapi("POST", "/api/system/sicherung");
        toast(t("system.gesichert", { name: r.name }));
        return zeigeBereich();
      }
      if (!d.ja) return;
      b.disabled = true;
      const [art, name] = d.ja.split(/:(.*)/s);
      if (art === "wiederherstellen") {
        const r = await sapi("POST", "/api/system/wiederherstellen", { name });
        toast(t("system.uebernommen", r));
      } else if (art === "uebernehmen") {
        const datei = $("[data-uebernahme-datei]", ziel).files[0];
        const pfad = $("[data-uebernahme-pfad]", ziel).value.trim();
        let r;
        if (datei) { const fd = new FormData(); fd.append("datei", datei); r = await sapi("POST", "/api/system/uebernehmen", fd, true); }
        else r = await sapi("POST", "/api/system/uebernehmen-pfad", { pfad });
        toast(t("system.uebernommen", r));
      } else if (art === "produkte" || art === "alles") {
        const r = await sapi("POST", "/api/system/loeschen", { was: art });
        toast(t("system.geloescht", { name: r.sicherung_vorher }));
      } else if (art === "schluessel") {
        return zeigeSchluessel((await sapi("POST", "/api/system/schluessel")).schluessel);
      }
      return zeigeBereich();
    } catch (err) {
      toast(err.message, { fehler: true });
      b.disabled = false;
    }
  });

  ziel.addEventListener("submit", async (e) => {
    if (!e.target.matches("[data-pw-form]")) return;
    e.preventDefault();
    try {
      await sapi("POST", "/api/system/passwort", Object.fromEntries(new FormData(e.target)));
      e.target.reset();
      toast(t("system.passwort_geaendert"));
    } catch (err) { toast(err.message, { fehler: true }); }
  });

  start().catch((err) => toast(err.message, { fehler: true }));
})();
