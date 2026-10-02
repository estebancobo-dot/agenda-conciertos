from datetime import date

from scraper.model import Source
from scraper.pipeline import metricas_fuente, salas_sin_fuente, salud_fuente

S = Source("a", "Agenda A", "https://a", "agregador", 3, "media", "a")


def _r(fuentes, conflictos=None, hora="21:00", estilo=None, precio=None, sala="Sala X", sala_ok=False, fecha="2026-10-10"):
    return {"fecha": fecha, "hora": hora, "sala": sala, "municipio": "Madrid",
            "fuentes": [{"id": f, "nombre": {"a": "Agenda A", "b": "Agenda B", "c": "Agenda C"}[f]} for f in fuentes],
            "conflictos": conflictos or [], "estilo_fuente": [{"estilo": "Rock", "fuente": estilo}] if estilo else [],
            "precio_fuente": {"nombre": precio} if precio else None,
            "confirmado_sala": {"nombre": "Sala"} if sala_ok else None}


def test_metricas():
    grupo = {"a": "a", "b": "b", "c": "c"}
    contra = [{"campo": "hora", "versiones": [{"valor": "20:00", "fuentes": ["Agenda A"]},
                                              {"valor": "21:00", "fuentes": ["Agenda B", "Agenda C"]}]}]
    mios = [_r(["a"], estilo="Agenda A"), _r(["a", "b"], precio="Agenda A"), _r(["a", "b", "c"], contra, hora=None),
            _r(["a", "c"])]
    m = metricas_fuente(S, mios, grupo)
    assert m["otra_web"] == 75 and m["comparte"] == 3
    assert m["coincide"] == 67  # lleva la contraria en 1 de los 3 que comparte
    assert (m["hora"], m["precio"], m["estilo"]) == (75, 25, 25)


def test_salud_14_dias():
    dias = {"2026-09-01": {"ok": 1, "n": 1}}
    salud_fuente(dias, {"funciono": True, "brutos": 10, "completa": True}, 10, date(2026, 10, 2))
    out = salud_fuente(dias, {"funciono": False, "brutos": 0, "estado": "error"}, 10, date(2026, 10, 2))
    assert out == [{"fecha": "2026-10-02", "ok": 1, "n": 2, "c": 10, "e": "error"}]  # lo de hace un mes se olvida
    # una ejecución que no la lee (reintento de otras) no cuenta
    assert salud_fuente(dias, {"no_leida": True}, 10, date(2026, 10, 2))[0]["n"] == 2


def test_salas_sin_fuente():
    recs = [_r(["a"], sala="Café Berlín") for _ in range(5)] + [_r(["a"], sala="Sala X", sala_ok=True) for _ in range(5)]
    recs += [_r(["a"], sala="Bar Pequeño")]
    out = salas_sin_fuente(recs, date(2026, 10, 2))
    assert [x["sala"] for x in out] == ["Café Berlín"] and out[0]["conciertos"] == 5
    assert out[0]["motivo"] and "carteles" in out[0]["motivo"]  # el de la lista de salas sin agenda legible


def test_cambio_de_diseno():
    from datetime import date as d

    from scraper.model import RawEvent
    from scraper.pipeline import cambio_de_diseno, campos_leidos
    antes = campos_leidos([RawEvent(fecha=d(2026, 10, i % 28 + 1), artista="x", url="u", sala="S", hora="21:00")
                           for i in range(20)])
    sin_hora = campos_leidos([RawEvent(fecha=d(2026, 10, i % 28 + 1), artista="x", url="u", sala="S") for i in range(20)])
    mismo_dia = campos_leidos([RawEvent(fecha=d(2026, 10, 2), artista="x", url="u", sala="S", hora="21:00")
                               for i in range(20)])
    assert "ya no se lee la hora" in cambio_de_diseno(antes, sin_hora)
    assert "mismo día" in cambio_de_diseno(antes, mismo_dia)
    assert cambio_de_diseno(antes, antes) is None and cambio_de_diseno(None, sin_hora) is None
