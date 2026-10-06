"""Diagnóstico: ¿qué aportaría Festify Indie (festifyindie.com) como fuente? Su agenda de Madrid se monta con
JavaScript: se lee con un navegador real (scraper/render.py: robots.txt también de cada petición, mismo ritmo e
identificación), con sus subpáginas de Madrid, y se cruza con la agenda actual (data/concerts.json): cuántos
conciertos ya tenemos, cuántos son nuevos, cuántos ganarían la pata de agenda y cuántos el enlace de compra. También
mira si la página de cada concierto se lee sin navegador. Solo escribe en la salida.

Uso: python tools/diagnostico_festify.py [máx. subpáginas]
"""
import json
import re
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup  # noqa: E402

from scraper.entradas import _eventos_jsonld, _offer_url, _precio, ticketera  # noqa: E402
from scraper.fetch import Fetcher  # noqa: E402
from scraper.merge import artistas_coinciden, mismo_acto_en_sala  # noqa: E402
from scraper.normalize import canon_sala  # noqa: E402
from scraper.pipeline import HORIZONTE_DIAS  # noqa: E402
from scraper.registry import FUENTES  # noqa: E402
from scraper.render import Navegador  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
INICIO = "https://festifyindie.com/conciertos/madrid"
MAX_SUB = int(sys.argv[1]) if len(sys.argv) > 1 else 15
hoy = date.today()
horizonte = hoy + timedelta(days=HORIZONTE_DIAS)
f = Fetcher()
nav = Navegador(f)

eventos: dict[tuple, dict] = {}
pendientes, vistas = [INICIO], set()
while pendientes and len(vistas) < MAX_SUB:
    u = pendientes.pop(0)
    if u in vistas:
        continue
    vistas.add(u)
    try:
        sp = BeautifulSoup(nav.html(u), "lxml")
    except Exception as e:  # noqa: BLE001
        print(f"- {u}: {type(e).__name__} {str(e)[:120]}")
        continue
    n0 = len(eventos)
    for ev in _eventos_jsonld(sp):
        ini = str(ev.get("startDate") or "")
        if not re.match(r"\d{4}-\d{2}-\d{2}", ini):
            continue
        loc = ev.get("location") or {}
        loc = loc[0] if isinstance(loc, list) and loc else loc
        sala = (loc.get("name") if isinstance(loc, dict) else str(loc or "")) or ""
        ciudad = ""
        if isinstance(loc, dict) and isinstance(loc.get("address"), dict):
            ciudad = str(loc["address"].get("addressLocality") or "")
        k = (ini[:10], str(ev.get("name") or "").strip().lower(), sala.lower())
        eventos[k] = {"fecha": ini[:10], "artista": str(ev.get("name") or "").strip(), "sala": sala, "ciudad": ciudad,
                      "url": ev.get("url") if isinstance(ev.get("url"), str) else u,
                      "compra": _offer_url(ev), "precio": _precio(ev.get("offers"))}
    print(f"- {u}: {len(eventos) - n0} conciertos nuevos en esta página (total {len(eventos)})")
    for a in sp.select("a[href]"):
        h = urljoin(u, a["href"]).split("#")[0].split("?")[0]
        if urlsplit(h).netloc == "festifyindie.com" and h.startswith(INICIO) and h not in vistas:
            pendientes.append(h)

evs = [e for e in eventos.values() if hoy.isoformat() <= e["fecha"] <= horizonte.isoformat()]
print(f"\n## Festify: {len(eventos)} conciertos leídos en {len(vistas)} páginas; {len(evs)} entre hoy y 120 días")
print("ciudades:", Counter(e["ciudad"] for e in evs).most_common(8))
print("salas:", Counter(e["sala"] for e in evs).most_common(12))
print("con enlace de compra:", sum(1 for e in evs if e["compra"]), "· de una ticketera conocida:",
      sum(1 for e in evs if e["compra"] and ticketera(e["compra"])), "· con precio:", sum(1 for e in evs if e["precio"]))
print("dominios de compra:", Counter(urlsplit(e["compra"]).netloc for e in evs if e["compra"]).most_common(8))

# cruce con la agenda actual
por = {s.id: s for s in FUENTES}
recs = [r for r in json.loads((RAIZ / "data" / "concerts.json").read_text())["conciertos"] if not r.get("oculto")]
por_dia: dict[str, list] = {}
for r in recs:
    por_dia.setdefault(r["fecha"], []).append(r)


def es_agenda(r):
    return any(por[x["id"]].tipo in ("agregador", "blog") for x in r.get("fuentes") or [] if x.get("id") in por)


ya, nuevos, gana_agenda, gana_compra, ejemplos_nuevos = 0, [], 0, 0, []
for e in evs:
    cand = [r for r in por_dia.get(e["fecha"], [])
            if artistas_coinciden([r["artista"]], [e["artista"]])
            or (canon_sala(r.get("sala")) == canon_sala(e["sala"]) and mismo_acto_en_sala(r["artista"], e["artista"], e["sala"]))]
    if cand:
        ya += 1
        r = cand[0]
        gana_agenda += not es_agenda(r)
        gana_compra += bool(e["compra"] and ticketera(e["compra"]) and not r.get("entradas"))
    else:
        nuevos.append(e)
print(f"\n## Cruce con la agenda actual ({len(recs)} conciertos)")
print(f"ya los tenemos: {ya} · nuevos: {len(nuevos)}")
print(f"de los que ya tenemos: ganarían la pata de agenda {gana_agenda}; ganarían enlace de compra {gana_compra}")
print("nuevos por sala:", Counter(e["sala"] for e in nuevos).most_common(12))
for e in nuevos[:25]:
    print(f"  nuevo: {e['fecha']} · {e['artista'][:50]} · {e['sala']} · {e['ciudad']}")

# ¿la página de cada concierto se lee sin navegador?
print("\n## Páginas de concierto sin navegador")
for e in evs[:4]:
    try:
        sp = BeautifulSoup(f.get(e["url"]), "lxml")
        n = len([x for x in _eventos_jsonld(sp) if x.get("startDate")])
        print(f"- {e['url']}: JSON-LD con fecha {n}")
    except Exception as ex:  # noqa: BLE001
        print(f"- {e['url']}: {type(ex).__name__}")
if nav.cortadas:
    print(f"peticiones de la página que robots.txt no permite (no se hicieron): {len(nav.cortadas)}")
nav.cerrar()
