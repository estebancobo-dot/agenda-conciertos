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
           "estilos_discogs", "genero_discogs", "grupos", "categoria", "grupos_generico", "estado", "origen_no_aplica",
           "nacionalidad_estimada")


def genericas(recs: list[dict]) -> set[str]:
    """Imágenes que la agenda pone a muchos artistas distintos: el fondo genérico de Madrid en Vivo (392
    conciertos), el logo de una sala… No son del artista: mejor las iniciales que una foto que confunde."""
    from collections import defaultdict as dd
    artistas = dd(set)
    for r in recs:
        u = (r.get("imagen") or {}).get("url")
        if u:
            artistas[u].add(" ".join(str(r.get("artista", "")).lower().split())[:30])
    return {u for u, a in artistas.items() if len(a) >= MAX_ARTISTAS_IMAGEN}


MAX_ARTISTAS_IMAGEN = 4
MINIATURAS: dict[str, str] = {}  # url original → ruta de la miniatura propia (tools/miniaturas.py)
GRANDES: dict[str, str] = {}  # url original → ruta de la foto reducida para la ficha


def ligero(r: dict) -> dict:
    out = {k: r[k] for k in LIGEROS if r.get(k) not in (None, [], "", False)}
    if r.get("conflictos"):  # la tarjeta dice qué dato no cuadra ("hora sin confirmar") y la hora más votada
        out["conflictos"] = [{"campo": c.get("campo"), "versiones": [{"valor": v["valor"], "fuentes": v.get("fuentes", [])}
                                                                     for v in c.get("versiones") or []]}
                             for c in r["conflictos"]]
    etiquetas = list(dict.fromkeys(e["estilo"] for e in r.get("estilo_fuente") or []))
    if etiquetas:
        out["estilo_fuente"] = [{"estilo": e} for e in etiquetas]
    if r.get("agotado"):
        out["agotado"] = True
    if r.get("estado_evento"):
        out["evento"] = r["estado_evento"]["tipo"]  # "cancelado" | "aplazado": se ve en la tarjeta
    im = r.get("imagen") or {}
    if im.get("url"):
        out["img"] = im["url"]
        if MINIATURAS and im["url"] in MINIATURAS:
            out["mini"] = MINIATURAS[im["url"]]
        if GRANDES and im["url"] in GRANDES:
            out["foto"] = GRANDES[im["url"]]
    return out


def cargar_miniaturas(recs: list[dict], carpeta: Path) -> None:
    """Anota qué imágenes tienen miniatura propia hecha (tools/miniaturas.py)."""
    from miniaturas import nombre
    hechas = {p.name for p in carpeta.glob("*.webp")} if carpeta.exists() else set()
    for r in recs:
        u = (r.get("imagen") or {}).get("url")
        if u and nombre(u) in hechas:
            MINIATURAS[u] = f"miniaturas/{nombre(u)}"
        if u and nombre(u, True) in hechas:
            GRANDES[u] = f"miniaturas/{nombre(u, True)}"
        g = (r.get("gira") or {}).get("imagen")  # cartel de la gira: solo hace falta la grande (ficha)
        if g and nombre(g, True) in hechas:
            GRANDES[g] = f"miniaturas/{nombre(g, True)}"


def preparar(concerts: dict, destino: Path) -> dict:
    import copy
    genericas_ = genericas(concerts.get("conciertos", []))
    recs = []
    for r in concerts.get("conciertos", []):
        if (r.get("imagen") or {}).get("url") in genericas_:
            r = copy.copy(r)
            r["imagen"] = None
        g = r.get("gira") or {}
        if g.get("imagen") in GRANDES:  # el cartel, servido desde la propia web (copia reducida)
            r = copy.copy(r)
            r["gira"] = {**g, "foto": GRANDES[g["imagen"]]}
        recs.append(r)
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
    sitio = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "_site"
    destino = sitio / "data"
    concerts = json.loads((RAIZ / "data" / "concerts.json").read_text(encoding="utf-8"))
    carpeta = RAIZ / "miniaturas"
    cargar_miniaturas(concerts.get("conciertos", []), carpeta)
    if MINIATURAS or GRANDES:
        import shutil
        (sitio / "miniaturas").mkdir(parents=True, exist_ok=True)
        for ruta in set(MINIATURAS.values()) | set(GRANDES.values()):
            shutil.copy(carpeta / ruta.split("/")[1], sitio / ruta)
    print(preparar(concerts, destino), "miniaturas propias:", len(set(MINIATURAS.values())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
