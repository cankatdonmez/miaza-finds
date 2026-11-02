// Produktdetail als ganze Seite (Telefon, QR-Link /p/<Nr>).
(function () {
  const ziel = MF.$("[data-detail]");
  if (!ziel) return;
  MF.api("GET", "/api/produkte/" + ziel.dataset.detail)
    .then((p) => { ziel.innerHTML = MF.detailHtml(p); })
    .catch((err) => MF.toast(err.message, { fehler: true }));
})();
