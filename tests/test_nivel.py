"""Nivel del concierto: tipo de recinto + oyentes de Last.fm con identidad segura; nunca adivinado."""
import json
from pathlib import Path

from scraper.nivel import audiencia_segura, nivel, oyentes_txt, tipo_recinto
from scraper.normalize import canon_sala

MBID = "identificador de MusicBrainz en Wikidata"


def aud(n, via=MBID):
    return {"audiencia": {"encontrado": True, "oyentes": n, "nombre": "Muse", "identificado_por": via}}


def test_tipo_de_recinto_por_lista_y_por_nombre():
    assert tipo_recinto("Movistar Arena") == "gran recinto"
    assert tipo_recinto("La Sala del Movistar Arena / Movistar Arena") == "sala grande"  # la primera con tipo
    assert tipo_recinto("Centro Cultural Eduardo Úrculo (Tetuán)") == "centro cultural"
    assert tipo_recinto("Basílica Pontificia de San Miguel") == "iglesia"
    assert tipo_recinto("Plaza Mayor") is None  # al aire libre: el tamaño no se sabe
    assert tipo_recinto("") is None and tipo_recinto(None) is None


def test_lista_de_salas_con_nombres_canonicos():
    d = json.loads((Path(__file__).resolve().parent.parent / "data" / "salas_tipo.json").read_text())
    vistos = set()
    for t, salas in d.items():
        if t.startswith("_"):
            continue
        for s in salas:
            assert canon_sala(s) == s, s  # si no, nunca coincidiría con la sala del concierto
            assert s not in vistos, s  # una sala, un tipo
            vistos.add(s)


def test_solo_cuentan_oyentes_con_identidad_segura():
    assert audiencia_segura(aud(5_000_000))["oyentes"] == 5_000_000
    assert audiencia_segura(aud(5_000_000, "coincidencia por nombre")) is None  # puede ser un homónimo
    assert audiencia_segura({"audiencia": {"encontrado": False}}) is None
    assert audiencia_segura({}) is None and audiencia_segura(None) is None


def test_niveles():
    cache = {"muse": aud(7_100_000), "local": aud(3_000), "homonimo": aud(9_000_000, "coincidencia por nombre")}
    g = nivel({"artista": "Muse", "sala": "Sala Villanos"}, cache)
    assert g["nivel"] == "gran formato" and g["oyentes"] == 7_100_000
    assert "7,1 M de oyentes" in g["motivo"] and "Sala Villanos: sala" in g["motivo"]
    assert nivel({"artista": "Local", "sala": "Movistar Arena"}, cache)["nivel"] == "gran formato"
    assert nivel({"artista": "Local", "sala": "Teatro Lope de Vega"}, cache)["nivel"] == "formato medio"
    assert nivel({"artista": "Local", "sala": "Intruso Bar"}, cache)["nivel"] == "formato íntimo"
    # el homónimo famoso no sube el nivel; sin sala con tipo y sin oyentes seguros no hay nivel
    assert nivel({"artista": "Homonimo", "sala": "Intruso Bar"}, cache)["nivel"] == "formato íntimo"
    assert nivel({"artista": "Homonimo", "sala": "Plaza Mayor"}, cache) is None
    assert nivel({"artista": "Desconocido", "sala": "Plaza Mayor"}, cache) is None


def test_tributos_y_festivales_no_usan_oyentes():
    cache = {"muse": aud(7_100_000)}
    assert nivel({"artista": "Muse", "sala": "Plaza Mayor", "grupos": ["tributos y versiones"]}, cache) is None
    assert nivel({"artista": "Muse", "sala": "Plaza Mayor", "festival": True}, cache) is None
    t = nivel({"artista": "Muse", "sala": "Intruso Bar", "grupos": ["tributos y versiones"]}, cache)
    assert t["nivel"] == "formato íntimo" and "oyentes" not in t


def test_texto_de_oyentes():
    assert oyentes_txt(7_100_000) == "7,1 M de oyentes"
    assert oyentes_txt(2_000_000) == "2 M de oyentes"
    assert oyentes_txt(45_600) == "46 mil oyentes"
    assert oyentes_txt(800) == "800 oyentes"


def test_buscar_audiencia():
    from scraper.artistas import buscar_audiencia
    from tests.fakefetch import FakeFetcher
    r = {"artist": {"name": "Muse", "url": "https://www.last.fm/music/Muse", "stats": {"listeners": "7100000"}}}
    f = FakeFetcher({"https://ws.audioscrobbler.com/*": lambda u, kw: json.dumps(r)})
    a = buscar_audiencia(f, "Muse", "9c9f1380", "k", MBID)
    assert a["oyentes"] == 7_100_000 and a["identificado_por"] == MBID and "mbid=9c9f1380" in f.urls[0]
    a = buscar_audiencia(f, "muse", None, "k")
    assert a["identificado_por"] == "coincidencia por nombre" and "autocorrect=0" in f.urls[1]
    assert not buscar_audiencia(f, "Muse Tribute", None, "k")["encontrado"]  # Last.fm devuelve otro nombre
    f = FakeFetcher({"https://ws.audioscrobbler.com/*": lambda u, kw: json.dumps({"error": 6, "message": "no"})})
    assert not buscar_audiencia(f, "X", None, "k")["encontrado"]
