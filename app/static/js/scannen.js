// Scannen-Seite (SPEC 4.5, 6.7, D-040, D-041). Live-Kamera nur bei sicherer Verbindung (HTTPS, localhost): der Code
// wird erkannt, sobald er im Bild ist. Sonst „Foto aufnehmen“ (MF.scan.foto, mit Rückmeldung). Tippen geht immer.
// Mit ?fach=<id> ordnet die Seite ein (D-043): jedes gescannte Produkt kommt in das Fach, die Kamera bleibt offen.
(function () {
  const { $, esc, icon, t, api, toast } = MF;
  const rahmen = $("[data-scan-bild]");
  if (!rahmen) return;
  const video = $("video", rahmen);
  const fotoKnopf = $("[data-scan-foto]");
  const kameraWahl = $("[data-scan-kamera]");
  const frage = $("[data-einordnen-frage]");
  const liste = $("[data-eingeordnet]");
  const KAMERA = "mf-kamera";     // gleiche Wahl wie beim Foto im Produktformular
  let strom = null;
  let fertig = false;
  let ziel = null;                // Einordnen: {id, code} des Fachs; null = normales Scannen
  let fragt = false;              // solange eine Frage offen ist, wird nichts Neues verarbeitet
  let zuletztText = "", zuletztZeit = 0;

  function gehen(url) {
    if (fertig) return;
    fertig = true;
    if (navigator.vibrate) navigator.vibrate(30);
    stoppen();
    location.href = url;
  }

  // ---------- Einordnen (D-043) ----------
  async function fachVon(id) {
    const plan = await api("GET", "/api/plan");
    return plan.einheiten.flatMap((e) => e.faecher).find((f) => f.id === id) || null;
  }

  function zielSetzen(f) {
    ziel = { id: f.id, code: f.code };
    MF.einordnen.starten({ id: f.id, code: f.code });   // auch die Produktseiten der Kamera-App zeigen „In … einordnen“
    $("[data-einordnen-kopf]").hidden = false;
    $("[data-einordnen-titel]").textContent = t("einordnen.knopf", { code: f.code });
    $("[data-scan-foto-text]").textContent = t("einordnen.produkt_scannen");
    $(".einordnen-leiste")?.remove();                    // die Leiste wäre hier doppelt
  }

  function zeile(p, text, rueck) {
    const el = document.createElement("div");
    el.className = "zeile eingeordnet-zeile";
    el.innerHTML = `<span class="eingeordnet-haken">${icon("check", 18)}</span>
      <span class="zeile-haupt"><span class="karte-name">${esc(p.name || t("produkt.unbenannt", { nr: p.inventar_nr }))}</span>
      <span class="karte-sub num">${esc(p.code)} · ${esc(text)}</span></span>
      ${rueck ? `<button class="btn" type="button">${esc(t("allg.rueckgaengig"))}</button>` : ""}`;
    if (rueck) {
      el.querySelector("button").addEventListener("click", async (e) => {
        e.target.disabled = true;
        try { await api("POST", `/api/produkte/${p.inventar_nr}/einordnen/zurueck`, rueck); el.remove(); }
        catch (err) { e.target.disabled = false; toast(err.message, { fehler: true }); }
      });
    }
    liste.prepend(el);
  }

  async function einordnen(p) {
    const r = await api("POST", `/api/produkte/${p.inventar_nr}/einordnen`, { fach_id: ziel.id });
    if (navigator.vibrate) navigator.vibrate(30);
    zeile(r.produkt, t("einordnen.erledigt", { code: ziel.code }), r.rueckgaengig);
  }

  // Liegt es schon woanders, entscheidet der Mensch (SPEC 6.7/4)
  function fragen(p) {
    fragt = true;
    frage.hidden = false;
    frage.innerHTML = `<div class="fach-scan-titel">${esc(t("einordnen.liegt_in", { name: p.name || p.code, code: p.platz.code }))}</div>
      <div class="actions">
        <button class="btn primary" type="button" data-antwort="ja">${esc(t("einordnen.hierher", { code: ziel.code }))}</button>
        <button class="btn" type="button" data-antwort="nein">${esc(t("einordnen.ueberspringen"))}</button>
      </div>`;
    frage.onclick = async (e) => {
      const a = e.target.closest("[data-antwort]")?.dataset.antwort;
      if (!a) return;
      frage.hidden = true;
      fragt = false;
      if (a === "ja") { try { await einordnen(p); } catch (err) { toast(err.message, { fehler: true }); } }
    };
  }

  async function behandeln(z) {
    try {
      if (z.art === "fach") {
        if (z.id === ziel.id) return;
        const f = await fachVon(z.id);
        if (!f) return toast(t("fehler.fach_unbekannt"), { fehler: true });
        zielSetzen(f);
        return toast(t("einordnen.ziel_neu", { code: f.code }));
      }
      const p = await api("GET", `/api/produkte/${z.id}`);
      if (p.art !== "physisch") return toast(t("fehler.digital_kein_platz"), { fehler: true });
      if (p.platz?.id === ziel.id && !p.entnahme) return zeile(p, t("einordnen.schon", { code: ziel.code }), null);
      if (p.platz && p.platz.id !== ziel.id) return fragen(p);
      await einordnen(p);
    } catch (err) { toast(err.message, { fehler: true }); }
  }

  // Ein Treffer: beim Einordnen verarbeiten (nicht zweimal hintereinander denselben), sonst hingehen
  async function treffer(z, text) {
    if (!ziel) return gehen(z.url);
    const jetzt = performance.now();
    if (text === zuletztText && jetzt - zuletztZeit < 3000) return;
    zuletztText = text;
    zuletztZeit = jetzt;
    await behandeln(z);
  }

  $("[data-einordnen-fertig]").addEventListener("click", () => {
    MF.einordnen.beenden();
    gehen(`/buero?fach=${ziel.id}`);
  });

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
    if (!fragt && zeit - zuletzt > 180 && video.readyState >= 2 && video.videoWidth) {
      zuletzt = zeit;
      const text = await MF.scan.lesen(video, video.videoWidth, video.videoHeight, 640);
      if (text) {
        const z = MF.scan.ziel(text);
        if (z) await treffer(z, text);
        else { toast(t("scan.fremd"), { fehler: true }); zuletzt = zeit + 2000; }   // fremden Code nicht im Takt melden
      }
    }
    requestAnimationFrame(schleife);
  }

  kameraWahl.addEventListener("change", async () => {
    try { localStorage.setItem(KAMERA, kameraWahl.value); } catch { /* nur Komfort */ }
    if (await starten(kameraWahl.value)) requestAnimationFrame(schleife);
  });

  fotoKnopf.addEventListener("click", () => MF.scan.foto(ziel ? (z) => behandeln(z) : undefined));

  // ---------- Code tippen: „265“, „FL-021-024“ → Produkt; „1.6.4“ → Fach; sonst Suche ----------
  $("[data-scan-code]").addEventListener("submit", async (e) => {
    e.preventDefault();
    const feld = e.target.code;
    const roh = feld.value.trim();
    if (!roh) return;
    const nr = /^\d+$/.test(roh) ? roh : (/^[A-Za-z]{2}-\d+-(\d+)$/.exec(roh) || [])[1];
    if (nr) {
      if (!ziel) return gehen(`/produkt/${Number(nr)}`);
      feld.value = "";
      return behandeln({ art: "produkt", id: Number(nr) });
    }
    if (/^\d+(\.\d+){2}$/.test(roh)) {
      try {
        const plan = await api("GET", "/api/plan");
        const fach = plan.einheiten.flatMap((x) => x.faecher).find((f) => f.code === roh);
        if (!fach) return toast(t("scan.fach_unbekannt", { code: roh }), { fehler: true });
        if (!ziel) return gehen(`/buero?fach=${fach.id}`);
        feld.value = "";
        return behandeln({ art: "fach", id: fach.id });
      } catch (err) { return toast(err.message, { fehler: true }); }
    }
    if (!ziel) gehen(`/bibliothek?q=${encodeURIComponent(roh)}`);
    else toast(t("scan.fremd"), { fehler: true });
  });

  // ---------- Start ----------
  async function los() {
    const fachId = Number(new URLSearchParams(location.search).get("fach")) || null;
    if (fachId && !ziel) {
      try {
        const f = await fachVon(fachId);
        if (f) zielSetzen(f);
        else toast(t("fehler.fach_unbekannt"), { fehler: true });
      } catch (err) { toast(err.message, { fehler: true }); }
    }
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
