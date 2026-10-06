"""Precisión de cada regla de origen deducido: se aplica a los conciertos cuyo origen sí dice una fuente (como si no
lo supiéramos) y se compara. Una regla solo debe usarse si acierta casi siempre (ver pipeline.PRECISION_MINIMA).

Uso: python tools/medir_estimaciones.py [concerts.json] [artistas.json]
"""
import copy
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper.pipeline import tributo_y_estimacion  # noqa: E402

LATAM = {"AR", "BO", "BR", "CL", "CO", "CR", "CU", "DO", "EC", "SV", "GT", "HN", "MX", "NI", "PA", "PY", "PE", "PR",
         "UY", "VE"}


def regla(motivo: str) -> str:
    return re.sub(r"\s*\(.*", "", motivo or "")[:80]


def medir(recs: list[dict], cache: dict) -> dict:
    out = defaultdict(Counter)
    for r in recs:
        real = r.get("nacionalidad")
        if not real or r.get("oculto") or r.get("origen_no_aplica"):
            continue
        x = copy.deepcopy(r)
        x["nacionalidad"] = None
        tributo_y_estimacion(x, cache)
        est = x.get("nacionalidad_estimada")
        if not est:
            continue
        ok = real == "ES" if est == "ES" else real in LATAM if est == "LATAM" else real == est
        out[regla(x.get("nacionalidad_estimada_motivo"))]["bien" if ok else "mal"] += 1
        if not ok:
            out[regla(x.get("nacionalidad_estimada_motivo"))]["_" + real] += 1
    return out


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent.parent / "data"
    c = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else raiz / "concerts.json").read_text())
    a = json.loads(Path(sys.argv[2] if len(sys.argv) > 2 else raiz / "artistas.json").read_text())
    for k, v in sorted(medir(c["conciertos"], a).items(), key=lambda kv: -sum(kv[1][x] for x in ("bien", "mal"))):
        n = v["bien"] + v["mal"]
        print(f"{v['bien']}/{n} ({100 * v['bien'] / n:.0f} %) · {k} · fallos: "
              f"{dict((p[1:], m) for p, m in v.most_common() if p.startswith('_'))}")
