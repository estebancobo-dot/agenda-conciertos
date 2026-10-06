"""Festify Indie: conciertos del JSON-LD y, los demás, de la tarjeta ("Artista" + "Sala · 8 oct 2026")."""
from datetime import date

from scraper.sources.agregadores import festify_parse

HTML = """<html><head><script type="application/ld+json">
{"@type": "MusicEvent", "name": "MC Enroe", "startDate": "2026-10-08T21:00",
 "url": "https://festifyindie.com/evento/mc-enroe-madrid",
 "location": {"@type": "Place", "name": "Sala Villanos", "address": {"addressLocality": "Madrid"}}}
</script></head><body>
<a href="/evento/mc-enroe-madrid"><h3>MC Enroe</h3><p>Sala Villanos · 8 oct 2026</p><span>Ver entradas</span></a>
<a href="/evento/late-capital-madrid"><h3>Late Capital</h3><p>Sala El Sol · 11 oct 2026</p><span>Ver entradas</span></a>
<a href="/evento/sin-fecha"><h3>Algo</h3><p>Ver entradas</p></a>
<a href="/evento/pasado"><h3>Viejo</h3><p>Sala B · 1 sep 2026</p></a>
</body></html>"""


def test_festify():
    evs = {e.artista: e for e in festify_parse(HTML, "https://festifyindie.com/conciertos/madrid", date(2026, 10, 6))}
    assert set(evs) == {"MC Enroe", "Late Capital"}  # sin fecha o ya pasado: fuera
    assert evs["MC Enroe"].hora == "21:00" and evs["MC Enroe"].sala == "Sala Villanos"
    lc = evs["Late Capital"]
    assert (lc.fecha, lc.sala, lc.url) == (date(2026, 10, 11), "Sala El Sol", "https://festifyindie.com/evento/late-capital-madrid")
