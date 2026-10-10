"""Varias lecturas seguidas, días distintos, con el estado guardado entre una y otra (data/estado.json y la caché de
cada fuente), como pasa en GitHub: una agenda que cae y vuelve, el reintento de cada 2 horas, una fuente congelada,
la caché de 14 días y lo que nadie reconfirma en un mes. Cada pieza tiene su prueba; aquí, que encajan día a día."""
import json
from datetime import date, timedelta

import pytest

from scraper import pipeline
from scraper.model import RawEvent, Source
from tests.fakefetch import FakeFetcher

D0 = date(2026, 10, 1)
CONCIERTO = D0 + timedelta(days=60)  # dentro del horizonte durante toda la prueba


def ev(artista, sala, sid, hora="21:00"):
    return RawEvent(fecha=CONCIERTO, artista=artista, url=f"https://{sid}.es/{artista}", sala=sala, ciudad="Madrid",
                    hora=hora)


@pytest.fixture
def lectura(tmp_path, monkeypatch):
    """lectura(días desde D0, **opciones) con lo que dé cada fuente según `plan` ("falla": la web no responde)."""
    plan = {}

    def fuente(sid, nombre, tipo, prioridad):
        def parser(ctx):
            if plan[sid] == "falla":
                raise RuntimeError("la web no responde")
            yield from plan[sid]
        return Source(sid, nombre, f"https://{sid}.es", tipo, prioridad, "alta", sid, parser)

    monkeypatch.setattr(pipeline, "DATA", tmp_path)
    monkeypatch.setattr(pipeline, "FUENTES", [fuente("salaa", "Sala A (web oficial)", "sala", 1),
                                              fuente("agb", "Agenda B", "agregador", 2)])
    monkeypatch.setattr(pipeline, "load_json", lambda n: {"correcciones": []} if n == "correcciones.json"
                        else json.loads((pipeline.Path(__file__).parent.parent / "data" / n).read_text()))

    def leer(dias, **kw):
        inf = pipeline.ejecutar(hoy=D0 + timedelta(days=dias), musicbrainz=False, pausa_reintento=0,
                                fetcher=FakeFetcher({}), **kw)
        recs = {r["artista"]: r for r in json.loads((tmp_path / "concerts.json").read_text())["conciertos"]}
        return inf, recs
    leer.plan, leer.datos = plan, tmp_path
    return leer


def test_una_agenda_que_cae_vuelve_y_se_congela(lectura):
    lectura.plan["salaa"] = [ev("Banda Uno", "Sala A", "salaa")]
    lectura.plan["agb"] = [ev("Banda Uno", "Sala A", "agb"), ev("Solo B", "Sala C", "agb")]
    _, r = lectura(0)
    assert r["Banda Uno"]["confianza"]["nivel"] == "confirmado" and r["Solo B"]["confianza"]["nivel"] == "probable"

    # día 1: la agenda B no responde → lo que solo ella anuncia sigue, de su última lectura, y se dice
    lectura.plan["agb"] = "falla"
    _, r = lectura(1)
    assert "Solo B" in r and r["Solo B"]["confianza"]["nivel"] == "probable"
    assert any("se usa su última lectura" in m for m in r["Solo B"]["confianza"]["motivos"])

    # el reintento de cada 2 horas: si ninguna responde, no cambia nada
    antes = (lectura.datos / "concerts.json").read_bytes()
    inf, _ = lectura(1, reintentar=True)
    assert inf is None and (lectura.datos / "concerts.json").read_bytes() == antes

    # vuelve con otra hora: el reintento solo lee la que falló, y el cambio queda en el historial
    lectura.plan["agb"] = [ev("Banda Uno", "Sala A", "agb"), ev("Solo B", "Sala C", "agb", hora="22:00")]
    inf, r = lectura(1, reintentar=True)
    assert inf["modo"] == "reintento de agb"
    assert r["Solo B"]["hora"] == "22:00" and [c["campo"] for c in r["Solo B"]["cambios"]] == ["hora"]

    # más de 2 días sin poder leerla: congelada; lo que solo ella anuncia baja a "sin confirmar" y se dice
    lectura.plan["agb"] = "falla"
    _, r = lectura(4)
    assert r["Solo B"]["congelado"]["fuentes"] == ["Agenda B"] and r["Solo B"]["confianza"]["nivel"] == "sin confirmar"
    assert r["Banda Uno"]["confianza"]["nivel"] == "confirmado" and "congelado" not in r["Banda Uno"]  # lo anuncia la sala

    # pasados 14 días su caché ya no vale: Banda Uno ya no cuenta con la agenda B (la sala lo sigue confirmando)
    _, r = lectura(16)
    assert [f["id"] for f in r["Banda Uno"]["fuentes"]] == ["salaa"] and r["Banda Uno"]["estado"] == "1_fuente"

    # un mes sin que nadie lo reconfirme: se oculta en la web, pero sigue en los datos con su motivo
    _, r = lectura(40)
    assert r["Solo B"]["oculto"]["congelado"] and "sin reconfirmar desde el 2026-10-02" in r["Solo B"]["oculto"]["motivo"]
    assert "oculto" not in r["Banda Uno"]


def test_la_lectura_completa_del_dia_no_la_pisa_un_reintento(lectura):
    lectura.plan["salaa"] = [ev("Banda Uno", "Sala A", "salaa")]
    lectura.plan["agb"] = "falla"
    inf, _ = lectura(0)
    completa = inf["ultima_completa"]
    lectura.plan["agb"] = [ev("Solo B", "Sala C", "agb")]
    inf, r = lectura(0, reintentar=True)
    assert "Solo B" in r and inf["ultima_completa"] == completa  # el reintento no cuenta como lectura completa
