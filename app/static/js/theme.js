// Gewählte Darstellung vor dem ersten Zeichnen setzen (kein Aufblitzen). Gilt je Gerät (SPEC 4.3).
(function () {
  try {
    var t = localStorage.getItem("mf-theme");
    if (t === "dark" || t === "light") document.documentElement.setAttribute("data-theme", t);
  } catch (e) { /* ohne Speicher: Systemeinstellung */ }
})();

// Auftakt (SPEC 4.1): Markenbild nur beim Kaltstart (erste Seite dieser Browsersitzung), höchstens 700 ms.
// Ausblenden nach 700 ms (CSS-Überblendung + Zeitgeber) oder sofort beim Antippen. Ohne JS bleibt es verborgen.
(function () {
  var wurdeGezeigt = false;
  try {
    wurdeGezeigt = sessionStorage.getItem("mf-auftakt") === "1";
    if (!wurdeGezeigt) sessionStorage.setItem("mf-auftakt", "1");
  } catch (e) { wurdeGezeigt = true; /* ohne Speicher: nicht zeigen */ }
  if (wurdeGezeigt) return;
  var root = document.documentElement;
  root.classList.add("auftakt-an");
  function weg() {
    root.classList.remove("auftakt-an");
    document.removeEventListener("pointerdown", weg, true);
    document.removeEventListener("keydown", weg, true);
  }
  setTimeout(weg, 700); // sicher auch ohne Animation (Bewegung reduzieren)
  document.addEventListener("pointerdown", weg, true);
  document.addEventListener("keydown", weg, true);
})();
