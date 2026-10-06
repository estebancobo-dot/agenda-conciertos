"""Recorrido completo con datos fijos y sin red: agendas → unión de conciertos → fichas de artista guardadas →
origen, nivel y enlace de compra → datos de la web. Comprueba que las piezas encajan (cada una tiene sus pruebas)."""
import json
from datetime import date, timedelta

import pytest

from scraper import pipeline
from scraper.model import RawEvent, Source

HOY = date.today()  # la web de la prueba en el navegador enseña desde hoy
DIA = HOY + timedelta(days=5)
MBID = "identificador de MusicBrainz en Wikidata"


def _fuente(sid, nombre, tipo, prioridad, eventos):
    def parser(ctx):
        yield from eventos
    return Source(sid, nombre, f"https://{sid}.es", tipo, prioridad, "alta", sid, parser)


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    sala = [RawEvent(fecha=DIA, artista="Muse", url="https://movistar.es/muse", sala="Movistar Arena", ciudad="Madrid",
                     hora="21:00", precio="65 €"),
            RawEvent(fecha=DIA, artista="Los Grumpys", url="https://movistar.es/grumpys", sala="Intruso Bar",
                     ciudad="Madrid", hora="22:00")]
    mev = [RawEvent(fecha=DIA, artista="MUSE", url="https://madridenvivo.com/evento/muse/", sala="Movistar Arena",
                    ciudad="Madrid", entradas="https://www.ticketmaster.es/event/muse-123?utm_source=mev"),
           RawEvent(fecha=DIA, artista="Orfeón de Moratalaz", url="https://madridenvivo.com/evento/orfeon/",
                    sala="Centro Cultural Hortaleza", ciudad="Madrid")]
    monkeypatch.setattr(pipeline, "DATA", tmp_path)
    monkeypatch.setattr(pipeline, "FUENTES", [_fuente("movistar", "Movistar Arena (web oficial)", "sala", 1, sala),
                                              _fuente("madridenvivo", "Madrid en Vivo", "agregador", 3, mev)])
    monkeypatch.setattr(pipeline, "load_json", lambda n: {"correcciones": []} if n == "correcciones.json"
                        else json.loads((pipeline.Path(__file__).parent.parent / "data" / n).read_text()))
    fichas = {
        # identificado por el identificador de Wikidata: país y oyentes valen
        "muse": {"nombre": "Muse", "fecha": "2026-09-30",
                 "wikidata": {"encontrado": True, "pais": "GB", "ids": {"musicbrainz": "9c9f"}},
                 "musicbrainz": {"encontrado": True, "pais": "GB", "mbid": "9c9f", "identificado_por": MBID},
                 "discogs": {"encontrado": True, "nombre": "Muse", "url": "/artist/1003", "estilos": ["Alternative Rock"],
                             "generos": ["Rock"], "identificado_por": "identificador de Discogs en Wikidata"},
                 "audiencia": {"encontrado": True, "oyentes": 7_100_000, "nombre": "Muse", "identificado_por": MBID}},
        # solo MusicBrainz por el nombre y ninguna otra web: el país sería el de un homónimo alemán
        "los grumpys": {"nombre": "Los Grumpys", "fecha": "2026-09-30",
                        "musicbrainz": {"encontrado": True, "pais": "DE", "mbid": "x",
                                        "identificado_por": "única coincidencia exacta del nombre en MusicBrainz"}},
    }
    (tmp_path / "artistas.json").write_text(json.dumps(fichas))
    return tmp_path


def test_recorrido_completo(entorno, tmp_path):
    import sys
    sys.path.insert(0, str(pipeline.Path(__file__).parent.parent / "tools"))
    import web_datos

    pipeline.ejecutar(hoy=HOY, musicbrainz=False, pausa_reintento=0)
    recs = {r["artista"].lower(): r for r in json.loads((entorno / "concerts.json").read_text())["conciertos"]}
    muse = recs["muse"]
    # las dos webs son el mismo concierto
    assert {f["id"] for f in muse["fuentes"]} == {"movistar", "madridenvivo"} and len(recs) == 3
    # origen: el de Wikidata; el grupo local sin otra web, sin confirmar (no el del homónimo); el orfeón, deducido
    assert muse["nacionalidad"] == "GB"
    assert not recs["los grumpys"].get("nacionalidad") and not recs["los grumpys"].get("nacionalidad_estimada")
    assert recs["orfeón de moratalaz"]["nacionalidad_estimada"] == "ES"
    # nivel con su porqué; enlace de compra que da Madrid en Vivo, sin parámetros de seguimiento
    assert muse["nivel"]["nivel"] == "gran formato" and "7,1 M de oyentes" in muse["nivel"]["motivo"]
    assert recs["los grumpys"]["nivel"]["nivel"] == "formato íntimo"
    assert muse["entradas"] == {"url": "https://www.ticketmaster.es/event/muse-123", "nombre": "Ticketmaster",
                                "via": "Madrid en Vivo"}
    # recalcular sin leer las agendas da lo mismo
    antes = json.loads((entorno / "concerts.json").read_text())["conciertos"]
    pipeline.reaplicar_fichas()
    despues = json.loads((entorno / "concerts.json").read_text())["conciertos"]
    campos = ("nacionalidad", "nacionalidad_estimada", "nivel", "entradas")
    assert [{k: r.get(k) for k in campos} for r in antes] == [{k: r.get(k) for k in campos} for r in despues]
    # datos de la web: agenda ligera con la marca de gran formato y detalle con el resto
    web = tmp_path / "web"
    web_datos.preparar(json.loads((entorno / "concerts.json").read_text()), web)
    agenda = json.loads((web / "agenda.json").read_text())["conciertos"]
    ligero = next(r for r in agenda if r["artista"].lower() == "muse")
    assert ligero.get("gf") is True and "entradas" not in ligero
    detalle = json.loads((web / "detalles" / f"{DIA.isoformat()}.json").read_text())
    assert any((d.get("nivel") or {}).get("nivel") == "gran formato" for d in
               (detalle.values() if isinstance(detalle, dict) else detalle))
