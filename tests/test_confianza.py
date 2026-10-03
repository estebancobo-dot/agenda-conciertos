"""Fase A: puntuación de confirmación, duplicados con otro nombre en la misma sala y día, ausencias en la web de la
sala, una grafía por sala y propuestas de alias."""
from datetime import date

from scraper.merge import mismo_acto_en_sala
from scraper.model import RawEvent, Source
from scraper.pipeline import ausencias_web_sala, posibles_alias_salas, puntuar_confianza
from tests.test_dedup import HOY, ev, run, src


def fuente(id_, tipo, prioridad, fiab="media", grupo=None):
    return Source(id_, f"Fuente {id_}", f"https://{id_}", tipo, prioridad, fiab, grupo or id_)


F = {"sala": fuente("sala", "sala", 1, "alta"), "mev": fuente("mev", "agregador", 3, "alta"),
     "cc": fuente("cc", "agregador", 3, "media"), "lg": fuente("lg", "agregador", 3, "media"),
     "blog": fuente("blog", "blog", 4, "baja"), "tm": fuente("tm", "ticketera", 2, "alta")}


def rec(*ids, **kw):
    r = {"fecha": "2026-10-10", "artista": "X", "sala": "Sala El Sol", "estado": "1_fuente",
         "fuentes": [{"id": i, "nombre": F[i].nombre} for i in ids], "conflictos": []}
    r.update(kw)
    return r


def test_niveles():
    assert puntuar_confianza(rec("sala"), F)["nivel"] == "confirmado"
    assert puntuar_confianza(rec("cc"), F)["nivel"] == "sin confirmar"
    assert puntuar_confianza(rec("mev"), F)["nivel"] == "probable"
    assert puntuar_confianza(rec("cc", "lg"), F)["nivel"] == "probable"
    assert puntuar_confianza(rec("cc", "lg", "tm"), F)["nivel"] == "confirmado"
    c = puntuar_confianza(rec("cc", "lg", "mev", "blog"), F)
    assert c["nivel"] == "confirmado" and "En 4 agendas" in c["motivos"][0]


def test_lo_que_resta():
    assert puntuar_confianza(rec("cc", "lg", conflictos=[{"campo": "hora"}]), F)["nivel"] == "sin confirmar"
    assert puntuar_confianza(rec("mev", "cc", ausente_web_sala="Sala El Sol"), F)["nivel"] == "sin confirmar"
    assert puntuar_confianza(rec("sala", estado="posiblemente cancelado"), F)["nivel"] == "sin confirmar"
    # un enlace de compra de la misma web que la agenda no confirma más
    assert puntuar_confianza(rec("cc", entradas={"nombre": "Fuente cc entradas"}), F)["nivel"] == "sin confirmar"
    assert puntuar_confianza(rec("cc", entradas={"nombre": "Dice"}), F)["nivel"] == "probable"


def test_mismo_acto_con_otro_nombre():
    assert mismo_acto_en_sala("THE DOORS ARE OPEN (Trib The Doors)", "EL GRAN TRIBUTO A THE DOORS")
    assert mismo_acto_en_sala("EMMA SWIFT (AUST-USA)", "Emma Swift with Luther Russell")
    assert mismo_acto_en_sala("CARO CAXI", "CARO TAXI")
    assert not mismo_acto_en_sala("Tributo a Queen", "Tributo a Mecano")
    assert not mismo_acto_en_sala("BLACK BIRDS", "THE BLACK CROWES")
    assert not mismo_acto_en_sala("Jam Session Blues", "Blues Night")


def test_se_unen_en_la_misma_sala_y_dia_a_hora_cercana():
    recs = run((ev("THE DOORS ARE OPEN (Trib The Doors)", "Honky Tonk", hora="21:30"), src("mev")),
               (ev("EL GRAN TRIBUTO A THE DOORS", "Honky Tonk", hora="21:30"), src("honky", 1)))
    assert len(recs) == 1
    # a cuatro horas de distancia son dos cosas
    recs = run((ev("Emma Swift (AUST-USA)", "Wurlitzer Ballroom", hora="19:00"), src("mev")),
               (ev("Emma Swift with Luther Russell", "Wurlitzer Ballroom", hora="23:30"), src("w", 1)))
    assert len(recs) == 2
    # siglas con puntos
    recs = run((ev("O.M.N.I", "El Perro Club"), src("perro", 1)), (ev("OMNI", "El Perro Club"), src("mev")))
    assert len(recs) == 1


def test_ausente_solo_si_la_sala_no_anuncia_nada_ese_dia():
    s = fuente("elsol", "sala", 1, "alta")
    evs = [RawEvent(date(2026, 10, d), f"Grupo {d}", "u", sala="Sala El Sol") for d in (10, 11, 12, 13, 20)]
    recs = [rec("cc", fecha="2026-10-11", artista="Otro nombre"),  # ese día la sala anuncia algo: no se marca
            rec("cc", fecha="2026-10-15", artista="Fantasma"),     # ese día la sala no anuncia nada
            rec("cc", fecha="2026-11-30", artista="Lejano")]       # más allá de lo que publica la sala
    n = ausencias_web_sala(recs, {"elsol": {"completa": True}}, {"elsol": s, **F}, {"elsol": evs}, "2026-10-03")
    assert n == 1 and recs[1]["ausente_web_sala"] == "Fuente elsol" and "ausente_web_sala" not in recs[0]
    # si la web de la sala no se leyó entera, no se marca nada
    assert ausencias_web_sala(recs, {"elsol": {"completa": False}}, {"elsol": s, **F}, {"elsol": evs}, "2026-10-03") == 0


def test_una_grafia_por_sala_y_propuestas():
    recs = run((ev("Uno", "Teatro Salón Cervantes"), src("a")), (ev("Dos", "TEATRO SALÓN CERVANTES", fecha=date(2026, 10, 18)), src("b")))
    assert {r["sala"] for r in recs} == {"Teatro Salón Cervantes"}
    props = posibles_alias_salas([{"fecha": "2026-10-10", "sala": "Café Libertad Ocho", "artista": "A"},
                                  {"fecha": "2026-10-11", "sala": "Libertad Ocho Café", "artista": "B"}], "2026-10-01")
    assert props and props[0]["motivo"] == "nombres casi iguales"
