"""Ficha musical: Discogs (API pública) y Wikipedia, con respuestas reales guardadas el 29-09-2026."""
import json
from pathlib import Path

from scraper import artistas as A
from scraper.clasificar import categorias_de_ficha

FIX = Path(__file__).parent / "fixtures"


def j(name):
    return json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))


def _mb_vacio():
    from tests.fakefetch import FakeFetcher
    return FakeFetcher({"https://musicbrainz.org/ws/2/artist/?query=*": lambda u, kw: json.dumps({"artists": []})})


MB_VACIO = _mb_vacio()


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
    assert categorias_de_ficha(["Folk, World, & Country"], ["Flamenco"]) == ["flamenco y copla"]
    assert categorias_de_ficha(["Hip Hop"], []) == ["urbana y hip hop"]


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
                      fetcher_lf=lf, clave_lastfm="CLAVE", fetcher_mb=MB_VACIO, mb_cache={})
    assert st["completados"] == 1 and st["lastfm"] == 1 and len(lf.urls) == 1
    assert cache["grupo pequeno"]["lastfm"]["estilos"] == ["Stoner Rock", "Hard Rock"]
    # la segunda vez ya no consulta nada
    st = A.enriquecer(recs, cache, date(2026, 9, 29), fetcher_dc=FakeFetcher({}), fetcher_wp=FakeFetcher({}),
                      fetcher_lf=lf, clave_lastfm="CLAVE", fetcher_mb=MB_VACIO, mb_cache={})
    assert st["desde_cache"] == 1 and len(lf.urls) == 1


def test_discogs_id_de_wikidata_borrado_busca_por_nombre():
    import requests
    from datetime import date
    from tests.fakefetch import FakeFetcher

    class R404:
        status_code = 404

    def borrado(url, kw):
        raise requests.HTTPError("404 Client Error", response=R404())

    dc = FakeFetcher({"https://api.discogs.com/artists/9340201": borrado,
                      "https://api.discogs.com/database/search?q=*": lambda u, kw: json.dumps({"results": []})})
    r = A.buscar_discogs(dc, "Los Deltonos", "9340201")
    assert not r["encontrado"] and any("search?q=" in u for u in dc.urls)
    # una ficha guardada con error se vuelve a consultar en la siguiente ejecución (solo ese paso)
    cache = {"los deltonos": {"nombre": "Los Deltonos", "fecha": "2026-09-29", "wikipedia": {"encontrado": False},
                              "discogs": {"encontrado": False, "motivo": "error: HTTPError"}}}
    dc2 = FakeFetcher({"https://api.discogs.com/*": lambda u, kw: json.dumps({"results": []})})
    wp = FakeFetcher({})
    st = A.enriquecer([{"artista": "Los Deltonos", "en_foco": True, "fecha": "2026-10-10"}], cache, date(2026, 9, 29),
                      fetcher_dc=dc2, fetcher_wp=wp, fetcher_lf=FakeFetcher({}), clave_lastfm="",
                      fetcher_mb=MB_VACIO, mb_cache={})
    assert st["completados"] == 1 and dc2.urls and not wp.urls
    assert cache["los deltonos"]["discogs"]["motivo"] == "sin coincidencia exacta"


def test_unir_caches_de_dos_ejecuciones():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("gd", Path(__file__).parent.parent / "tools" / "guardar_datos.py")
    gd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gd)
    nuestra = {"a": {"fecha": "2026-09-29", "v": 1}, "c": {"fecha": "2026-09-28", "v": "nuestra"}}
    suya = {"b": {"fecha": "2026-09-29", "v": 2}, "c": {"fecha": "2026-09-29", "v": "suya"}}
    u = gd.unir_caches(nuestra, suya)
    assert set(u) == {"a", "b", "c"} and u["c"]["v"] == "suya"  # gana la consulta más reciente


