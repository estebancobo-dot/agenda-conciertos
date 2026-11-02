"""Science of Noise: el bloque «Datos del concierto» de cada previa (no el texto del artículo)."""
from datetime import date

from scraper.sources.blogs import scienceofnoise_articulo

HOY = date(2026, 11, 2)


def previa(bandas, fecha, lugar, horarios="Por confirmar", anticipada="27,50 €", taquilla="€"):
    return f"""<html><body><article><div class="entry-content">
    <h3>Datos del concierto</h3><p>Bandas: {bandas}<br>Fecha: {fecha}<br>Lugar: {lugar}<br>
    Organiza: Bring The Noise<br>Precio anticipada: {anticipada}<br>Precio taquilla: {taquilla}<br>
    Venta de entradas: https://www.bringthenoise.events/evento/x/<br>Horarios: {horarios}</p>
    <p>El próximo jueves 12 de noviembre será la única fecha española…</p></div></article></body></html>"""


def test_previa_de_madrid():
    r = scienceofnoise_articulo(previa("Käärijä", "12 de noviembre de 2026", "Mon Live (Madrid)"),
                                "https://www.scienceofnoise.net/la-previa-x/", HOY)[0]
    assert (r.fecha, r.artista, r.sala, r.ciudad, r.precio, r.hora) == (
        date(2026, 11, 12), "Käärijä", "Mon Live", "Madrid", "27,50 €", None)
    assert r.entradas == "https://www.bringthenoise.events/evento/x/"


def test_varias_bandas_puertas_y_otra_ciudad():
    r = scienceofnoise_articulo(previa("MASTER BOOT RECORD + FULCI", "20 de noviembre de 2026", "Sala Upload (Barcelona)",
                                       horarios="20:00 - Apertura de puertas", anticipada="24 €", taquilla="25 €"),
                                "https://x/", HOY)[0]
    assert r.artista == "MASTER BOOT RECORD" and r.invitados == ["FULCI"]
    assert r.ciudad == "Barcelona" and r.hora is None and r.precio == "24 € · 25 €"  # la apertura no es el comienzo


def test_sin_bloque_o_pasada():
    assert scienceofnoise_articulo("<html><body><p>Crónica del concierto</p></body></html>", "https://x/", HOY) == []
    assert scienceofnoise_articulo(previa("X", "1 de octubre de 2026", "Sala (Madrid)"), "https://x/", HOY) == []
