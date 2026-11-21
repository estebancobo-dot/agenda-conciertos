"""Madrid en Vivo: eventos con varias fechas ("Todos los VIERNES del … al …"). El buscador solo da la primera."""
from datetime import date
from pathlib import Path

from scraper.model import RawEvent
from scraper.sources import agregadores as ag
from scraper.sources.base import Ctx

FIX = Path(__file__).parent / "fixtures"
HOY = date(2026, 11, 21)


def test_dias_de_la_semana_del_rango():
    assert ag.mev_dias("Todos los VIERNES del 06/11/2026 al 27/11/2026", HOY, date(2027, 1, 1)) == [date(2026, 11, 27)]
    assert ag.mev_dias("Todos los JUEVES y SÁBADOS del 01/11/2026 al 30/11/2026", HOY, date(2027, 1, 1)) == [
        date(2026, 11, 21), date(2026, 11, 26), date(2026, 11, 28)]
    # como mucho las 8 próximas
    assert len(ag.mev_dias("Todos los días del 01/07/2026 al 31/12/2026", HOY, date(2027, 1, 1))) == 8
    assert ag.mev_dias("28 de noviembre del 2026", HOY, date(2027, 1, 1)) is None
    assert ag.mev_dias("Todos los VIERNES del 06/11/2026 al 13/11/2026", HOY, date(2027, 1, 1)) == []  # terminó


def test_ficha_del_evento():
    assert ag.mev_ficha_fechas((FIX / "mev_evento_recurrente.html").read_text(encoding="utf-8")) == {
        "dias": "Todos los VIERNES del 06/11/2026 al 27/11/2026", "hora": None}   # "Pase: 00:00h": sin hora
    un_dia = ag.mev_ficha_fechas((FIX / "mev_evento_un_dia.html").read_text(encoding="utf-8"))
    assert un_dia["dias"] == "" and un_dia["hora"] == "20:30"


class F:
    def __init__(self):
        self.urls = []

    def get(self, url, **kw):
        self.urls.append(url)
        nombre = "mev_evento_recurrente" if "mr-black" in url else "mev_evento_un_dia"
        return (FIX / f"{nombre}.html").read_text(encoding="utf-8")


def test_cambia_la_fecha_pasada_por_las_proximas():
    f = F()
    ctx = Ctx(fetcher=f, today=HOY, horizon=date(2027, 11, 21), estado={})
    black = RawEvent(fecha=date(2026, 11, 6), artista="MR. BLACK", url="https://madridenvivo.com/evento/mr-black-20/",
                     sala="Jazzville")
    futuro = RawEvent(fecha=date(2026, 12, 1), artista="Otro", url="https://madridenvivo.com/evento/otro/")
    pasado = RawEvent(fecha=date(2026, 11, 5), artista="Un día", url="https://madridenvivo.com/evento/un-dia/")
    out = ag.mev_recurrentes(ctx, [black, futuro, pasado])
    assert [(e.artista, str(e.fecha)) for e in out] == [("MR. BLACK", "2026-11-27"), ("Otro", "2026-12-01"),
                                                         ("Un día", "2026-11-05")]   # sin varias fechas: igual
    assert "Todos los VIERNES" in out[0].nota and out[0].sala == "Jazzville"
    assert len(f.urls) == 2   # solo las páginas de los que tenían la fecha pasada
    # la siguiente pasada usa lo guardado (no vuelve a pedir la página en una semana)
    ag.mev_recurrentes(ctx, [black])
    assert len(f.urls) == 2
    # el que ya no sale en el buscador se olvida
    ag.mev_recurrentes(ctx, [futuro])
    assert ctx.estado["recurrentes"] == {}
