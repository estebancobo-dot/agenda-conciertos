"""Diagnóstico de fuentes candidatas (fase 4: géneros con pocos conciertos). Para cada web: si su robots.txt deja
leerla (el mismo lector que las agendas: robots.txt, identificación y ritmo), qué devuelve y si trae conciertos
legibles (JSON-LD de eventos, fechas en el texto, o un JSON de datos abiertos). Solo escribe en la salida.

Uso: python tools/diagnostico_candidatas.py
"""
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper.fetch import Fetcher, RobotsBlocked  # noqa: E402
from scraper.sources.base import jsonld_events, soup_of  # noqa: E402

CANDIDATAS = [
    # datos abiertos del Ayuntamiento de Madrid: actividades culturales municipales de los próximos 100 días
    ("datos.madrid.es (100 días)", "https://datos.madrid.es/egob/catalogo/206974-0-agenda-eventos-culturales-100.json"),
    ("datos.madrid.es (agenda)", "https://datos.madrid.es/egob/catalogo/300107-0-agenda-actividades-eventos.json"),
    # cantautores
    ("Café Libertad 8", "https://libertad8cafe.es/event_cat/conciertos/"),
    # gótico, dark wave, post-punk
    ("GotiFiestas", "https://www.gotifiestas.com/"),
    ("GotiFiestas (eventos)", "https://www.gotifiestas.com/eventos/"),
    # reggae
    ("DotheReggae (Comunidad de Madrid)", "https://www.dothereggae.com/agenda/c-de-madrid/"),
    # generales con géneros poco cubiertos
    ("esMadrid (música)", "https://www.esmadrid.com/agenda-musica-madrid"),
    ("Festify Indie", "https://festifyindie.com/conciertos/madrid"),
    ("Comunidad de Madrid (actividades)", "https://www.comunidad.madrid/actividades"),
    ("conciertos.club (reggae-ska)", "https://conciertos.club/madrid/conciertos/estilos/reggae-ska"),
    ("conciertos.club (estilos)", "https://conciertos.club/madrid/conciertos/estilos/"),
]
FECHA = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2,4}))?\b|\b\d{1,2} de (?:enero|febrero|marzo|abril|mayo|junio|"
                   r"julio|agosto|septiembre|octubre|noviembre|diciembre)\b", re.I)
f = Fetcher()


def resumen_json(datos) -> None:
    lista = datos.get("@graph") if isinstance(datos, dict) else datos
    if not isinstance(lista, list):
        print("  JSON sin lista de eventos; claves:", list(datos)[:20] if isinstance(datos, dict) else type(datos))
        return
    print(f"  {len(lista)} elementos; claves del primero: {list(lista[0])[:30] if lista else []}")
    tipos = collections.Counter()
    musica = []
    for e in lista:
        t = " ".join(str(e.get(k) or "") for k in ("@type", "tipo", "type", "audience")).lower()
        tipos[(str(e.get("@type") or ""))[-60:]] += 1
        texto = json.dumps(e, ensure_ascii=False).lower()
        if any(x in texto for x in ("concierto", "música", "musica", "musicales/", "/musica")) or "music" in t:
            musica.append(e)
    print("  tipos:", dict(tipos.most_common(12)))
    print(f"  con música/concierto: {len(musica)}")
    for e in musica[:12]:
        loc = e.get("event-location") or (e.get("location") or {})
        print(f"   - {e.get('dtstart') or e.get('startDate')} · {str(e.get('title') or e.get('name'))[:70]} · "
              f"{str(loc)[:60] if not isinstance(loc, dict) else loc.get('name') or loc.get('event-location')} · "
              f"{str(e.get('@type'))[-40:]} · {str(e.get('link') or e.get('url'))[:80]}")


for nombre, url in CANDIDATAS:
    print(f"\n## {nombre} — {url}")
    try:
        print("  robots:", f.robots_status(url), "· permitido:", f.robots_allows(url))
    except Exception as e:  # noqa: BLE001
        print("  robots: error", type(e).__name__, e)
    try:
        cuerpo = f.get(url)
    except RobotsBlocked:
        print("  robots.txt NO permite leerla")
        continue
    except Exception as e:  # noqa: BLE001
        print(f"  error: {type(e).__name__}: {str(e)[:200]}")
        continue
    print(f"  {len(cuerpo)} caracteres")
    if url.endswith(".json") or cuerpo.lstrip()[:1] in "[{":
        try:
            resumen_json(json.loads(cuerpo))
        except ValueError as e:
            print("  JSON no válido:", e)
        continue
    s = soup_of(cuerpo)
    evs = jsonld_events(s)
    print(f"  JSON-LD de eventos: {len(evs)}")
    for e in evs[:8]:
        loc = e.get("location")
        loc = loc.get("name") if isinstance(loc, dict) else loc
        print(f"   - {str(e.get('startDate'))[:16]} · {str(e.get('name'))[:70]} · {str(loc)[:50]}")
    for t in s(["script", "style", "noscript"]):
        t.decompose()
    lineas = [x.strip() for x in s.get_text("\n").split("\n") if len(x.strip()) > 2]
    con_fecha = [x for x in lineas if FECHA.search(x)]
    print(f"  líneas con fecha: {len(con_fecha)} de {len(lineas)}")
    for x in con_fecha[:15]:
        print("   |", x[:160])
    enlaces = collections.Counter(re.sub(r"[^/]+/?$", "", a.get("href", "")) for a in s.find_all("a", href=True)
                                  if a.get("href", "").startswith("http"))
    print("  patrones de enlace más repetidos:", [k for k, v in enlaces.most_common(6) if v > 3])
