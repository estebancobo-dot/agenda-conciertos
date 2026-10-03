"""Intruso y Moe: agenda pintada con JavaScript, leída con un navegador real."""
from datetime import date

from scraper.sources.salas import salas_js_parse

HTML = """<a href="#/evento/2329/2026-10-03/THE-CLAMS">21:30 THE CLAMS</a>
<a href="#/evento/2361/2026-10-07/POETRY-SLAM-MADRID">20:30 POETRY SLAM MADRID</a>
<a href="#/evento/1700/2026-10-15/THE-FADE-OUT-BLUES-BAND"></a>
<a href="#/evento/1700/2026-10-15/THE-FADE-OUT-BLUES-BAND">Ver más</a>
<a href="#/evento/1700/2026-10-15/THE-FADE-OUT-BLUES-BAND">THE FADE OUT BLUES BAND</a>
<a href="#/evento/1683/2026-09-30/MOE-JAZZ-JAM-SESSION">MOE JAZZ JAM SESSION</a>
<a href="#/eventos">EVENTOS</a>"""


def test_enlaces_de_evento():
    evs = salas_js_parse(HTML, "https://intrusobar.com/", date(2026, 10, 3), "Intruso Bar")
    assert [(e.fecha.isoformat(), e.hora, e.artista) for e in evs] == [
        ("2026-10-03", "21:30", "THE CLAMS"),
        ("2026-10-15", None, "THE FADE OUT BLUES BAND")]  # sin poesía, sin repetidos, sin pasados
    assert evs[0].url == "https://intrusobar.com/#/evento/2329/2026-10-03/THE-CLAMS"
