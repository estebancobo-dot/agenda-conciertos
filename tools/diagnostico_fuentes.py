"""Diagnóstico: ¿encuentran Bandcamp y Deezer a los artistas sin estilo o sin origen? (y ¿lo permite su robots.txt?)

Solo escribe en la salida; no guarda nada. Uso: python tools/diagnostico_fuentes.py [N]
"""
import json
import random
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bs4 import BeautifulSoup  # noqa: E402

from scraper.fetch import Fetcher  # noqa: E402
from scraper.nombres import claves_ficha  # noqa: E402
from scraper.normalize import norm  # noqa: E402

n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
recs = json.loads((RAIZ / "data" / "concerts.json").read_text(encoding="utf-8"))["conciertos"]
hoy = date.today().isoformat()
casos = [r for r in recs if r["fecha"] >= hoy and not r.get("origen_no_aplica")
         and (r.get("grupos_generico") or not r.get("estilos_discogs") or not r.get("nacionalidad"))]
random.seed(11)
nombres = []
for r in random.sample(casos, len(casos)):
    x = (claves_ficha(r)[1:2] or claves_ficha(r)[:1] or [None])[0]
    if x and norm(x) not in {norm(y) for y in nombres} and len(norm(x)) > 2:
        nombres.append(x)
    if len(nombres) >= n:
        break
f = Fetcher()
for u in ("https://bandcamp.com/robots.txt", "https://api.deezer.com/robots.txt"):
    try:
        print(f"\n### {u}\n" + f.get(u, check_robots=False)[:800])
    except Exception as e:  # noqa: BLE001
        print(u, "ERROR", type(e).__name__, str(e)[:100])
bc = dz = 0
for nombre in nombres:
    print(f"\n===== {nombre}")
    try:
        html = f.get(f"https://bandcamp.com/search?q={quote(nombre)}&item_type=b")
        s = BeautifulSoup(html, "html.parser")
        for it in s.select("li.searchresult")[:3]:
            hd = it.select_one(".heading")
            sub = it.select_one(".subhead")
            tags = it.select_one(".tags")
            t = hd.get_text(" ", strip=True) if hd else ""
            ok = norm(t) == norm(nombre)
            bc += ok
            lugar = sub.get_text(" ", strip=True)[:50] if sub else ""
            etiquetas = re.sub(r"\s+", " ", tags.get_text(" ", strip=True))[:90] if tags else ""
            print(f"  BC {'✓' if ok else ' '} {t[:40]!r} · {lugar} · {etiquetas}")
    except Exception as e:  # noqa: BLE001
        print("  BC ERROR", type(e).__name__, str(e)[:120])
    try:
        d = json.loads(f.get(f"https://api.deezer.com/search/artist?q={quote(nombre)}&limit=3", check_robots=False))
        for a in d.get("data", [])[:3]:
            ok = norm(a.get("name", "")) == norm(nombre)
            dz += ok
            gen = ""
            if ok:
                al = json.loads(f.get(f"https://api.deezer.com/artist/{a['id']}/albums?limit=3", check_robots=False))
                gid = {x.get("genre_id") for x in al.get("data", []) if x.get("genre_id")}
                gen = str(sorted(gid))
            print(f"  DZ {'✓' if ok else ' '} {a.get('name')!r} fans={a.get('nb_fan')} albums={a.get('nb_album')} {gen}")
    except Exception as e:  # noqa: BLE001
        print("  DZ ERROR", type(e).__name__, str(e)[:120])
print(f"\nResumen: {len(nombres)} nombres; Bandcamp coincidencias exactas {bc}; Deezer {dz}")
