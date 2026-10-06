"""Diagnóstico: ¿se pueden leer con un navegador real las webs que montan su agenda con JavaScript? Por cada dirección:
si robots.txt la permite, cuántos eventos con fecha trae en datos estructurados (JSON-LD) una vez montada, cuántas
fechas se ven en el texto, los enlaces que parecen de conciertos, y unas líneas de muestra con fecha. Mismas reglas
que la lectura (scraper/render.py: robots.txt también de cada petición de la página, mismo ritmo e identificación).
Solo escribe en la salida.

Uso: python tools/diagnostico_render.py URL [URL…]
"""
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup  # noqa: E402

from scraper.entradas import _eventos_jsonld  # noqa: E402
from scraper.fetch import Fetcher  # noqa: E402
from scraper.render import Navegador  # noqa: E402

MESES = r"ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre"
FECHA = re.compile(rf"(?i)\b(\d{{1,2}}\s*(de\s+)?({MESES})\b|\d{{1,2}}[/.-]\d{{1,2}}([/.-]\d{{2,4}})?|\d{{4}}-\d{{2}}-\d{{2}})")
f = Fetcher()
nav = Navegador(f)
for url in sys.argv[1:]:
    print(f"\n## {url}\n  robots: {f.robots_status(url)} · permitido: {f.robots_allows(url)}")
    for modo in ("sin navegador", "con navegador"):
        try:
            html = f.get(url) if modo == "sin navegador" else nav.html(url)
        except Exception as e:  # noqa: BLE001
            print(f"  [{modo}] error: {type(e).__name__}: {str(e)[:160]}")
            continue
        sp = BeautifulSoup(html, "lxml")
        evs = [e for e in _eventos_jsonld(sp) if re.match(r"\d{4}-\d{2}-\d{2}", str(e.get("startDate") or ""))]
        for t in sp(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
            t.decompose()
        lineas = [x.strip() for x in sp.get_text("\n").split("\n") if x.strip()]
        con_fecha = [x for x in lineas if FECHA.search(x) and len(x) < 200]
        host = urlsplit(url).netloc
        enlaces = Counter()
        muestras = []
        for a in sp.select("a[href]"):
            h = urljoin(url, a["href"])
            if urlsplit(h).netloc == host and re.search(r"(?i)evento|event|concierto|agenda|actividad|programa", h) \
                    and h.rstrip("/") != url.rstrip("/"):
                ruta = "/".join(urlsplit(h).path.strip("/").split("/")[:-1])
                enlaces[ruta] += 1
                if len(muestras) < 4:
                    muestras.append(f"{h} · {a.get_text(' ', strip=True)[:60]}")
        print(f"  [{modo}] {len(html)} letras · JSON-LD con fecha: {len(evs)} · líneas con fecha: {len(con_fecha)}"
              f" · enlaces de eventos por sección: {dict(enlaces.most_common(4))}")
        for e in evs[:3]:
            print(f"     JSON-LD: {str(e.get('startDate'))[:16]} · {str(e.get('name'))[:70]} · {str((e.get('location') or {}).get('name') if isinstance(e.get('location'), dict) else e.get('location'))[:40]}")
        for x in con_fecha[:6]:
            print(f"     texto: {x[:150]}")
        for m in muestras:
            print(f"     enlace: {m}")
    if nav.cortadas:
        print(f"  peticiones de la página que robots.txt no permite (no se hicieron): {len(nav.cortadas)}")
        nav.cortadas.clear()
nav.cerrar()
