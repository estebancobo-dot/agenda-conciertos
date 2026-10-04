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
    assert not mismo_acto_en_sala("INTRUSO JAZZ SESSION", "INTRUSO ACID JAM!", "Intruso Bar")


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
    assert n == {"elsol": {"ausentes": 1, "otra_fecha": 0}}
    assert recs[1]["ausente_web_sala"] == "Fuente elsol" and "ausente_web_sala" not in recs[0]
    # si la web de la sala no se leyó entera, no se marca nada (y se quita lo de antes)
    assert ausencias_web_sala(recs, {"elsol": {"completa": False}}, {"elsol": s, **F}, {"elsol": evs}, "2026-10-03") == {}
    assert "ausente_web_sala" not in recs[1]
    # ni si se leyó entera pero da muchos menos conciertos de lo habitual (diseño cambiado, lectura a medias)
    assert ausencias_web_sala(recs, {"elsol": {"completa": True}}, {"elsol": s, **F}, {"elsol": evs}, "2026-10-03",
                              {"elsol": {"ultimo_conteo": 40}}) == {}
    # ni si hoy falló y sus conciertos son de la última lectura
    assert ausencias_web_sala(recs, {"elsol": {"completa": True, "desde_cache": 5}}, {"elsol": s, **F},
                              {"elsol": evs}, "2026-10-03") == {}


def test_la_web_de_la_sala_lo_anuncia_otro_dia():
    s = fuente("villanos", "sala", 1, "alta")
    evs = [RawEvent(date(2026, 10, d), f"Grupo {d}", "u", sala="Sala El Sol") for d in (10, 12, 13, 20)]
    evs.append(RawEvent(date(2026, 10, 19), "El Naan Trio", "u", sala="Sala El Sol"))
    recs = [rec("cc", fecha="2026-10-18", artista="EL NAAN TRIO")]
    n = ausencias_web_sala(recs, {"villanos": {"completa": True}}, {"villanos": s, **F}, {"villanos": evs}, "2026-10-03")
    r = recs[0]
    assert n == {"villanos": {"ausentes": 0, "otra_fecha": 1}} and "ausente_web_sala" not in r
    assert r["estado"] == "conflicto"
    c = r["conflictos"][0]
    assert c["campo"] == "fecha" and [v["valor"] for v in c["versiones"]] == ["2026-10-19", "2026-10-18"]
    conf = puntuar_confianza(r, F)
    assert conf["nivel"] == "sin confirmar" and "La web de la sala lo anuncia el 2026-10-19" in conf["motivos"]
    # al día siguiente la agenda ya lo corrige: el conflicto de fecha desaparece, sin acumularse
    r["fecha"] = "2026-10-19"
    ausencias_web_sala(recs, {"villanos": {"completa": True}}, {"villanos": s, **F}, {"villanos": evs}, "2026-10-03")
    assert not r["conflictos"]


def test_solo_de_la_ultima_lectura_no_llega_a_confirmado():
    r = rec("sala")
    r["fuentes"][0]["cache"] = "2026-10-01"
    c = puntuar_confianza(r, F)
    assert c["nivel"] == "probable" and any("2026-10-01" in m for m in c["motivos"])
    # si otra web lo da hoy, cuenta con normalidad
    r["fuentes"].append({"id": "tm", "nombre": "Fuente tm"})
    assert puntuar_confianza(r, F)["nivel"] == "confirmado"


def test_la_fuente_marca_lo_que_viene_de_su_cache():
    from scraper.pipeline import completar_con_cache
    s = fuente("elsol", "sala", 1, "alta")
    cache = {"elsol": {"fecha": "2026-10-01", "eventos": [RawEvent(date(2026, 10, 10), "X", "u", sala="Sala El Sol").to_dict()]}}
    eventos, resultados = {}, {"elsol": {"completa": False}}
    completar_con_cache([s], eventos, resultados, date(2026, 10, 3), date(2026, 12, 31), cache)
    recs = run((eventos["elsol"][0], s))
    assert recs[0]["fuentes"][0]["cache"] == "2026-10-01"


def test_una_grafia_por_sala_y_propuestas():
    recs = run((ev("Uno", "Teatro Salón Cervantes"), src("a")), (ev("Dos", "TEATRO SALÓN CERVANTES", fecha=date(2026, 10, 18)), src("b")))
    assert {r["sala"] for r in recs} == {"Teatro Salón Cervantes"}
    props = posibles_alias_salas([{"fecha": "2026-10-10", "sala": "Café Libertad Ocho", "artista": "A"},
                                  {"fecha": "2026-10-11", "sala": "Libertad Ocho Café", "artista": "B"}], "2026-10-01")
    assert props and props[0]["motivo"] == "nombres casi iguales"


def test_listado_incompleto_de_la_sala_no_penaliza():
    s = fuente("vistalegre", "sala", 1, "alta")
    evs = [RawEvent(date(2026, 10, d), f"Grupo {d}", "u", sala="Sala El Sol") for d in (10, 11, 12, 13, 30)]
    papa = rec("cc", "lg", "mev", fecha="2026-10-20", artista="Papa Roach")  # 3 webs independientes
    otro = rec("cc", fecha="2026-10-21", artista="Pequeño")
    n = ausencias_web_sala([papa, otro], {"vistalegre": {"completa": True}}, {"vistalegre": s, **F},
                           {"vistalegre": evs}, "2026-10-03")
    assert "Papa Roach" in n["vistalegre"]["incompleta"] and n["vistalegre"]["ausentes"] == 0
    assert "ausente_web_sala" not in papa and "ausente_web_sala" not in otro


def test_varias_salas_en_una_fuente_y_series():
    s = fuente("salas_js", "sala", 1, "alta")
    # Intruso publica una semana; Moe, un mes: lo que pasa de la semana de Intruso no se contrasta
    evs = [RawEvent(date(2026, 10, d), f"Intruso {d}", "u", sala="Intruso Bar") for d in (3, 4, 6, 7, 8)]
    evs += [RawEvent(date(2026, 10, 5), "Blues & Roots", "u", sala="Intruso Bar")]
    evs += [RawEvent(date(2026, 10, d), f"Moe {d}", "u", sala="Moe") for d in range(4, 31, 3)]
    jam = rec("cc", fecha="2026-10-12", artista="Blues & Roots", sala="Intruso Bar")
    n = ausencias_web_sala([jam], {"salas_js": {"completa": True}}, {"salas_js": s, **F}, {"salas_js": evs}, "2026-10-03")
    assert not jam["conflictos"] and "ausente_web_sala" not in jam and not n
    # una serie que la web anuncia varios días no es "otra fecha"
    evs2 = [RawEvent(date(2026, 10, d), "Jam de los martes", "u", sala="Sala El Sol") for d in (6, 13, 27)]
    evs2 += [RawEvent(date(2026, 10, d), f"G{d}", "u", sala="Sala El Sol") for d in (7, 8, 9, 10)]
    j = rec("cc", fecha="2026-10-20", artista="Jam de los martes")
    ausencias_web_sala([j], {"elsol": {"completa": True}}, {"elsol": fuente("elsol", "sala", 1), **F}, {"elsol": evs2},
                       "2026-10-03")
    assert not j["conflictos"]


def test_jams_con_otro_nombre_y_rellenos():
    from scraper.origen import sin_artista
    assert mismo_acto_en_sala("Jam Session Blues", "MOE BLUES JAM SESSION", "Moe")
    assert not mismo_acto_en_sala("Jam Session Jazz", "MOE BLUES JAM SESSION", "Moe")
    assert sin_artista("BAND NAME") and sin_artista("PIANO BAR") and not sin_artista("The Band")
