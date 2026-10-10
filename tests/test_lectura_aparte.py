"""Lectura con fuentes aparte (fase 2): 'todas menos Madrid en Vivo' cuenta como completa y sus conciertos entran
de su última lectura; 'solo Madrid en Vivo' no rehace la lectura completa del día."""
import json
from datetime import date, timedelta

import pytest

from scraper import pipeline
from scraper.model import RawEvent, Source
from tests.fakefetch import FakeFetcher

HOY = date(2026, 10, 1)


def _src(sid, nombre, artista, sala, contador):
    def parser(ctx):
        contador[sid] = contador.get(sid, 0) + 1
        yield RawEvent(fecha=HOY + timedelta(days=5), artista=artista, url=f"https://{sid}.es/{artista}",
                       sala=sala, ciudad="Madrid", hora="21:00")
    return Source(sid, nombre, f"https://{sid}.es", "agregador" if sid == "madridenvivo" else "sala",
                  3 if sid == "madridenvivo" else 1, "alta", sid, parser)


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    leidas = {}
    fuentes = [_src("sala1", "Sala Uno", "Banda A", "Sala Uno", leidas),
               _src("madridenvivo", "Madrid en Vivo", "Banda B", "Sala Dos", leidas)]
    monkeypatch.setattr(pipeline, "DATA", tmp_path)
    monkeypatch.setattr(pipeline, "FUENTES", fuentes)
    for n in ("correcciones.json",):
        (tmp_path / n).write_text(json.dumps({"correcciones": []}))
    monkeypatch.setattr(pipeline, "load_json", lambda n: {"correcciones": []} if n == "correcciones.json"
                        else json.loads((pipeline.Path(__file__).parent.parent / "data" / n).read_text()))
    return tmp_path, leidas


def _artistas(tmp):
    return sorted(r["artista"] for r in json.loads((tmp / "concerts.json").read_text())["conciertos"])


def test_sin_madridenvivo_usa_su_cache_y_cuenta_como_completa(entorno):
    tmp, leidas = entorno
    inf = pipeline.ejecutar(hoy=HOY, musicbrainz=False, pausa_reintento=0, fetcher=FakeFetcher({}))  # primera: todas
    assert _artistas(tmp) == ["Banda A", "Banda B"] and inf["modo"] == "completa"
    inf = pipeline.ejecutar(hoy=HOY, musicbrainz=False, pausa_reintento=0, fetcher=FakeFetcher({}), sin=["madridenvivo"])
    assert leidas == {"sala1": 2, "madridenvivo": 1}  # Madrid en Vivo no se ha vuelto a leer
    assert _artistas(tmp) == ["Banda A", "Banda B"]  # pero sus conciertos siguen (de su última lectura)
    assert inf["modo"].startswith("completa") and inf["ultima_completa"]["generado"] == inf["generado"]
    # solo Madrid en Vivo: no es la lectura completa del día (se conserva la anterior)
    previa = inf["ultima_completa"]
    inf = pipeline.ejecutar(hoy=HOY, musicbrainz=False, pausa_reintento=0, fetcher=FakeFetcher({}), solo=["madridenvivo"])
    assert leidas["madridenvivo"] == 2 and inf["modo"] == "solo madridenvivo"
    assert inf["ultima_completa"] == previa and _artistas(tmp) == ["Banda A", "Banda B"]
