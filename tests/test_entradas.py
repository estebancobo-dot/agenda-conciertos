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
    assert ticketera("https://tickets.salaxyz.com/e/1") == "Salaxyz"
    assert ticketera("https://www.spotify.com/x") is None


def test_imagenes_genericas():
    recs = [{"artista": a, "imagen_evento": {"url": "https://mev.com/fondo-privado.jpg"}} for a in ("A", "B", "C")]
    recs += [{"artista": "El Rey León", "imagen_evento": {"url": "https://cc.com/reyleon.jpg"}}] * 5
    assert imagenes_genericas(recs) == {"https://mev.com/fondo-privado.jpg"}


def _rec(i, hora=None, fuentes=None, **kw):
    return {"id": str(i), "artista": f"Artista {i}", "fecha": "2026-10-15", "hora": hora, "precio": None,
            "fuentes": fuentes or [], **kw}


def _ld(hora, precio="20", disp="InStock", img=None):
    return {"hora": hora, "precio": precio + " €", "disponibilidad": "agotado" if disp == "SoldOut" else "a la venta",
            **({"imagen": img} if img else {})}


def test_confianza_por_web_y_no_pisa_la_hora():
    from scraper.entradas import aplicar_entradas
    cache, recs = {}, []
    # buena.es coincide en 3 de 3; mala.es pone 20:00 a todo
    for i, h in enumerate(["21:00", "21:30", "22:00"]):
        cache[f"https://buena.es/e{i}"] = {"fecha": "2026-10-01", "d": _ld(h)}
        cache[f"https://mala.es/e{i}"] = {"fecha": "2026-10-01", "d": _ld("20:00")}
        recs.append(_rec(i, h, [{"id": "b", "nombre": "Buena", "url": f"https://buena.es/e{i}", "prioridad": 3},
                                {"id": "m", "nombre": "Mala", "url": f"https://mala.es/e{i}", "prioridad": 3}]))
    cache["https://buena.es/e9"] = {"fecha": "2026-10-01", "d": _ld("19:30")}
    cache["https://mala.es/e8"] = {"fecha": "2026-10-01", "d": _ld("20:00")}
    sin_b = _rec(9, None, [{"id": "b", "nombre": "Buena", "url": "https://buena.es/e9", "prioridad": 3}])
    sin_m = _rec(8, None, [{"id": "m", "nombre": "Mala", "url": "https://mala.es/e8", "prioridad": 3}])
    recs += [sin_b, sin_m]
    aplicar_entradas(recs, cache)
    assert sin_b["hora"] == "19:30" and sin_b["hora_pagina"]["nombre"] == "Buena"
    assert sin_m["hora"] is None  # mala.es no es fiable
    assert recs[0]["hora"] == "21:00" and "hora_pagina" not in recs[0]  # la que había no se toca
    # idempotente: si la página deja de decirlo, en la siguiente pasada se quita
    cache["https://buena.es/e9"]["d"].pop("hora")
    aplicar_entradas(recs, cache)
    assert sin_b["hora"] is None and "hora_pagina" not in sin_b


def test_entradas_agotado_y_cartel():
    from scraper.entradas import aplicar_entradas
    sala = "https://sala.es/evento/x"
    cache = {sala: {"fecha": "2026-10-01", "d": {"enlaces": [{"url": "https://mutick.com/e/x", "nombre": "Mutick",
                                                              "compra": True}], "og_imagen": "https://sala.es/cartel.jpg"}},
             "https://mutick.com/e/x": {"fecha": "2026-10-01", "d": _ld("21:00", disp="SoldOut")}}
    r = _rec(1, "21:00", [{"id": "sala", "nombre": "Sala X (web oficial)", "url": sala, "prioridad": 1}],
             imagen={"url": "https://wiki/foto.jpg"})
    otro = _rec(2, None, [{"id": "riviera", "nombre": "La Riviera", "prioridad": 1,
                           "url": "https://www.entradas.com/event/fyahbwoy-4107141/?Affiliate=RIV"}])
    aplicar_entradas([r, otro], cache)
    assert r["entradas"] == {"url": "https://mutick.com/e/x", "nombre": "Mutick", "via": "Sala X"}
    assert r["agotado"]["nombre"] == "Mutick"
    assert r["gira"]["imagen"] == "https://sala.es/cartel.jpg"  # de la sala; distinta de la foto del artista
    assert otro["entradas"]["nombre"] == "Entradas.com"  # la propia fuente ya es la página de entradas
    # misma imagen que la foto del artista: no hay cartel aparte
    r["imagen"] = {"url": "https://sala.es/cartel.jpg"}
    aplicar_entradas([r, otro], cache)
    assert "gira" not in r


