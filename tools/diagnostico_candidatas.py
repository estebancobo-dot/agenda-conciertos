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

from bs4 import BeautifulSoup

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
# Americana y folk (country, bluegrass, folk, celta, southern rock…): candidatas del 2-10-2026
AMERICANA = [
    ("Houston Party (promotora)", "https://houstonpartymusic.com/"),
    ("Houston Party (fechas)", "https://houstonpartymusic.com/tour-dates/"),
    ("SalirMadrid (country)", "https://salirmadrid.es/live-music-country-madrid"),
    ("SalirMadrid (folk)", "https://salirmadrid.es/live-music-folk-madrid"),
    ("SalirMadrid (música en directo)", "https://salirmadrid.es/live-music"),
    ("NocheMAD (folk)", "https://www.nochemad.com/conciertos-folk-madrid"),
    ("NocheMAD (country)", "https://www.nochemad.com/conciertos-country-madrid"),
    ("Songkick (folk)", "https://www.songkick.com/metro-areas/28755-spain-madrid/genre/folk"),
    ("Songkick (country)", "https://www.songkick.com/metro-areas/28755-spain-madrid/genre/country"),
    ("Qconciertos (folk)", "https://qconciertos.es/estilo/folk/"),
    ("Qconciertos (americana)", "https://qconciertos.es/estilo/americana/"),
    ("Qconciertos (bluegrass)", "https://qconciertos.es/estilo/bluegrass/"),
    ("Qconciertos (rock sureño)", "https://qconciertos.es/estilo/rock-sureno/"),
    ("conciertos.club (world music)", "https://conciertos.club/madrid/conciertos/estilos/world-music-musica-etnica"),
    ("Deviolines (jam de bluegrass)", "https://www.deviolines.com/eventos/spain/madrid/madrid/jam-sessions/jam-de-bluegrass-en-madrid/"),
    ("Folklore Plaza Castilla", "http://www.folkloreplazacastilla.com/"),
    ("Diariofolk (en vivo)", "https://www.diariofolk.com/en-vivo/"),
    ("Taquilla (folk)", "https://www.taquilla.com/conciertos/folk"),
    ("El Corte Inglés entradas (folk Madrid)", "https://www.elcorteingles.es/entradas/conciertos/madrid/folk/"),
]
# salas con muchos conciertos cuya web no leíamos (página de Fuentes): su web, su agenda y, si es un WordPress con
# The Events Calendar, su API de eventos (/wp-json/tribe/events/v1/events). Candidatas del 3-10-2026
TRIBE = "wp-json/tribe/events/v1/events?per_page=50"
SALAS = [
    ("Intruso Bar", "https://www.intrusobar.com/"),
    ("Intruso Bar (API)", "https://www.intrusobar.com/" + TRIBE),
    ("Moe Club", "https://www.moeclub.com/"),
    ("Moe Club (API)", "https://www.moeclub.com/" + TRIBE),
    ("Rincón del Arte Nuevo", "https://www.elrincondelartenuevo.com/"),
    ("Café El Despertar", "https://cafeeldespertar.com/"),
    ("Café El Despertar (API)", "https://cafeeldespertar.com/" + TRIBE),
    ("Café Central (programación)", "https://cafecentralmadrid.com/programacion/"),
    ("Café Central (API)", "https://cafecentralmadrid.com/" + TRIBE),
    ("Thundercat (programación)", "https://thundercatclub.com/programacion-conciertos/"),
    ("Thundercat (API)", "https://thundercatclub.com/" + TRIBE),
    ("Café La Palma (agenda)", "https://cafelapalma.com/es/agenda-de-conciertos/"),
    ("Café La Palma (API)", "https://cafelapalma.com/" + TRIBE),
    ("Cadillac Solitario (eventos)", "https://cadillacsolitario.com/eventos/"),
    ("Cadillac Solitario (API)", "https://cadillacsolitario.com/" + TRIBE),
    ("Sala Vesta", "https://salavesta.com/"),
    ("Sala Vesta (API)", "https://salavesta.com/" + TRIBE),
    ("Hangar 48", "https://www.hangar48.es/"),
    ("Hangar 48 (API)", "https://www.hangar48.es/" + TRIBE),
    ("Dime que me Quieres", "https://conciertos.dimequemequieresbardecopas.com/"),
    ("Dime que me Quieres (API)", "https://conciertos.dimequemequieresbardecopas.com/" + TRIBE),
    ("El Café de la Ópera", "https://www.elcafedelaopera.com/"),
]
# segunda tanda (3-10-2026): Hangar 48 y otras salas que venden por TicketAndRoll, y webs de salas con conciertos
SALAS2 = [
    ("TicketAndRoll (robots y portada)", "https://ticketandroll.com/"),
    ("TicketAndRoll: Hangar 48", "https://ticketandroll.com/local/sala-hangar-48"),
    ("TicketAndRoll: Hangar 48 (2)", "https://ticketandroll.com/local/hangar-48"),
    ("TicketAndRoll: Rincón del Arte Nuevo", "https://ticketandroll.com/local/el-rincon-del-arte-nuevo"),
    ("TicketAndRoll: Jazzville", "https://ticketandroll.com/local/jazzville"),
    ("El Perro Club (conciertos)", "https://elperroclub.es/conciertos/"),
    ("El Perro Club (API)", "https://elperroclub.es/" + TRIBE),
    ("Sala Uni", "https://salauni.es/"),
    ("Sala Uni (API)", "https://salauni.es/" + TRIBE),
    ("Fulanita de Tal", "https://fulanitadetal.com/"),
    ("Fulanita de Tal (API)", "https://fulanitadetal.com/" + TRIBE),
    ("Live Las Ventas", "https://livelasventas.com/es/"),
    ("Círculo de Bellas Artes (eventos)", "https://www.circulobellasartes.com/eventos/"),
    ("Círculo de Bellas Artes (API)", "https://www.circulobellasartes.com/" + TRIBE),
    ("Ateneo de Madrid", "https://www.ateneodemadrid.com/"),
    ("Palacio Vistalegre", "https://www.palaciovistalegre.com/"),
    ("Café Berlín", "https://berlincafe.es/"),
    ("Tempo Audiophile Club (API)", "https://tempoclub.es/" + TRIBE),
    ("Teatro Eslava", "https://teatroeslava.com/"),
]
if len(sys.argv) > 1 and sys.argv[1] == "americana":
    CANDIDATAS = AMERICANA
