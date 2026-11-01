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
})();
