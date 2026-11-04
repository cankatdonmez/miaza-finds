// Einstellungen › Allgemein (D-038): Personen des Büros und die Person dieses Geräts.
// Namen werden direkt im Chip umbenannt (Enter oder Verlassen speichert); Entfernen mit „Rückgängig“ statt Rückfrage.
(function () {
  const { $, esc, icon, t, api, toast } = MF;
  const liste = $("[data-personen]");
  const wahl = $("[data-geraet-person]");
  if (!liste || !wahl) return;

  let personen = [];
  let neu = "";

  function geraetSetzen(id) {
    try {
      if (id) localStorage.setItem("mf-person", String(id));
      else localStorage.removeItem("mf-person");
    } catch (e) { /* ohne Speicher gilt die Wahl nur bis zum Neuladen */ }
  }

  function zeichnen() {
    // Entfernte Person darf nicht mehr als Person dieses Geräts gelten
    const ich = MF.geraetPerson();
    if (ich && !personen.some((p) => p.id === ich)) geraetSetzen(null);
    wahl.innerHTML = personen.map((p) => `<button class="pill" type="button" data-ich="${p.id}" aria-pressed="${p.id === MF.geraetPerson()}">${esc(p.name)}</button>`).join("")
      || `<span class="sub">${esc(t("personen.leer"))}</span>`;
    liste.innerHTML = personen.map((p) => `<span class="option">
        <input class="option-name" data-name="${p.id}" value="${esc(p.name)}" size="${Math.max(3, p.name.length)}" maxlength="60" aria-label="${esc(t("personen.name"))}">
        <button class="option-x" type="button" data-weg="${p.id}" aria-label="${esc(t("personen.entfernen", { name: p.name }))}">×</button>
      </span>`).join("") + `<span class="option-neu-zeile">
        <input class="eingabe option-neu" data-neu value="${esc(neu)}" maxlength="60" placeholder="${esc(t("personen.neu"))}" aria-label="${esc(t("personen.neu"))}">
        <button class="iconbtn" type="button" data-hinzu ${neu.trim() ? "" : "disabled"} aria-label="${esc(t("personen.neu"))}">${icon("plus", 18)}</button>
      </span>`;
  }

  async function laden() {
    try { personen = (await api("GET", "/api/personen")).personen; zeichnen(); } catch (err) { toast(err.message, { fehler: true }); }
  }

  async function hinzufuegen() {
    const name = neu.trim();
    if (!name) return;
    // Feld sofort leeren: wer gleich den nächsten Namen tippt, verliert nichts, während gespeichert wird
    neu = "";
    $("[data-neu]").value = "";
    $("[data-hinzu]").disabled = true;
    try {
      personen = (await api("POST", "/api/personen", { name })).personen;
    } catch (err) {
      if (!neu) neu = name;
      toast(err.message, { fehler: true });
    }
    const imFeld = document.activeElement?.matches("[data-neu]");
    zeichnen();
    if (imFeld) $("[data-neu]").focus();
  }

  async function umbenennen(feld) {
    const id = Number(feld.dataset.name);
    const alt = personen.find((p) => p.id === id);
    if (!alt || feld.value.trim() === alt.name) return;
    try { personen = (await api("PUT", `/api/personen/${id}`, { name: feld.value })).personen; }
    catch (err) { toast(err.message, { fehler: true }); }
    zeichnen();
  }

  wahl.addEventListener("click", (e) => {
    const b = e.target.closest("[data-ich]");
    if (!b) return;
    const id = Number(b.dataset.ich);
    geraetSetzen(MF.geraetPerson() === id ? null : id);      // nochmal tippen = niemand
    zeichnen();
  });

  liste.addEventListener("input", (e) => {
    if (e.target.matches("[data-neu]")) {
      neu = e.target.value;
      $("[data-hinzu]").disabled = !neu.trim();
    } else if (e.target.matches("[data-name]")) {
      e.target.size = Math.max(3, e.target.value.length);
    }
  });
  liste.addEventListener("keydown", (e) => {
    if (e.key !== "Enter") return;
    if (e.target.matches("[data-neu]")) { e.preventDefault(); hinzufuegen(); }
    else if (e.target.matches("[data-name]")) { e.preventDefault(); e.target.blur(); }
  });
  liste.addEventListener("focusout", (e) => { if (e.target.matches("[data-name]")) umbenennen(e.target); });
  liste.addEventListener("click", async (e) => {
    if (e.target.closest("[data-hinzu]")) return hinzufuegen();
    const weg = e.target.closest("[data-weg]");
    if (!weg) return;
    const id = Number(weg.dataset.weg);
    const name = personen.find((p) => p.id === id)?.name || "";
    const warIch = MF.geraetPerson() === id;
    try {
      personen = (await api("DELETE", `/api/personen/${id}`)).personen;
      zeichnen();
      toast(t("personen.entfernt", { name }), {
        rueckgaengig: async () => {
          try {
            personen = (await api("POST", `/api/personen/${id}/zurueck`)).personen;
            if (warIch) geraetSetzen(id);
            zeichnen();
          } catch (err) { toast(err.message, { fehler: true }); }
        },
      });
    } catch (err) { toast(err.message, { fehler: true }); }
  });

  laden();
})();
