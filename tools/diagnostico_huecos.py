"""Diagnóstico: hora y precio escritos en el texto de las páginas de concierto (entradas.hora_precio_texto).

Por web: cuántas páginas dan hora o precio en el texto, si coincide con lo que ya se sabe por otras fuentes (mide el
acierto antes de usarlo) y cuántos huecos llenaría. Respeta robots.txt (el mismo lector que las agendas). Solo
escribe en la salida: no guarda ni publica nada.

Uso: python tools/diagnostico_huecos.py [páginas por web] [minutos máx.]
"""
import collections
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup  # noqa: E402

from scraper.entradas import _num_precio, destino_compra, dominio, leer_pagina, paginas_de, sin_fragmento  # noqa: E402
from scraper.fetch import Fetcher, RobotsBlocked  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
MINUTOS = float(sys.argv[2]) if len(sys.argv) > 2 else 14
fin = time.monotonic() + MINUTOS * 60
datos = json.load(open(Path(__file__).resolve().parent.parent / "data" / "concerts.json"))["conciertos"]
hoy = time.strftime("%Y-%m-%d")
recs = [r for r in datos if r["fecha"] >= hoy and not r.get("oculto")]
usos = collections.Counter(sin_fragmento(x.get("url")) for r in datos for x in r.get("fuentes") or [] if x.get("url"))
# por web: conciertos con su página propia; mitad con hora y precio ya sabidos (para medir el acierto), mitad sin
por_web: dict[str, list] = collections.defaultdict(list)
for r in recs:
    for u, x in paginas_de(r, usos):
        if (r.get("hora_pagina") or {}).get("url") == u or (r.get("precio_fuente") or {}).get("url") == u:
            continue  # el dato ya salió de esta misma página: no sirve para medir
        por_web[dominio(u)].append((r, u))
random.seed(11)
f = Fetcher()


def medir(dom: str) -> list[dict]:
    todos = por_web[dom]
    con = [t for t in todos if t[0].get("hora") and t[0].get("precio")]
    sin = [t for t in todos if not (t[0].get("hora") and t[0].get("precio"))]
    muestra = random.sample(con, min(N // 2, len(con))) + random.sample(sin, min(N - min(N // 2, len(con)), len(sin)))
    out = []
    for r, u in muestra:
        if time.monotonic() > fin:
            break
        fila = {"web": dom, "concierto": r["artista"][:40], "fecha": r["fecha"], "hora": r.get("hora"),
                "precio": r.get("precio"), "url": u}
        try:
            html = f.get(u)
            fila["pag"] = leer_pagina(html, u, r["fecha"])
            t = destino_compra(fila["pag"])
            if t and dominio(t) != dom and time.monotonic() < fin:
                try:
                    fila["ticket"] = leer_pagina(f.get(t), t, r["fecha"])
                except Exception as e:  # noqa: BLE001
                    fila["ticket"] = {"url": t, "error": type(e).__name__}
        except RobotsBlocked:
            fila["error"] = "robots.txt"
        except Exception as e:  # noqa: BLE001
            fila["error"] = f"{type(e).__name__}"
        out.append(fila)
    return out


webs = sorted(por_web, key=lambda k: -len(por_web[k]))[:45]
with ThreadPoolExecutor(max_workers=10) as ex:
    filas = [x for lista in ex.map(medir, webs) for x in lista]


def mide(filas, campo, clave):
    """(aciertos, comparables, huecos que llenaría)"""
    a = n = llena = 0
    for x in filas:
        for p in [x.get("pag") or {}, x.get("ticket") or {}]:
            v = p.get(clave)
            if not v:
                continue
            if x[campo]:
                n += 1
                if campo == "hora":
                    a += v == x["hora"]
                else:
                    pa, pb = _num_precio(v), _num_precio(x["precio"])
                    libre = lambda s: "libre" in str(s).lower() or "gratu" in str(s).lower()  # noqa: E731
                    a += (pa is not None and pb is not None and abs(pa - pb) <= 0.6) or (libre(v) and libre(x["precio"]))
            else:
                llena += 1
            break
    return a, n, llena


print(f"\n## Hora y precio en el texto de la página, por web (muestra de hasta {N})\n")
print("web | conciertos con página | leídas | hora texto: acierta/comparables · llenaría | "
      "precio texto: acierta/comparables · llenaría | errores")
for dom in webs:
    fs = [x for x in filas if x["web"] == dom]
    if not fs:
        continue
    ok = [x for x in fs if "pag" in x]
    ha, hn, hl = mide(ok, "hora", "hora_t")
    pa, pn, pl = mide(ok, "precio", "precio_t")
    print(f"{dom} | {len(por_web[dom])} | {len(ok)}/{len(fs)} | {ha}/{hn} · {hl} | {pa}/{pn} · {pl} | "
          f"{'; '.join(sorted({x['error'] for x in fs if 'error' in x}))[:60]}")

print("\n## No coincide (hasta 40)")
k = 0
for x in filas:
    p = x.get("pag") or {}
    for campo, clave in (("hora", "hora_t"), ("precio", "precio_t")):
        if p.get(clave) and x[campo] and (p[clave] != x[campo] if campo == "hora" else
                                           _num_precio(p[clave]) != _num_precio(x[campo])):
            k += 1
            if k <= 40:
                print(f"- [{x['web']}] {x['concierto']} {x['fecha']} {campo}: sabemos {x[campo]!r}, texto {p[clave]!r} · {x['url'][:90]}")
print("\n## Llenaría (hasta 40)")
k = 0
for x in filas:
    p = x.get("pag") or {}
    for campo, clave in (("hora", "hora_t"), ("precio", "precio_t")):
        if p.get(clave) and not x[campo]:
            k += 1
            if k <= 40:
                print(f"- [{x['web']}] {x['concierto']} {x['fecha']} {campo}: {p[clave]!r} · {x['url'][:90]}")
print(f"\nTotal: {len(filas)} páginas, {sum('pag' in x for x in filas)} leídas")
