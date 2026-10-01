"""Diagnóstico: qué dice la página del concierto de los artistas con etiqueta genérica o sin estilo.

Lee unas cuantas páginas (con el mismo lector educado que las agendas: robots.txt y ritmo por web) y saca el texto
alrededor del nombre del artista, para ver por qué no se reconoce el estilo. Solo escribe en la salida.

Uso: python tools/diagnostico_agenda.py [N]
"""
import json
import random
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bs4 import BeautifulSoup  # noqa: E402

from scraper.fetch import Fetcher  # noqa: E402
from scraper.nombres import claves_ficha  # noqa: E402
from scraper.normalize import norm  # noqa: E402
from scraper.origen import estilos_en_texto, pais_en_texto  # noqa: E402

n = int(sys.argv[1]) if len(sys.argv) > 1 else 16
solo = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else None  # webs a mirar (por defecto, todas)
recs = json.loads((RAIZ / "data" / "concerts.json").read_text(encoding="utf-8"))["conciertos"]
hoy = date.today().isoformat()
casos = [r for r in recs if r["fecha"] >= hoy and (r.get("grupos_generico") or not r.get("estilos_discogs"))
         and not r.get("origen_no_aplica")]
random.seed(7)
f = Fetcher()
por_host: dict = {}
for r in random.sample(casos, len(casos)):
    for x in r.get("fuentes") or []:
        h = (x.get("url") or "").split("/")[2:3]
        if h and (not solo or any(x in h[0] for x in solo)) and len(por_host.setdefault(h[0], [])) < max(2, n // 4):
            por_host[h[0]].append((r, x["url"]))
for host, lista in por_host.items():
    for r, u in lista[:n if solo else 4]:
        nombre = (claves_ficha(r)[1:2] or claves_ficha(r)[:1] or [r["artista"]])[0]
        print(f"\n===== {host} · {r['artista']} · nombre buscado: {nombre!r}\n{u}")
        try:
            s = BeautifulSoup(f.get(u), "html.parser")
        except Exception as e:  # noqa: BLE001
            print("  ERROR", type(e).__name__, str(e)[:120])
            continue
        for t in s(["script", "style", "nav", "header", "footer", "form", "aside", "noscript"]):
            t.decompose()
        texto = s.get_text("\n")
        lineas = [x.strip() for x in texto.split("\n") if len(x.strip()) > 25]
        con = [x for x in lineas if norm(nombre) in norm(x)]
        print(f"  líneas con el nombre: {len(con)} de {len(lineas)}")
        for x in (con or lineas)[:6]:
            print("  |", x[:300])
        print("  estilos:", estilos_en_texto(texto, nombre), "· país:", pais_en_texto(texto, nombre)[0])
