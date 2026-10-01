"""País de origen leído en textos (scraper/origen.py): solo frases explícitas y un único país."""
from scraper.artistas import discogs_pais, lf_pais, musicbrainz_parse
from scraper.origen import pais_en_texto, sin_artista


def test_frases_de_agenda():
    assert pais_en_texto("La banda madrileña Sho-Hai presenta su disco.", "Sho-Hai")[0] == "ES"
    assert pais_en_texto("El cantautor argentino Kevin Johansen llega a Madrid.", "Kevin Johansen")[0] == "AR"
    assert pais_en_texto("Thee Nameshakes son un grupo de garage procedentes de Glasgow, Escocia.",
                         "Thee Nameshakes")[0] == "GB"
    assert pais_en_texto("El grupo de rock argentino Los Amados vuelve.", "Los Amados")[0] == "AR"


def test_sin_frase_explicita_no_hay_pais():
    assert pais_en_texto("Una noche de cocina italiana con Epical.", "Epical")[0] is None
    assert pais_en_texto("Live from Madrid: the new tour.", solo_con_nombre=False)[0] is None
    # dos países en el texto (cartel con varios artistas): no se decide
    assert pais_en_texto("Los Amados y The Bang, banda inglesa y grupo mexicano.", "Los Amados")[0] is None
    # la frase tiene que hablar del artista
    assert pais_en_texto("La banda madrileña Sho-Hai abre la noche.", "Epical")[0] is None
    # el gentilicio de otro (el grupo homenajeado) no es del artista
    assert pais_en_texto("En 2017 reclutó a gente que compartía su devoción por la banda inglesa y en 2018 "
                         "Alchemy Project empezó a tocar.", "Alchemy Project")[0] is None
    # dónde vive no es su origen
    assert pais_en_texto("Epical, banda afincada en Madrid.", "Epical")[0] is None


def test_textos_del_artista():
    assert pais_en_texto("Spanish rock band from Bilbao.", solo_con_nombre=False)[0] == "ES"
    assert pais_en_texto("Clarence Bekker is a Dutch soul singer.", solo_con_nombre=False)[0] == "NL"
    assert discogs_pais("Spanish punk rock band formed in 1995.") == "ES"
    assert discogs_pais("Band from Glasgow, Scotland.") == "GB"


def test_musicbrainz_zona():
    assert musicbrainz_parse({"id": "x", "name": "X", "area": {"name": "Madrid"}})["pais"] == "ES"
    assert musicbrainz_parse({"id": "x", "name": "X", "country": "AR", "area": {"name": "Madrid"}})["pais"] == "AR"


def test_lastfm_por_nombre_solo_espana():
    por_nombre = {"lastfm": {"encontrado": True, "identificado_por": "coincidencia por nombre"}}
    assert lf_pais({"lastfm": dict(por_nombre["lastfm"], etiquetas=["spanish", "rock"])}) == "ES"
    assert lf_pais({"lastfm": dict(por_nombre["lastfm"], etiquetas=["british", "rock"])}) is None


def test_sin_artista():
    for t in ("Jam Session", "Jam de Cumbia", "On Fire Jam!", "Concierto de Blues", "After Church Open Mic",
              "Karaoke rockero"):
        assert sin_artista(t), t
    for t in ("80 REDNECKS", "Blues & Roots", "Pearl Jam Tribute", "Jamiroquai Experience",
              "CONCIERTO DE ROCK OVER & ARTISTA INVITADO"):
        assert not sin_artista(t), t


def test_nombre_en_titulo():
    from scraper.artistas import nombre_en_titulo
    assert nombre_en_titulo("ESPECTÁCULO FLAMENCO: CLAUDIA CRUZ") == "CLAUDIA CRUZ"
    assert nombre_en_titulo("THE RUMORS: TRIBUTO FLEETWOOD MAC") == "THE RUMORS"
    assert nombre_en_titulo("LA VAN GOGH (TRIB. LA OREJA DE VAN GOGH)") == "LA VAN GOGH"
    assert nombre_en_titulo("Los Miserables") == "Los Miserables"