def test_discogs_buscador_enlaza_ficha_borrada():
    import requests
    from tests.fakefetch import FakeFetcher

    class R404:
        status_code = 404

    def borrada(url, kw):
        raise requests.HTTPError("404 Client Error", response=R404())

    res = {"results": [{"title": "Los Deltonos", "type": "artist", "resource_url": "https://api.discogs.com/artists/9340201"}]}
    dc = FakeFetcher({"https://api.discogs.com/database/search?q=*": lambda u, kw: json.dumps(res),
                      "https://api.discogs.com/artists/9340201": borrada})
    r = A.buscar_discogs(dc, "Los Deltonos")
    assert r == {"encontrado": False, "motivo": "el buscador de Discogs enlaza una ficha que ya no existe"}


# ---------------------------------------------------------------- clasificación por consenso (casos reales del 30-09-2026)
def _rec(artista, etiquetas, **kw):
    r = {"artista": artista, "estilo_fuente": [{"estilo": e, "fuente": f} for e, f in etiquetas], "categorias": [],
         "nacionalidad": None, "nacionalidad_fuente": None, "imagen_evento": None}
    r.update(kw)
    return r


def test_musical_no_se_confunde_con_un_grupo():
    from scraper.pipeline import aplicar_ficha
    ent = {"discogs": {"encontrado": True, "estilos": ["Punk", "Ska"], "generos": ["Rock"], "url": "/a/1"},
           "wikidata": {"encontrado": True, "pais": "CL", "ids": {}}}
    r = _rec("Los Miserables", [("Musicales/Teatro musical", "conciertos.club (buscador semanal)")],
             nacionalidad="CL", nacionalidad_fuente="Wikidata")
    aplicar_ficha(r, A.ficha(ent))
    assert r["grupos"] == ["musicales y espectáculos"] and r["ficha"] is None and r["nacionalidad"] is None


def test_consenso_no_mete_en_rock_a_quien_solo_lo_menciona():
    from scraper.pipeline import aplicar_ficha
    ent = {"wikipedia": {"encontrado": True, "generos": ["Latin", "pop", "dance", "rock"], "url": "u"},
           "lastfm": {"encontrado": True, "etiquetas": ["pop", "latin", "female vocalists"], "estilos": [],
                      "generos": ["Pop", "Latin"], "identificado_por": "coincidencia por nombre", "url": "u"}}
    r = _rec("Shakira", [("Pop Latino", "conciertos.club (buscador semanal)")])
    aplicar_ficha(r, A.ficha(ent))
    assert r["grupos"][0] == "latina" and not {"rock y metal", "pop e indie"} & set(r["grupos"])  # ni rock ni indie
    assert "Rock" not in r["genero_discogs"]


def test_lastfm_por_nombre_sin_apoyo_de_la_agenda_no_clasifica():
    from scraper.pipeline import aplicar_ficha
    ent = {"lastfm": {"encontrado": True, "etiquetas": ["doom metal", "funk"], "estilos": ["Doom Metal"],
                      "generos": ["Rock"], "identificado_por": "coincidencia por nombre", "url": "u"}}
    r = _rec("ETERNAL", [])
    aplicar_ficha(r, A.ficha(ent))
    assert r["grupos"] == ["sin clasificar"] and r["estilos_discogs"] == [] and r["estilo_descartado"]


def test_etiqueta_paraguas_de_agenda_es_generica():
    from scraper.pipeline import aplicar_ficha
    r = _rec("Grupo X", [("Pop / Rock", "Madrid en Vivo (asociación de salas)")])
    aplicar_ficha(r, None)
    assert set(r["grupos"]) == {"pop e indie", "rock y metal"} and r["grupos_generico"]
    r = _rec("Grupo Y", [("Pop / Rock", "Madrid en Vivo (asociación de salas)"),
                         ("Metal/Rock duro", "conciertos.club (buscador semanal)")])
    aplicar_ficha(r, None)
    assert r["grupos"] == ["rock y metal"] and not r["grupos_generico"]  # la etiqueta concreta manda


