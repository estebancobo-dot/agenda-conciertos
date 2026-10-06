"""Madrid en Vivo: hora y precio de la ficha del evento (API de la web), que el buscador no trae."""
from datetime import date

from scraper.model import RawEvent
from scraper.sources.agregadores import mev_datos_ficha


def ev(**kw):
    return RawEvent(date(2027, 2, 11), "CERVATANA", "https://madridenvivo.com/evento/cervatana/", **kw)


def test_hora_y_precio():
    e = ev()
    mev_datos_ficha(e, {"fecha_del_evento": "20270211", "hora_del_pase": [{"hora": "21:00"}],
                        "precio_del_evento": "20€", "entrada_libre": False})
    assert (e.hora, e.precio) == ("21:00", "20€")


def test_entrada_libre_varios_pases_y_otra_fecha():
    e = ev()
    mev_datos_ficha(e, {"fecha_del_evento": "20270211", "hora_del_pase": [{"hora": "19:00"}, {"hora": "22:00"}],
                        "precio_del_evento": "", "entrada_libre": True})
    assert e.hora == "19:00" and e.precio == "Entrada libre" and "19:00, 22:00" in e.nota
    otro = ev()
    mev_datos_ficha(otro, {"fecha_del_evento": "20270212", "hora_del_pase": [{"hora": "21:00"}]})
    assert otro.hora is None  # la ficha es de otro día
    ya = ev(hora="20:30", precio="15 €")
    mev_datos_ficha(ya, {"fecha_del_evento": "20270211", "hora_del_pase": [{"hora": "21:00"}], "precio_del_evento": "20€"})
    assert (ya.hora, ya.precio) == ("20:30", "15 €")  # lo que ya dice el listado no se toca


def test_enlace_de_compra_de_la_ficha():
    from scraper.entradas import aplicar_entradas
    e = ev()
    mev_datos_ficha(e, {"fecha_del_evento": "20270211", "venta_de_entradas_url": "https://feverup.com/m/677140?utm_source=x"})
    assert e.entradas.startswith("https://feverup.com/m/677140")
    mev_datos_ficha(otro := ev(), {"fecha_del_evento": "20270211", "venta_de_entradas_url": "no es un enlace"})
    assert otro.entradas is None
    fuente = {"nombre": "Madrid en Vivo (asociación de salas)", "id": "madridenvivo", "prioridad": 3,
              "url": "https://madridenvivo.com/evento/cervatana/", "entradas": e.entradas}
    r = {"artista": "Cervatana", "fecha": "2027-02-11", "fuentes": [fuente]}
    aplicar_entradas([r], {})
    assert r["entradas"] == {"url": "https://feverup.com/m/677140", "nombre": "Fever", "via": "Madrid en Vivo"}
    # la misma página de venta para tres artistas es la taquilla general, no la de este concierto
    taq = "https://taquilla.microteatro.es/madrid/programacion"
    rs = [{"artista": a, "fecha": "2027-02-11", "fuentes": [{**fuente, "url": f"https://madridenvivo.com/evento/{a}/",
                                                              "entradas": taq}]} for a in ("a", "b", "c")]
    aplicar_entradas(rs, {})
    assert not any("entradas" in x for x in rs)
