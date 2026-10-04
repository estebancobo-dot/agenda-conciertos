"""Fase C: hora habitual de la sala (estimada) y origen estimado por las agendas locales."""
from scraper.normalizacion import estado_hora, estimar_horas
from scraper.pipeline import pais_por_agendas_locales


def rec(hora=None, sala="Sala El Sol", **kw):
    r = {"fecha": "2026-10-10", "artista": "X", "hora": hora, "sala": sala, "fuentes": [], "conflictos": []}
    r.update(kw)
    return r


def test_hora_habitual_de_la_sala():
    recs = [rec("21:00") for _ in range(8)] + [rec("20:00"), rec("22:30")] + [rec(None)]
    otra = [rec("20:00", sala="Otra"), rec("21:00", sala="Otra"), rec(None, sala="Otra")]
    conflicto = rec(None, conflictos=[{"campo": "hora", "versiones": [{"valor": "20:00"}, {"valor": "21:00"}]}])
    todos = recs + otra + [conflicto]
    assert estimar_horas(todos) == 1
    sin = recs[-1]
    assert sin["hora_estimada"]["hora"] == "21:00" and "8 de sus 10" in sin["hora_estimada"]["motivo"]
    assert "hora_estimada" not in otra[-1]       # Otra no tiene hora habitual clara
    assert "hora_estimada" not in conflicto       # con horas distintas en las webs no se estima
    e = estado_hora(sin)
    assert e["estado"] == "estimado" and e["valor"] == "21:00"


def test_origen_por_agendas_locales():
    loc = [{"id": "madridenvivo"}, {"id": "cc_buscador"}]
    assert pais_por_agendas_locales(rec(fuentes=loc, grupos=["pop e indie"]), "Los Rayos")[0] == "ES"
    assert pais_por_agendas_locales(rec(fuentes=loc, grupos=["pop e indie"]), "The Midnight Riders")[0] is None
    assert pais_por_agendas_locales(rec(fuentes=loc, grupos=["jazz y swing"]), "Cuarteto Vega")[0] is None
    assert pais_por_agendas_locales(rec(fuentes=loc + [{"id": "songkick"}], grupos=["pop e indie"]), "Los Rayos")[0] is None
