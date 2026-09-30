"""Conjunto de control de la clasificación y reglas del consenso (grupos de filtro)."""
import copy
import json
from pathlib import Path

import pytest

from scraper.artistas import ficha
from scraper.clasificar import (contexto_de_fuentes, discogs, grupo_de, grupos_de_evidencias, pesos_de_agenda,
                                sin_generos_cubiertos, traducir_musicbrainz)
from scraper.pipeline import aplicar_ficha, cambios_grupos

CONTROL = json.loads((Path(__file__).parent / "fixtures" / "control_clasificacion.json").read_text(encoding="utf-8"))
SYNTH = "synth y dark wave"


@pytest.mark.parametrize("caso", CONTROL["casos"], ids=lambda c: c["artista"])
def test_conjunto_de_control(caso):
    r = copy.deepcopy(caso["concierto"])
    aplicar_ficha(r, ficha(copy.deepcopy(caso["ficha"])))
    for g in caso["debe"]:
        assert g in r["grupos"], f"{caso['artista']}: falta {g} en {r['grupos']}"
    for g in caso["no_debe"]:
        assert g not in r["grupos"], f"{caso['artista']}: sobra {g} en {r['grupos']}"
    if caso.get("homonimo"):
        assert r.get("homonimo_descartado"), f"{caso['artista']}: no se detecta el homónimo de Discogs"


@pytest.mark.parametrize("etiqueta,estilo", [
    ("synthwave", "Synthwave"), ("Retrowave", "Synthwave"), ("outrun", "Synthwave"), ("darksynth", "Synthwave"),
    ("dreamwave", "Synthwave"), ("sovietwave", "Synthwave"), ("dark wave", "Darkwave"), ("minimal wave", "Coldwave"),
    ("synthpop", "Synth-pop"), ("aggrotech", "EBM"), ("electro-industrial", "EBM"), ("italo disco", "Italo-Disco"),
])
def test_familia_synth_completa(etiqueta, estilo):
    assert discogs([etiqueta])[0] == [estilo]
    assert grupo_de(estilo, "estilo") == SYNTH


def test_resto_de_la_electronica_sigue_fuera():
    assert grupo_de("Electronic", "genero") == "fuera de foco"
    assert traducir_musicbrainz("techno") == [("Electronic", "genero")]
    assert traducir_musicbrainz("darksynth") == [("Synthwave", "estilo")]


def test_el_genero_no_vota_contra_su_propio_estilo():
    evs = [{"nombre": "Indie Pop", "tipo": "estilo", "fuente": "Discogs", "peso": 1.0},
           {"nombre": "Pop", "tipo": "genero", "fuente": "Discogs", "peso": 0.6},
           {"nombre": "Pop", "tipo": "genero", "fuente": "Wikipedia", "peso": 0.6}]
    assert [e["nombre"] for e in sin_generos_cubiertos(evs)] == ["Indie Pop"]
    assert grupos_de_evidencias(evs)[0] == ["pop e indie"]


def test_la_agenda_suma_pero_sola_no_supera_a_discogs():
    assert pesos_de_agenda([["Pop-rock/Indie"]]) == {"pop e indie": 0.5}
    assert pesos_de_agenda([["Pop / Rock"]]) == {}  # etiqueta paraguas: no dice cuál de los dos
    assert pesos_de_agenda([["Rock"], ["Rock/Rock Alternativo"], ["Metal/Rock duro"]]) == {"rock y metal": 1.0}
    evs = [{"nombre": "Techno", "tipo": "estilo", "fuente": "Discogs", "peso": 1.0},
           {"nombre": "Electronic", "tipo": "genero", "fuente": "Discogs", "peso": 1.0}]
    assert grupos_de_evidencias(evs, [], {"rock y metal": 0.5})[0] == ["fuera de foco"]


def test_contexto_de_la_web_acepta_lastfm_por_nombre():
    evs = [{"nombre": "Hard Rock", "tipo": "estilo", "fuente": "Last.fm", "peso": 0.8, "debil": True}]
    assert grupos_de_evidencias(evs, [])[0] == []
    assert "rock y metal" in contexto_de_fuentes(["thm"])
    assert grupos_de_evidencias(evs, [], None, contexto_de_fuentes(["thm"]))[0] == ["rock y metal"]
    assert contexto_de_fuentes(["cc_buscador"]) == []  # agenda generalista: no da contexto


def test_cambios_por_grupo():
    previos = {"a": ["rock y metal"], "b": ["pop e indie"]}
    recs = [{"id": "a", "fecha": "2030-01-01", "artista": "A", "grupos": ["rock y metal"]},
            {"id": "b", "fecha": "2030-01-01", "artista": "B", "grupos": ["fuera de foco"]},
            {"id": "c", "fecha": "2030-01-01", "artista": "C", "grupos": ["pop e indie"]}]
    c = cambios_grupos(previos, recs, "2029-12-31")
    assert c["pop e indie"]["total"] == 1 and c["pop e indie"]["salen"] == 1
    assert c["pop e indie"]["ejemplos_salen"] == ["B"]
    assert c["fuera de foco"]["entran"] == 1
    assert c["rock y metal"] == {"total": 1, "entran": 0, "salen": 0, "ejemplos_entran": [], "ejemplos_salen": []}


def test_homonimo_de_discogs_que_contradice_a_todo():
    from scraper.clasificar import revisar_homonimos
    evs = [{"nombre": "Death Metal", "tipo": "estilo", "fuente": "Discogs", "peso": 1.0, "verificar": "The Hate",
            "muy_dudosa": True}]
    evs2, nombre = revisar_homonimos(evs, {"fuera de foco": 0.5})
    assert nombre == "The Hate" and evs2[0]["debil"]
    # mismo nombre: una sola agenda en contra no basta (a un DJ de techno lo etiquetan "rock"); dos agendas, sí
    igual = [dict(evs[0], verificar="Mardom", muy_dudosa=False)]
    assert revisar_homonimos(igual, {"fuera de foco": 0.5})[1] is None
    assert revisar_homonimos(igual, {"fuera de foco": 1.0})[1] == "Mardom"
    # grupos vecinos (rock frente a punk) no son contradicción: no se descarta
    assert revisar_homonimos(evs, {"punk y garage": 0.5})[1] is None
    # identificado por Wikidata con el mismo nombre: no se revisa
    assert revisar_homonimos([dict(evs[0], verificar=None)], {"fuera de foco": 0.5})[1] is None
