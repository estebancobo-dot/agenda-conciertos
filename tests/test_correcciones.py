"""Correcciones manuales (data/correcciones.json)."""
import json
from datetime import date

from scraper.correcciones import aplicar
from scraper.normalize import DATA
from tests.test_dedup import ev, run, src

CORR = json.loads((DATA / "correcciones.json").read_text(encoding="utf-8"))["correcciones"]


def test_formato_ampliable():
    for c in CORR:
        assert c["tipo"] in ("descarte", "conflicto", "nota") and c["fecha"] and c.get("nota")


def test_descartes():
    recs = run((ev("Threats", "Silikona", invitados=["It Came From The Void", "Kenpark"]), src("mariskal")),
               (ev("Mägo de Oz", "Palacio Vistalegre"), src("x")),
               (ev("Sabbat", "Silikona"), src("y")))
    for i, r in enumerate(recs):
        r["id"] = str(i)
    out, res = aplicar(recs, CORR, "2026-09-29")
    assert [r["artista"] for r in out] == ["Sabbat"]
    assert len(res["descartados"]) == 2


def test_mago_de_oz_en_leganes_no_se_descarta():
    recs = run((ev("Mägo de Oz", "La Nueva Cubierta", fecha=date(2026, 10, 17)), src("x")))
    out, _ = aplicar(recs, CORR, "2026-09-29")
    assert len(out) == 1  # la corrección solo afecta a Madrid capital


def test_conflicto_gruta_fusiona_versiones():
    recs = run((ev("La Pestilencia", "Gruta 77", "21:30"), src("rfe")),
               (ev("Larsen", "Gruta 77", "21:30", ["Klobber"]), src("cc")))
    for i, r in enumerate(recs):
        r["id"] = str(i)
    out, res = aplicar(recs, CORR, "2026-09-29")
    assert len(out) == 1
    r = out[0]
    assert r["estado"] == "conflicto" and len(r["fuentes"]) == 2
    assert r["notas"][0].startswith("Corrección manual verificada") and "La Pestilencia" in r["notas"][0]
    assert len(r["conflictos"][-1]["versiones"]) == 2


def test_conflicto_de_hora_manual():
    recs = run((ev("Amann & the Wayward Sons", "Tempo Club", "22:00"), src("cc")))
    out, _ = aplicar(recs, CORR, "2026-09-29")
    assert out[0]["estado"] == "conflicto" and "23:30 según Bandsintown" in out[0]["notas"][0]


def test_nota_informativa_no_es_conflicto():
    recs = run((ev("Laura Cox", "Sala Villanos", fecha=date(2026, 10, 20)), src("cpm")))
    out, _ = aplicar(recs, CORR, "2026-09-29")
    assert out[0]["estado"] == "1_fuente" and "Deep Purple" in out[0]["notas"][-1]


def test_correccion_sin_coincidencia_se_informa():
    out, res = aplicar([], CORR, "2026-09-29")
    assert len(res["sin_coincidencia"]) == len(CORR)
