// Einstellungen › Dieses Gerät › Darstellung (SPEC 4.3): System · Hell · Dunkel, je Gerät gespeichert.
(function () {
  const knoepfe = document.querySelectorAll("[data-darstellung]");

  function gewaehlt() {
    try { return localStorage.getItem("mf-theme") || "system"; } catch (e) { return "system"; }
  }

  function anwenden(wahl) {
    if (wahl === "system") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", wahl);
    knoepfe.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.darstellung === wahl)));
  }

  knoepfe.forEach((b) => b.addEventListener("click", () => {
    const wahl = b.dataset.darstellung;
    try {
      if (wahl === "system") localStorage.removeItem("mf-theme");
      else localStorage.setItem("mf-theme", wahl);
    } catch (e) { /* ohne Speicher gilt die Wahl nur bis zum Neuladen */ }
    anwenden(wahl);
  }));

  anwenden(gewaehlt());

  // Büro: Fach beim Zurücklegen bestätigen (D-042), gilt für alle Geräte
  const fachKnoepfe = MF.$$("[data-fach-bestaetigen]");
  const fachZeigen = (an) => fachKnoepfe.forEach((b) => b.setAttribute("aria-pressed", String((b.dataset.fachBestaetigen === "1") === an)));
  if (fachKnoepfe.length) {
    MF.api("GET", "/api/einstellungen").then((e) => fachZeigen(e.fach_bestaetigen)).catch(() => {});
    fachKnoepfe.forEach((b) => b.addEventListener("click", async () => {
      try { fachZeigen((await MF.api("PUT", "/api/einstellungen", { fach_bestaetigen: b.dataset.fachBestaetigen === "1" })).fach_bestaetigen); }
      catch (err) { MF.toast(err.message, { fehler: true }); }
    }));
  }

  // Reiter (nur am Desktop sichtbar). Am Telefon gilt immer „Allgemein“ (SPEC 5).
  const reiter = MF.$$("[data-reiter]");
  const schmal = window.matchMedia("(max-width: 899px)");
  function zeigen(name) {
    reiter.forEach((b) => {
      const an = b.dataset.reiter === name;
      b.setAttribute("aria-selected", String(an));
      b.setAttribute("aria-pressed", String(an));
    });
    MF.$$("[data-reiter-inhalt]").forEach((s) => { s.hidden = s.dataset.reiterInhalt !== name; });
  }
  reiter.forEach((b) => b.addEventListener("click", () => zeigen(b.dataset.reiter)));

  // Büroplan: nur die Zahlen; bearbeitet wird auf /plan (SPEC 6.4)
  const zahlen = MF.$("[data-plan-zahlen]");
  if (zahlen) MF.api("GET", "/api/plan").then((p) => {
    zahlen.textContent = MF.t("einstellungen.plan_zahlen", { r: p.raeume.length, e: p.einheiten.length,
      f: p.einheiten.reduce((s, e) => s + e.faecher.length, 0) });
  }).catch(() => {});
  const passend = () => zeigen(schmal.matches ? "allgemein" : "kategorien");
  schmal.addEventListener("change", passend);
  passend();
})();
