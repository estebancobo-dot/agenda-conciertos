from datetime import date
from pathlib import Path

from scraper.sources.agregadores import jackson_parse

FIX = Path(__file__).parent / "fixtures"
URL = "https://www.jacksonlive.es/madrid/conciertos/punk"


def evs():
    return jackson_parse((FIX / "jacksonlive_punk.html").read_text(encoding="utf-8"), URL, date(2026, 10, 4))


def test_datos_del_concierto():
    b = next(e for e in evs() if e.artista == "The Buzz Lovers")
    assert (b.fecha, b.hora, b.sala, b.ciudad, b.precio, b.estilo) == (
        date(2026, 10, 9), "19:00", "Sala Changó", "Madrid", "desde 15,00 €", "Rock")
    assert b.invitados == ["Green Land"]
    assert b.url.endswith("/concierto-de-the-buzz-lovers-en-madrid")


def test_sin_precio_ni_hora_no_se_inventan():
    s = next(e for e in evs() if e.artista == "STVW")
    assert s.precio is None and s.hora == "20:00"
    x = next(e for e in evs() if e.sala == "Sala Margarita")
    assert x.hora is None and x.ciudad == "Alcalá de Henares" and x.artista == "X"


def test_cancelados_fuera():
    assert all(e.artista != "Y" for e in evs())
    assert len(evs()) == 3
