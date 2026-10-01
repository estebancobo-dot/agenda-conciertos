"""Estilos concretos de Madrid en Vivo por la API de WordPress de la web (además de la categoría del buscador)."""
import json
from datetime import date

from scraper.sources.agregadores import mev_estilos_api
from scraper.sources.base import make


class Ctx:
    def __init__(self):
        self.errors = []

    def get(self, u, **k):
        if "/evento?" in u:
            if "page=1" in u:
                return json.dumps([{"id": 1, "link": "https://madridenvivo.com/evento/sr-chinarro-2/", "tags": [10, 11]},
                                   {"id": 794616, "link": "https://madridenvivo.com/evento/x/", "tags": [12]}])
            return "[]"
        return json.dumps([{"id": 10, "name": "#Folk-Rock"}, {"id": 11, "name": "Madrid"}, {"id": 12, "name": "#Indie"}])


def test_estilos_por_la_api():
    a = make(date(2026, 10, 1), "SR. CHINARRO", "https://madridenvivo.com/evento/sr-chinarro-2/", estilo="Pop / Rock")
    b = make(date(2026, 10, 1), "THE PASTOS GANSOS", "https://madridenvivo.com/?post_type=evento&p=794616",
             estilo="Pop / Rock")
    c = make(date(2026, 10, 1), "OTRO", "https://madridenvivo.com/evento/otro/", estilo="Pop / Rock")
    assert mev_estilos_api(Ctx(), [a, b, c]) == 2
    assert a.estilo == "Folk Rock"      # la etiqueta "Madrid" no es un estilo: no cuenta
    assert b.estilo == "Indie"          # enlace corto "?p=": se reconoce por el identificador
    assert c.estilo == "Pop / Rock"     # sin estilos en la API: se queda la categoría del buscador
