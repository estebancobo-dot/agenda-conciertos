"""Identificar a un artista por los perfiles suyos que enlaza la página del concierto (Bandcamp, Instagram, Spotify…):
MusicBrainz dice qué artista los tiene enlazados, sin depender del nombre. Y el precio que pone Dice en su página."""
import json
from datetime import date

from bs4 import BeautifulSoup

import scraper.artistas as A
from scraper.entradas import _resumen, enlaces_artista, leer_pagina, precio_dice
from tests.fakefetch import FakeFetcher


def test_enlaces_de_artista_en_la_pagina():
    html = """<a href="https://open.spotify.com/intl-es/artist/3xuiqNVeSn3hpnWlAto2eq?si=x">Spotify</a>
      <a href="https://losdeltonos.bandcamp.com/">Bandcamp</a>
      <a href="https://www.instagram.com/losdeltonos/?hl=es">IG</a>
      <a href="https://www.instagram.com/p/C123/">una foto</a>
      <a href="https://www.facebook.com/sharer/sharer.php?u=x">compartir</a>
      <a href="https://soundcloud.com/losdeltonos">SC</a>
      <a href="https://agenda.es/instagram">propia</a>"""
    out = enlaces_artista(BeautifulSoup(html, "html.parser"), "https://agenda.es/concierto/1")
    assert out == ["https://open.spotify.com/artist/3xuiqNVeSn3hpnWlAto2eq", "https://losdeltonos.bandcamp.com",
                   "https://instagram.com/losdeltonos", "https://soundcloud.com/losdeltonos"]
    d = leer_pagina(f"<html><body>{html}</body></html>", "https://agenda.es/concierto/1")
    assert "enlaces_artista" in _resumen(d)  # se guarda en la caché de páginas


def test_precio_de_dice():
    assert precio_dice("Desde 15,00 €") == "desde 15 €"
    assert precio_dice("18,50 €") == "18,5 €"
    assert precio_dice("Desde gratis") == "Desde gratis"
    assert precio_dice("Agotado") is None
    html = ('<div data-testid="event-details-cta-price"><span>Desde 22,00 €</span><small>Este es el precio que '
            'pagarás.</small></div>')
    assert leer_pagina(html, "https://dice.fm/event/abc-madrid-tickets")["precio"] == "desde 22 €"
    assert "precio" not in leer_pagina(html, "https://otra.es/evento")  # solo en Dice


def test_enlaces_repetidos_en_muchos_artistas_no_son_del_artista():
    pag = {}
    recs = []
    for i, a in enumerate(["Los Deltonos", "Kmmn", "Muse"]):
        u = f"https://agenda.es/c{i}"
        pag[u] = {"d": {"enlaces_artista": ["https://instagram.com/agendaoficial", f"https://{i}.bandcamp.com"]}}
        recs.append({"artista": a, "fuentes": [{"url": u}]})
    recs.append({"artista": "Cartel A", "invitados": ["B"], "fuentes": [{"url": "https://agenda.es/c0"}]})
    de = A.enlaces_de_artistas(recs, pag)
    assert de["los deltonos"] == ["https://0.bandcamp.com"]  # el Instagram de la agenda sale con 3 artistas: fuera
    assert "cartel a" not in de  # en un cartel no se sabe de quién es cada enlace


def _mb(nombre_mb):
    return FakeFetcher({
        "https://musicbrainz.org/ws/2/url?resource=https%3A%2F%2Flosdeltonos.bandcamp.com*":
            lambda u, kw: json.dumps({"relations": [{"artist": {"id": "mb-1"}}]}),
        "https://musicbrainz.org/ws/2/artist/mb-1*":
            lambda u, kw: json.dumps({"id": "mb-1", "name": nombre_mb, "country": "ES", "genres": []}),
        "https://musicbrainz.org/ws/2/artist?query=*": lambda u, kw: json.dumps({"artists": []}),
    })


def _enriquecer(mb):
    recs = [{"artista": "Los Deltonos", "en_foco": True, "fecha": "2026-10-20",
             "fuentes": [{"url": "https://agenda.es/c1"}]}]
    pag = {"https://agenda.es/c1": {"d": {"enlaces_artista": ["https://losdeltonos.bandcamp.com"]}}}
    cache = {"los deltonos": {"nombre": "Los Deltonos", "fecha": "2026-10-01", "wikipedia": {"encontrado": False},
                              "discogs": {"encontrado": False, "motivo": "sin coincidencia exacta"},
                              "musicbrainz": {"encontrado": False, "motivo": "sin coincidencia exacta"}}}
    A.enriquecer(recs, cache, date(2026, 10, 10), fetcher_dc=FakeFetcher({}), fetcher_wp=FakeFetcher({}),
                 fetcher_lf=FakeFetcher({}), clave_lastfm="", fetcher_mb=mb, mb_cache={}, paginas=pag)
    return cache["los deltonos"]


def test_identificado_por_su_bandcamp():
    ent = _enriquecer(_mb("Los Deltonos"))
    assert ent["enlaces"]["mbid"] == "mb-1" and ent["musicbrainz"]["pais"] == "ES"
    assert "losdeltonos.bandcamp.com" in ent["musicbrainz"]["identificado_por"]


def test_si_la_pagina_enlazada_es_de_otro_artista_no_se_usa():
    ent = _enriquecer(_mb("Otro Grupo"))
    assert not ent["musicbrainz"]["encontrado"] and "otro artista" in ent["musicbrainz"]["motivo"]
