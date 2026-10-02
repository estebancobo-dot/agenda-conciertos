"""Diagnóstico del cartel (fase 3): qué dicen las fuentes de los conciertos con varios artistas (festivales,
teloneros, ciclos). Respeta robots.txt (el mismo lector que las agendas). Solo escribe en la salida.

  1. Songkick: los eventos con varios artistas tal como vienen (nombre, tipo, performer).
  2. Páginas de concierto de cada fuente: si traen performer en el JSON-LD, cuántos, si incluyen al artista que
     tenemos y a nuestros invitados, y qué nombre de evento ponen.
  3. Lo que ya tenemos: conciertos con invitados por fuente, y títulos que parecen carteles o festivales.

Uso: python tools/diagnostico_cartel.py [páginas por fuente] [minutos máx.]
"""
import collections
import json
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper.entradas import leer_pagina  # noqa: E402
from scraper.fetch import Fetcher, RobotsBlocked  # noqa: E402
from scraper.normalize import norm  # noqa: E402
from scraper.sources.base import jsonld_events, soup_of  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
MINUTOS = float(sys.argv[2]) if len(sys.argv) > 2 else 12
fin = time.monotonic() + MINUTOS * 60
datos = json.load(open(Path(__file__).resolve().parent.parent / "data" / "concerts.json"))["conciertos"]
hoy = time.strftime("%Y-%m-%d")
recs = [r for r in datos if r["fecha"] >= hoy]
f = Fetcher()

print("## 1. Songkick: eventos con varios artistas (páginas 1-4)\n")
for pag in range(1, 5):
    url = "https://www.songkick.com/metro-areas/28755-spain-madrid" + (f"?page={pag}" if pag > 1 else "")
    try:
        evs = jsonld_events(soup_of(f.get(url)))
    except Exception as e:  # noqa: BLE001
        print(f"  {url}: {type(e).__name__} {e}")
        continue
    for ev in evs:
        perf = ev.get("performer") or []
        perf = perf if isinstance(perf, list) else [perf]
        nombres = [p.get("name") for p in perf if isinstance(p, dict)]
        if len(nombres) > 1 or "festival" in str(ev.get("@type")).lower():
            print(f"- {str(ev.get('startDate'))[:10]} · tipo {ev.get('@type')} · nombre {ev.get('name')!r} · "
                  f"{len(nombres)} artistas: {', '.join(map(str, nombres[:12]))} · {str(ev.get('url'))[:90]}")

print("\n## 2. Páginas de concierto: performer en el JSON-LD\n")
usos = collections.Counter(x["url"] for r in recs for x in r.get("fuentes") or [] if x.get("url"))
por_fuente: dict[str, list] = collections.defaultdict(list)
for r in recs:
    for x in r.get("fuentes") or []:
        if x.get("url") and usos[x["url"]] == 1 and x["id"] != "madridenvivo":
            por_fuente[x["id"]].append((r, x))
random.seed(11)


def medir(fid):
    # los que tienen invitados primero: es lo que interesa comparar
    lista = sorted(por_fuente[fid], key=lambda t: -len(t[0].get("invitados") or []))
    muestra = lista[: N // 2] + random.sample(lista[N // 2:], min(N - N // 2, max(0, len(lista) - N // 2)))
    out = []
    for r, x in muestra:
        if time.monotonic() > fin:
            break
        fila = {"fuente": fid, "artista": r["artista"], "invitados": r.get("invitados") or [], "fecha": r["fecha"]}
        try:
            fila["p"] = leer_pagina(f.get(x["url"]), x["url"], r["fecha"])
        except RobotsBlocked:
            fila["error"] = "robots.txt"
        except Exception as e:  # noqa: BLE001
            fila["error"] = f"{type(e).__name__}"
        out.append(fila)
    return out


with ThreadPoolExecutor(max_workers=10) as ex:
    filas = [x for lista in ex.map(medir, sorted(por_fuente)) for x in lista]
print("fuente | leídas | con performer | 2+ artistas | incluye a nuestro artista | incluye a nuestros invitados | "
      "artistas que no teníamos")
for fid in sorted(por_fuente):
    fs = [x for x in filas if x["fuente"] == fid and "p" in x]
    if not fs:
        continue
    con = [x for x in fs if x["p"].get("cartel")]
    varios = [x for x in con if len(x["p"]["cartel"]) > 1]
    nuestro = sum(any(norm(x["artista"]) in norm(c) or norm(c) in norm(x["artista"]) for c in x["p"]["cartel"]) for x in con)
    inv = [x for x in con if x["invitados"]]
    inv_ok = sum(all(any(norm(i) == norm(c) for c in x["p"]["cartel"]) for i in x["invitados"]) for x in inv)
    nuevos = sum(len([c for c in x["p"]["cartel"] if all(norm(c) != norm(n) for n in [x["artista"], *x["invitados"]])]) for x in con)
    print(f"{fid} | {len(fs)} | {len(con)} | {len(varios)} | {nuestro}/{len(con)} | {inv_ok}/{len(inv)} | {nuevos}")
print("\n### Ejemplos con 2+ artistas o con nombre de evento distinto del artista (hasta 50)")
k = 0
for x in filas:
    p = x.get("p") or {}
    c = p.get("cartel") or []
    if len(c) > 1 or (p.get("evento_nombre") and norm(x["artista"]) not in norm(p["evento_nombre"])):
        k += 1
        print(f"- [{x['fuente']}] {x['fecha']} tenemos {x['artista']!r} + {x['invitados'][:5]} · página: nombre "
              f"{p.get('evento_nombre')!r} tipo {p.get('evento_tipo')} · cartel {c[:10]}")
        if k >= 50:
            break

print("\n## 3. Lo que ya tenemos\n")
inv = [r for r in recs if r.get("invitados")]
print(f"{len(recs)} conciertos; {len(inv)} con invitados")
print("Por fuente:", dict(collections.Counter(x["id"] for r in inv for x in r["fuentes"]).most_common(15)))
pat = re.compile(r"\bfest(ival)?\b|\bciclo\b|\bencuentro\b|\bmaratón\b|\bweekender\b|\ball ?dayer\b", re.I)
fest = [r for r in recs if pat.search(r["artista"]) or pat.search(r.get("ciclo") or "")]
print(f"\nTítulos de festival o ciclo: {len(fest)}")
for r in fest[:40]:
    print(f"- {r['fecha']} {r['artista']!r} + {(r.get('invitados') or [])[:4]} · ciclo {r.get('ciclo')!r} · "
          f"{[x['id'] for x in r['fuentes']]}")
