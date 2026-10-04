from datetime import date
from pathlib import Path

from scraper.sources.agregadores import TOTALSTAGE, totalstage_parse

FIX = Path(__file__).parent / "fixtures"


def evs():
    return totalstage_parse((FIX / "totalstage.html").read_text(encoding="utf-8"), TOTALSTAGE, date(2026, 10, 4))


def test_lee_todos_los_conciertos():
    e = evs()
    assert len(e) == 12
    assert {x.artista for x in e} >= {"Bewitched", "Fyahbwoy", "Lolità", "Big Big Train"}


def test_hora_sala_y_estilo():
    f = next(x for x in evs() if x.artista == "Fyahbwoy")
    assert (f.fecha, f.hora, f.sala, f.ciudad, f.estilo) == (date(2026, 10, 4), "20:00", "La Riviera", "Madrid",
                                                           "Reggae/Ska")
    assert f.url == "https://totalstage.vercel.app/concierto/Fyahbwoy/2026-10-04"


def test_sin_hora_no_se_inventa():
    b = next(x for x in evs() if x.artista == "Bewitched")
    assert b.hora is None and b.sala == "Sala Silikona" and b.estilo is None
