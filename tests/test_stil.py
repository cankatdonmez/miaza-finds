"""Stilregeln wie miaza counts: jede Klasse hat eine Regel, nur Schriftstufen, Farben nur als Token (SPEC 4.4, 9)."""
import re
from pathlib import Path

APP = Path(__file__).parent.parent / "app"
CSS = (APP / "static/css/app.css").read_text(encoding="utf-8")
QUELLEN = list((APP / "static/js").glob("*.js")) + list((APP / "templates").rglob("*.html"))
TOKEN_ENDE = "/* ---------- Ende der Token ---------- */"


def test_alle_verwendeten_klassen_definiert():
    benutzt = set()
    for p in QUELLEN:
        for m in re.finditer(r'class="([^"${]+)"', p.read_text(encoding="utf-8")):
            benutzt |= {k for k in m.group(1).split() if re.fullmatch(r"[a-z][a-z0-9-]*", k)}
    definiert = set(re.findall(r"\.([a-z][a-z0-9-]*)", CSS))
    fehlend = sorted(benutzt - definiert)
    assert not fehlend, f"Klassen ohne Stilregel: {fehlend}"


def test_nur_schriftstufen():
    roh = [(p.name, m) for p in [APP / "static/css/app.css", *QUELLEN]
           for m in re.findall(r"font-size:\s*\d[\d.]*(?:px|rem|em)", p.read_text(encoding="utf-8"))]
    # Die Stufen selbst stehen als --fs-…:Npx, nicht als font-size
    assert not roh, f"Schriftgröße ohne Stufe: {roh}"


def test_farben_nur_im_tokenblock():
    assert TOKEN_ENDE in CSS
    nach_token = CSS.split(TOKEN_ENDE, 1)[1]
    css_farben = re.findall(r"#[0-9A-Fa-f]{3,8}\b|rgba?\(", nach_token)
    assert not css_farben, f"Farbwerte außerhalb der Token: {css_farben}"
    for p in QUELLEN:
        if p.name == "_icons.html":
            continue
        roh = re.findall(r"(?:color|background)[^;\"]*#[0-9A-Fa-f]{3,8}\b", p.read_text(encoding="utf-8"))
        assert not roh, f"{p.name}: Farbwert statt Token: {roh}"


def test_dunkles_thema_definiert_jedes_farbtoken():
    hell = CSS.split(TOKEN_ENDE, 1)[0]
    root = re.search(r":root\{(.*?)\n\}", hell, re.S).group(1)
    # In beiden Themen gleich: Materialfarben (SPEC 4.4), Papier der Etiketten (SPEC 4.3), Farben auf dem Einheitsfoto (D-026)
    farbtoken = {n for n, w in re.findall(r"(--[a-z0-9-]+):([^;]+);", root)
                 if re.search(r"#|rgba", w) and not n.startswith(("--farbe-", "--papier", "--foto-"))}
    dunkel = re.search(r':root\[data-theme="dark"\]\{(.*?)\n\}', hell, re.S).group(1)
    system = re.search(r"prefers-color-scheme:dark\)\{:root:not\(\[data-theme=\"light\"\]\)\{(.*?)\n\}\}", hell, re.S).group(1)
    for block in (dunkel, system):
        fehlend = farbtoken - set(re.findall(r"(--[a-z0-9-]+):", block))
        assert not fehlend, f"Im dunklen Thema fehlt: {sorted(fehlend)}"


def test_jedes_benutzte_symbol_gibt_es():
    """icon("…") ohne passendes <symbol> zeigt nichts – so fehlte lange das Häkchen."""
    symbole = set(re.findall(r'<symbol id="i-([a-z-]+)"', (APP / "templates/_icons.html").read_text(encoding="utf-8")))
    benutzt = set()
    for p in [*(APP / "static/js").glob("*.js"), *(APP / "templates").glob("*.html")]:
        benutzt |= set(re.findall(r'icon\(\s*"([a-z-]+)"', p.read_text(encoding="utf-8")))
    assert not benutzt - symbole, f"Symbol fehlt: {sorted(benutzt - symbole)}"


def test_unterlage_dunkel_invertiert_ueber_tokens():
    """SPEC 4.3: Plan-Unterlage im dunklen Thema invertiert und blass; hell unverändert (Systemweg und Handwahl)."""
    hell = CSS.split(TOKEN_ENDE, 1)[0]
    root = re.search(r":root\{(.*?)\n\}", hell, re.S).group(1)
    assert "--unterlage-filter:none" in root
    dunkel = re.search(r':root\[data-theme="dark"\]\{(.*?)\n\}', hell, re.S).group(1)
    system = re.search(r"prefers-color-scheme:dark\)\{:root:not\(\[data-theme=\"light\"\]\)\{(.*?)\n\}\}", hell, re.S).group(1)
    for block in (dunkel, system):
        assert re.search(r"--unterlage-filter:invert\(1\)", block)
        for n in ("--unterlage-deckkraft", "--unterlage-deckkraft-aktiv"):
            assert n + ":" in block
    regeln = CSS.split(TOKEN_ENDE, 1)[1]
    assert re.search(r"\.unterlage\{[^}]*filter:var\(--unterlage-filter\)", regeln)
    assert re.search(r"\.unterlage\{[^}]*opacity:var\(--unterlage-deckkraft\)", regeln)
    assert re.search(r"\.unterlage\.aktiv\{[^}]*opacity:var\(--unterlage-deckkraft-aktiv\)", regeln)
