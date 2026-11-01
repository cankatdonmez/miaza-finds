// Gewählte Darstellung vor dem ersten Zeichnen setzen (kein Aufblitzen). Gilt je Gerät (SPEC 4.3).
(function () {
  try {
    var t = localStorage.getItem("mf-theme");
    if (t === "dark" || t === "light") document.documentElement.setAttribute("data-theme", t);
  } catch (e) { /* ohne Speicher: Systemeinstellung */ }
})();
