"""Datos abiertos: la agenda cultural del Ayuntamiento de Madrid (datos.madrid.es).

"Actividades culturales y de ocio municipal en los próximos 100 días" (conjunto 206974): centros culturales de los
21 distritos, CentroCentro, Conde Duque, Matadero, bibliotecas, parques… en JSON, con título, fecha y hora, lugar,
dirección, precio y enlace a la ficha municipal. Su robots.txt deja leerlo (comprobado el 2-10-2026 desde GitHub).

Se toman las actividades de tipo "Música" y, de la "Programación destacada", las que por su título o descripción
son un concierto. El estilo solo si la descripción lo dice del artista ("X es una banda de rock…", el mismo lector
que las páginas de las agendas); si no, se queda sin estilo y lo dan la ficha del artista o nada.
"""
from __future__ import annotations

import html as html_lib
import json
import re
from datetime import date

from ..normalize import clean
from .base import Ctx, make
from .municipios import MUSICA, NO_MUSICA

URL = "https://datos.madrid.es/egob/catalogo/206974-0-agenda-eventos-culturales-100.json"
TIPO_MUSICA = "/actividades/Musica"
TIPO_DESTACADA = "/actividades/ProgramacionDestacadaAgendaCultura"
MAX_DIAS = 3  # una "actividad" de más días seguidos es un ciclo, un curso o una exposición, no un concierto
# lo que el propio título o descripción dice que es (la etiqueta que daría una agenda): sin esto, casi todos estos
# conciertos (coros, bandas municipales, zarzuela…) quedarían "sin clasificar" y saldrían en los géneros habituales
ESTILO_TEXTO = [
    (re.compile(r"(?i)\b(coral|coro|polif[oó]nica|orquesta|sinf[oó]nic[oa]|filarm[oó]nica|cuarteto de cuerda|"
                r"m[uú]sica cl[aá]sica|barroc[oa]|renacentista|m[uú]sica antigua|[oó]pera|l[ií]rica|recital de piano|"
                r"piano y viol[ií]n|bandas? sonoras?|banda (?:de m[uú]sica|sinf[oó]nica|municipal)|"
                r"m[uú]sica de c[aá]mara)\b"), "Música clásica"),
    (re.compile(r"(?i)\bzarzuela\b"), "Zarzuela"),
    (re.compile(r"(?i)\b(jazz|swing|big band|bebop)\b"), "Jazz"),
    (re.compile(r"(?i)\b(flamenco|flamenca|cante jondo)\b"), "Flamenco"),
    (re.compile(r"(?i)\b(copla|cupl[eé]|canci[oó]n espa[nñ]ola)\b"), "Copla"),
    (re.compile(r"(?i)\b(boleros?|tangos?|salsa|cumbia|son cubano|m[uú]sica latinoamericana)\b"), "Música latina"),
    (re.compile(r"(?i)\b(gospel|soul)\b"), "Soul"),
    (re.compile(r"(?i)\b(blues)\b"), "Blues"),
    (re.compile(r"(?i)\b(rock|pop rock)\b"), "Rock"),
    (re.compile(r"(?i)\b(cantautora?|cantautores)\b"), "Cantautor"),
    (re.compile(r"(?i)\b(folk|m[uú]sica tradicional|folcl[oó]rica)\b"), "Folk"),
]
# para público infantil o de alumnos: no son conciertos de artistas (se descartan)
NO_ARTISTAS = re.compile(r"(?i)\b(audici[oó]n(?:es)? de (?:los )?alumnos|alumnos de|escuela de m[uú]sica|"
                         r"cuentacuentos|para (?:beb[eé]s|ni[nñ]os)|infantil|caperucita)\b")


def _fecha(s: str | None) -> date | None:
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s or "")
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def _hora(e: dict) -> str | None:
    t = str(e.get("time") or "").strip()
    m = re.match(r"(\d{1,2}):(\d{2})", t) or re.search(r"\s(\d{1,2}):(\d{2})", str(e.get("dtstart") or ""))
    if not m or (m.group(1) in ("0", "00") and m.group(2) == "00"):
        return None
    return f"{int(m.group(1)):02d}:{m.group(2)}"


def _precio(e: dict) -> str | None:
    if str(e.get("free")) in ("1", "True", "true"):
        return "Gratis"
    p = clean(html_lib.unescape(str(e.get("price") or "")))
    return p[:80] or None


def _es_concierto(e: dict) -> bool:
    tipo = str(e.get("@type") or "")
    if TIPO_MUSICA in tipo:
        return True
    if TIPO_DESTACADA in tipo:
        texto = f"{e.get('title') or ''} {e.get('description') or ''}"
        return bool(MUSICA.search(texto)) and not NO_MUSICA.search(str(e.get("title") or ""))
    return False


