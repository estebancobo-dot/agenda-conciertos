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