def test_rnb_moderno_no_es_blues():
    from scraper.clasificar import generos_de_texto, discogs
    assert discogs(["R&B"])[0] == [] and generos_de_texto(["R&B"]) == ["Funk / Soul"]


def test_musicbrainz_generos_votados():
    dp = A.musicbrainz_parse(j("mb_dp"))
    assert dp["generos"][0] == ["hard rock", 28] and dp["pais"] == "GB"
    assert all(c >= 7 for _, c in dp["generos"])  # los de menos de 1/4 de los votos del principal se descartan
    ent = {"musicbrainz": {**dp, "identificado_por": "identificador de MusicBrainz en Wikidata"}}
    evs = A.evidencias(ent)
    assert evs[0]["nombre"] == "Hard Rock" and evs[0]["fuente"] == "MusicBrainz"
    tk = A.musicbrainz_parse(j("mb_teksuo"))  # 'metalcore' 2 votos, 'metal' 1
    assert [g for g, _ in tk["generos"]] == ["metalcore", "metal"]


def test_musicbrainz_en_el_consenso():
    from scraper.pipeline import aplicar_ficha
    ent = {"musicbrainz": {**A.musicbrainz_parse(j("mb_medina")), "identificado_por": "x"}}
    r = _rec("Medina Azahara", [("Pop / Rock", "Madrid en Vivo (asociación de salas)")])
    aplicar_ficha(r, A.ficha(ent))
    assert r["grupos"] == ["rock y metal"] and not r["grupos_generico"] and r["grupos_segun"] == ["MusicBrainz"]


def test_buscar_musicbrainz_usa_la_cache_de_nacionalidad():
    from datetime import date
    from tests.fakefetch import FakeFetcher
    mb = FakeFetcher({"https://musicbrainz.org/ws/2/artist/63d38a2c-55dc-4318-9ff4-82d4c265f89f*":
                      lambda u, kw: (FIX / "mb_medina.json").read_text(encoding="utf-8")})
    cache = {"medina azahara": {"pais": "ES", "coincidencias_exactas": 1,
                                "mbid": "63d38a2c-55dc-4318-9ff4-82d4c265f89f", "fecha": "2026-09-29"}}
    r = A.buscar_musicbrainz(mb, "Medina Azahara", None, cache, date(2026, 9, 30))
    assert r["encontrado"] and r["identificado_por"].startswith("única coincidencia") and len(mb.urls) == 1
    r = A.buscar_musicbrainz(MB_VACIO, "Grupo Nuevo", None, cache, date(2026, 9, 30))
    assert not r["encontrado"] and cache["grupo nuevo"]["coincidencias_exactas"] == 0


def test_indie_y_pop_rock_no_incluye_pop_comercial():
    from scraper.pipeline import aplicar_ficha
    ent = {"discogs": {"encontrado": True, "estilos": ["Ballad", "Europop", "Pop Rock"], "generos": ["Pop"], "url": "/a/1"}}
    r = _rec("Cantante Pop", [("Pop", "Songkick Madrid")])
    aplicar_ficha(r, A.ficha(ent))
    assert r["grupos"] == ["pop comercial"]
    ent = {"discogs": {"encontrado": True, "estilos": ["Indie Rock", "Pop Rock", "Indie Pop"], "generos": ["Rock", "Pop"], "url": "/a/2"}}
    r = _rec("Grupo Indie", [])
    aplicar_ficha(r, A.ficha(ent))
    assert r["grupos"] == ["pop e indie"]
    r = _rec("Sin ficha", [("Pop Latino", "conciertos.club (buscador semanal)")])
    aplicar_ficha(r, None)
    assert r["grupos"] == ["latina"]


