"""Diagnóstico: ¿da Madrid en Vivo el enlace de compra de sus conciertos? Mira los campos de la ficha de cada evento
en su API pública de WordPress (la que ya se lee para hora, precio y estilos: sin peticiones nuevas si el enlace
está ahí) y, para unos pocos eventos, los enlaces a ticketeras de la página del evento. Respeta su robots.txt
(10 s entre peticiones). Solo escribe en la salida.

Uso: python tools/diagnostico_mev_entradas.py [páginas de evento a mirar]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup  # noqa: E402

from scraper.entradas import ticketera  # noqa: E402
from scraper.fetch import Fetcher  # noqa: E402

N_PAGINAS = int(sys.argv[1]) if len(sys.argv) > 1 else 12
API = "https://madridenvivo.com/wp-json/wp/v2/evento?per_page=100&page={}&_fields=id%2Clink%2Cacf"
f = Fetcher()


def urls_en(x, out):
    if isinstance(x, dict):
        for v in x.values():
            urls_en(v, out)
    elif isinstance(x, list):
        for v in x:
            urls_en(v, out)
    elif isinstance(x, str):
        out.extend(re.findall(r"https?://[^\s\"'<>]+", x))
    return out


eventos = []
for p in (1, 2):
    try:
        eventos += json.loads(f.get(API.format(p)))
    except Exception as e:  # noqa: BLE001
        print(f"API página {p}: {type(e).__name__} {e}")
print(f"\n## API: {len(eventos)} eventos")
campos, con_valor = Counter(), Counter()
con_ticketera, ejemplos = 0, []
for ev in eventos:
    acf = ev.get("acf") or {}
    for k, v in acf.items():
        campos[k] += 1
        if v not in (None, "", [], False, {}):
            con_valor[k] += 1
    tk = [u for u in urls_en(acf, []) if ticketera(u)]
    if tk:
        con_ticketera += 1
        if len(ejemplos) < 8:
            ejemplos.append(f"{ev.get('link')} → {tk[:2]}")
from scraper.entradas import dominio  # noqa: E402
otros = Counter(dominio(str((ev.get("acf") or {}).get("venta_de_entradas_url") or "")) for ev in eventos
                if (ev.get("acf") or {}).get("venta_de_entradas_url")
                and not ticketera(str(ev["acf"]["venta_de_entradas_url"])))
print("enlaces de venta que no son de una ticketera conocida, por dominio:", otros.most_common(25))
for d, _ in otros.most_common(8):
    print("  ejemplo", d, next(ev["acf"]["venta_de_entradas_url"] for ev in eventos
                              if dominio(str((ev.get("acf") or {}).get("venta_de_entradas_url") or "")) == d)[:160])
print("campos de la ficha (con valor / total):")
for k, n in campos.most_common():
    print(f"  {k}: {con_valor[k]}/{n}")
print(f"eventos con enlace a una ticketera en la ficha: {con_ticketera} de {len(eventos)}")
for e in ejemplos:
    print("  -", e)
for k in campos:  # campos que parecen de entradas: un ejemplo de valor
    if re.search(r"entrad|ticket|compra|venta|url|enlace|link", k, re.I):
        v = next((ev["acf"][k] for ev in eventos if (ev.get("acf") or {}).get(k)), None)
        print(f"  ejemplo {k}: {str(v)[:200]}")

print(f"\n## Páginas de evento ({N_PAGINAS})")
con = 0
for ev in eventos[:N_PAGINAS] if N_PAGINAS else []:
    u = ev.get("link")
    try:
        sp = BeautifulSoup(f.get(u), "lxml")
    except Exception as e:  # noqa: BLE001
        print(f"- {u}: {type(e).__name__}")
        continue
    tk = sorted({urljoin(u, a["href"]) for a in sp.select("a[href]") if ticketera(urljoin(u, a["href"]))})
    otros = sorted({a["href"] for a in sp.select("a[href]")
                    if re.search(r"entrad|ticket|compra", (a.get_text() + a["href"]).lower())})[:4]
    con += bool(tk)
    print(f"- {u}: ticketeras {tk[:3]} · enlaces que dicen entradas {otros}")
print(f"páginas con enlace a una ticketera: {con} de {min(N_PAGINAS, len(eventos))}")
