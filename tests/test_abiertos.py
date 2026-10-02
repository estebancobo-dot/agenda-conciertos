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


def test_datos_madrid_estilo_del_texto_y_sin_actos_infantiles():
    d = {"@graph": [
        {"@type": "x/actividades/Musica", "title": "Concierto. Coral Polifónica", "dtstart": "2026-10-16 18:30:00.0",
         "event-location": "Centro Cultural el Torito (Moratalaz)"},
        {"@type": "x/actividades/Musica", "title": "Antonio Serrano y Kaele Jiménez Quartet. Jazz Caló for Coltrane",
         "dtstart": "2026-11-27 20:00:00.0", "event-location": "Conde Duque"},
        {"@type": "x/actividades/Musica", "title": "Audición de los alumnos de violín y piano", "dtstart": "2026-10-24 12:00:00.0"},
        {"@type": "x/actividades/Musica", "title": "Caperucita cumple años", "dtstart": "2026-10-03 12:00:00.0"},
        {"@type": "x/actividades/Musica", "title": "Concierto en el Amazonas", "dtstart": "2026-10-24 18:00:00.0",
         "audience": "Niños,Familias"},
        {"@type": "x/actividades/Musica", "title": "Carlos Escobedo", "dtstart": "2026-10-03 19:00:00.0"}]}
    evs = parse(d, date(2026, 10, 2), date(2027, 1, 30))
    assert [(e.artista, e.estilo) for e in evs] == [("Concierto. Coral Polifónica", "Música clásica"),
                                                   ("Antonio Serrano y Kaele Jiménez Quartet. Jazz Caló for Coltrane", "Jazz"),
                                                   ("Carlos Escobedo", None)]  # sin estilo si nada lo dice
