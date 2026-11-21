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


def test_diseno_de_noviembre_2026():
    # hora en su propio <span>, línea 'sala · Madrid [· hora por confirmar]' y el estilo fuera del enlace
    e = totalstage_parse((FIX / "totalstage_2026_11.html").read_text(encoding="utf-8"), TOTALSTAGE,
                         date(2026, 11, 21))
    por = {x.artista: x for x in e}
    assert set(por) == {"Aga", "Manuel Jesús", "L.A. Guns"}
    assert (por["Aga"].fecha, por["Aga"].hora, por["Aga"].sala, por["Aga"].ciudad) == (
        date(2026, 11, 21), "12:30", "Fun House", "Madrid")
    assert por["Manuel Jesús"].estilo == "Pop" and por["Manuel Jesús"].sala == "Tempo Audiophile Club"
    assert por["L.A. Guns"].hora is None and por["L.A. Guns"].sala == "Nazca"
