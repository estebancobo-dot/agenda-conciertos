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
