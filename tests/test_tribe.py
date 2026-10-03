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


def test_cafe_central():
    from scraper.sources.salas import cafecentral_parse
    html = """<div class="event-item hidden" data-event-date=2026-10-02 data-end-date=2026-10-03 data-venue-id=x>
      <a href=https://cafecentralmadrid.com/events/tazelaar/><img src=/uploads/events/t.webp></a>
      <a href=https://cafecentralmadrid.com/events/tazelaar/><h2>TAZELAAR &amp; ARTVED QUARTET</h2></a>
      <div><span>viernes 2-sábado 3 oct.</span></div><div><span>8PM &amp; 10PM</span></div><div><span>Café Central Ateneo</span></div></div>
      <div class="event-item" data-event-date=2026-09-30 data-end-date=2026-10-01><h2>PASADO</h2><span>9PM</span></div>
      <div class="event-item" data-event-date=2026-10-20 data-end-date=2026-10-20><h2>X</h2><span>7:30 PM</span>
      <span>La Cátedra (Auditorio)</span></div>"""
    out = cafecentral_parse(html, "https://cafecentralmadrid.com/programacion/", HOY)
    assert [(r.fecha.isoformat(), r.artista, r.hora, r.sala) for r in out] == [
        ("2026-10-02", "TAZELAAR & ARTVED QUARTET", "20:00", "Café Central Ateneo"),
        ("2026-10-03", "TAZELAAR & ARTVED QUARTET", "20:00", "Café Central Ateneo"),
        ("2026-10-20", "X", "19:30", "La Cátedra")]
    assert out[0].imagen == "https://cafecentralmadrid.com/uploads/events/t.webp"


def test_clamores():
    from scraper.sources.salas import clamores_parse
    def item(href, dow, d, mes, precio, hora, titulo):
        return f"""<div class="collection-item-post"><a href="{href}"><div class="date-component-calendar dayclass">{dow}</div>
          <div class="date-component-calendar-2">{d}</div><div class="date-component-calendar-3 dateclass">{mes}</div>
          <img src="https://cdn/x.jpg"><h1 class="post-heading">{precio}</h1><div class="date-component-calendar4">{hora}</div>
          <h2 class="heading-4">{titulo}</h2></a></div>"""
    html = (item("/eventos/a", "Saturday", 3, "October", "14€ + G.G.", "17:30", "Manu Míguez (Folk)")
            + item("/eventos/b", "Saturday", 3, "October", "10€ + G.G.", "22:00", "Los Blody + Lavin + Jike (Rock &amp; Roll)")
            + item("/eventos/c", "Saturday", 3, "October", "Dsd Free", "23:55", "Clamores Dance Club: Kennah (Urban)")
            + item("/eventos/d", "Monday", 4, "January", "12€", "21:00", "Grupo de enero")
            + item("/eventos/e", "Sunday", 11, "October", "12€", "21:00", "Esto no es un trío (Comedia)")
            + item("/eventos/f", "Friday", 9, "October", "Dsd Free", "23:55", "Perreo Baby by Maggie &amp; Noree")
            + item("/eventos/g", "Saturday", 17, "October", "Dsd Free", "23:55", "DaBasemnt Classics en Clamores Club"))
    out = clamores_parse(html, "https://www.salaclamores.es/calendario", date(2026, 10, 3))
    assert [(r.fecha.isoformat(), r.artista, r.invitados, r.hora, r.estilo, r.precio) for r in out] == [
        ("2026-10-03", "Manu Míguez", [], "17:30", "Folk", "14€ + G.G"),
        ("2026-10-03", "Los Blody", ["Lavin", "Jike"], "22:00", "Rock & Roll", "10€ + G.G"),
        ("2027-01-04", "Grupo de enero", [], "21:00", None, "12€")]
    assert out[0].url == "https://www.salaclamores.es/eventos/a"


def test_estilo_entre_parentesis_y_tras_punto():
    d = {"events": [ev("MUXU (Pop Rock) + MONKEY MOON (Punk Rock)", "2026-10-09 21:00:00", ["Conciertos"], valores=["10", "12"]),
                    ev("JUAN ZELADA · Soul / Funk / R&amp;B", "2026-10-10 22:00:00", ["Conciertos"]),
                    ev("ZEUHL DJ", "2026-10-10 23:30:00", ["DJs"]),
                    ev("EVENTO PRIVADO", "2026-10-07 17:00:00", ["Conciertos", "DJs"]),
                    ev("LAS ERAS (ARG)", "2026-11-22 21:00:00", ["Conciertos"]),
                    ev("VIOFLESH (Chile)", "2026-10-30 21:00:00", ["Conciertos"])]}
    out = tribe_parse(d, "El Perro Club", "Madrid", HOY, HOR, r"conciertos?$")
    assert [(r.artista, r.invitados, r.estilo, r.nacionalidad) for r in out] == [
        ("MUXU", ["MONKEY MOON"], "Pop Rock", None), ("JUAN ZELADA", [], "Soul, Funk, R&B", None),
        ("LAS ERAS", [], None, "AR"), ("VIOFLESH", [], None, None)]
    assert out[0].precio == "10-12 €"


def test_ticketandroll():
    import json
    from scraper.sources.salas import ticketandroll_parse
    def ld(nombre, inicio):
        return {"@context": "https://schema.org", "@type": "MusicEvent", "name": nombre, "startDate": inicio,
                "url": "https://ticketandroll.com/evento/x", "location": {"@type": "Place", "name": "Jazzville"}}
    html = "".join(f'<script type="application/ld+json">{json.dumps(x)}</script>' for x in [
        ld("JAVIER MACARRO EN JAZZVILLE", "2026-10-10T13:00"), ld("La del Pirata Cojo", "2026-10-03T21:00"),
        ld("THE VELVET HANDS en Hangar 48", "2026-10-14T21:00"), ld("Viejo", "2026-09-01T21:00")])
    out = ticketandroll_parse(html, "https://ticketandroll.com/local/jazzville", HOY, "Jazzville")
    assert [(r.artista, r.hora, r.sala) for r in out] == [("JAVIER MACARRO", "13:00", "Jazzville"),
                                                          ("La del Pirata Cojo", "21:00", "Jazzville"),
                                                          ("THE VELVET HANDS en Hangar 48", "21:00", "Jazzville")]
