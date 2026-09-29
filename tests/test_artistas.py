"""Ficha musical: Discogs (API pública) y Wikipedia, con respuestas reales guardadas el 29-09-2026."""
import json
from pathlib import Path

from scraper import artistas as A
from scraper.clasificar import categorias_de_ficha

FIX = Path(__file__).parent / "fixtures"


def j(name):
    return json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))


def w(name):
    return (FIX / f"{name}.html").read_text(encoding="utf-8")


def test_discogs_coincidencia_unica():
    cand, n = A.discogs_identificar(j("dc_s_hallas")["results"], "Hällas")
    assert cand and cand["title"] == "Hällas" and n == 1
    cand, n = A.discogs_identificar(j("dc_s_toldos")["results"], "Toldos Verdes")
    assert cand and n == 1


def test_discogs_homonimos_no_se_asignan():
    # 'Europe', 'Europe (2)', 'Europe (3)', 'Europe (4)': no se puede saber cuál es
    cand, n = A.discogs_identificar(j("dc_s_europe")["results"], "Europe")
    assert cand is None and n >= 2


def test_discogs_estilos_y_pais():
    generos, estilos = A.discogs_estilos(j("dc_s_master")["results"])
    assert generos == ["Rock"] and "Hard Rock" in estilos
    assert A.discogs_pais(j("dc_art")["profile"]) == "GB"


def test_wikipedia_grupo_espanol():
    r = A.wikipedia_parse(w("wp_es_vinagres"), "https://es.wikipedia.org/wiki/Los_Vinagres")
    assert r["encontrado"] and r["pais"] == "ES"
    assert "Garage rock" in r["generos"] and r["imagen"].startswith("https://")
    assert "Archivo:" in r["imagen_pagina"]


def test_wikipedia_extranjeros_y_solistas():
    assert A.wikipedia_parse(w("wp_es_dp"), "u")["pais"] == "GB"
    assert A.wikipedia_parse(w("wp_en_hallas"), "u")["pais"] == "SE"
    r = A.wikipedia_parse(w("wp_es_leiva"), "u")
    assert r["pais"] == "ES" and "Pop rock" in r["generos"]


def test_ficha_prioriza_discogs_y_traduce_wikipedia():
    wp = A.wikipedia_parse(w("wp_es_vinagres"), "https://es.wikipedia.org/wiki/Los_Vinagres")
    f = A.ficha({"wikipedia": wp, "discogs": {"encontrado": False}})
    assert f["fuente_estilo"] == "Wikipedia" and "Garage Rock" in f["estilos"] and f["pais"] == "ES"
    assert f["imagen"]["credito"] == "Wikimedia Commons"
    dc = {"encontrado": True, "id": 1, "url": "/artist/1-X", "generos": ["Rock"], "estilos": ["Hard Rock"],
          "pais": "GB", "imagen": None}
    f = A.ficha({"wikipedia": {"encontrado": False}, "discogs": dc})
    assert f["fuente_estilo"] == "Discogs" and f["estilos"] == ["Hard Rock"] and f["fuente_pais"] == "Discogs"


def test_pais_de_texto():
    assert A.pais_de_texto("Hertford, Inglaterra, Reino Unido") == "GB"
    assert A.pais_de_texto("Madrid ( España )") == "ES"
    assert A.pais_de_texto("Bilbao") == "ES"
    assert A.pais_de_texto("Jönköping, Småland, Sweden") == "SE"


def test_grupos_de_filtro_desde_discogs():
    assert categorias_de_ficha(["Rock"], ["Hard Rock", "Heavy Metal"]) == ["rock y metal"]
    assert categorias_de_ficha(["Rock"], ["Garage Rock"]) == ["punk y garage"]
    assert categorias_de_ficha(["Rock", "Blues"], ["Blues Rock"]) == ["blues"]
    assert categorias_de_ficha(["Folk, World, & Country"], ["Flamenco"]) == ["fuera de foco"]
    assert categorias_de_ficha(["Hip Hop"], []) == ["fuera de foco"]


def test_no_se_consultan_titulos_de_evento():
    for n in ["Concierto de Blues", "Tributo a Queen. Candlelight", "Jam Session", "Festival Grunge XXL"]:
        assert not A.nombre_consultable(n)
    assert A.nombre_consultable("Los Vinagres")


