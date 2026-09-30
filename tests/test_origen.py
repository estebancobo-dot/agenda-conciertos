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
