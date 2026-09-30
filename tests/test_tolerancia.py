"""Tolerancia a fallos de las fuentes: reintento dentro de la ejecución y caché de la última lectura completa."""
from datetime import date

from scraper import pipeline as P
from scraper.model import RawEvent, Source

HOY = date(2026, 9, 29)
HOR = date(2027, 1, 27)


class Bloqueo(Exception):
    pass


class F:
    """Fetcher mínimo para las fuentes de prueba."""
    def olvidar(self, url):
        pass

    def robots_status(self, url):
        return "ok"


def fuente(sid, parser):
    return Source(sid, sid.upper(), f"https://{sid}.test/", "sala", 1, "alta", sid, parser)


def ev(dia, artista, sid):
    return RawEvent(fecha=date(2026, 10, dia), artista=artista, url=f"https://{sid}.test/x", sala="Sala X", fuente=sid)


def test_reintento_dentro_de_la_ejecucion():
    llamadas = {"n": 0}

    def intermitente(ctx):
        llamadas["n"] += 1
        if llamadas["n"] == 1:
            raise Bloqueo("403 Client Error: Forbidden")
        yield ev(17, "Grupo A", "b")

    eventos, res = P.rastrear([fuente("b", intermitente)], F(), HOY, HOR, {}, pausa_reintento=0)
    assert res["b"]["funciono"] and res["b"]["reintento"] == "funcionó en el 2.º intento"
    assert [e.artista for e in eventos["b"]] == ["Grupo A"]


def test_fuente_caida_usa_su_ultima_lectura_completa():
    cache = {}
    s = fuente("g", None)
    # día 1: se lee bien → se guarda en caché
    eventos = {"g": [ev(17, "Hällas", "g"), ev(20, "Larsen", "g")]}
    res = {"g": {"funciono": True, "completa": True, "estado": "ok"}}
    P.completar_con_cache([s], eventos, res, HOY, HOR, cache)
    assert len(cache["g"]["eventos"]) == 2
    # día 2: 403 → sus conciertos siguen entrando, avisando de que son de la última lectura
    eventos = {"g": []}
    res = {"g": {"funciono": False, "completa": False, "estado": "bloqueado_403"}}
    P.completar_con_cache([s], eventos, res, date(2026, 9, 30), HOR, cache)
    assert [e.artista for e in eventos["g"]] == ["Hällas", "Larsen"]
    assert res["g"]["desde_cache"] == 2 and res["g"]["cache_fecha"] == "2026-09-29"
    assert "última lectura completa" in eventos["g"][0].nota
    # lectura parcial: se completa solo con lo que falta
    eventos = {"g": [ev(17, "Hällas", "g")]}
    res = {"g": {"funciono": True, "completa": False, "estado": "ok"}}
    P.completar_con_cache([s], eventos, res, date(2026, 9, 30), HOR, cache)
    assert sorted(e.artista for e in eventos["g"]) == ["Hällas", "Larsen"] and res["g"]["desde_cache"] == 1


def test_cache_caducada_no_se_usa():
    cache = {"g": {"fecha": "2026-09-01", "eventos": [ev(17, "Viejo", "g").to_dict()]}}
    eventos, res = {"g": []}, {"g": {"funciono": False, "completa": False}}
    P.completar_con_cache([fuente("g", None)], eventos, res, HOY, HOR, cache)
    assert eventos["g"] == []  # más de 14 días: la fuente pudo cambiar o desaparecer


def test_fuentes_no_leidas_en_un_reintento_entran_sin_aviso():
    cache = {"ok": {"fecha": "2026-09-29", "eventos": [ev(17, "Sabbat", "ok").to_dict()]}}
    eventos, res = {}, {"ok": {"funciono": True, "completa": True, "no_leida": True}}
    P.completar_con_cache([fuente("ok", None)], eventos, res, HOY, HOR, cache, no_leidas={"ok"})
    assert [e.artista for e in eventos["ok"]] == ["Sabbat"] and not eventos["ok"][0].nota
    assert cache["ok"]["fecha"] == "2026-09-29"  # no se reescribe con datos no leídos hoy


def test_avisos_de_fuentes():
    from datetime import date as d
    from scraper.pipeline import informe_fuentes
    s = fuente("mev", None)
    recs = [{"id": str(i), "fecha": "2026-10-01", "fuentes": [{"id": "mev"}]} for i in range(5)]
    hist = {"mev": {"ultima_ok": "2026-09-25", "ultimo_conteo": 40}}
    # lee, pero muchos menos de lo habitual
    f = informe_fuentes([s], {"mev": {"funciono": True, "brutos": 5}}, recs, set(), dict(hist), d(2026, 9, 30))[0]
    assert "muchos menos" in f["aviso"]
    # varios días sin leerse
    f = informe_fuentes([s], {"mev": {"funciono": False}}, [], set(), dict(hist), d(2026, 9, 30))[0]
    assert "5 días" in f["aviso"]
    # normal: sin aviso
    f = informe_fuentes([s], {"mev": {"funciono": True, "brutos": 40}}, recs * 8, set(), dict(hist), d(2026, 9, 30))[0]
    assert f["aviso"] is None
