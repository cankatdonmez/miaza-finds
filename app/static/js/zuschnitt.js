// Foto zuschneiden, bevor es hochgeladen wird (D-027): Einzel- und Serienerfassung.
// MF.zuschneiden(datei) → Promise<File | null>; null = verworfen, dieselbe Datei = unverändert („Ganzes Bild“).
// Der Rahmen steht in Anteilen des Fotos (0–1): Ecken und Kanten ziehen, innen verschieben, außerhalb neu aufziehen.
(function () {
  const { esc, icon, t } = MF;
  const MAX = 3000;       // längste Kante des Ergebnisses; der Server rechnet ohnehin auf 2400 px herunter
  const MIN = 0.05;       // kleinster Rahmen in Anteilen des Fotos
  const GRIFFE = ["nw", "n", "ne", "e", "se", "s", "sw", "w"];
  const klemmen = (v, a, b) => Math.min(Math.max(v, a), b);

  // Geht etwas schief, kommt das Foto unbeschnitten durch: ein Foto darf nie verloren gehen
  MF.zuschneiden = async (datei) => {
    try { return await zuschneiden(datei); } catch { document.querySelector(".zuschnitt")?.remove(); return datei; }
  };

  async function zuschneiden(datei) {
    // Das Foto nur einmal dekodieren: als <img> für die Anzeige und als Quelle des Zuschnitts. Kamerafotos haben
    // 12–50 Megapixel; eine zweite Kopie (createImageBitmap) sprengte am Telefon den Speicher und lud die Seite neu.
    const url = URL.createObjectURL(datei);
    const bild = new Image();
    bild.src = url;
    try { await bild.decode(); } catch { URL.revokeObjectURL(url); return datei; }
    const B = bild.naturalWidth, H = bild.naturalHeight;   // schon nach EXIF gedreht (image-orientation: from-image)
    let r = { x: 0, y: 0, w: 1, h: 1 };

    const el = document.createElement("div");
    el.className = "zuschnitt";
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-modal", "true");
    el.setAttribute("aria-label", t("zuschnitt.titel"));
    el.innerHTML = `
      <div class="zuschnitt-kopf">
        <button class="iconbtn" type="button" data-z="zu" aria-label="${esc(t("zuschnitt.verwerfen"))}" title="${esc(t("zuschnitt.verwerfen"))}">${icon("close")}</button>
        <span>${esc(t("zuschnitt.titel"))}</span></div>
      <div class="zuschnitt-flaeche" data-flaeche>
        <div class="zuschnitt-bild" data-bild>
          <div class="zuschnitt-maske"><div class="zuschnitt-loch" data-loch></div></div>
          <div class="zuschnitt-rahmen" data-g="m">${GRIFFE.map((g) => `<span class="zuschnitt-griff g-${g}" data-g="${g}"></span>`).join("")}</div>
        </div></div>
      <div class="zuschnitt-knoepfe">
        <button class="btn" type="button" data-z="ganz">${esc(t("zuschnitt.ganz"))}</button>
        <button class="btn primary" type="button" data-z="ok">${esc(t("zuschnitt.ok"))}</button></div>`;
    const flaeche = el.querySelector("[data-flaeche]"), bildEl = el.querySelector("[data-bild]"), rahmen = el.querySelector("[data-g=m]"), loch = el.querySelector("[data-loch]");
    bild.alt = "";
    bildEl.prepend(bild);

    // Foto so groß wie möglich, im Seitenverhältnis
    const einpassen = () => {
      const st = getComputedStyle(flaeche);
      const breite = flaeche.clientWidth - parseFloat(st.paddingLeft) - parseFloat(st.paddingRight);
      const hoehe = flaeche.clientHeight - parseFloat(st.paddingTop) - parseFloat(st.paddingBottom);
      const k = Math.min(breite / B, hoehe / H);
      bildEl.style.width = `${B * k}px`;
      bildEl.style.height = `${H * k}px`;
    };
    // Abdunkeln (in der Maske, auf das Foto beschnitten) und Rahmen mit Griffen (darf über den Rand ragen) liegen gleich
    const zeichnen = () => {
      const lage = `left:${r.x * 100}%;top:${r.y * 100}%;width:${r.w * 100}%;height:${r.h * 100}%`;
      rahmen.style.cssText = lage;
      loch.style.cssText = lage;
    };
    const beobachter = new ResizeObserver(einpassen);

    // ---------- Ziehen ----------
    let zug = null;
    const anteil = (e) => {
      const b = bildEl.getBoundingClientRect();
      return [klemmen((e.clientX - b.left) / b.width, 0, 1), klemmen((e.clientY - b.top) / b.height, 0, 1)];
    };
    bildEl.addEventListener("pointerdown", (e) => {
      let g = e.target.closest("[data-g]")?.dataset.g;
      // Rahmen über dem ganzen Foto: Ziehen im Inneren zieht einen neuen Rahmen auf
      if (g === "m" && r.w > 0.996 && r.h > 0.996) g = null;
      const p = anteil(e);
      zug = g ? { g, p, r: { ...r } } : { g: "neu", p };
      bildEl.setPointerCapture(e.pointerId);
      e.preventDefault();
    });
    bildEl.addEventListener("pointermove", (e) => {
      if (!zug) return;
      const p = anteil(e);
      if (zug.g === "neu") {
        // außerhalb des Rahmens: neuen Rahmen aufziehen
        const [x1, y1] = zug.p, [x2, y2] = p;
        if (Math.abs(x2 - x1) < MIN || Math.abs(y2 - y1) < MIN) return;
        r = { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1) };
        return zeichnen();
      }
      const dx = p[0] - zug.p[0], dy = p[1] - zug.p[1], a = zug.r;
      if (zug.g === "m") {
        r = { ...a, x: klemmen(a.x + dx, 0, 1 - a.w), y: klemmen(a.y + dy, 0, 1 - a.h) };
        return zeichnen();
      }
      let [l, o, re, u] = [a.x, a.y, a.x + a.w, a.y + a.h];
      if (zug.g.includes("w")) l = klemmen(l + dx, 0, re - MIN);
      if (zug.g.includes("e")) re = klemmen(re + dx, l + MIN, 1);
      if (zug.g.includes("n")) o = klemmen(o + dy, 0, u - MIN);
      if (zug.g.includes("s")) u = klemmen(u + dy, o + MIN, 1);
      r = { x: l, y: o, w: re - l, h: u - o };
      zeichnen();
    });
    const loslassen = () => { zug = null; };
    bildEl.addEventListener("pointerup", loslassen);
    bildEl.addEventListener("pointercancel", loslassen);

    // ---------- Ergebnis ----------
    const ergebnis = await new Promise((fertig) => {
      const taste = (e) => { if (e.key === "Escape") fertig(null); if (e.key === "Enter") fertig("ok"); };
      document.addEventListener("keydown", taste);
      el.addEventListener("click", (e) => {
        const z = e.target.closest("[data-z]")?.dataset.z;
        if (z === "zu") fertig(null);
        if (z === "ganz") fertig("ganz");
        if (z === "ok") fertig("ok");
      });
      el.aufraeumen = () => document.removeEventListener("keydown", taste);
      document.body.appendChild(el);
      beobachter.observe(flaeche);
      einpassen();
      zeichnen();
      el.querySelector("[data-z=ok]").focus();
    });
    el.aufraeumen();
    beobachter.disconnect();
    el.remove();
    URL.revokeObjectURL(url);

    const ganz = r.x < 0.002 && r.y < 0.002 && r.w > 0.996 && r.h > 0.996;
    if (ergebnis === null) return null;
    if (ergebnis === "ganz" || ganz) return datei;
    const sx = r.x * B, sy = r.y * H, sw = r.w * B, sh = r.h * H;
    const k = Math.min(1, MAX / Math.max(sw, sh));
    const c = document.createElement("canvas");
    c.width = Math.round(sw * k);
    c.height = Math.round(sh * k);
    c.getContext("2d").drawImage(bild, sx, sy, sw, sh, 0, 0, c.width, c.height);
    const blob = await new Promise((ok) => c.toBlob(ok, "image/jpeg", 0.9));
    if (!blob) return datei;
    return new File([blob], (datei.name || "foto").replace(/\.\w+$/, "") + "-zuschnitt.jpg", { type: "image/jpeg" });
  }
})();