def parse(datos: dict | list, hoy: date, horizonte: date) -> list:
    from ..origen import estilos_en_texto
    lista = datos.get("@graph", []) if isinstance(datos, dict) else datos
    out = []
    for e in lista:
        if not isinstance(e, dict) or not _es_concierto(e):
            continue
        d1, d2 = _fecha(e.get("dtstart")), _fecha(e.get("dtend")) or _fecha(e.get("dtstart"))
        if not d1 or (d2 - d1).days >= MAX_DIAS:
            continue
        titulo = clean(html_lib.unescape(str(e.get("title") or "")))
        if not titulo:
            continue
        descripcion = clean(re.sub(r"<[^>]+>", " ", html_lib.unescape(str(e.get("description") or ""))))
        publico = json.dumps(e.get("audience") or "", ensure_ascii=False)
        if NO_ARTISTAS.search(titulo) or NO_ARTISTAS.search(descripcion[:300]) or re.search(r"(?i)ni[nñ]os|familias", publico):
            continue
        estilos = estilos_en_texto(descripcion, titulo) if descripcion else []
        if not estilos:
            # lo que dice el título; si no, la descripción, solo si nombra un único género ("de jazz a boleros" no)
            del_titulo = [est for rx, est in ESTILO_TEXTO if rx.search(titulo)]
            de_desc = {est for rx, est in ESTILO_TEXTO if rx.search(descripcion[:300])}
            estilos = del_titulo[:1] or (list(de_desc) if len(de_desc) == 1 else [])
        area = ((e.get("address") or {}).get("area") or {})
        lugar = clean(html_lib.unescape(str(e.get("event-location") or "")))
        url = str(e.get("link") or URL)
        # actividades de 2-3 días seguidos (dos funciones): una por día
        n = (d2 - d1).days + 1 if d2 and d2 >= d1 else 1
        for i in range(n):
            f = date.fromordinal(d1.toordinal() + i)
            if not (hoy <= f <= horizonte):
                continue
            out.append(make(f, titulo, url, split=False, sala=lugar, ciudad=area.get("locality") or "Madrid",
                            hora=_hora(e), precio=_precio(e), estilo=", ".join(estilos) or None))
    return out


def datos_madrid(ctx: Ctx):
    yield from parse(json.loads(ctx.get(URL)), ctx.today, ctx.horizon)


# ------------------------------------------------------------------ GotiFiestas (escena gótica y dark wave)
# Directorio sin ánimo de lucro de la escena gótica y alternativa de Madrid. Publica sus eventos con la API pública
# de WordPress (/wp-json/wp/v2/eventos): fecha y hora, local, enlace y precio de las entradas, cartel, tipo
# (Concierto, Festival, Fiesta, Quedada) y géneros (EBM, Darkwave, Post-Punk, Synthwave…). Se toman los conciertos
# y festivales; las fiestas y sesiones de DJ no. Su robots.txt deja leerla (comprobado el 2-10-2026).
GOTI = "https://www.gotifiestas.com/wp-json/wp/v2/eventos?per_page=100&page={}"
GOTI_TIPOS = {"concierto", "festival"}
# "LEROY SE MEURT + WE ARE NOT BROTHERS_SYNTH-PUNK_EBM", "BOUND BY ENDOGAMY (CH) + TBA _Electronic Post-Punk":
# los géneros pegados al final con "_" (ya vienen en sus etiquetas) y "en concierto" no son parte del nombre
_GOTI_COLA = re.compile(r"\s*_[^_]*(?:_[^_]*)*$|\s+en concierto$", re.I)


def _goti_titulo(titulo: str, sala: str) -> str:
    """Sin lo que no es el nombre: "Entradas IST IST en MOBY DICK, MADRID 2026" → "IST IST", "GREY GALLOWS – Cadavra
    Club – Madrid" → "GREY GALLOWS", "Suicide Commando “40th Anniversary Tour” // Madrid" → "Suicide Commando"."""
    from ..normalize import norm
    t = _GOTI_COLA.sub("", titulo)
    t = re.sub(r"(?i)^entradas\s+(?:para\s+)?", "", t)
    t = re.split(r"\s+//\s+", t)[0]
    t = re.sub(r"\s*[“\"«][^”\"»]*\b(?:tour|gira)\b[^”\"»]*[”\"»]", "", t, flags=re.I)
    ns = norm(sala)

    def es_lugar(p: str) -> bool:
        n = norm(p)
        return n in ("madrid", "") or bool(re.fullmatch(r"madrid \d{4}", n)) or bool(ns and (n in ns or ns in n))

    t = " – ".join(p for p in re.split(r"\s+[–—]\s+", t) if not es_lugar(p)) or t
    # "… en MOBY DICK, MADRID 2026": lo que va tras " en " nombra la sala
    m = re.search(r"\s+en\s+(.+)$", t, re.I)
    if m and ns and any(w in ns.split() for w in norm(m.group(1)).replace(",", " ").split() if len(w) > 3):
        t = t[: m.start()]
    return clean(t)


def _meta(e: dict, k: str) -> str:
    v = (e.get("meta") or {}).get(k)
    v = v[0] if isinstance(v, list) and v else v
    return clean(html_lib.unescape(str(v or "")))


