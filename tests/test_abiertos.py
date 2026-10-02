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


def test_datos_madrid_descripcion_con_varios_generos_no_da_estilo():
    d = {"@graph": [{"@type": "x/actividades/Musica", "title": "Canciones para recordar", "dtstart": "2026-10-21 19:00:00.0",
                     "description": "Un recorrido del jazz al bolero y la copla."},
                    {"@type": "x/actividades/Musica", "title": "Trío Arbós", "dtstart": "2026-10-21 19:00:00.0",
                     "description": "Concierto de música de cámara."}]}
    assert [e.estilo for e in parse(d, date(2026, 10, 2), date(2027, 1, 30))] == [None, "Música clásica"]


def test_dos_coros_distintos_el_mismo_dia_no_se_unen():
    from scraper.merge import Item
    from scraper.pipeline import preparar, unificar
    from scraper.registry import por_id
    src = por_id()["datos_madrid"]
    d = {"@graph": [
        {"@type": "x/actividades/Musica", "title": "Concierto. Coral Polifónica Nuestra Señora de la Merced",
         "dtstart": "2026-10-24 20:30:00.0", "time": "20:30", "link": "https://madrid.es/a",
         "event-location": "Parroquia Nuestra Señora de la Merced"},
        {"@type": "x/actividades/Musica", "title": "Concierto. Coral Fundación Gredos San Diego",
         "dtstart": "2026-10-24 16:45:00.0", "time": "16:45", "link": "https://madrid.es/b", "event-location": ""}]}
    items, _ = preparar([Item(e, src) for e in parse(d, date(2026, 10, 2), date(2027, 1, 30))],
                        date(2026, 10, 2), date(2027, 1, 30))
    assert len(unificar(items)) == 2


def test_gotifiestas():
    from scraper.sources.abiertos import gotifiestas_parse
    datos = json.loads((Path(__file__).parent / "fixtures" / "gotifiestas.json").read_text(encoding="utf-8"))
    evs = gotifiestas_parse(datos, date(2026, 10, 2), date(2027, 1, 30))
    assert [(e.fecha.isoformat(), e.artista, e.invitados) for e in evs] == [
        ("2026-11-05", "BOUND BY ENDOGAMY", []),  # "(CH)" es su país y "TBA" no es un artista
        ("2026-10-02", "LEROY SE MEURT", ["WE ARE NOT BROTHERS"]),
        ("2026-12-12", "Dark Christmas Festival", []),
        ("2027-01-08", "SPAMMERHEADS Y AZOTE MENTAL", [])]  # la fiesta (Body Electric) no entra
    a = evs[0]
    assert (a.hora, a.precio, a.sala, a.estilo, a.nacionalidad) == ("20:30", "20,69 €", "Hangar 48", "EBM, Post-Punk", "CH")
    assert evs[1].precio is None and evs[2].tipo == "festival" and evs[2].hora is None


def test_gotifiestas_titulos():
    from scraper.sources.abiertos import _goti_titulo
    assert _goti_titulo("Entradas IST IST en MOBY DICK, MADRID 2026", "Moby Dick Club") == "IST IST"
    assert _goti_titulo("GREY GALLOWS – Cadavra Club – Madrid", "Cadavra") == "GREY GALLOWS"
    assert _goti_titulo("Suicide Commando “40th Anniversary Tour” // Madrid", "Nazca Music Live") == "Suicide Commando"
    assert _goti_titulo("Diorama – Bragolin – Carrellee // Madrid", "Nazca Music Live") == "Diorama – Bragolin – Carrellee"
    assert _goti_titulo("Chameleons “Arctic Tour 2026”", "Sala Mon Madrid Conciertos") == "Chameleons"
    assert _goti_titulo("Las Novias", "Sala El Sol") == "Las Novias"