if len(sys.argv) > 1 and sys.argv[1] == "salas":
    CANDIDATAS = SALAS
if len(sys.argv) > 1 and sys.argv[1] == "salas2":
    CANDIDATAS = SALAS2
FECHA = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2,4}))?\b|\b\d{1,2} de (?:enero|febrero|marzo|abril|mayo|junio|"
                   r"julio|agosto|septiembre|octubre|noviembre|diciembre)\b", re.I)
f = Fetcher()
if len(sys.argv) > 2 and sys.argv[1] in ("--crudo", "--render"):
    if sys.argv[1] == "--render":  # la página ya montada por un navegador real (webs con la agenda en JavaScript)
        from scraper.render import Navegador
        nav = Navegador(f)
        f.get = lambda u, **kw: nav.html(u)
    # lo que devuelve una dirección tal cual (las primeras 12.000 letras), p. ej. la API de WordPress de una web
    for u in sys.argv[2:]:
        u, _, marca = u.partition("@")
        print(f"\n## {u}\n  robots: {f.robots_status(u)} · permitido: {f.robots_allows(u)}")
        try:
            # sin <head>, dibujos SVG, scripts ni estilos: lo que importa es cómo vienen los conciertos
            t = f.get(u)
            if marca.startswith("enlaces"):
                # "URL@enlaces:patrón": solo los enlaces (y su texto) cuya dirección cumple el patrón
                pat = re.compile(marca.partition(":")[2] or ".", re.I)
                vistos = set()
                for a in BeautifulSoup(t, "lxml").select("a[href]"):
                    h = a["href"]
                    if pat.search(h) and h not in vistos:
                        vistos.add(h)
                        print(f"  {h} · {a.get_text(' ', strip=True)[:90]}")
                print(f"  ({len(vistos)} enlaces)")
                continue
            if marca == "claves":
                # "URL@claves": la forma de los datos que trae la página (claves, tamaño de las listas y un ejemplo)
                # y el título; para ver dónde están los conciertos en un JSON demasiado largo para enseñarlo entero
                sp = BeautifulSoup(t, "lxml")
                print("  título:", sp.title.get_text(strip=True) if sp.title else None)

                def forma(x, pre="", fondo=0):
                    if fondo > 6:
                        return
                    if isinstance(x, dict):
                        for k, v in list(x.items())[:40]:
                            tam = f"[{len(v)}]" if isinstance(v, list) else ""
                            ej = "" if isinstance(v, (dict, list)) else f" = {str(v)[:70]!r}"
                            print(f"  {pre}{k}{tam}{ej}")
                            forma(v, pre + "  ", fondo + 1)
                    elif isinstance(x, list) and x:
                        forma(x[0], pre + "  ", fondo + 1)
                for sc in sp.select('script[type="application/json"], script#__NEXT_DATA__, [data-page]'):
                    raw = sc.get("data-page") if (sc.get("data-page") or "").startswith("{") else sc.get_text()
                    try:
                        datos = json.loads(raw)
                    except ValueError as e:
                        print(f"  <{sc.name}> {len(raw)} letras: no es JSON ({e}); empieza {raw[:80]!r} y acaba {raw[-80:]!r}")
                        continue
                    print(f"  <{sc.name} {sc.get('id') or sc.get('type') or 'data-page'}> {len(raw)} letras")
                    forma(datos)
                continue
            if marca == "json":
                # "URL@json": los datos que trae la página para montarse con JavaScript (Next.js, JSON-LD…)
                for sc in BeautifulSoup(t, "lxml").select('script[type="application/json"], script[type="application/ld+json"], script#__NEXT_DATA__'):
                    print(f"  <script {sc.get('id') or sc.get('type')}> {len(sc.get_text())} letras")
                    print(sc.get_text()[:12000])
                continue
            t = re.sub(r"(?is)<head\b.*?</head>|<svg\b.*?</svg>|<script\b.*?</script>|<style\b.*?</style>", "", t)
            # con "URL@texto": desde la primera vez que sale ese texto (para ver un bloque concreto de una página larga)
            i = t.find(marca) if marca else 0
            print(t[max(0, i - 300):][:15000])
        except Exception as e:  # noqa: BLE001
            print("  error:", type(e).__name__, e)
    if sys.argv[1] == "--render":
        print(f"\n  peticiones que robots.txt no permite (no se hicieron): {len(nav.cortadas)}",
              *nav.cortadas[:20], sep="\n   ")
        nav.cerrar()
    sys.exit(0)


def resumen_json(datos) -> None:
    if isinstance(datos, dict) and isinstance(datos.get("events"), list):  # The Events Calendar (WordPress)
        evs = datos["events"]
        print(f"  The Events Calendar: {len(evs)} eventos (total {datos.get('total')}, páginas {datos.get('total_pages')})")
        for e in evs[:15]:
            v = e.get("venue") or {}
            cats = [c.get("name") for c in e.get("categories") or []]
            print(f"   - {e.get('start_date')} · {str(e.get('title'))[:70]} · {v.get('venue') if isinstance(v, dict) else v} · "
                  f"{cats} · {e.get('cost') or ''} · {str(e.get('url'))[:80]}")
        return
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
