// Scannen (SPEC 4.5, 6.7, D-040). Live-Kamera nur bei sicherer Verbindung (HTTPS, localhost); sonst öffnet
// „Foto aufnehmen“ die Kamera-App und der QR wird aus dem Foto gelesen. Gelesen wird nur das Ende der Adresse
// (…/p/<nr>, …/f/<id>): so bleiben gedruckte Etiketten gültig, auch wenn der Server einmal anders heißt (D-038).
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

  // ---------- Was bedeutet der Inhalt? ----------
  function ziel(text) {
    const m = /\/(p|f)\/(\d+)(?:[/?#]|$)/.exec(String(text).trim());
    if (!m) return null;
    return m[1] === "p" ? `/produkt/${m[2]}` : `/buero?fach=${m[2]}`;
  }

  function gehen(url) {
    if (fertig) return;
    fertig = true;
    if (navigator.vibrate) navigator.vibrate(30);
    stoppen();
    location.href = url;
  }

  function gelesen(text) {
    const url = ziel(text);
    if (url) gehen(url);
    else toast(t("scan.fremd"), { fehler: true });
  }

  // ---------- QR aus einem Bild (Canvas) ----------
  const detektor = "BarcodeDetector" in window ? (() => { try { return new BarcodeDetector({ formats: ["qr_code"] }); } catch { return null; } })() : null;
  const leinwand = document.createElement("canvas");
  const ctx = leinwand.getContext("2d", { willReadFrequently: true });

  async function lesen(quelle, breite, hoehe, max) {
    if (detektor) {
      try {
        const codes = await detektor.detect(quelle);
        if (codes.length) return codes[0].rawValue;
      } catch { /* weiter mit jsQR */ }
    }
    if (!window.jsQR) return null;
    // Klein rechnen: jsQR ist auf ~1000 px schnell und sicher genug, große Fotos machen es nur langsam
    const s = Math.min(1, max / Math.max(breite, hoehe));
    leinwand.width = Math.round(breite * s);
    leinwand.height = Math.round(hoehe * s);
    ctx.drawImage(quelle, 0, 0, leinwand.width, leinwand.height);
    const bild = ctx.getImageData(0, 0, leinwand.width, leinwand.height);
    const code = window.jsQR(bild.data, bild.width, bild.height, { inversionAttempts: "dontInvert" });
    return code ? code.data : null;
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
      const text = await lesen(video, video.videoWidth, video.videoHeight, 640);
      if (text) {
        const url = ziel(text);
        if (url) return gehen(url);
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

  // ---------- Foto (ohne sichere Verbindung, oder wenn die Kamera nicht will) ----------
  $("[data-scan-datei]").addEventListener("change", async (e) => {
    const datei = e.target.files?.[0];
    e.target.value = "";
    if (!datei) return;
    const url = URL.createObjectURL(datei);
    const img = new Image();
    img.onload = async () => {
      // erst mittelgroß, dann größer: kleine QR-Codes auf großen Fotos brauchen mehr Pixel
      let text = await lesen(img, img.naturalWidth, img.naturalHeight, 1000);
      if (!text) text = await lesen(img, img.naturalWidth, img.naturalHeight, 2000);
      URL.revokeObjectURL(url);
      if (text) gelesen(text);
      else toast(t("scan.nichts"), { fehler: true });
    };
    img.onerror = () => { URL.revokeObjectURL(url); toast(t("scan.nichts"), { fehler: true }); };
    img.src = url;
  });

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
    const live = window.isSecureContext && navigator.mediaDevices?.getUserMedia;
    let gemerkt = null;
    try { gemerkt = localStorage.getItem(KAMERA); } catch { /* Standardkamera */ }
    if (live && await starten(gemerkt)) {
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
