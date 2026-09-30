"""Datos de la web: agenda ligera + detalle por días (tools/web_datos.py)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from web_datos import LIGEROS, preparar  # noqa: E402

REC = {"id": "a1", "fecha": "2026-10-09", "hora": None, "artista": "Devin Townsend", "invitados": [],
       "sala": "Revi Live", "municipio": "Madrid", "grupos": ["rock y metal"], "categoria": "rock y metal",
       "estilos_discogs": ["Progressive Metal"], "nacionalidad": "CA", "estado": "conflicto",
       "conflictos": [{"campo": "hora", "versiones": [{"valor": "20:00", "fuentes": ["x"]}]},
                      {"campo": "sala", "versiones": [{"valor": "Otra", "fuentes": ["y"]}]}],
       "estilo_fuente": [{"estilo": "Metal", "fuente": "a"}, {"estilo": "Metal", "fuente": "b"}],
       "imagen": {"url": "https://x/y.jpg", "credito": "Commons"}, "fuentes": [{"nombre": "Revi", "url": "u"}],
       "ficha": {"evidencias": [1, 2, 3]}, "precio": "30 €", "notas": ["n"]}


def test_agenda_ligera_y_detalle(tmp_path):
    r = preparar({"generado": "2026-09-30T05:00:00+00:00", "conciertos": [REC]}, tmp_path)
    assert r == {"conciertos": 1, "dias": 1}
    ag = json.loads((tmp_path / "agenda.json").read_text())
    assert ag["generado"] and ag["detalles"] == "detalles/{fecha}.json"
    x = ag["conciertos"][0]
    assert set(x) <= set(LIGEROS) | {"conflictos", "estilo_fuente", "img"}
    assert "fuentes" not in x and "ficha" not in x and "precio" not in x and "hora" not in x  # vacíos fuera
    assert x["img"] == "https://x/y.jpg"
    assert [c["campo"] for c in x["conflictos"]] == ["hora", "sala"]
    assert x["estilo_fuente"] == [{"estilo": "Metal"}]
    det = json.loads((tmp_path / "detalles" / "2026-10-09.json").read_text())
    assert det["a1"] == REC  # el detalle es el registro completo
