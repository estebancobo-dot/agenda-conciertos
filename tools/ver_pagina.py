"""Diagnóstico: qué trae una página de concierto (texto completo, metadatos, JSON-LD, categorías) y, si es un
WordPress, qué expone su API pública. Respeta robots.txt (mismo lector que las agendas). Solo escribe en la salida.

Uso: python tools/ver_pagina.py URL
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup  # noqa: E402

from scraper.fetch import Fetcher  # noqa: E402

url = sys.argv[1]
base = "{0.scheme}://{0.netloc}".format(urlsplit(url))
f = Fetcher()
try:
    print("### robots.txt\n" + f.get(base + "/robots.txt", check_robots=False)[:1500])
except Exception as e:  # noqa: BLE001
    print("robots.txt:", type(e).__name__, e)
html = f.get(url)
s = BeautifulSoup(html, "html.parser")
print("\n### <title>", s.title.get_text(strip=True) if s.title else "")
for m in s.find_all("meta"):
    k = m.get("property") or m.get("name")
    if k and any(x in k for x in ("description", "og:", "keywords", "article:")):
        print("meta", k, "=", (m.get("content") or "")[:300])
for j in s.find_all("script", type="application/ld+json"):
    print("\n### JSON-LD\n", (j.string or "")[:1500])
print("\n### elementos con categoría/estilo/género/etiqueta en la clase o el enlace")
vistos = set()
for el in s.find_all(True):
    cls = " ".join(el.get("class") or [])
    href = el.get("href") or ""
    if re.search(r"categ|estilo|genero|género|tag|tax|term", cls + " " + href, re.I):
        t = el.get_text(" ", strip=True)[:120]
        clave = (cls[:60], t, href[:100])
        if t and clave not in vistos:
            vistos.add(clave)
            print(f"  <{el.name} class='{cls[:60]}' href='{href[:100]}'> {t}")
    if len(vistos) > 60:
        break
print("\n### texto completo (sin scripts)")
for t in s(["script", "style", "noscript"]):
    t.decompose()
lineas = [x.strip() for x in s.get_text("\n").split("\n") if len(x.strip()) > 2]
for x in lineas[:160]:
    print("  |", x[:220])
print("\n### API de WordPress")
for ruta in ("/wp-json/", "/wp-json/wp/v2/types", "/wp-json/wp/v2/taxonomies"):
    try:
        d = json.loads(f.get(base + ruta))
        if ruta == "/wp-json/":
            print(ruta, "nombre:", d.get("name"), "· rutas:", [r for r in d.get("routes", {}) if "/wp/v2/" in r][:60])
        else:
            print(ruta, json.dumps({k: {"rest_base": v.get("rest_base"), "name": v.get("name"),
                                        "types": v.get("types")} for k, v in d.items()}, ensure_ascii=False)[:2500])
    except Exception as e:  # noqa: BLE001
        print(ruta, "→", type(e).__name__, str(e)[:150])
