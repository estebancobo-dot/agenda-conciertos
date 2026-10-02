"""Salas con The Events Calendar (API de WordPress): conciertos sí, sesiones de club no."""
from datetime import date

from scraper.sources.salas import tribe_parse

HOY, HOR = date(2026, 10, 2), date(2027, 1, 30)


def ev(titulo, inicio, cats=(), cost="", valores=None, **kw):
    return {"title": titulo, "start_date": inicio, "url": "https://sala/evento/x/", "cost": cost,
            "cost_details": {"values": valores or []}, "categories": [{"name": c} for c in cats], **kw}


def test_conciertos_y_no_clubbing():
    d = {"events": [ev("PINTURA ESPEJO + CAPRICHÖSA", "2026-10-02 21:00:00", ["Concierto"], "12€", ["12"]),
                    ev("TELECLUB: SAM S + ADRIEN", "2026-10-03 23:59:00", ["Clubbing"], "16€"),
                    ev("Antiguo", "2026-09-01 21:00:00", ["Concierto"])]}
    out = tribe_parse(d, "Café La Palma", "Madrid", HOY, HOR)
    assert len(out) == 1
    r = out[0]
    assert (r.artista, r.invitados, r.hora, r.precio, r.sala, r.estilo) == ("PINTURA ESPEJO", ["CAPRICHÖSA"], "21:00",
                                                                             "12 €", "Café La Palma", None)


def test_tributo_en_el_titulo_y_precio_largo():
    d = {"events": [ev("Matasuegras &#8211; Tributo Pop-Rock", "2026-10-09 23:30:00",
                       cost="Precio Anticipada: Entrada + Copa 10 € Entrada +Cerveza 6 € | Precio Taquillla: Entrada + Copa 12 €")]}
    r = tribe_parse(d, "Cadillac Solitario", "Madrid", HOY, HOR)[0]
    assert (r.artista, r.estilo, r.precio) == ("Matasuegras", "Tributo Pop-Rock", "6-12 €")


def test_categorias_de_genero_son_estilo():
    d = {"events": [ev("Delta Tango Romeo", "2026-10-08 21:00:00", ["Bolero", "Versiones"], "8€")]}
    r = tribe_parse(d, "Dime que me Quieres", "Madrid", HOY, HOR)[0]
    assert r.estilo == "Bolero, Versiones" and r.precio == "8 €"


def test_solo_conciertos_marcados():
    d = {"events": [ev("PALMEROS SOCIAL CLUB", "2026-10-30", ["Carrusel", "Palmeros"]),
                    ev("CELEBRA TU EVENTO EN CAFÉ LA PALMA", "2026-12-31", ["Actividades", "Carrusel"]),
                    ev("CARO TAXI", "2026-10-09 22:00:00", ["Concierto"])]}
    assert [r.artista for r in tribe_parse(d, "Café La Palma", "Madrid", HOY, HOR, r"conciertos?$")] == ["CARO TAXI"]
