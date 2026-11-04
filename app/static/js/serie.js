// Serienerfassung (SPEC 6.2): vor dem Regal stehen und Produkte nacheinander fotografieren.
// Ohne HTTPS öffnet jedes Foto die Kamera-App des Telefons (SPEC 8.2). Das Hochladen läuft im Hintergrund,
// die Kamera wartet nie darauf.
(function () {
  const { $, esc, t, api, toast } = MF;
  const serie = $("[data-serie]");
  if (!serie) return;
  const LETZTE = "mf-letzte-kategorie";

  let warteschlange = [];     // {datei, url}
  let fertige = [];           // {inventar_nr, code, url}
  let laeuft = false;

  // ---------- „+“ ----------
  const plus = $("[data-plus-blatt]");
  $("[data-plus]")?.addEventListener("click", () => { plus.hidden = false; });
  plus.addEventListener("click", (e) => { if (e.target === plus) plus.hidden = true; });

  $("[data-serie-start]").addEventListener("click", async () => {
    plus.hidden = true;
    const { kategorien } = await api("GET", "/api/kategorien");
    let letzte = 0;
    try { letzte = Number(localStorage.getItem(LETZTE)); } catch { /* keine */ }
    const vorwahl = kategorien.find((k) => k.id === letzte) || kategorien.find((k) => k.fest);
    $("[data-serie-kategorie]").innerHTML = kategorien.map((k) =>
      `<option value="${k.id}" ${k.id === vorwahl.id ? "selected" : ""}>${esc(k.name)}</option>`).join("");
    warteschlange = [];
    fertige = [];
    zeichnen();
    serie.hidden = false;
  });

  $("[data-serie-kategorie]").addEventListener("change", (e) => {
    try { localStorage.setItem(LETZTE, e.target.value); } catch { /* egal */ }
  });

  // ---------- Fotos ----------
  serie.addEventListener("change", async (e) => {
    if (!e.target.matches("[data-serie-eingabe]")) return;
    let dateien = [...e.target.files].filter((d) => !d.type || d.type.startsWith("image/"));   // manche Kameras: ohne Typ
    e.target.value = "";
    // Jedes Foto zuschneiden, bei mehreren nacheinander (D-027, D-045). Jedes geht sofort in die Warteschlange:
    // das Hochladen läuft, während das nächste zugeschnitten wird
    await MF.zuschneidenAlle(dateien, (datei) => {
      warteschlange.push({ datei, url: URL.createObjectURL(datei) });
      zeichnen();
      abarbeiten();
    });
  });

  async function abarbeiten() {
    if (laeuft) return;
    laeuft = true;
    while (warteschlange.length) {
      const eintrag = warteschlange[0];
      const fd = new FormData();
      fd.append("kategorie_id", $("[data-serie-kategorie]").value);
      fd.append("foto", eintrag.datei);
      try {
        const res = await fetch("/api/produkte/serie", { method: "POST", body: fd, credentials: "same-origin" });
        const d = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(d.fehler?.text || t("allg.fehler"));
        if (warteschlange[0] === eintrag) {
          warteschlange.shift();
          fertige.push({ ...d, url: eintrag.url });
        } else {
          // Während des Hochladens zurückgenommen → gleich wieder löschen
          await api("DELETE", "/api/produkte/" + d.inventar_nr).catch(() => {});
        }
      } catch (err) {
        warteschlange.shift();
        toast(err.message, { fehler: true });
      }
      zeichnen();
    }
    laeuft = false;
    zeichnen();
  }

  function zeichnen() {
    const alle = [...fertige, ...warteschlange];
    const letztes = alle[alle.length - 1];
    $("[data-serie-vorschau]").innerHTML = letztes
      ? `<img src="${letztes.url}" alt="">${letztes.code ? `<span class="serie-code num">${esc(letztes.code)}</span>` : ""}`
      : "";
    $("[data-serie-anzahl]").textContent = t("serie.anzahl", { n: alle.length });
    $("[data-serie-laedt]").textContent = warteschlange.length ? t("serie.laedt", { n: warteschlange.length }) : "";
    $("[data-serie-weg]").hidden = !alle.length;
  }

  // Letztes Foto zurücknehmen: ein Tipp, keine Rückfrage (SPEC 6.2)
  $("[data-serie-weg]").addEventListener("click", async () => {
    if (warteschlange.length) {
      // Lädt es gerade hoch, löscht abarbeiten() das entstandene Produkt gleich wieder
      URL.revokeObjectURL(warteschlange.pop().url);
    } else if (fertige.length) {
      const weg = fertige.pop();
      try { await api("DELETE", "/api/produkte/" + weg.inventar_nr); } catch (err) { fertige.push(weg); toast(err.message, { fehler: true }); }
      URL.revokeObjectURL(weg.url);
    }
    zeichnen();
  });

  $("[data-serie-fertig]").addEventListener("click", async () => {
    if (warteschlange.length) { toast(t("serie.ungeladen")); return; }
    serie.hidden = true;
    fertige.forEach((f) => URL.revokeObjectURL(f.url));
    if (fertige.length) {
      toast(t("serie.ergebnis", { n: fertige.length }));
      window.dispatchEvent(new CustomEvent("mf:serie-fertig"));
    }
  });

  window.addEventListener("beforeunload", (e) => { if (warteschlange.length) e.preventDefault(); });
})();
