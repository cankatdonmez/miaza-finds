// Scannen-Seite (SPEC 4.5, 6.7, D-040, D-041). Live-Kamera nur bei sicherer Verbindung (HTTPS, localhost): der Code
// wird erkannt, sobald er im Bild ist. Sonst „Foto aufnehmen“ (MF.scan.foto, mit Rückmeldung). Tippen geht immer.
(function () {
  const { $, esc, t, api, toast } = MF;
  const rahmen = $("[data-scan-bild]");
  if (!rahmen) return;
  const video = $("video", rahmen);
  const fotoKnopf = $("[data-scan-foto]");
  const kameraWahl = $("[data-scan-kamera]");
  const KAMERA = "mf-kamera";     // gleiche Wahl wie beim Foto im Produktformular
  let strom = null;
  let fertig = false;

  function gehen(url) {
    if (fertig) return;
    fertig = true;
    if (navigator.vibrate) navigator.vibrate(30);
    stoppen();
    location.href = url;
  }

  // ---------- Live-Kamera ----------
  function stoppen() {
    if (strom) strom.getTracks().forEach((s) => s.stop());
    strom = null;
  }

  async function starten(id) {
    stoppen();
    const wunsch = { width: { ideal: 1280 }, height: { ideal: 720 } };
    const versuche = id ? [{ ...wunsch, deviceId: { exact: id } }] : [];
    versuche.push({ ...wunsch, facingMode: { ideal: "environment" } });
    for (const v of versuche) {
      try { strom = await navigator.mediaDevices.getUserMedia({ video: v }); break; } catch { /* nächster Versuch */ }
    }
    if (!strom) return false;
    video.srcObject = strom;
    rahmen.hidden = false;
    return true;
  }

  async function kamerasZeigen() {
    const kameras = (await navigator.mediaDevices.enumerateDevices()).filter((d) => d.kind === "videoinput");
    if (kameras.length < 2) return;
    const aktiv = strom?.getVideoTracks()[0]?.getSettings().deviceId;
    kameraWahl.innerHTML = kameras.map((k, i) => `<option value="${esc(k.deviceId)}" ${k.deviceId === aktiv ? "selected" : ""}>${esc(k.label || t("produkt.kamera_n", { n: i + 1 }))}</option>`).join("");
    kameraWahl.hidden = false;
  }

  let zuletzt = 0;
  async function schleife(zeit) {
    if (fertig || !strom) return;
    if (zeit - zuletzt > 180 && video.readyState >= 2 && video.videoWidth) {
      zuletzt = zeit;
      const text = await MF.scan.lesen(video, video.videoWidth, video.videoHeight, 640);
      if (text) {
        const z = MF.scan.ziel(text);
        if (z) return gehen(z.url);
        toast(t("scan.fremd"), { fehler: true });
        zuletzt = zeit + 2000;            // fremden Code nicht im Takt melden
      }
    }
    requestAnimationFrame(schleife);
  }

  kameraWahl.addEventListener("change", async () => {
    try { localStorage.setItem(KAMERA, kameraWahl.value); } catch { /* nur Komfort */ }
    if (await starten(kameraWahl.value)) requestAnimationFrame(schleife);
  });

  fotoKnopf.addEventListener("click", () => MF.scan.foto());

  // ---------- Code tippen: „265“, „FL-021-024“ → Produkt; „1.6.4“ → Fach; sonst Suche ----------
  $("[data-scan-code]").addEventListener("submit", async (e) => {
    e.preventDefault();
    const roh = e.target.code.value.trim();
    if (!roh) return;
    const nr = /^\d+$/.test(roh) ? roh : (/^[A-Za-z]{2}-\d+-(\d+)$/.exec(roh) || [])[1];
    if (nr) return gehen(`/produkt/${Number(nr)}`);
    if (/^\d+(\.\d+){2}$/.test(roh)) {
      try {
        const plan = await api("GET", "/api/plan");
        const fach = plan.einheiten.flatMap((x) => x.faecher).find((f) => f.code === roh);
        if (fach) return gehen(`/buero?fach=${fach.id}`);
        return toast(t("scan.fach_unbekannt", { code: roh }), { fehler: true });
      } catch (err) { return toast(err.message, { fehler: true }); }
    }
    gehen(`/bibliothek?q=${encodeURIComponent(roh)}`);
  });

  // ---------- Start ----------
  async function los() {
    let gemerkt = null;
    try { gemerkt = localStorage.getItem(KAMERA); } catch { /* Standardkamera */ }
    if (MF.scan.liveMoeglich() && await starten(gemerkt)) {
      kamerasZeigen().catch(() => {});
      requestAnimationFrame(schleife);
    } else {
      fotoKnopf.hidden = false;
    }
  }
  // Zurück-Taste (bfcache): Kamera wieder an
  window.addEventListener("pageshow", (e) => { if (e.persisted) { fertig = false; los(); } });
  window.addEventListener("pagehide", stoppen);
  los();
})();