def test_leer_entradas_incremental():
    from datetime import date

    from scraper.entradas import leer_entradas

    class F:
        n = 0

        def get(self, url):
            F.n += 1
            if "mutick" in url:
                return '<script type="application/ld+json">{"@type":"Event","startDate":"2026-10-15T21:00",' \
                       '"offers":{"price":"15","availability":"SoldOut"}}</script>'
            return '<a href="https://mutick.com/e/x">Comprar entradas</a>'
    recs = [_rec(1, None, [{"id": "sala", "url": "https://sala.es/e1", "prioridad": 1},
                           {"id": "madridenvivo", "url": "https://madridenvivo.com/?p=1", "prioridad": 3}])]
    cache = {}
    st = leer_entradas(recs, cache, F(), date(2026, 10, 1), 30)
    assert st["leidas"] == 2 and cache["https://mutick.com/e/x"]["d"]["disponibilidad"] == "agotado"
    assert "https://madridenvivo.com/?p=1" not in cache  # Madrid en Vivo no se lee
    leer_entradas(recs, cache, F(), date(2026, 10, 2), 30)
    assert F.n == 2  # al día siguiente no se vuelve a leer (caché)


def test_errores_vistos_en_la_primera_pasada():
    from scraper.entradas import aplicar_entradas, limpiar
    assert ticketera("https://ticketmaster.evyy.net/RG4nXa") == "Ticketmaster"
    assert ticketera("https://ventas.geeticket.com/x") == "Geeticket"
    assert ticketera("https://tickets.salaxyz.com/e/1") == "Salaxyz"
    assert limpiar("https://feverup.com/m/648932?_gl=1*abc&srsltid=x&utm_source=y&id=3") == "https://feverup.com/m/648932?id=3"
    # el blog de una ticketera (listado de toda la agenda) no es la página de entradas; ni una página de contacto
    blog = "https://blog.ticketmaster.es/post/agenda-rock-2026-38621/"
    rs = [_rec(i, "21:00", [{"id": "tm_blog", "nombre": "Blog de Ticketmaster", "url": blog, "prioridad": 3}]) for i in range(3)]
    rs.append(_rec(9, "21:00", [{"id": "s", "nombre": "Sala", "prioridad": 1, "url": "https://sala.es/e9"}],
                   imagen={"url": "https://x/foto.jpg"}))
    cache = {"https://sala.es/e9": {"fecha": "2026-10-01", "d": {
        "enlaces": [{"url": "https://www.enterticket.es/info/contact?page=consultanos", "nombre": "Enterticket", "compra": False}],
        "og_imagen": "https://sala.es/wp-content/uploads/Logo-Sala-2024.png"}}}
    aplicar_entradas(rs, cache)
    assert not any(r.get("entradas") for r in rs)
    assert "gira" not in rs[3]  # el logo de la sala no es un cartel


def test_cartel_del_jsonld():
    html = """<script type="application/ld+json">{"@type":"MusicEvent","name":"Noche Punk: Evaristo &amp; amigos",
    "startDate":"2026-10-03T20:00","performer":[{"@type":"MusicGroup","name":"Evaristo"},{"name":"Boikot"},
    {"name":"boikot"},"Reincidentes"]}</script>"""
    r = leer_pagina(html, "https://x.es/e", "2026-10-03")
    assert r["cartel"] == ["Evaristo", "Boikot", "Reincidentes"]
    assert r["evento_nombre"] == "Noche Punk: Evaristo & amigos" and r["evento_tipo"] == "MusicEvent"
