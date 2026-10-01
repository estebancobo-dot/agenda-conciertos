from scraper.entradas import imagenes_genericas, leer_pagina, ticketera

SALA = """<html><head><meta property="og:image" content="/img/cartel-gira.jpg">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"MusicEvent","name":"Blood Red Shoes",
"startDate":"2026-10-15T21:00:00+02:00","image":["https://sala.es/img/brs.jpg"],
"eventStatus":"https://schema.org/EventScheduled",
"offers":[{"@type":"Offer","price":"22","priceCurrency":"EUR","availability":"https://schema.org/InStock",
"url":"https://www.entradas.com/event/blood-red-shoes-123"},{"@type":"Offer","price":"26","availability":"InStock"}]}
</script></head><body>
<a href="https://www.entradas.com/event/blood-red-shoes-123" class="btn">Comprar entradas</a>
<a href="https://www.instagram.com/sala">Instagram</a><a href="/agenda">Agenda</a>
<a href="https://dice.fm/event/abc">DICE</a></body></html>"""


def test_lee_hora_precio_imagen_y_entradas_del_concierto():
    r = leer_pagina(SALA, "https://sala.es/evento/brs", "2026-10-15")
    assert r["hora"] == "21:00" and r["precio"] == "22 € – 26 €" and r["disponibilidad"] == "a la venta"
    assert r["imagen"] == "https://sala.es/img/brs.jpg" and r["og_imagen"] == "https://sala.es/img/cartel-gira.jpg"
    assert r["entradas_jsonld"].startswith("https://www.entradas.com/")
    assert [e["nombre"] for e in r["enlaces"]] == ["Entradas.com", "DICE"]  # el de "Comprar entradas", primero
    assert "estado" not in r


def test_otro_dia_no_cuenta_y_agotado_y_cancelado():
    # el JSON-LD es de otro día (la página lista varios conciertos): no se usa
    r = leer_pagina(SALA, "https://sala.es/evento/brs", "2026-10-16")
    assert "hora" not in r and "precio" not in r and r["jsonld"] and not r["jsonld_del_dia"]
    agotado = SALA.replace("InStock", "SoldOut")
    assert leer_pagina(agotado, "https://sala.es/e", "2026-10-15")["disponibilidad"] == "agotado"
    cancel = SALA.replace("EventScheduled", "EventCancelled")
    assert leer_pagina(cancel, "https://sala.es/e", "2026-10-15")["estado"] == "cancelado"


def test_sin_hora_real_y_graph():
    html = """<script type="application/ld+json">{"@graph":[{"@type":"WebPage"},{"@type":"Event",
    "startDate":"2026-10-15T00:00","offers":{"lowPrice":"10","highPrice":"10.5"}}]}</script>"""
    r = leer_pagina(html, "https://x.es/e", "2026-10-15")
    assert "hora" not in r and r["precio"] == "10 € – 10,5 €"


def test_ticketeras():
    assert ticketera("https://www.wegow.com/es/conciertos/x") == "Wegow"
    assert ticketera("https://tickets.salaxyz.com/e/1") == "tickets.salaxyz.com"
    assert ticketera("https://www.spotify.com/x") is None


def test_imagenes_genericas():
    recs = [{"artista": a, "imagen_evento": {"url": "https://mev.com/fondo-privado.jpg"}} for a in ("A", "B", "C")]
    recs += [{"artista": "El Rey León", "imagen_evento": {"url": "https://cc.com/reyleon.jpg"}}] * 5
    assert imagenes_genericas(recs) == {"https://mev.com/fondo-privado.jpg"}
