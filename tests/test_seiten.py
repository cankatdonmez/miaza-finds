"""Seitengerüst: jede Seite lädt, Menü markiert die aktuelle Seite, Texte kommen aus dem Wörterbuch."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.texte import DE

SEITEN = ["bibliothek", "etiketten", "einstellungen", "mehr"]
APP = Path(__file__).parent.parent / "app"


@pytest.mark.parametrize("seite", SEITEN)
def test_seite_laedt_mit_marke_und_menue(client, seite):
    r = client.get(f"/{seite}")
    assert r.status_code == 200
    assert 'class="marke-miaza">miaza<' in r.text and "finds" in r.text
    assert f'href="/{seite}" aria-current="page"' in r.text or seite == "mehr"


def test_produktseiten_und_qr_link(client):
    assert 'data-produktform data-inventar-nr=""' in client.get("/produkt/neu").text
    assert client.get("/produkt/999").status_code == 404
    kid = client.get("/api/kategorien").json()["kategorien"][0]["id"]
    inv = client.post("/api/produkte", json={"name": "Eichendiele", "kategorie_id": kid}).json()["inventar_nr"]
    r = client.get(f"/p/{inv}", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == f"/produkt/{inv}"
    seite = client.get(f"/produkt/{inv}").text
    assert '<h1 class="seitentitel">Eichendiele</h1>' in seite


def test_einstellungen_liegen_am_telefon_unter_mehr(client):
    html = client.get("/einstellungen").text
    leiste = html[html.index('class="leiste"'):]
    assert 'href="/mehr" aria-current="page"' in leiste


def test_darstellung_hat_drei_wahlen(client):
    html = client.get("/einstellungen").text
    assert re.findall(r'data-darstellung="(\w+)"', html) == ["system", "light", "dark"]


def test_alle_verwendeten_textschluessel_gibt_es():
    quellen = [p.read_text(encoding="utf-8") for p in (APP / "templates").rglob("*.html")]
    quellen += [p.read_text(encoding="utf-8") for p in (APP / "routes").glob("*.py")]
    quellen += [p.read_text(encoding="utf-8") for p in (APP / "services").glob("*.py")]
    quellen += [p.read_text(encoding="utf-8") for p in (APP / "static/js").glob("*.js")]
    benutzt = set()
    for q in quellen:
        benutzt |= set(re.findall(r'\bt\(\s*["\']([a-z_]+\.[a-z0-9_]+)["\']', q))
        benutzt |= set(re.findall(r'["\']((?:menue|bibliothek|etiketten|einstellungen|mehr)\.[a-z0-9_]+)["\']', q))
    # Zusammengesetzte Schlüssel („kat.typ_" + typ) werden unten einzeln geprüft
    fehlend = sorted(k for k in benutzt - DE.keys() if not k.endswith("_"))
    assert not fehlend, f"Text fehlt im Wörterbuch: {fehlend}"


def test_texte_fuer_jede_filterart():
    from app.services.kategorien import FILTER_TYPEN
    for typ in FILTER_TYPEN:
        assert f"kat.typ_{typ}" in DE and f"kat.beispiel_{typ}" in DE


def test_keine_sichtbaren_texte_direkt_in_seitenvorlagen():
    """Sichtbarer Text gehört ins Wörterbuch (DESIGN-PRINCIPLES 7); erlaubt sind nur Marke und Platzhalter."""
    erlaubt = {"miaza", "miaza finds", "v"}     # „v“ vor der Versionsnummer
    for p in (APP / "templates").rglob("*.html"):
        if p.name == "_icons.html":
            continue
        html = re.sub(r"{#.*?#}|{%.*?%}|{{.*?}}|<script.*?</script>|<[^>]+>", " ", p.read_text(encoding="utf-8"), flags=re.S)
        woerter = {w.strip(" ·") for w in re.split(r"\s{2,}|\n", html)} - {""}
        assert woerter <= erlaubt, f"{p.name}: Text ohne Wörterbuch: {woerter - erlaubt}"