def test_wikidata_ids_y_pais():
    assert A.wikipedia_parse(w("wp_es_vinagres"), "u")["wikidata"] == "Q136447247"
    v = A.wikidata_parse(j("wd_vinagres"))
    assert v["pais"] == "ES" and v["ids"]["discogs"] == "4629354" and "spotify" in v["ids"]
    dp = A.wikidata_parse(j("wd_dp"))
    assert dp["pais"] == "GB" and dp["ids"]["discogs"] == "170355" and dp["ids"]["allmusic"] == "mn0000192382"
    ha = A.wikidata_parse(j("wd_hallas"))
    assert "discogs" not in ha["ids"] and "musicbrainz" in ha["ids"]


def test_ficha_con_wikidata():
    wp = A.wikipedia_parse(w("wp_es_dp"), "https://es.wikipedia.org/wiki/Deep_Purple")
    f = A.ficha({"wikipedia": wp, "wikidata": A.wikidata_parse(j("wd_dp")), "discogs": {"encontrado": False}})
    assert f["pais"] == "GB" and f["fuente_pais"] == "Wikidata" and f["tiene_allmusic"]
    nombres = [e["nombre"] for e in f["enlaces"]]
    assert "AllMusic" in nombres and "MusicBrainz" in nombres
    assert "Wikidata" in f["identidad"]


# Respuesta de artist.gettoptags con la estructura documentada por Last.fm (construida para la prueba).
LF = {"toptags": {"tag": [{"name": "stoner rock", "count": 100}, {"name": "seen live", "count": 60},
                          {"name": "spanish", "count": 40}, {"name": "hard rock", "count": 30},
                          {"name": "doom metal", "count": 5}], "@attr": {"artist": "Grupo Pequeño"}}}


def test_lastfm_etiquetas_a_discogs():
    r = A.lastfm_parse(LF, "Grupo Pequeño", por_mbid=False)
    assert r["encontrado"] and r["estilos"] == ["Stoner Rock", "Hard Rock"]  # 'doom' no llega al 25 %
    assert r["identificado_por"] == "coincidencia por nombre"
    assert not A.lastfm_parse(LF, "Otro Grupo", por_mbid=False)["encontrado"]
    assert not A.lastfm_parse({"error": 6, "message": "not found"}, "x", False)["encontrado"]
    f = A.ficha({"lastfm": r, "discogs": {"encontrado": False}, "wikipedia": {"encontrado": False}})
    assert f["estilos"] == ["Stoner Rock", "Hard Rock"] and "coincidencia por nombre" in f["fuente_estilo"]


def test_ficha_discogs_tiene_prioridad_sobre_lastfm():
    dc = {"encontrado": True, "estilos": ["Garage Rock"], "generos": ["Rock"], "url": "/artist/1"}
    f = A.ficha({"discogs": dc, "lastfm": A.lastfm_parse(LF, "Grupo Pequeño", False)})
    assert f["estilos"] == ["Garage Rock"] and f["fuente_estilo"] == "Discogs"


def test_wikipedia_no_prueba_sufijos_si_no_existe():
    from tests.fakefetch import FakeFetcher
    ff = FakeFetcher({})
    r = A.buscar_wikipedia(ff, "Grupo Desconocido")
    assert not r["encontrado"] and len(ff.urls) == 2  # es y en, sin '(banda)' ni '(band)'


def test_enriquecer_solo_completa_lo_que_falta():
    from datetime import date
    from tests.fakefetch import FakeFetcher
    cache = {"grupo pequeno": {"nombre": "Grupo Pequeño", "fecha": "2026-09-01",
                               "wikipedia": {"encontrado": False}, "discogs": {"encontrado": False}}}
    lf = FakeFetcher({"https://ws.audioscrobbler.com/*": lambda u, kw: json.dumps(LF)})
    recs = [{"artista": "Grupo Pequeño", "en_foco": True, "fecha": "2026-10-17"}]
    st = A.enriquecer(recs, cache, date(2026, 9, 29), fetcher_dc=FakeFetcher({}), fetcher_wp=FakeFetcher({}),
                      fetcher_lf=lf, clave_lastfm="CLAVE")
    assert st["completados"] == 1 and st["lastfm"] == 1 and len(lf.urls) == 1
    assert cache["grupo pequeno"]["lastfm"]["estilos"] == ["Stoner Rock", "Hard Rock"]
    # la segunda vez ya no consulta nada
    st = A.enriquecer(recs, cache, date(2026, 9, 29), fetcher_dc=FakeFetcher({}), fetcher_wp=FakeFetcher({}),
                      fetcher_lf=lf, clave_lastfm="CLAVE")
    assert st["desde_cache"] == 1 and len(lf.urls) == 1
