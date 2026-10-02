import json
from datetime import date
from pathlib import Path

from scraper.sources.abiertos import parse

DATOS = json.loads((Path(__file__).parent / "fixtures" / "datos_madrid.json").read_text(encoding="utf-8"))


def test_datos_madrid_solo_conciertos():
    evs = parse(DATOS, date(2026, 10, 2), date(2027, 1, 30))
    t = [(e.fecha.isoformat(), e.artista) for e in evs]
    assert t == [("2026-10-23", "Alejandra Torres Rovira & Osvaldo Burucuá Dúo"), ("2026-11-04", "Andrés Coll Cosmic Trio"),
                 ("2026-10-10", "Banda Sinfónica Municipal"), ("2026-10-11", "Banda Sinfónica Municipal")]
    a, b, c = evs[0], evs[1], evs[2]
    assert (a.hora, a.precio, a.sala, a.ciudad) == ("19:00", "Gratis", "Centro Cultural San Juan Bautista (Ciudad Lineal)",
                                                    "MADRID")
    assert a.invitados == []  # "&" no separa artistas
    assert (b.hora, b.precio) == ("20:30", "12 euros")
    assert c.hora is None and c.precio == "Entrada libre hasta completar aforo"
    # fuera de la ventana: no sale
    assert not parse(DATOS, date(2026, 11, 5), date(2027, 1, 30))