def test_origen_por_agenda():
    from scraper.artistas import clave_agenda
    from scraper.pipeline import origen_por_agenda
    r = {"artista": "THE RUMORS: TRIBUTO FLEETWOOD MAC"}
    cache = {clave_agenda(r["artista"]): {"nombre": "THE RUMORS", "agenda": {"encontrado": True, "pais": "ES", "url": "https://x.es/e/1",
                                                      "frase": "The Rumors es una banda tributo madrileña"}}}
    origen_por_agenda(r, cache)
    assert r["nacionalidad"] == "ES" and "x.es" in r["nacionalidad_fuente"]


def test_estimacion_por_nombre():
    from scraper.origen import pais_estimado
    assert pais_estimado("FELIPE ARCE CUARTETO")[0] == "ES"
    assert pais_estimado("Los Amados")[0] == "ES"
    assert pais_estimado("LUCÍA FERNÁNDEZ")[0] == "ES"
    for n in ("80 REDNECKS", "Eternal", "Max Cooper", "Noel McKay", "THE BANG", "Noches de Piano Jazz"):
        assert pais_estimado(n)[0] is None, n


def test_homenajeado():
    from scraper.nombres import homenajeado
    assert homenajeado("THE RUMORS: TRIBUTO FLEETWOOD MAC") == "FLEETWOOD MAC"
    assert homenajeado("LA VAN GOGH (TRIB. LA OREJA DE VAN GOGH)") == "LA OREJA DE VAN GOGH"
    assert homenajeado("Queen Tribute Band") == "Queen"
    assert homenajeado("Brit Floyd - The Pink Floyd Tribute") == "Pink Floyd"
    assert homenajeado("METAL on METAL: tribute Festival") is None
    assert homenajeado("Leiva") is None


def test_estilos_en_texto():
    from scraper.origen import estilos_en_texto
    assert estilos_en_texto("Claim es un grupo murciano de rock alternativo y post punk.", "Claim") == \
        ["rock alternativo", "post punk"]
    assert estilos_en_texto("Haches es una banda española de rock urbano formada en 2019.", "Haches") == ["rock urbano"]
    assert estilos_en_texto("La banda de power pop Los Bengala presenta disco.", "Los Bengala") == ["power pop"]
    assert estilos_en_texto("Thee Nameshakes, a Glasgow garage rock band.", "Thee Nameshakes") == ["garage rock"]
    assert estilos_en_texto("Un concierto de rock en Madrid.", "Claim") == []


def test_grupos_nuevos():
    from scraper.clasificar import categoria_de, grupo_de_titulo
    assert categoria_de("Jazz/Swing") == "jazz y swing"
    assert categoria_de("Flamenco Capital") == "flamenco y copla"
    assert categoria_de("Soul/Funk") == "soul, funk y r&b"
    assert categoria_de("Rock urbano") == "rock y metal"
    assert grupo_de_titulo("Tributo a Queen. Candlelight") == "clásica y lírica"
    assert grupo_de_titulo("Los Miserables, el musical") == "musicales y espectáculos"
    assert grupo_de_titulo("Leiva") is None


def test_estilos_de_programacion_real():
    # textos reales de las páginas de las salas (diagnóstico del 1 de octubre)
    from scraper.origen import estilos_en_texto
    assert estilos_en_texto("LUNES 05 – JOSH MEADER TRIO (Jazz-Fusión / 21:00 horas / Entrada 16 €)",
                            "JOSH MEADER TRIO") == ["jazz fusion"]
    assert set(estilos_en_texto("Clarence Bekker Band + Quentin Moore (Soul & Funk)", "Clarence Bekker Band")) == \
        {"soul", "funk"}
    assert "shoegaze" in estilos_en_texto("miaw es un dúo de pop experimental formado por Liza Dries. Su música "
                                          "transita entre el avant-pop y el shoegaze.", "miaw")
