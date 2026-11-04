// „Wird bearbeitet“ (SPEC 4.9, D-044). MF.bearbeitung.beginnen(art, id, bereich) meldet dem Server, dass dieses Gerät
// den Datensatz bearbeitet. Bearbeitet schon jemand anderes, steht oben ein Streifen und der Bereich ist nur lesbar,
// bis der Hinweis wegfällt. Liefert {ende()} für Wechsel innerhalb der Seite (Kategorien).
(function () {
  const { esc, t, api } = MF;
  const SIGNAL_MS = 30000, NACHFRAGE_MS = 10000;

  // Dieses Gerät, für den Server unterscheidbar; kein Konto, nur eine Zufallskennung im Browser
  function geraet() {
    let g = null;
    try { g = localStorage.getItem("mf-geraet"); } catch { /* ohne Speicher je Seite neu */ }
    if (!g) {
      g = (crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2) + Date.now().toString(36));
      try { localStorage.setItem("mf-geraet", g); } catch { /* egal */ }
    }
    return g;
  }

  function beginnen(art, id, bereich) {
    const schluessel = { art, id, geraet: geraet() };
    let geaendert = false, takt = null, streifen = null, aus = false;
    const tippen = () => { geaendert = true; };

    const ende = () => {
      if (aus) return;
      aus = true;
      clearInterval(takt);
      bereich.removeEventListener("input", tippen, true);
      bereich.removeEventListener("pointerup", tippen, true);
      streifen?.remove();
      bereich.inert = false;
      bereich.classList.remove("nur-lesen");
      // auch beim Verlassen der Seite zuverlässig: sendBeacon wartet nicht auf eine Antwort
      const daten = new Blob([JSON.stringify(schluessel)], { type: "application/json" });
      if (!navigator.sendBeacon?.("/api/bearbeitung/ende", daten)) api("POST", "/api/bearbeitung/ende", schluessel).catch(() => {});
      window.removeEventListener("pagehide", ende);
    };

    function belegt(r) {
      bereich.inert = true;
      bereich.classList.add("nur-lesen");
      if (!streifen) {
        streifen = document.createElement("div");
        streifen.className = "bearbeitet-streifen";
        streifen.setAttribute("role", "status");
        bereich.before(streifen);
      }
      const wer = r.wer || t("bearbeitet.anderes_geraet");
      streifen.innerHTML = `<strong>${esc(t("bearbeitet.titel"))}</strong><span>${esc(t("bearbeitet.wer", { wer, min: r.minuten }))}</span>`;
      clearInterval(takt);
      takt = setInterval(async () => {
        try {
          const s = await api("GET", `/api/bearbeitung?art=${art}&id=${id}&geraet=${encodeURIComponent(schluessel.geraet)}`);
          if (!s.frei) return belegt(s);
          clearInterval(takt);
          // Die anderen haben vielleicht gespeichert: erst neu laden, dann bearbeiten
          streifen.classList.add("frei");
          streifen.innerHTML = `<span>${esc(t("bearbeitet.frei"))}</span><button class="btn" type="button">${esc(t("bearbeitet.neu_laden"))}</button>`;
          streifen.querySelector("button").addEventListener("click", () => location.reload());
        } catch { /* nächster Versuch */ }
      }, NACHFRAGE_MS);
    }

    function halten() {
      bereich.addEventListener("input", tippen, true);
      bereich.addEventListener("pointerup", tippen, true);
      takt = setInterval(async () => {
        try {
          const r = await api("POST", "/api/bearbeitung/signal", { ...schluessel, geaendert });
          geaendert = false;
          // abgelaufen (lange still): einfach neu setzen, solange niemand anderes übernommen hat
          if (!r.frei && r.abgelaufen) {
            const neu = await api("POST", "/api/bearbeitung", { ...schluessel, person_id: MF.geraetPerson() });
            if (!neu.frei) belegt(neu);
          } else if (!r.frei) belegt(r);
        } catch { /* Netz weg: beim nächsten Takt wieder */ }
      }, SIGNAL_MS);
    }

    (async () => {
      try {
        const r = await api("POST", "/api/bearbeitung", { ...schluessel, person_id: MF.geraetPerson() });
        if (aus) return;
        if (r.frei) halten();
        else belegt(r);
      } catch { /* ohne Server-Hinweis bleibt die Versionsprüfung als Schutz */ }
    })();
    window.addEventListener("pagehide", ende);
    return { ende };
  }

  MF.bearbeitung = { beginnen };
})();
