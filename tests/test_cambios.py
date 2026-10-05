"""Historial de cambios de cada concierto (fase 7): qué se apunta y qué no."""
from datetime import date

from scraper.pipeline import conciliar, foto_cambios, registrar_cambios
from tests.test_dedup import HOY, ev, run, src


def rec(**kw):
    r = {"id": "a1", "fecha": "2026-10-10", "artista": "Grupo Q", "sala": "Sala El Sol", "hora": "21:00",
         "precio": "15€", "estado": "1_fuente", "invitados": [], "fuentes": [{"id": "x"}], "notas": []}
    r.update(kw)
    return r


def test_cambio_de_hora_y_precio():
    antes = foto_cambios([rec()])
    r = rec(hora="22:00", precio="18,00 EUR")
    assert registrar_cambios([r], antes, "2026-10-02") == 2
    assert [(c["campo"], c["antes"], c["despues"]) for c in r["cambios"]] == [("hora", "21:00", "22:00"),
                                                                              ("precio", "15€", "18,00 EUR")]


def test_lo_que_no_es_un_cambio():
    antes = foto_cambios([rec(hora=None, precio="15 €")])
    r = rec(hora="21:00", precio="15,00€")  # aparece una hora (dato nuevo) y el mismo precio escrito de otra forma
    assert registrar_cambios([r], antes, "2026-10-02") == 0 and "cambios" not in r
    # la hora pasa a salir de la página de entradas: otra web, no un cambio
    antes = foto_cambios([rec()])
    r = rec(hora="21:30", hora_pagina={"hora": "21:30"})
    assert registrar_cambios([r], antes, "2026-10-02") == 0


def test_ida_y_vuelta_no_queda():
    r = rec(hora="22:00")
    registrar_cambios([r], foto_cambios([rec()]), "2026-10-02")
    antes = foto_cambios([r])
    r2 = rec(hora="21:00", cambios=r["cambios"])
    registrar_cambios([r2], antes, "2026-10-03")
    assert "cambios" not in r2


def test_cancelado_agotado_y_cartel_una_sola_vez():
    antes = foto_cambios([rec()])
    r = rec(estado_evento={"tipo": "cancelado", "nombre": "La Ganzúa", "url": "u"}, agotado={"nombre": "Dice"},
            invitados=["Telonera"])
    assert registrar_cambios([r], antes, "2026-10-02") == 3
    assert {c["campo"] for c in r["cambios"]} == {"evento", "agotado", "cartel"}
    # la página se vuelve a leer y el telonero desaparece y vuelve: nada nuevo
    antes = foto_cambios([{**r, "invitados": [], "agotado": None, "estado_evento": None}])
    assert registrar_cambios([r], antes, "2026-10-03") == 0


def test_desaparece_y_reaparece():
    antes = foto_cambios([rec()])
    r = rec(estado="posiblemente cancelado")
    registrar_cambios([r], antes, "2026-10-02")
    antes = foto_cambios([r])
    r2 = rec(estado="1_fuente", cambios=r["cambios"])
    registrar_cambios([r2], antes, "2026-10-06")
    assert [c["campo"] for c in r2["cambios"]] == ["desaparece", "reaparece"]
    # faltó en una lectura y volvió el mismo día: no queda nada
    r3 = rec(estado="1_fuente", cambios=r["cambios"])
    registrar_cambios([r3], foto_cambios([r]), "2026-10-02")
    assert "cambios" not in r3


def test_otra_web_no_es_un_cambio():
    antes = foto_cambios([rec()])
    r = rec(hora="22:00", invitados=["Otra Banda"], fuentes=[{"id": "x"}, {"id": "sala_nueva"}])
    assert registrar_cambios([r], antes, "2026-10-03") == 0


def test_el_cabeza_escrito_de_otra_forma_no_es_cartel_nuevo():
    antes = foto_cambios([rec(artista="Ashleys")])
    r = rec(artista="Ashleys", invitados=["RADAR JOVEN 2026: ASHLEYS", "ASHLEYS", "Nenazas"])
    registrar_cambios([r], antes, "2026-10-03")
    assert r["cambios"][0]["nombres"] == ["Nenazas"]


def test_cambios_de_reglas_anteriores_se_descartan():
    antes = foto_cambios([rec(cambios=[{"dia": "2026-10-03", "campo": "cartel", "nombres": ["X"]}])])
    r = rec(cambios=[{"dia": "2026-10-03", "campo": "cartel", "nombres": ["X"]}])
    registrar_cambios([r], antes, "2026-10-04")
    assert "cambios" not in r


def test_cambio_de_fecha_conserva_el_concierto():
    s = src("mev")
    prev = run((ev("Grupo Q", "Sala El Sol", fecha=date(2026, 10, 10)), s))
    prev[0]["id"] = "p1"
    antes = foto_cambios(prev)
    nuevo = run((ev("Grupo Q", "Sala El Sol", fecha=date(2026, 11, 14)), s))
    out = conciliar(nuevo, prev, HOY, {"mev": {"funciono": True, "completa": True}}, {"mev": s})
    assert len(out) == 1 and out[0]["id"] == "p1" and out[0]["fecha"] == "2026-11-14"
    registrar_cambios(out, antes, HOY.isoformat())
    assert out[0]["cambios"][0] == {"dia": "2026-09-29", "campo": "fecha", "antes": "2026-10-10",
                                    "despues": "2026-11-14", "r": 2}


