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
    farbtoken = {n for n, w in re.findall(r"(--[a-z0-9-]+):([^;]+);", root) if re.search(r"#|rgba", w)}
    dunkel = re.search(r':root\[data-theme="dark"\]\{(.*?)\n\}', hell, re.S).group(1)
    system = re.search(r"prefers-color-scheme:dark\)\{:root:not\(\[data-theme=\"light\"\]\)\{(.*?)\n\}\}", hell, re.S).group(1)
    for block in (dunkel, system):
        fehlend = farbtoken - set(re.findall(r"(--[a-z0-9-]+):", block))
        assert not fehlend, f"Im dunklen Thema fehlt: {sorted(fehlend)}"
