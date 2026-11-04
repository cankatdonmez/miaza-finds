// Sammlungen (SPEC 6.8, D-047): Liste mit „Neue Sammlung“ und Detail mit Produktzeilen.
// Änderungen gelten sofort; Entfernen mit „Rückgängig“ statt Rückfrage.
(function () {
  const { $, esc, icon, t, api, toast } = MF;
  const listeEl = $("[data-sammlungen]");
  const detailEl = $("[data-sammlung]");
  const name = (p) => p.name || t("produkt.unbenannt", { nr: p.inventar_nr });

  // ---------- Liste ----------
  if (listeEl) {
    let sammlungen = [];
    let neu = "";

    const zeichnen = () => {
      listeEl.innerHTML = `
        <form class="card sammlung-neu" data-neu-form>
          <input class="eingabe" data-neu value="${esc(neu)}" maxlength="60" placeholder="${esc(t("sammlungen.neu"))}" aria-label="${esc(t("sammlungen.neu"))}" enterkeyhint="done">
          <button class="btn primary" type="submit" ${neu.trim() ? "" : "disabled"}>${icon("plus", 20)}<span>${esc(t("sammlungen.anlegen"))}</span></button>
        </form>
        ${sammlungen.length ? `<div class="card zeilen">${sammlungen.map((s) => `
          <a class="zeile" href="/sammlungen/${s.id}"><span class="zeile-haupt"><span class="karte-name">${esc(s.name)}</span>
            <span class="karte-sub">${esc(t("sammlungen.anzahl", { n: s.anzahl }))}</span></span>${icon("right", 18)}</a>`).join("")}</div>`
          : `<div class="card leer">${esc(t("sammlungen.leer"))}</div>`}`;
    };

    listeEl.addEventListener("input", (e) => {
      if (!e.target.matches("[data-neu]")) return;
      neu = e.target.value;
      $("button[type=submit]", listeEl).disabled = !neu.trim();
    });
    listeEl.addEventListener("submit", async (e) => {
      e.preventDefault();
      const n = neu.trim();
      if (!n) return;
      try {
        const r = await api("POST", "/api/sammlungen", { name: n });
        location.href = `/sammlungen/${r.id}`;
      } catch (err) { toast(err.message, { fehler: true }); }
    });
    api("GET", "/api/sammlungen").then((r) => { sammlungen = r.sammlungen; zeichnen(); })
      .catch((err) => toast(err.message, { fehler: true }));
    zeichnen();
  }

  // ---------- Detail ----------
  if (detailEl) {
    const id = Number(detailEl.dataset.sammlung);
    let s = null;

    const zeile = (p) => `<div class="zeile">
      <a class="zeile-link" href="/produkt/${p.inventar_nr}">
        ${p.foto ? `<img class="zeile-img" src="/media/fotos/${esc(p.foto)}-320.webp" alt="" loading="lazy">` : `<span class="zeile-img leer-bild">${icon("image", 24)}</span>`}
        <span class="zeile-haupt"><span class="karte-name">${esc(name(p))}</span><span class="karte-sub num">${esc(p.code)}</span></span>
      </a>
      <button class="iconbtn" type="button" data-raus="${p.inventar_nr}" aria-label="${esc(t("sammlungen.raus", { name: name(p) }))}">${icon("close", 18)}</button>
    </div>`;

    const zeichnen = () => {
      detailEl.innerHTML = `
        <div class="card stack">
          <input class="eingabe" data-feld="name" value="${esc(s.name)}" maxlength="60" aria-label="${esc(t("sammlungen.name"))}">
          <textarea class="eingabe" data-feld="notiz" rows="2" maxlength="1000" placeholder="${esc(t("sammlungen.notiz_platzhalter"))}" aria-label="${esc(t("sammlungen.notiz"))}">${esc(s.notiz || "")}</textarea>
        </div>
        ${s.produkte.length ? `<div class="card zeilen">${s.produkte.map(zeile).join("")}</div>`
          : `<div class="card leer">${esc(t("sammlungen.inhalt_leer"))}</div>`}
        <p><button class="linkbtn leise" type="button" data-sammlung-weg>${esc(t("sammlungen.entfernen"))}</button></p>`;
    };

    async function speichern(feld) {
      if (feld.value.trim() === (s[feld.dataset.feld] || "")) return;
      try { s = await api("PUT", `/api/sammlungen/${id}`, { [feld.dataset.feld]: feld.value }); }
      catch (err) { toast(err.message, { fehler: true }); }
      zeichnen();
    }

    detailEl.addEventListener("focusout", (e) => { if (e.target.matches("[data-feld]")) speichern(e.target); });
    detailEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && e.target.matches("input[data-feld]")) { e.preventDefault(); e.target.blur(); }
    });
    detailEl.addEventListener("click", async (e) => {
      const raus = e.target.closest("[data-raus]");
      if (raus) {
        const nr = Number(raus.dataset.raus);
        const p = s.produkte.find((x) => x.inventar_nr === nr);
        try {
          await api("DELETE", `/api/sammlungen/${id}/produkte/${nr}`);
          s = await api("GET", `/api/sammlungen/${id}`);
          zeichnen();
          toast(t("sammlungen.raus_erledigt", { name: name(p) }), {
            rueckgaengig: async () => {
              try { await api("PUT", `/api/sammlungen/${id}/produkte/${nr}`); s = await api("GET", `/api/sammlungen/${id}`); zeichnen(); }
              catch (err) { toast(err.message, { fehler: true }); }
            },
          });
        } catch (err) { toast(err.message, { fehler: true }); }
        return;
      }
      if (e.target.closest("[data-sammlung-weg]")) {
        const alt = s.name;
        try {
          await api("DELETE", `/api/sammlungen/${id}`);
          // Rückgängig geht von der Liste aus: dort bleibt der Hinweis stehen
          sessionStorage.setItem("mf-sammlung-weg", JSON.stringify({ id, name: alt }));
          location.href = "/sammlungen";
        } catch (err) { toast(err.message, { fehler: true }); }
      }
    });

    api("GET", `/api/sammlungen/${id}`).then((r) => { s = r; zeichnen(); }).catch((err) => toast(err.message, { fehler: true }));
  }

  // Nach dem Entfernen einer Sammlung: Hinweis mit Rückgängig auf der Liste
  if (listeEl) {
    let weg = null;
    try { weg = JSON.parse(sessionStorage.getItem("mf-sammlung-weg") || "null"); sessionStorage.removeItem("mf-sammlung-weg"); } catch (e) { /* ohne Speicher kein Hinweis */ }
    if (weg) {
      toast(t("sammlungen.entfernt", { name: weg.name }), {
        rueckgaengig: async () => {
          try { await api("POST", `/api/sammlungen/${weg.id}/zurueck`); location.href = `/sammlungen/${weg.id}`; }
          catch (err) { toast(err.message, { fehler: true }); }
        },
      });
    }
  }
})();
