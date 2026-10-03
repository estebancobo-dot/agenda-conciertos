"""Enterticket: datos de la página de cada evento (__NEXT_DATA__) y lectura incremental desde el sitemap."""
import json
from datetime import date

from scraper.sources.base import Ctx
from scraper.sources.enterticket import enterticket, evento_de_pagina


def pagina(nombre="Álvaro Garcia - Madrid", sala="Sala Villanos", ciudad="Madrid", provincia="Madrid",
           categoria="conciertos", inicio="2026-10-12 20:30:00.000000", artistas=("Álvaro García",), precio=26.4):
    ev = {"name": nombre, "active": True, "front_active": True, "start_date": {"date": inicio},
          "venue": {"name": sala, "address": {"city": ciudad, "province": provincia}},
          "minimum_price": precio, "category": {"slug": categoria},
          "artists": [{"name": a} for a in artistas]}
    datos = json.dumps({"props": {"pageProps": {"event": ev}}})
    return f'<html><body><div id="__next"></div><script id="__NEXT_DATA__" type="application/json">{datos}</script></body></html>'


def test_evento_de_madrid():
    d = evento_de_pagina(pagina(), "https://www.enterticket.es/eventos/alvaro-garcia-madrid-851230")
    assert d["madrid"] and d["nombre"] == "Álvaro Garcia" and d["sala"] == "Sala Villanos"
    assert (d["fecha"], d["hora"], d["ciudad"], d["precio"]) == ("2026-10-12", "20:30", "Madrid", "desde 26,40 €")


def test_fuera_de_madrid_o_no_concierto():
    assert not evento_de_pagina(pagina(ciudad="Barcelona", provincia="Barcelona"), "u")["madrid"]
    assert not evento_de_pagina(pagina(categoria="humor"), "u")["madrid"]
    assert not evento_de_pagina(pagina(nombre="Brunch Electronik Madrid x BSMT LIVE - The Blaze (DJ Set)"), "u")["madrid"]
    assert evento_de_pagina("<html>sin datos</html>", "u") is None


class FalsoFetcher:
    def __init__(self, paginas):
        self.paginas, self.pedidas = paginas, []

    def get(self, url, **kw):
        self.pedidas.append(url)
        return self.paginas[url]


def test_incremental_solo_abre_lo_nuevo():
    base = "https://www.enterticket.es/eventos/"
    sitemap = "".join(f"<url><loc>{base}{s}</loc></url>" for s in ("a-madrid-1", "b-barcelona-2"))
    paginas = {"https://www.enterticket.es/sitemap.xml": sitemap, base + "a-madrid-1": pagina(),
               base + "b-barcelona-2": pagina(ciudad="Barcelona", provincia="Barcelona")}
    f = FalsoFetcher(paginas)
    estado = {}
    ctx = Ctx(f, date(2026, 10, 3), date(2027, 1, 31), estado=estado)
    evs = list(enterticket(ctx))
    assert [e.artista for e in evs] == ["Álvaro Garcia"] and len(f.pedidas) == 3
    # al día siguiente: solo el sitemap (nada nuevo) y los conciertos siguen saliendo de lo recordado
    f.pedidas.clear()
    evs = list(enterticket(Ctx(f, date(2026, 10, 4), date(2027, 1, 31), estado=estado)))
    assert [e.artista for e in evs] == ["Álvaro Garcia"] and f.pedidas == ["https://www.enterticket.es/sitemap.xml"]
    # si sale del sitemap (ya no se vende), deja de salir
    paginas["https://www.enterticket.es/sitemap.xml"] = f"<url><loc>{base}b-barcelona-2</loc></url>"
    assert list(enterticket(Ctx(f, date(2026, 10, 5), date(2027, 1, 31), estado=estado))) == []
