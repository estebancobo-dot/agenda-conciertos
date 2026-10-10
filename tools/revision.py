"""Listas para revisar a mano (no cambia nada): artistas cuyo origen contradicen otras webs y posibles conciertos
repetidos que no se han unido. Lee data/concerts.json y data/artistas.json y escribe un Markdown.

    python tools/revision.py [salida.md]
"""
import collections
import json
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from rapidfuzz import fuzz  # noqa: E402

from scraper.merge import _con_sesiones  # noqa: E402
from scraper.normalize import es_generico, misma_sala, norm  # noqa: E402

ENLACES = (("wikidata", "Wikidata", lambda p: f"https://www.wikidata.org/wiki/{p['id']}" if p.get("id") else ""),
           ("musicbrainz", "MusicBrainz",
            lambda p: f"https://musicbrainz.org/artist/{p['mbid']}" if p.get("mbid") else ""),
           ("discogs", "Discogs", lambda p: p.get("url") or ""))


def contradicciones(futuros: list[dict], artistas: dict) -> list[str]:
    por = collections.defaultdict(list)
    for r in futuros:
        o = (r.get("normalizacion") or {}).get("origen") or {}
        if o.get("contradice"):
            por[r["artista"]].append((r, o))
    out = [f"## Origen: otras webs dicen otro país ({sum(map(len, por.values()))} conciertos, {len(por)} artistas)", "",
           "La web muestra el país elegido (el de la ficha más fiable) y, en la ficha del concierto, el que dan las "
           "otras webs. Suele ser alguien nacido en un país que vive o trabaja en otro, o un homónimo en una de ellas.",
           "",
           "| Artista | Elegido | Otras webs | Fichas | Conciertos |", "|---|---|---|---|---|"]
    for nombre, lista in sorted(por.items(), key=lambda x: norm(x[0])):
        r, o = lista[0]
        otras = "; ".join(f"{c['valor']} ({', '.join(c['fuentes'])})" for c in o["contradice"])
        ent = artistas.get(norm(nombre)) or {}
        fichas = " · ".join(f"[{t}]({u})" for k, t, f in ENLACES
                            if (ent.get(k) or {}).get("encontrado") and (u := f(ent[k])))
        fechas = ", ".join(f"{x['fecha']} {x.get('sala') or ''}".strip() for x, _ in lista[:3])
        out.append(f"| {nombre} | {o['valor']} ({o.get('fuente', '')}) | {otras} | {fichas} | {fechas} |")
    return out


def repetidos(futuros: list[dict]) -> list[str]:
    por = collections.defaultdict(list)
    for r in futuros:
        if not _con_sesiones(r["artista"]) and not es_generico(r["artista"]):
            por[r["fecha"]].append(r)
    pares = []
    for fecha, lista in sorted(por.items()):
        for i, a in enumerate(lista):
            for b in lista[i + 1:]:
                na, nb = norm(a["artista"]), norm(b["artista"])
                if min(len(na), len(nb)) < 2 or fuzz.token_set_ratio(na, nb) < 90:
                    continue
                pares.append((fecha, a, b, misma_sala(a.get("sala") or "", b.get("sala") or "")))
    out = [f"## Posibles conciertos repetidos que no se han unido ({len(pares)})", "",
           "Mismo día y nombre parecido. Si es la misma sala, normalmente es el mismo concierto anunciado de dos "
           "formas. Si son salas distintas, puede ser un error de sala en una de las webs o dos conciertos de verdad.",
           "", "| Fecha | Uno | Otro | ¿Misma sala? |", "|---|---|---|---|"]
    fmt = lambda r: f"{r['artista']} · {r.get('sala') or '¿sala?'} · {r.get('hora') or '¿hora?'} · " \
                    f"{', '.join(f.get('nombre', '').split(' (')[0] for f in r.get('fuentes') or [])}"  # noqa: E731
    for fecha, a, b, ms in pares:
        out.append(f"| {fecha} | {fmt(a)} | {fmt(b)} | {'sí' if ms else 'no'} |")
    return out


def main() -> int:
    salida = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "REVISION.md"
    datos = json.loads((RAIZ / "data" / "concerts.json").read_text(encoding="utf-8"))
    artistas = json.loads((RAIZ / "data" / "artistas.json").read_text(encoding="utf-8"))
    hoy = date.today().isoformat()
    futuros = [r for r in datos["conciertos"] if r["fecha"] >= hoy and not r.get("oculto")]
    texto = [f"# Para revisar — datos de {datos.get('generado', '')[:16].replace('T', ' ')} UTC", "",
             *contradicciones(futuros, artistas), "", *repetidos(futuros), ""]
    salida.write_text("\n".join(texto), encoding="utf-8")
    print(f"{salida}: {len(texto)} líneas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
