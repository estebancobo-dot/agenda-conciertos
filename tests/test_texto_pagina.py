"""Hora y precio escritos en el texto de la página del concierto (sin datos estructurados)."""
from bs4 import BeautifulSoup

from scraper.entradas import hora_precio_texto, leer_pagina


def tx(cuerpo: str) -> dict:
    return hora_precio_texto(BeautifulSoup(f"<html><body><nav>Menú 10:00</nav><main>{cuerpo}</main>"
                                           f"<footer>Taquilla 11:00 a 14:00</footer></body></html>", "html.parser"))


def test_hora_de_concierto_no_la_de_puertas():
    assert tx("<p>Apertura de puertas: 20:30h</p><p>Concierto: 21:30h</p>")["hora_t"] == "21:30"
    assert tx("<p>Hora: 21.00 h</p>").get("hora_t") is None  # "21.00" sin "h" pegada al número es ambigua (fechas)
    assert tx("<p>Inicio 21h00</p>")["hora_t"] == "21:00"


def test_dos_horas_de_concierto_no_se_adivina():
    assert "hora_t" not in tx("<p>Concierto 20:00</p><p>Segundo pase 22:30</p><p>Concierto 22:30</p>")


def test_fechas_no_son_horas():
    assert "hora_t" not in tx("<p>Sábado 20/10/2026</p><p>20.10.2026</p>")


def test_precio_junto_a_entrada():
    assert tx("<p>Entrada anticipada 12€ · Taquilla 15 €</p>")["precio_t"] == "12 € – 15 €"
    assert tx("<p>Precio: 8,50 euros</p>")["precio_t"] == "8,5 €"
    assert tx("<p>Entrada libre hasta completar aforo</p>")["precio_t"] == "Entrada libre"
    assert "precio_t" not in tx("<p>Cerveza 3 €</p>")  # un precio sin "entrada", "precio"… no cuenta


def test_jsonld_manda_sobre_el_texto():
    html = ('<script type="application/ld+json">{"@type":"MusicEvent","startDate":"2026-10-20T21:00",'
            '"offers":{"price":"15"}}</script><main><p>Concierto 22:00 · Entradas 20 €</p></main>')
    d = leer_pagina(html, "https://sala.es/x", "2026-10-20")
    assert d["hora"] == "21:00" and d["precio"] == "15 €" and "hora_t" not in d and "precio_t" not in d


def test_hora_habitual_por_dia_de_la_semana():
    from scraper.normalizacion import estimar_horas
    # domingos (2026-10-04, 11, 18, 25) a las 13:00; viernes a las 21:00
    recs = [{"sala": "Jazzville", "fecha": f, "hora": "13:00"} for f in ("2026-10-04", "2026-10-11", "2026-10-18")]
    recs += [{"sala": "Jazzville", "fecha": f, "hora": "21:00"} for f in ("2026-10-02", "2026-10-09", "2026-10-16")]
    dom = {"sala": "Jazzville", "fecha": "2026-10-25", "hora": None}
    vie = {"sala": "Jazzville", "fecha": "2026-10-23", "hora": None}
    estimar_horas(recs + [dom, vie])
    assert dom["hora_estimada"]["hora"] == "13:00" and "domingos" in dom["hora_estimada"]["motivo"]
    assert vie["hora_estimada"]["hora"] == "21:00"


def test_precio_con_gastos_de_una_web_que_siempre_los_suma():
    from scraper.entradas import aplicar_entradas
    cache, recs = {}, []
    for i, (sabido, web) in enumerate([("20€", "22 €"), ("15€", "16,5 €"), ("10€", "11 €"), ("30€", "33 €")]):
        u = f"https://www.songkick.com/concerts/{i}"
        cache[u] = {"fecha": "2026-10-05", "d": {"precio": web}, "v": 2}
        recs.append({"id": str(i), "artista": f"A{i}", "fecha": "2026-10-20", "precio": sabido, "conflictos": [],
                     "fuentes": [{"id": "songkick", "url": u, "nombre": "Songkick"}]})
    u = "https://www.songkick.com/concerts/99"
    cache[u] = {"fecha": "2026-10-05", "d": {"precio": "19,8 €"}, "v": 2}
    nuevo = {"id": "n", "artista": "B", "fecha": "2026-10-21", "precio": None, "conflictos": [],
             "fuentes": [{"id": "songkick", "url": u, "nombre": "Songkick"}]}
    aplicar_entradas(recs + [nuevo], cache)
    assert nuevo["precio"] == "19,8 €" and nuevo["precio_fuente"]["gastos"] is True
