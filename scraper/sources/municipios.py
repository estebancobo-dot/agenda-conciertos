"""Agendas culturales municipales. Solo se usan si la agenda es legible: se toman los eventos con datos
estructurados (JSON-LD) o, si no hay, las entradas 'título + fecha' cuyo título indica música en directo."""
from __future__ import annotations

import re

from .base import Ctx, jsonld_events, ld_to_raw, soup_of
from .salas import secuencia

MUSICA = re.compile(r"(?i)concierto|en concierto|m[uú]sica en directo|rock|blues|folk|country|metal|punk|banda|"
                    r"tributo|festival|jazz|pop|cantautor|recital|orquesta|coro")

AGENDAS = {
    "Alcalá de Henares": "https://www.ayto-alcaladehenares.es/agenda/",
    "Getafe": "https://www.getafe.es/agenda/",
    "Leganés": "https://www.leganes.org/agenda",
    "Móstoles": "https://www.mostoles.es/es/agenda",
    "Fuenlabrada": "https://www.ayto-fuenlabrada.es/agenda",
    "Alcorcón": "https://www.ayto-alcorcon.es/agenda",
    "Rivas-Vaciamadrid": "https://www.rivasciudad.es/agenda/",
    "Coslada": "https://www.ayto-coslada.es/agenda",
    "Torrejón de Ardoz": "https://www.ayto-torrejon.es/agenda",
    "Parla": "https://www.ayuntamientoparla.es/agenda",
    "Alcobendas": "https://www.alcobendas.org/es/agenda",
    "San Sebastián de los Reyes": "https://www.ssreyes.org/es/agenda",
    "Las Rozas de Madrid": "https://www.lasrozas.es/agenda",
    "Majadahonda": "https://www.majadahonda.org/agenda",
    "Pozuelo de Alarcón": "https://www.pozuelodealarcon.org/agenda",
    "Boadilla del Monte": "https://www.aytoboadilla.com/agenda",
    "Collado Villalba": "https://www.collado-villalba.es/agenda",
    "Aranjuez": "https://www.aranjuez.es/agenda",
    "Arganda del Rey": "https://www.ayto-arganda.es/agenda",
    "Valdemoro": "https://www.valdemoro.es/agenda",
    "Pinto": "https://www.ayto-pinto.es/agenda",
}


def municipal_parse(html: str, url: str, today, municipio: str) -> list:
    s = soup_of(html)
    out = []
    for ev in jsonld_events(s):
        r = ld_to_raw(ev, today, url)
        if r and MUSICA.search(r.artista):
            r.ciudad = r.ciudad or municipio
            out.append(r)
    if out:
        return out
    for e in secuencia(html, url, today, ciudad=municipio):
        if MUSICA.search(e.artista):
            e.nota = "Tomado de la agenda municipal: el título incluye referencia musical."
            out.append(e)
    return out


def hacer(municipio: str, url: str):
    def run(ctx: Ctx):
        yield from municipal_parse(ctx.get(url), url, ctx.today, municipio)
    return run
