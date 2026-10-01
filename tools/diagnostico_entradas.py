"""Diagnóstico: qué dicen las páginas de concierto de cada fuente y las páginas de entradas que enlazan (hora,
precio, agotado/cancelado, imagen, enlaces de compra), y si coincide con lo que ya tenemos. Respeta robots.txt (el
mismo lector que las agendas). Solo escribe en la salida: no guarda ni publica nada.

Uso: python tools/diagnostico_entradas.py [páginas por fuente] [minutos máx.]
"""
import collections
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper.entradas import dominio, imagenes_genericas, leer_pagina  # noqa: E402
from scraper.fetch import Fetcher, RobotsBlocked  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
MINUTOS = float(sys.argv[2]) if len(sys.argv) > 2 else 14
LENTAS = {"madridenvivo": 3}  # Crawl-delay de 10 s: pocas páginas
fin = time.monotonic() + MINUTOS * 60
datos = json.load(open(Path(__file__).resolve().parent.parent / "data" / "concerts.json"))["conciertos"]
hoy = time.strftime("%Y-%m-%d")
recs = [r for r in datos if r["fecha"] >= hoy]
genericas = imagenes_genericas(recs)
# URL de evento: la que solo sale en un concierto (las que salen en muchos son listados o agendas enteras)
usos = collections.Counter(x["url"] for r in recs for x in r.get("fuentes") or [] if x.get("url"))
por_fuente: dict[str, list] = collections.defaultdict(list)
for r in recs:
    for x in r.get("fuentes") or []:
        if x.get("url") and usos[x["url"]] == 1:
            por_fuente[x["id"]].append((r, x))
random.seed(7)
f = Fetcher()
tick_vistos = collections.Counter()


def medir(fid: str) -> list[dict]:
    muestra = random.sample(por_fuente[fid], min(LENTAS.get(fid, N), len(por_fuente[fid])))
    out = []
    for r, x in muestra:
        if time.monotonic() > fin:
            break
        fila = {"fuente": fid, "concierto": r["artista"][:40], "fecha": r["fecha"], "hora_actual": r.get("hora"),
                "precio_actual": r.get("precio")}
        try:
            fila["pag"] = leer_pagina(f.get(x["url"]), x["url"], r["fecha"])
        except RobotsBlocked:
            fila["error"] = "robots.txt no lo permite"
        except Exception as e:  # noqa: BLE001
            fila["error"] = f"{type(e).__name__}: {str(e)[:80]}"
        p = fila.get("pag") or {}
        destino = p.get("entradas_jsonld") or next((e["url"] for e in p.get("enlaces", [])), None)
        if destino and tick_vistos[dominio(destino)] < 4 and time.monotonic() < fin:
            tick_vistos[dominio(destino)] += 1
            try:
                fila["ticket"] = leer_pagina(f.get(destino), destino, r["fecha"])
            except RobotsBlocked:
                fila["ticket"] = {"url": destino, "error": "robots.txt no lo permite"}
            except Exception as e:  # noqa: BLE001
                fila["ticket"] = {"url": destino, "error": f"{type(e).__name__}: {str(e)[:80]}"}
        out.append(fila)
    return out


fuentes = sorted(por_fuente, key=lambda k: -len(por_fuente[k]))
with ThreadPoolExecutor(max_workers=10) as ex:
    filas = [x for lista in ex.map(medir, fuentes) for x in lista]


def pct(n, d):
    return f"{n}/{d}" if d else "-"


print(f"\n## Páginas de concierto por fuente (muestra de hasta {N}; solo URLs de un solo concierto)\n")
print("fuente | leídas | JSON-LD del día | hora | precio | agotado/a la venta | cancelado/aplazado | imagen JSON-LD | "
      "og:image (no genérica) | enlace a entradas | hora coincide | errores")
for fid in fuentes:
    fs = [x for x in filas if x["fuente"] == fid]
    if not fs:
        continue
    ok = [x for x in fs if "pag" in x]
    P = [x["pag"] for x in ok]
    coinc = [x for x in ok if x["pag"].get("hora") and x["hora_actual"]]
    print(f"{fid} | {pct(len(ok), len(fs))} | {sum(p.get('jsonld_del_dia', False) for p in P)} | "
          f"{sum(bool(p.get('hora')) for p in P)} | {sum(bool(p.get('precio')) for p in P)} | "
          f"{sum(bool(p.get('disponibilidad')) for p in P)} | {sum(bool(p.get('estado')) for p in P)} | "
          f"{sum(bool(p.get('imagen')) for p in P)} | "
          f"{sum(bool(p.get('og_imagen')) and p['og_imagen'] not in genericas for p in P)} | "
          f"{sum(bool(p.get('enlaces') or p.get('entradas_jsonld')) for p in P)} | "
          f"{pct(sum(x['pag']['hora'] == x['hora_actual'] for x in coinc), len(coinc))} | "
          f"{'; '.join(sorted({x['error'] for x in fs if 'error' in x}))[:120]}")

print("\n## Ticketeras enlazadas (dominios) por fuente")
for fid in fuentes:
    c = collections.Counter(e["dominio"] for x in filas if x["fuente"] == fid for e in (x.get("pag") or {}).get("enlaces", []))
    if c:
        print(f"{fid}: {dict(c.most_common(8))}")

print("\n## Páginas de entradas leídas (máx. 4 por ticketera)\n")
print("ticketera | leídas | JSON-LD del día | hora | precio | disponibilidad | imagen | errores")
por_t = collections.defaultdict(list)
for x in filas:
    if "ticket" in x:
        por_t[dominio(x["ticket"]["url"])].append(x)
for d, xs in sorted(por_t.items(), key=lambda kv: -len(kv[1])):
    T = [x["ticket"] for x in xs if "error" not in x["ticket"]]
    print(f"{d} | {pct(len(T), len(xs))} | {sum(t.get('jsonld_del_dia', False) for t in T)} | "
          f"{sum(bool(t.get('hora')) for t in T)} | {sum(bool(t.get('precio')) for t in T)} | "
          f"{sum(bool(t.get('disponibilidad')) for t in T)} | {sum(bool(t.get('imagen') or t.get('og_imagen')) for t in T)} | "
          f"{'; '.join(sorted({x['ticket']['error'] for x in xs if 'error' in x['ticket']}))[:120]}")

print("\n## Ejemplos (hasta 25)")
for x in [x for x in filas if (x.get("pag") or {}).get("hora") or (x.get("ticket") or {}).get("precio")][:25]:
    p, t = x.get("pag") or {}, x.get("ticket") or {}
    print(f"- [{x['fuente']}] {x['concierto']} {x['fecha']} · ya: {x['hora_actual']} / {x['precio_actual']} · "
          f"página: {p.get('hora')} / {p.get('precio')} / {p.get('disponibilidad')} · "
          f"entradas: {t.get('url', '')[:60]} {t.get('hora')} / {t.get('precio')} / {t.get('disponibilidad')}")
print(f"\nTotal: {len(filas)} páginas de concierto, {sum('ticket' in x for x in filas)} de entradas")
