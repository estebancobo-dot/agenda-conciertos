"""Acierto de la hora de cada agenda frente a la web de la sala y conflictos de hora resueltos con él (scraper/horas.py)."""
import json
from datetime import date, timedelta

from scraper import horas, pipeline
from scraper.model import RawEvent, Source
from tests.fakefetch import FakeFetcher

BIEN = {"n": 100, "coinciden": 79, "antes": 15, "despues": 6}   # Madrid en Vivo, La Ganzúa…
PUERTAS = {"n": 78, "coinciden": 31, "antes": 41, "despues": 6}  # Songkick: suele dar la apertura de puertas
MEDIO = {"n": 50, "coinciden": 30, "antes": 10, "despues": 10}   # 60 %: ni mucho ni poco
NOMBRES = {"La Ganzúa": "laganzua", "Songkick Madrid": "songkick", "Otra agenda": "otra", "Sin medida": "nueva"}


def conflicto(*versiones):
    return {"artista": "X", "hora": None, "estado": "conflicto", "notas": ["Conflicto de hora: …"],
            "conflictos": [{"campo": "hora", "versiones": [{"valor": v, "fuentes": f} for v, f in versiones]}]}


def test_resuelve_si_una_acierta_mucho_y_la_otra_poco():
    r = conflicto(("21:00", ["La Ganzúa"]), ("20:00", ["Songkick Madrid"]))
    assert horas.resolver([r], {"laganzua": BIEN, "songkick": PUERTAS}, NOMBRES) == 1
    assert r["hora"] == "21:00" and r["conflictos"] == []
    d = r["hora_descartada"][0]
    assert d["valor"] == "20:00" and "40 %" in d["motivo"] and "apertura de puertas" in d["motivo"]
    assert any("Resuelto por acierto medido" in n for n in r["notas"]) and not any(n.startswith("Conflicto") for n in r["notas"])


def test_no_resuelve_si_no_esta_claro():
    acierto = {"laganzua": BIEN, "songkick": PUERTAS, "otra": MEDIO, "nueva": {"n": 5, "coinciden": 5, "antes": 0, "despues": 0}}
    casos = [conflicto(("21:00", ["La Ganzúa"]), ("20:00", ["Otra agenda"])),      # la otra acierta un 60 %
             conflicto(("21:00", ["La Ganzúa"]), ("20:00", ["Sin medida"])),       # pocos conciertos para medirla
             conflicto(("21:00", ["Songkick Madrid"]), ("20:00", ["Otra agenda"])),  # ninguna acierta mucho
             conflicto(("21:00", ["La Ganzúa"]), ("20:00", ["La Ganzúa"]))]          # dos que aciertan mucho
    assert horas.resolver(casos, acierto, NOMBRES) == 0
    assert all(r["hora"] is None and r["conflictos"] for r in casos)


def test_si_la_descartada_es_posterior_no_habla_de_puertas():
    r = conflicto(("20:00", ["La Ganzúa"]), ("21:00", ["Songkick Madrid"]))
    horas.resolver([r], {"laganzua": BIEN, "songkick": PUERTAS}, NOMBRES)
    assert r["hora"] == "20:00" and "puertas" not in r["hora_descartada"][0]["motivo"]


def test_medir_conserva_la_ultima_medida_buena():
    previo = {"songkick": {**PUERTAS, "fecha": "2026-10-01"}}
    out = horas.medir({}, {}, previo, "2026-10-10")  # hoy no hay con qué comparar: vale la de antes
    assert out["songkick"]["fecha"] == "2026-10-01"


def test_en_una_lectura_completa(tmp_path, monkeypatch):
    hoy = date(2026, 10, 1)
    dias = [hoy + timedelta(days=d) for d in range(5, 30)]  # 25 conciertos comparables

    def ev(a, sala, hora, dia, sid):
        return RawEvent(fecha=dia, artista=a, url=f"https://{sid}.es/{a}", sala=sala, ciudad="Madrid", hora=hora)
    plan = {"sala": [ev(f"Banda {i}", "Sala A", "21:00", d, "sala") for i, d in enumerate(dias)],
            "bien": [ev(f"Banda {i}", "Sala A", "21:00", d, "bien") for i, d in enumerate(dias)]
            + [ev("Los Dudosos", "Sala Sin Web", "21:30", dias[0], "bien")],
            "puertas": [ev(f"Banda {i}", "Sala A", "20:00", d, "puertas") for i, d in enumerate(dias)]
            + [ev("Los Dudosos", "Sala Sin Web", "20:30", dias[0], "puertas")]}

    def fuente(sid, nombre, tipo, prio):
        def parser(ctx):
            yield from plan[sid]
        return Source(sid, nombre, f"https://{sid}.es", tipo, prio, "alta", sid, parser)
    monkeypatch.setattr(pipeline, "DATA", tmp_path)
    monkeypatch.setattr(pipeline, "FUENTES", [fuente("sala", "Sala A (web oficial)", "sala", 1),
                                              fuente("bien", "Agenda Buena", "agregador", 3),
                                              fuente("puertas", "Agenda Puertas", "agregador", 3)])
    monkeypatch.setattr(pipeline, "load_json", lambda n: {"correcciones": []} if n == "correcciones.json"
                        else json.loads((pipeline.Path(__file__).parent.parent / "data" / n).read_text()))
    inf = pipeline.ejecutar(hoy=hoy, musicbrainz=False, pausa_reintento=0, fetcher=FakeFetcher({}))
    r = next(x for x in json.loads((tmp_path / "concerts.json").read_text())["conciertos"] if x["artista"] == "Los Dudosos")
    assert r["hora"] == "21:30" and r["estado"] == "contrastado" and not r["conflictos"]
    assert r["hora_descartada"][0]["valor"] == "20:30" and "apertura de puertas" in r["hora_descartada"][0]["motivo"]
    f = {x["id"]: x for x in inf["fuentes"]}
    assert f["bien"]["acierto_hora"]["coinciden"] == 25 and f["puertas"]["acierto_hora"]["antes"] == 25
    assert inf["totales"]["horas_por_acierto"] == 1
    estado = json.loads((tmp_path / "estado.json").read_text())
    assert estado["acierto_hora"]["puertas"]["n"] == 25  # se guarda para la próxima lectura
