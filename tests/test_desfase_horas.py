"""Diagnóstico de desfase de horas (tools/desfase_horas.py): compara cada agenda con la web oficial de la sala."""
import sys
from pathlib import Path

from scraper.model import Source

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import desfase_horas  # noqa: E402


def test_compara_con_la_web_de_la_sala():
    f = [Source("sala", "Sala X (web oficial)", "u", "sala", 1, "alta", "g", None),
         Source("ag", "Agenda", "u", "agregador", 3, "media", "g", None)]
    ev = lambda a, h, sala="Sala X": {"fecha": "2026-10-20", "artista": a, "sala": sala, "hora": h}  # noqa: E731
    cache = {"sala": {"eventos": [ev("Muse", "21:00"), ev("Kmmn", "22:00"), ev("Otro", "20:00")]},
             "ag": {"eventos": [ev("MUSE", "20:00"), ev("Kmmn", "22:00"), ev("Otro", None), ev("Nadie", "19:00")]}}
    out = desfase_horas.comparar(cache, f)
    assert out["ag"] == {-60: 1, 0: 1}  # Muse una hora antes (las puertas); Kmmn igual; sin hora o sin pareja, nada