def test_estilos_ambiguos_de_discogs_no_son_rock():
    from scraper.pipeline import aplicar_ficha
    ent = {"discogs": {"encontrado": True, "estilos": ["Neo-Classical", "Contemporary", "Instrumental"],
                       "generos": ["Classical", "Electronic"], "url": "/a/1"}}
    r = _rec("Martin Kohlstedt", [])
    aplicar_ficha(r, A.ficha(ent))
    assert "rock y metal" not in r["grupos"] and r["grupos"][0] == "clásica y lírica"
    r = _rec("Callas en concierto - En holograma", [("Versiones/Tributos", "conciertos.club (buscador semanal)")])
    aplicar_ficha(r, None)
    assert r["grupos"] == ["fuera de foco"]


def test_lastfm_se_confirma_con_el_identificador_de_musicbrainz():
    from scraper.artistas import _lastfm_mejorable, _mbid
    ent = {"lastfm": {"encontrado": True, "identificado_por": "coincidencia por nombre"},
           "musicbrainz": {"encontrado": True, "mbid": "abc"}}
    assert _mbid(ent) == ("abc", "identificador de MusicBrainz (único artista con ese nombre)")
    assert _lastfm_mejorable(ent)
    ent["lastfm"]["mbid_probado"] = True  # ya se probó y Last.fm no lo conocía: no se repite
    assert not _lastfm_mejorable(ent)
    ent = {"wikidata": {"ids": {"musicbrainz": "wd"}}, "musicbrainz": {"encontrado": True, "mbid": "abc"}}
    assert _mbid(ent)[0] == "wd"


def test_nacionalidad_de_musicbrainz_en_la_ficha():
    from scraper.artistas import ficha
    f = ficha({"discogs": {"encontrado": False}, "wikipedia": {"encontrado": False},
               "musicbrainz": {"encontrado": True, "mbid": "x", "generos": [["hard rock", 5]], "pais": "SE"}})
    assert (f["pais"], f["fuente_pais"]) == ("SE", "MusicBrainz")


def test_discogs_sin_masters_usa_los_discos_sueltos():
    # un grupo pequeño sin "master": el estilo y el país salen de sus discos sueltos
    import json as _j

    class F:
        def get(self, u, **k):
            if "type=master" in u:
                return _j.dumps({"results": []})
            return _j.dumps({"results": [
                {"title": "Gorila Flo - Primero", "genre": ["Rock"], "style": ["Garage Rock", "Punk"], "country": "Spain"},
                {"title": "Gorila Flo - Segundo", "genre": ["Rock"], "style": ["Garage Rock"], "country": "Spain"},
                {"title": "Otro Grupo - Split", "genre": ["Pop"], "style": ["Ballad"], "country": "US"}]})
    r = A.discogs_ficha(F(), {"id": 1, "name": "Gorila Flo", "uri": "/a/1", "profile": ""}, "Gorila Flo", "x")
    assert r["estilos"][0] == "Garage Rock" and r["discos_analizados"] == 2 and r["pais_discos"] == "ES"


def test_discogs_homonimos_elige_el_espanol():
    import json as _j

    class F:
        def get(self, u, **k):
            if "type=artist" in u:
                return _j.dumps({"results": [
                    {"type": "artist", "title": "Trapiche", "resource_url": "u1"},
                    {"type": "artist", "title": "Trapiche (2)", "resource_url": "u2"}]})
            if u == "u1":
                return _j.dumps({"id": 1, "name": "Trapiche", "uri": "/a/1", "profile": "Brazilian samba group."})
            if u == "u2":
                return _j.dumps({"id": 2, "name": "Trapiche (2)", "uri": "/a/2", "profile": "Spanish rock band from Madrid."})
            return _j.dumps({"results": [{"title": "Trapiche - Uno", "genre": ["Rock"], "style": ["Hard Rock"]}]})
    r = A.buscar_discogs(F(), "TRAPICHE")
    assert r["encontrado"] and r["id"] == 2 and r["pais"] == "ES" and "único de España" in r["identificado_por"]
