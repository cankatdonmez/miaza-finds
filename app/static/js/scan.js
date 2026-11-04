// Scan-Kern für alle Seiten (D-040, D-041): was ein QR bedeutet, QR aus Bild oder Video lesen, und der Foto-Weg
// ohne HTTPS mit sichtbarer Rückmeldung. jsQR (250 KB) wird erst geladen, wenn wirklich gelesen wird.
(function () {
  const { esc, icon, t, api } = MF;

  // Nur das Ende der Adresse zählt (…/p/<nr>, …/f/<id>): der Servername darf sich ändern (D-038)
  function ziel(text) {
    const m = /\/(p|f)\/(\d+)(?:[/?#]|$)/.exec(String(text || "").trim());
    if (!m) return null;
    return m[1] === "p" ? { art: "produkt", id: Number(m[2]), url: `/produkt/${m[2]}` }
                        : { art: "fach", id: Number(m[2]), url: `/buero?fach=${m[2]}` };
  }

  // Live-Kamera gibt der Browser nur bei sicherer Verbindung (HTTPS, localhost) her (SPEC 8.2)
  const liveMoeglich = () => window.isSecureContext && !!navigator.mediaDevices?.getUserMedia;

  let jsqr = null;
  function jsqrLaden() {
    if (window.jsQR) return Promise.resolve();
    jsqr = jsqr || new Promise((ok, fehler) => {
      const s = document.createElement("script");
      s.src = "/static/vendor/jsQR.js?v=" + (document.querySelector('meta[name="app-stand"]')?.content || "");
      s.onload = ok;
      s.onerror = () => { jsqr = null; fehler(new Error(t("allg.fehler"))); };
      document.head.appendChild(s);
    });
    return jsqr;
  }

  const detektor = "BarcodeDetector" in window ? (() => { try { return new BarcodeDetector({ formats: ["qr_code"] }); } catch { return null; } })() : null;
  const leinwand = document.createElement("canvas");
  const ctx = leinwand.getContext("2d", { willReadFrequently: true });

  // Text des ersten QR im Bild/Video, sonst null. max = längste Kante, auf die verkleinert wird (jsQR ist dann schnell)
  async function lesen(quelle, breite, hoehe, max) {
    if (detektor) {
      try {
        const codes = await detektor.detect(quelle);
        if (codes.length) return codes[0].rawValue;
      } catch { /* weiter mit jsQR */ }
    }
    await jsqrLaden();
    const s = Math.min(1, max / Math.max(breite, hoehe));
    leinwand.width = Math.round(breite * s);
    leinwand.height = Math.round(hoehe * s);
    ctx.drawImage(quelle, 0, 0, leinwand.width, leinwand.height);
    const bild = ctx.getImageData(0, 0, leinwand.width, leinwand.height);
    const code = window.jsQR(bild.data, bild.width, bild.height, { inversionAttempts: "dontInvert" });
    return code ? code.data : null;
  }

  // ---------- Foto-Weg mit Rückmeldung (D-041) ----------
  let schicht = null;
  function zeigen({ bild, text, fehler = false, knoepfe = "" }) {
    if (!schicht) {
      schicht = document.createElement("div");
      schicht.className = "scan-schicht";
      schicht.setAttribute("role", "dialog");
      schicht.setAttribute("aria-modal", "true");
      document.body.appendChild(schicht);
    }
    schicht.innerHTML = `
      ${bild ? `<img class="scan-schicht-bild" src="${bild}" alt="">` : ""}
      <div class="scan-schicht-text${fehler ? " fehler" : ""}" role="status">${text}</div>
      ${knoepfe ? `<div class="scan-schicht-knoepfe">${knoepfe}</div>` : ""}`;
  }
  function schliessen() { schicht?.remove(); schicht = null; }

  // Öffnet die Kamera-App (muss aus einem Tippen heraus aufgerufen werden). beiTreffer(ziel) übernimmt;
  // ohne beiTreffer wird kurz gezeigt, was gefunden wurde, und dorthin gewechselt.
  function foto(beiTreffer) {
    const eingabe = document.createElement("input");
    eingabe.type = "file";
    eingabe.accept = "image/*";
    eingabe.setAttribute("capture", "environment");
    eingabe.addEventListener("change", () => {
      const datei = eingabe.files?.[0];
      if (datei) auswerten(datei, beiTreffer);
    });
    eingabe.click();
  }

  async function auswerten(datei, beiTreffer) {
    const url = URL.createObjectURL(datei);
    zeigen({ bild: url, text: esc(t("scan.liest")) });
    let text = null;
    try {
      const img = new Image();
      img.src = url;
      await img.decode();
      // erst mittelgroß, dann größer: ein kleiner QR auf einem großen Foto braucht mehr Pixel
      text = await lesen(img, img.naturalWidth, img.naturalHeight, 1000)
        || await lesen(img, img.naturalWidth, img.naturalHeight, 2000);
    } catch { text = null; }
    const z = ziel(text);
    if (!z) return misslungen(url, t(text ? "scan.fremd" : "scan.nichts"), beiTreffer);
    if (navigator.vibrate) navigator.vibrate(30);
    if (beiTreffer) { schliessen(); URL.revokeObjectURL(url); return beiTreffer(z); }
    try {
      zeigen({ bild: url, text: `${icon("check", 22)}<span>${esc(await name(z))}</span>` });
      setTimeout(() => { location.href = z.url; }, 500);
    } catch (err) { misslungen(url, err.message, beiTreffer); }
  }

  // Was der Code meint, in Worten: Produktname mit Code, oder Fach mit Code
  async function name(z) {
    if (z.art === "produkt") {
      const p = await api("GET", `/api/produkte/${z.id}`);
      return `${p.name || t("produkt.unbenannt", { nr: p.inventar_nr })} · ${p.code}`;
    }
    const plan = await api("GET", "/api/plan");
    const f = plan.einheiten.flatMap((e) => e.faecher).find((x) => x.id === z.id);
    if (!f) throw new Error(t("fehler.fach_unbekannt"));
    return t("scan.fach", { code: f.code });
  }

  function misslungen(url, text, beiTreffer) {
    zeigen({ bild: url, text: esc(text), fehler: true, knoepfe: `
      <button class="btn primary" type="button" data-scan-nochmal>${icon("camera", 20)}<span>${esc(t("scan.nochmal"))}</span></button>
      ${beiTreffer ? "" : `<a class="btn" href="/scannen">${esc(t("scan.code"))}</a>`}
      <button class="btn" type="button" data-scan-zu>${esc(t("scan.schliessen"))}</button>` });
    schicht.querySelector("[data-scan-nochmal]").addEventListener("click", () => { schliessen(); URL.revokeObjectURL(url); foto(beiTreffer); });
    schicht.querySelector("[data-scan-zu]").addEventListener("click", () => { schliessen(); URL.revokeObjectURL(url); });
  }

  // Unten im Menü: ohne Live-Kamera öffnet „Scannen“ gleich die Kamera, ohne Zwischenseite (D-041)
  document.addEventListener("click", (e) => {
    const a = e.target.closest(".leiste-scan");
    if (!a || liveMoeglich()) return;
    e.preventDefault();
    foto();
  });

  // Live-Kamera in ein <video> (Rückkamera, zuletzt gewählte Kamera zuerst); beiTreffer(ziel) kommt einmal,
  // fremde Codes melden sich höchstens alle 2 s. Liefert stop() oder null, wenn keine Kamera aufgeht.
  async function kamera(video, beiTreffer) {
    if (!liveMoeglich()) return null;
    let gemerkt = null;
    try { gemerkt = localStorage.getItem("mf-kamera"); } catch { /* Standardkamera */ }
    const wunsch = { width: { ideal: 1280 }, height: { ideal: 720 } };
    const versuche = [...(gemerkt ? [{ ...wunsch, deviceId: { exact: gemerkt } }] : []), { ...wunsch, facingMode: { ideal: "environment" } }];
    let strom = null;
    for (const v of versuche) {
      try { strom = await navigator.mediaDevices.getUserMedia({ video: v }); break; } catch { /* nächster Versuch */ }
    }
    if (!strom) return null;
    video.srcObject = strom;
    let aus = false;
    let zuletzt = 0;
    const stop = () => { aus = true; strom.getTracks().forEach((s) => s.stop()); };
    const schleife = async (zeit) => {
      if (aus || !video.isConnected) return stop();
      if (zeit - zuletzt > 180 && video.readyState >= 2 && video.videoWidth) {
        zuletzt = zeit;
        const text = await lesen(video, video.videoWidth, video.videoHeight, 640);
        const z = ziel(text);
        if (z && !aus) {
          if (navigator.vibrate) navigator.vibrate(30);
          stop();
          return beiTreffer(z);
        }
        if (text) { MF.toast(t("scan.fremd"), { fehler: true }); zuletzt = zeit + 2000; }
      }
      requestAnimationFrame(schleife);
    };
    requestAnimationFrame(schleife);
    return stop;
  }

  MF.scan = { ziel, lesen, liveMoeglich, foto, kamera };
})();