def gotifiestas_parse(datos: list, hoy: date, horizonte: date) -> list:
    out = []
    for e in datos if isinstance(datos, list) else []:
        cl = e.get("gf_classification") or {}
        tipo = norm_tipo((cl.get("category") or {}).get("name"))
        if tipo not in GOTI_TIPOS:
            continue
        ini = _meta(e, "fecha_inicio")
        f = _fecha(ini)
        if not f or not (hoy <= f <= horizonte):
            continue
        m = re.search(r"T(\d{2}):(\d{2})", ini)
        hora = f"{m.group(1)}:{m.group(2)}" if m and m.group(0) != "T00:00" else None
        titulo = _meta(e, "titulo_evento") or clean(html_lib.unescape(str((e.get("title") or {}).get("rendered") or "")))
        sala = _meta(e, "_gf_event_venue") or _meta(e, "ubicacion")
        titulo = _goti_titulo(titulo, sala)
        if not titulo:
            continue
        generos = [clean(t.get("name")) for t in cl.get("tags") or [] if clean(t.get("name")) and t.get("name") != "Varios"]
        precio = _meta(e, "_gf_event_ticket_text")
        r = make(f, titulo, str(e.get("link") or ""), sala=sala,
                 hora=hora, precio=precio if re.search(r"\d", precio) else None, estilo=", ".join(generos) or None,
                 imagen=_meta(e, "imagen_evento") or None)
        if tipo == "festival":
            r.tipo = "festival"
        out.append(r)
    return out


def norm_tipo(s) -> str:
    return clean(str(s or "")).lower()


def gotifiestas(ctx: Ctx):
    for pag in range(1, 6):
        try:
            datos = json.loads(ctx.get(GOTI.format(pag)))
        except Exception as ex:  # noqa: BLE001 - WordPress responde 400 al pasar de la última página
            if pag == 1:
                raise
            if "400" not in str(ex):
                ctx.errors.append(f"página {pag}: {type(ex).__name__}: {str(ex)[:120]}")
            break
        yield from gotifiestas_parse(datos, ctx.today, ctx.horizon)
        if len(datos) < 100:
            break


# ------------------------------------------------------------------ SalirMadrid (country y folk)
# Agenda de ocio de Madrid con páginas por género. Sus eventos llevan JSON-LD (schema.org/Event). Se leen las de
# country y folk. Su etiqueta de género es amplia (pone "folk" a Morat o a Depedro): el estilo solo se toma cuando el
# propio título lo dice ("Moonshine Wagon (Country)", "Los Sonex (Folk mexicano)"); si no, lo dan las fichas.
SALIR = ["https://salirmadrid.es/live-music-country-madrid", "https://salirmadrid.es/live-music-folk-madrid"]
_SALIR_ESTILO = re.compile(r"\s*\(([^()]*\b(?:country|folk|bluegrass|americana|celta|celtic|irish|irlandes[ao]?|"
                           r"rockabilly|western|cajun|honky tonk|rock sure[nñ]o|southern rock)\b[^()]*)\)", re.I)


# fiestas tras el concierto y sesiones de DJ: no son conciertos ("El Búho After Party . Modis")
_NO_CONCIERTO = re.compile(r"(?i)\b(after ?party|dj set|sesi[oó]n de dj|fiesta)\b")


def salirmadrid_titulo(t: str) -> tuple[str, str | None]:
    """"Concierto de Ryan Adams en Madrid" → Ryan Adams; "Moonshine Wagon (Country)" → (Moonshine Wagon, Country);
    "Concierto de Morat en Madrid (Segunda Fecha)" → Morat."""
    t = clean(html_lib.unescape(t or ""))
    m = _SALIR_ESTILO.search(t)
    estilo = clean(m.group(1)) if m else None
    t = _SALIR_ESTILO.sub("", t)
    t = re.sub(r"(?i)\s*\((?:primera|segunda|tercera|cuarta|nueva|[0-9]+\w*)\s+(?:fecha|sesi[oó]n|funci[oó]n)\)", "", t)
    t = re.sub(r"(?i)\s*\(\d{1,2} de \w+\)", "", t)  # "(29 de Octubre)"
    t = re.sub(r"(?i)^conciertos?\s+de\s+", "", t)
    t = re.sub(r"(?i)\s+en\s+madrid\b.*$", "", t)
    return clean(t), estilo


def salirmadrid_parse(html: str, page_url: str, today: date) -> list:
    from .base import jsonld_events, ld_to_raw, soup_of
    out = []
    for ev in jsonld_events(soup_of(html)):
        nombre, estilo = salirmadrid_titulo(str(ev.get("name") or ""))
        if not nombre or _NO_CONCIERTO.search(nombre):
            continue
        ev = dict(ev, name=nombre)
        r = ld_to_raw(ev, today, page_url, use_performers=False, split=True, estilo=estilo)
        if r:
            out.append(r)
    return out


def salirmadrid(ctx: Ctx):
    for url in SALIR:
        try:
            yield from salirmadrid_parse(ctx.get(url), url, ctx.today)
        except Exception as ex:  # noqa: BLE001 - una página caída no tumba la otra
            ctx.errors.append(f"{url}: {type(ex).__name__}: {str(ex)[:120]}")
