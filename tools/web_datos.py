"""Prepara los datos que descarga la web: una agenda ligera y el detalle de cada concierto por días.

La web descargaba data/concerts.json entero (casi 7 MB; 600 KB comprimido) antes de pintar nada. Ahora:
  - data/agenda.json: solo lo necesario para el calendario, las listas, los filtros y la búsqueda;
  - data/detalles/AAAA-MM-DD.json: el resto (fuentes, ficha, precio, notas…) de los conciertos de ese día, que
    se pide al abrir un concierto (unos pocos KB en vez de todo el mes).

Uso: python tools/web_datos.py DESTINO   (DESTINO/data/agenda.json y DESTINO/data/detalles/)
concerts.json se sigue publicando igual (para quien use los datos) y la web lo usa si falta agenda.json.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# campos de la agenda ligera (el resto va al detalle)
LIGEROS = ("id", "fecha", "hora", "artista", "invitados", "sala", "municipio", "ciclo", "nacionalidad",
           "estilos_discogs", "genero_discogs", "grupos", "categoria", "grupos_generico", "estado")


def ligero(r: dict) -> dict:
    out = {k: r[k] for k in LIGEROS if r.get(k) not in (None, [], "", False)}
    if r.get("conflictos"):  # la tarjeta dice qué dato no cuadra ("hora sin confirmar") y la hora más votada
        out["conflictos"] = [{"campo": c.get("campo"), "versiones": [{"valor": v["valor"], "fuentes": v.get("fuentes", [])}
                                                                     for v in c.get("versiones") or []]}
                             for c in r["conflictos"]]
    etiquetas = list(dict.fromkeys(e["estilo"] for e in r.get("estilo_fuente") or []))
    if etiquetas:
        out["estilo_fuente"] = [{"estilo": e} for e in etiquetas]
    im = r.get("imagen") or {}
    if im.get("url"):
        out["img"] = im["url"]
    return out


def preparar(concerts: dict, destino: Path) -> dict:
    recs = concerts.get("conciertos", [])
    (destino / "detalles").mkdir(parents=True, exist_ok=True)
    agenda = {k: v for k, v in concerts.items() if k != "conciertos"}
    agenda["conciertos"] = [ligero(r) for r in recs]
    agenda["detalles"] = "detalles/{fecha}.json"
    por_dia: dict[str, dict] = defaultdict(dict)
    for r in recs:
        por_dia[r["fecha"]][r["id"]] = r
    (destino / "agenda.json").write_text(json.dumps(agenda, ensure_ascii=False, separators=(",", ":")),
                                         encoding="utf-8")
    for dia, d in por_dia.items():
        (destino / "detalles" / f"{dia}.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")),
                                                          encoding="utf-8")
    return {"conciertos": len(recs), "dias": len(por_dia)}


def main() -> int:
    destino = Path(sys.argv[1]) / "data" if len(sys.argv) > 1 else RAIZ / "_site" / "data"
    concerts = json.loads((RAIZ / "data" / "concerts.json").read_text(encoding="utf-8"))
    print(preparar(concerts, destino))
    return 0


if __name__ == "__main__":
    sys.exit(main())