def test_dos_fechas_nuevas_no_se_adivina_cual():
    s = src("mev")
    prev = run((ev("Grupo Q", "Sala El Sol", fecha=date(2026, 10, 10)), s))
    prev[0]["id"] = "p1"
    nuevo = run((ev("Grupo Q", "Sala El Sol", fecha=date(2026, 11, 14)), s), (ev("Grupo Q", "Sala El Sol", fecha=date(2026, 11, 15)), s))
    out = conciliar(nuevo, prev, HOY, {"mev": {"funciono": True, "completa": True}}, {"mev": s})
    assert len(out) == 3 and any(r["id"] == "p1" and r["estado"] == "posiblemente cancelado" for r in out)


def test_otra_sala_no_es_cambio_de_fecha():
    s = src("mev")
    prev = run((ev("Grupo Q", "Sala El Sol", fecha=date(2026, 10, 10)), s))
    prev[0]["id"] = "p1"
    nuevo = run((ev("Grupo Q", "Sala Clamores", fecha=date(2026, 11, 14)), s))
    out = conciliar(nuevo, prev, date(2026, 9, 29), {"mev": {"funciono": True, "completa": True}}, {"mev": s})
    assert len(out) == 2


def test_cambio_de_sala_el_mismo_dia():
    s = src("revi")
    prev = run((ev("ItineruM", "Revi Space", fecha=date(2026, 11, 7)), s))
    prev[0]["id"] = "p1"
    antes = foto_cambios(prev)
    nuevo = run((ev("ItineruM", "Revi Live", fecha=date(2026, 11, 7)), s))
    out = conciliar(nuevo, prev, HOY, {"revi": {"funciono": True, "completa": True}}, {"revi": s})
    assert len(out) == 1 and out[0]["id"] == "p1" and out[0]["sala"] == "Revi Live"
    registrar_cambios(out, antes, HOY.isoformat())
    assert [(c["campo"], c["antes"], c["despues"]) for c in out[0]["cambios"]] == [("sala", "Revi Space", "Revi Live")]


def test_nombre_antiguo_de_la_sala_no_es_cancelacion_ni_cambio():
    s = src("mev")
    prev = [{"id": "p1", "fecha": "2026-11-07", "artista": "Grumpys", "sala": "El Perro de la parte de atrás del coche",
             "invitados": [], "fuentes": [{"id": "mev"}], "estado": "1_fuente", "notas": [], "hora": None}]
    antes = foto_cambios(prev)
    nuevo = run((ev("Grumpys", "El Perro Club", fecha=date(2026, 11, 7)), s))
    out = conciliar(nuevo, prev, HOY, {"mev": {"funciono": True, "completa": True}}, {"mev": s})
    assert len(out) == 1 and out[0]["id"] == "p1"
    assert registrar_cambios(out, antes, HOY.isoformat()) == 0


def test_festival_con_y_sin_la_palabra_festival():
    s = src("laganzua")
    prev = [{"id": "p1", "fecha": "2026-10-24", "artista": "Cadena 100 Por Ellas Festival 2026", "sala": "Movistar Arena",
             "invitados": [], "fuentes": [{"id": "laganzua"}], "estado": "1_fuente", "notas": [], "hora": None}]
    nuevo = run((ev("Cadena 100 Por Ellas 2026", "Movistar Arena", fecha=date(2026, 10, 24)), s))
    out = conciliar(nuevo, prev, HOY, {"laganzua": {"funciono": True, "completa": True}}, {"laganzua": s})
    assert not any(r["estado"] == "posiblemente cancelado" for r in out)


def test_misma_pagina_con_otro_titulo_no_queda_doble():
    s = src("mev")
    e = ev("CHEO PARDO FULL BANDA", "Tempo Audiophile Club", fecha=date(2026, 11, 28))
    prev = run((e, s))
    prev[0]["id"] = "p1"
    e2 = ev("PARDO FULL BANDA NY", "Tempo Audiophile Club", fecha=date(2026, 11, 28))
    e2.url = e.url  # la misma página de Madrid en Vivo
    nuevo = run((e2, s))
    out = conciliar(nuevo, prev, HOY, {"mev": {"funciono": True, "completa": True}}, {"mev": s})
    assert len(out) == 1


def test_nueva_fecha_queda_como_conflicto_en_los_dos():
    from scraper.pipeline import nueva_fecha_anunciada
    a = rec(id="a", fecha="2027-01-21", artista="Guille Galván", sala="Condeduque",
            fuentes=[{"id": "jl", "nombre": "JacksOnLive (agenda de Madrid)",
                      "url": "https://www.jacksonlive.es/concierto/concierto-de-guille-galvan-en-madrid-nueva-fecha"}],
            conflictos=[])
    b = rec(id="b", fecha="2027-01-22", artista="Guille Galván", sala="Condeduque",
            fuentes=[{"id": "cc", "nombre": "conciertos.club (buscador semanal)", "url": "https://conciertos.club/x"}],
            conflictos=[])
    otro = rec(id="c", fecha="2027-01-29", artista="Marwan", sala="Condeduque", conflictos=[])
    assert nueva_fecha_anunciada([a, b, otro], "2026-10-05") == 1
    for x in (a, b):
        c = x["conflictos"][0]
        assert x["estado"] == "conflicto" and c["campo"] == "fecha"
        assert [v["valor"] for v in c["versiones"]] == ["2027-01-21", "2027-01-22"] and "JacksOnLive" in c["motivo"]
    assert otro["estado"] == "1_fuente"
