"""Páginas de organizador de entradas.conciertos.club (salas cuya web no se puede leer)."""
from datetime import date

from scraper.sources.salas import cclub_evento_parse, cclub_parse

TARJETA = """<a title="{t}" class="event-card" href="/es/events/{slug}"><article>
<div class="date-price-badge"><div class="date {cls}"><span class="text-raro-700">{fecha}</span></div>
<div class="price"><span class="from">Desde</span><span>{precio}</span></div></div>
<div class="event-card-info"><div class="event-title">{t}</div><div class="event-venue"><span>{lugar}</span></div></div>
</article></a>"""


def pagina(*tarjetas):
    return "<html><body>" + "".join(TARJETA.format(**t) for t in tarjetas) + "</body></html>"


def t(titulo, fecha, lugar="Café Berlín, Madrid", precio="15,00 €", cls=""):
    return {"t": titulo, "slug": titulo.lower().replace(" ", "-"), "fecha": fecha, "precio": precio, "lugar": lugar,
            "cls": cls}


def test_tarjetas_del_organizador():
    html = pagina(t("El Búho presenta Hogar", "08 oct"),
                  t("AMYTHOLOGY “Tributo a Amy Winehouse” en Café Berlín", "09 oct"),
                  t("Anne Lukin", "18 mar"),
                  t("Christina Rosenvinge", "Varias<br>fechas", cls="several-dates"),
                  t("Otro sitio", "10 oct", lugar="Sala Clamores, Madrid"))
    evs, varias = cclub_parse(html, "https://entradas.conciertos.club/es/organizers/cafe-berlin", date(2026, 10, 3),
                              "Café Berlín")
    assert [(e.fecha.isoformat(), e.artista) for e in evs] == [
        ("2026-10-08", "El Búho presenta Hogar"),
        ("2026-10-09", "AMYTHOLOGY “Tributo a Amy Winehouse”"),   # sin "en Café Berlín"
        ("2027-03-18", "Anne Lukin")]                               # sin año: la próxima vez que cae
    assert evs[0].precio == "desde 15,00 €" and evs[0].sala == "Café Berlín"
    assert evs[0].url == "https://entradas.conciertos.club/es/events/el-búho-presenta-hogar"
    assert varias == ["https://entradas.conciertos.club/es/events/christina-rosenvinge"]


def test_pagina_de_un_concierto():
    html = """<h1><mark>El Búho presenta Hogar</mark></h1><div class="text-raro mt-3"><span class="me-4">
    <span class="me-3"><i class="icon-calendar"></i></span><span>8.10.2026</span></span>
    <span><span class="me-3"><i class="icon-clock"></i></span><span>22:30</span></span></div>"""
    evs = cclub_evento_parse(html, "https://x/e", date(2026, 10, 3), "Café Berlín")
    assert [(e.fecha.isoformat(), e.hora, e.artista) for e in evs] == [("2026-10-08", "22:30", "El Búho presenta Hogar")]
