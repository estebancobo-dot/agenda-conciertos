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
    registrar_cambios([r2], antes, "2026-10-04")
    assert [c["campo"] for c in r2["cambios"]] == ["desaparece", "reaparece"]


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
                                         "despues": "2026-11-14"}


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
