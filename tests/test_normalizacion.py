"""N3/N4: cada concierto termina con un estado explícito de estilo y de origen."""
from scraper.normalizacion import estado_estilo, estado_nacionalidad, normalizar, resumen


def rec(**kw):
    r = {"fecha": "2026-10-10", "artista": "Grupo X", "grupos": ["sin clasificar"], "grupos_origen": "agenda",
         "grupos_segun": [], "nacionalidad": None, "nacionalidad_fuente": None, "categorias": []}
    r.update(kw)
    return r


CACHE = {"grupo x": {"discogs": {"encontrado": False, "motivo": "sin coincidencia exacta"},
                     "musicbrainz": {"encontrado": False, "motivo": "3 artistas homónimos"}},
         "landa": {"lastfm": {"encontrado": True, "identificado_por": "coincidencia por nombre"},
                   "discogs": {"encontrado": True, "pais": "DE"}, "musicbrainz": {"encontrado": True, "pais": "ES"}}}


def test_estilo():
    assert estado_estilo(rec(grupos=["rock y metal"], grupos_origen="Discogs"), CACHE) == \
        {"estado": "conocido", "fuente": "Discogs"}
    e = estado_estilo(rec(grupos=["blues"], grupos_segun=["conciertos.club"]), CACHE)
    assert e["estado"] == "estimado" and "etiqueta de la agenda" in e["motivo"]
    # Last.fm de un artista encontrado solo por su nombre: podría ser un homónimo
    e = estado_estilo(rec(artista="LANDA", grupos=["electrónica"], grupos_origen="Last.fm"), CACHE)
    assert e["estado"] == "estimado"
    assert estado_estilo(rec(artista="WICKED, El Musical"), CACHE)["estado"] == "no_aplica"
    assert estado_estilo(rec(artista="Jam session de blues"), CACHE)["estado"] == "no_aplica"
    d = estado_estilo(rec(), CACHE)
    assert d["estado"] == "desconocido" and "Discogs: sin coincidencia exacta" in d["buscado"]
    assert "MusicBrainz: 3 artistas homónimos" in d["buscado"]
    assert estado_estilo(rec(artista="Nadie Buscado"), CACHE)["buscado"][0].startswith("aún no se ha buscado")


def test_origen():
    o = estado_nacionalidad(rec(nacionalidad="ES", nacionalidad_fuente="Wikidata"), CACHE)
    assert o == {"estado": "conocido", "valor": "ES", "fuente": "Wikidata"}
    o = estado_nacionalidad(rec(nacionalidad="CZ", nacionalidad_fuente="Last.fm (etiqueta de país de los oyentes, "
                                                                     "artista identificado por su nombre)"), CACHE)
    assert o["estado"] == "estimado" and "homónimo" in o["motivo"]
    o = estado_nacionalidad(rec(nacionalidad_estimada="ES", nacionalidad_estimada_motivo="nombre en español"), CACHE)
    assert o["estado"] == "estimado" and o["valor"] == "ES"
    assert estado_nacionalidad(rec(origen_no_aplica=True, artista="Jam session"), CACHE)["estado"] == "no_aplica"
    assert estado_nacionalidad(rec(), CACHE)["estado"] == "desconocido"
    # otras webs que dan otro país: se muestran
    o = estado_nacionalidad(rec(artista="LANDA", nacionalidad="ES", nacionalidad_fuente="MusicBrainz"), CACHE)
    assert o["contradice"] == [{"valor": "DE", "fuentes": ["Discogs"]}]


def test_resumen_cuenta_todos():
    recs = [rec(grupos=["rock y metal"], grupos_origen="Discogs", nacionalidad="ES", nacionalidad_fuente="Discogs"),
            rec(), rec(artista="WICKED, El Musical", origen_no_aplica=True)]
    for r in recs:
        normalizar(r, CACHE)
    res = resumen(recs, "2026-10-01")
    assert sum(res["estilo"].values()) == 3 and sum(res["origen"].values()) == 3
    assert res["estilo"]["conocido"] == 1 and res["origen"]["no_aplica"] == 1


def test_paginas_del_concierto_primero_sala_y_entradas():
    from scraper.artistas import paginas_del_concierto
    r = {"fuentes": [{"url": "https://conciertos.club/a", "prioridad": 3},
                     {"url": "https://conciertos.club/b", "prioridad": 3},
                     {"url": "https://madridenvivo.com/e/1", "prioridad": 3},
                     {"url": "https://salaelsol.com/agenda", "prioridad": 1}],
         "entradas": {"url": "https://www.enterticket.es/eventos/x-1"}}
    assert paginas_del_concierto(r) == ["https://salaelsol.com/agenda", "https://www.enterticket.es/eventos/x-1",
                                        "https://conciertos.club/a", "https://madridenvivo.com/e/1"]


def test_descripcion_incrustada():
    from bs4 import BeautifulSoup
    from scraper.artistas import _descripcion_incrustada
    html = ('<script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"event":{"description":'
            '"<div>Los Rayos es una banda madrile\\u00f1a de garage rock</div>"}}}}</script>')
    assert "banda madrileña de garage rock" in _descripcion_incrustada(BeautifulSoup(html, "html.parser"))


def test_n5_hora_precio_sala():
    from scraper.normalizacion import estado_hora, estado_precio, estado_sala
    f = [{"id": "mev", "nombre": "Madrid en Vivo (asociación de salas)"}]
    assert estado_hora({"hora": "21:00", "fuentes": f})["estado"] == "conocido"
    h = estado_hora({"hora": None, "fuentes": f, "conflictos": [{"campo": "hora", "versiones": [{"valor": "20:00"},
                                                                                              {"valor": "21:30"}]}]})
    assert h["estado"] == "estimado" and "20:00 o 21:30" in h["motivo"]
    assert estado_hora({"hora": None, "fuentes": f})["buscado"] == ["Madrid en Vivo: no la da"]
    assert estado_precio({"precio": "Entrada libre", "fuentes": f})["estado"] == "conocido"
    assert estado_precio({"precio": None, "fuentes": f})["estado"] == "desconocido"
    assert estado_sala({"sala": "", "fuentes": f})["estado"] == "desconocido"
