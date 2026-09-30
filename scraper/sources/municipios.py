"""Agendas culturales municipales.

Cada ayuntamiento publica su agenda con un sistema distinto. Se reconocen los formatos comunes (JSON-LD,
microdatos schema.org/Event, calendarios FullCalendar de Drupal) y, para el resto, hay un lector propio.
De cada agenda solo se toman los actos cuyo título o descripción indica música en directo; se descartan
talleres, exposiciones, inscripciones, etc. Direcciones comprobadas desde GitHub el 29-09-2026.
"""
from __future__ import annotations

import html as html_lib
import json
import re
from datetime import date

from ..normalize import clean, parse_fecha_texto, parse_hora
from .base import Ctx, jsonld_events, ld_to_raw, make, soup_of, text
from .salas import secuencia

MUSICA = re.compile(r"(?i)\b(conciertos?|en concierto|m[uú]sica|rock|blues|folk|country|metal|punk|jazz|pop|indie|"
                    r"cantautora?|recital|tributo|orquesta|coral|coro|big band|banda sinf[oó]nica|flamenco|soul|funk|"
                    r"reggae|swing|gospel|trova|rumba)\b")
NO_MUSICA = re.compile(r"(?i)\b(taller|inscripci[oó]n|inscripciones|curso|exposici[oó]n|clases?|matr[ií]cula|charla|"
                       r"conferencia|club de lectura|cuentacuentos|visita guiada|audiciones? de alumnos|junta de gobierno|"
                       r"pleno|campeonato)\b")

# Agenda de cada municipio: (URL, lector). Lectores: "generico" (JSON-LD, microdatos, FullCalendar) o uno propio.
AGENDAS = {
    "Alcalá de Henares": ("https://culturalcala.es/agenda/", "generico"),
    "Aranjuez": ("https://www.aranjuez.es/agenda", "generico"),
    "Collado Villalba": ("https://www.colladovillalba.es/agenda", "generico"),
    "Las Rozas de Madrid": ("https://www.lasrozas.es/calendario-de-eventos", "generico"),
    "Leganés": ("https://www.leganes.org/agenda/", "leganes"),
    "Alcorcón": ("https://www.ayto-alcorcon.es/es/sections/agenda-cultural", "alcorcon"),
    "Boadilla del Monte": ("https://ayuntamientoboadilladelmonte.org/boadilla-actualidad/agenda", "boadilla"),
    "Torrejón de Ardoz": ("https://teatro.ayto-torrejon.es/eventos_teatro", "torrejon"),
    "Valdemoro": ("https://www.valdemoro.es/teatro", "valdemoro"),
    "Pinto": ("https://www.ayto-pinto.es/agenda-de-actividades", "pinto"),
    "Móstoles": ("https://www.mostoles.es/culturaenmostoles/es/agenda-actividades", "generico"),
}

# Municipios cuya web no tiene una agenda legible (se listan en el informe)
SIN_AGENDA = {
    "Agenda municipal de Fuenlabrada": "No hay página de agenda: la programación se publica en noticias semanales.",
    "Agenda municipal de Majadahonda": "La agenda cultural (cultura.majadahonda.org) responde 404 y la general no incluye actos.",
    "Agenda municipal de Parla": "La web solo carga con JavaScript: el HTML no contiene la agenda.",
    "Agenda municipal de Pozuelo de Alarcón": "La programación del MIRA Teatro solo carga con JavaScript.",
    "Agenda municipal de Rivas-Vaciamadrid": "Sin agenda de actos en la web municipal; los conciertos del Auditorio Miguel Ríos llegan por los agregadores.",
    "Agenda municipal de Getafe (anterior)": "getafe.es/agenda ya no existe; se usa cultura.getafe.es.",
}


# En la descripción solo cuentan expresiones inequívocas: una obra de teatro puede "combinar la música y el humor"
MUSICA_DESC = re.compile(r"(?i)\b(conciertos?|en concierto|recital|tributo a|m[uú]sica en directo)\b|"
                         r"(?:^|[>\n|])\s*(?:m[uú]sica|concierto)\s*(?:[<\n|]|$)")


def es_musica(titulo: str, desc: str = "") -> bool:
    """Título con referencia musical, o descripción inequívoca (o con la categoría 'Música' en una línea propia)."""
    if NO_MUSICA.search(titulo or ""):
        return False
    return bool(MUSICA.search(titulo or "")) or bool(MUSICA_DESC.search(desc or ""))


def _fecha_iso(s: str | None) -> date | None:
    m = re.match(r"\s*(\d{4})-(\d{1,2})-(\d{1,2})", s or "")
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _hora_iso(s: str | None) -> str | None:
    m = re.search(r"T(\d{1,2}):(\d{2})", s or "")
    if m and (m.group(1), m.group(2)) != ("00", "00"):
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    return None


def _evento(fecha, titulo, url, municipio, *, hora=None, sala="", imagen=None, nota=None):
    titulo = clean(titulo)
    if not fecha or not titulo:
        return None
    return make(fecha, titulo, url, split=False, sala=clean(sala), ciudad=municipio, hora=hora, imagen=imagen,
                nota=nota or "Tomado de la agenda municipal.")


# ---------------------------------------------------------------- formatos comunes
def microdatos(s, page_url: str, municipio: str) -> list:
    """schema.org/Event en microdatos (EventON de WordPress, Liferay…)."""
    out = []
    for el in s.select('[itemtype*="schema.org/Event"]'):
        nombre = el.select_one('[itemprop="name"]')
        titulo = (nombre.get("content") or text(nombre)) if nombre else ""
        st = el.select_one('[itemprop="startDate"]')
        if not st:
            continue
        valor = st.get("content") or st.get("date") or st.get("datetime") or text(st)
        fecha = _fecha_iso(valor)
        u = el.select_one('[itemprop="url"]') or (nombre if nombre is not None and nombre.name == "a" else None)
        url = (u.get("href") or u.get("content")) if u is not None else page_url
        loc = el.select_one('[itemprop="location"] [itemprop="name"]')
        desc = el.select_one('[itemprop="description"]')
        desc = (desc.get("content") or text(desc)) if desc is not None else ""
        if not titulo:  # EventON pone el nombre solo en su JSON-LD, a veces mal formado
            sc = el.find("script", type="application/ld+json")
            m = re.search(r'"name"\s*:\s*"([^"]+)"', sc.string or "") if sc else None
            titulo = m.group(1) if m else ""
            m = re.search(r'"description"\s*:\s*"(.*?)"\s*[,}]', sc.string or "", re.S) if sc else None
            desc = desc or (re.sub(r"<[^>]+>", "|", m.group(1)) if m else "")
        hora = _hora_iso(valor)
        if not hora:
            t = el.select_one(".start-time, [itemprop='startTime']")
            hora = parse_hora(text(t)) if t else None
        if es_musica(titulo, desc):
            ev = _evento(fecha, titulo, url or page_url, municipio, hora=hora, sala=text(loc) if loc else "")
            if ev:
                out.append(ev)
    return out


def _fullcalendar(s) -> list[dict]:
    """Eventos de los calendarios FullCalendar que Drupal guarda en drupal-settings-json."""
    out = []
    for sc in s.select('script[data-drupal-selector="drupal-settings-json"], script[type="application/json"]'):
        try:
            stack = [json.loads(sc.string or "")]
        except ValueError:
            continue
        while stack:
            x = stack.pop()
            if isinstance(x, str) and x[:1] in "{[":
                try:
                    stack.append(json.loads(x))
                except ValueError:
                    pass
            elif isinstance(x, dict):
                if "title" in x and "start" in x:
                    out.append(x)
                else:
                    stack.extend(x.values())
            elif isinstance(x, list):
                stack.extend(x)
    return out


def fullcalendar(s, page_url: str, municipio: str) -> list:
    from urllib.parse import urljoin
    out = []
    for e in _fullcalendar(s):
        titulo = clean(html_lib.unescape(re.sub(r"<[^>]+>", " ", e.get("title") or "")))
        desc = re.sub(r"<[^>]+>", "|", e.get("des") or e.get("description") or "")
        if es_musica(titulo, desc):
            ev = _evento(_fecha_iso(e.get("start")), titulo, urljoin(page_url, e.get("url") or ""), municipio,
                         hora=_hora_iso(e.get("start")))
            if ev:
                out.append(ev)
    return out


def generico(html: str, url: str, today: date, municipio: str) -> list:
    s = soup_of(html)
    out = []
    for ev in jsonld_events(s):
        r = ld_to_raw(ev, today, url, split=False)
        if r and es_musica(r.artista, re.sub(r"<[^>]+>", "|", str(ev.get("description") or ""))):
            r.ciudad = r.ciudad or municipio
            out.append(r)
    if not out:
        out = microdatos(s, url, municipio)
    if not out:
        out = fullcalendar(s, url, municipio)
    if not out:  # último recurso: bloques "título + fecha" con referencia musical en el título
        for e in secuencia(html, url, today, ciudad=municipio):
            if es_musica(e.artista):
                e.nota = "Tomado de la agenda municipal: el título incluye referencia musical."
                out.append(e)
    return out


# ---------------------------------------------------------------- lectores propios
def leganes(html: str, url: str, today: date, municipio: str) -> list:
    """Liferay: cada acto deja en un <script> su fecha (diaIni/mesIni/anioIni) y su enlace."""
    out = []
    patron = re.compile(r'data-analytics-asset-title="([^"]+)"[^>]*>\s*<script>\s*var diaIni = (\d+);\s*'
                        r'var mesIni = (\d+);\s*var anioIni = (\d+);.*?link\s*:\s*\'([^\']+)\'', re.S)
    for m in patron.finditer(html):
        titulo, sala = m.group(1), ""
        partes = titulo.rsplit(" - ", 1)
        if len(partes) == 2 and re.search(r"(?i)teatro|auditorio|centro|sala|plaza|parque|recinto", partes[1]):
            titulo, sala = partes
        try:
            fecha = date(int(m.group(4)), int(m.group(3)), int(m.group(2)))
        except ValueError:
            continue
        if es_musica(titulo):
            ev = _evento(fecha, titulo, m.group(5), municipio, sala=sala)
            if ev:
                out.append(ev)
    return out


def alcorcon(html: str, url: str, today: date, municipio: str) -> list:
    from urllib.parse import urljoin
    s = soup_of(html)
    out = []
    for f in s.select(".event-ficha"):
        tit = text(f.select_one(".event-title"))
        ini = text(f.select_one(".start-date"))
        fin = text(f.select_one(".end-date"))
        fecha = parse_fecha_texto(ini, today)
        fecha_fin = parse_fecha_texto(fin, today)
        # la hora solo es fiable si el acto es de un día (en los de varios días es la de publicación)
        hora = parse_hora(ini.split("Hora:")[-1]) if fecha and fecha == fecha_fin else None
        lugar = f.select_one(".field--name-field-short-text .field--item")
        a = f.select_one("a[href]")
        cuerpo = text(f.select_one(".field--name-body"))
        if es_musica(tit, cuerpo):
            ev = _evento(fecha, tit, urljoin(url, a["href"]) if a else url, municipio, hora=hora, sala=text(lugar))
            if ev:
                out.append(ev)
    return out


def boadilla(html: str, url: str, today: date, municipio: str) -> list:
    from urllib.parse import urljoin
    s = soup_of(html)
    out = []
    for n in s.select(".node-evento"):
        fechas = text(n.select_one(".field-name-field-evento-fechas"))
        partes = [parse_fecha_texto(p, today) for p in re.split(r"\s+-\s+", re.sub(r",\s*(20\d\d)", r" \1", fechas))]
        if not partes or not partes[0]:
            continue
        if len(partes) > 1 and partes[1] and (partes[1] - partes[0]).days > 3:
            continue  # exposiciones y actos de varias semanas
        a = n.select_one("h2 a")
        cuerpo = text(n.select_one(".field-name-body"))
        if a and es_musica(text(a), cuerpo):
            ev = _evento(partes[0], text(a), urljoin(url, a["href"]), municipio, hora=parse_hora(cuerpo))
            if ev:
                out.append(ev)
    return out


def torrejon(html: str, url: str, today: date, municipio: str) -> list:
    from urllib.parse import urljoin
    s = soup_of(html)
    out = []
    for r in s.select(".views-row"):
        di, me = r.select_one("#di"), r.select_one("#me")
        a = r.select_one(".views-field-title a")
        if not (di and me and a):
            continue
        fecha = parse_fecha_texto(f"{text(di)} {text(me)}", today)
        cuerpo = text(r.select_one(".views-field-body"))
        if es_musica(text(a), cuerpo):
            ev = _evento(fecha, text(a), urljoin(url, a["href"]), municipio, hora=parse_hora(text(r.select_one("#ho"))),
                         sala="Teatro Municipal José María Rodero")
            if ev:
                out.append(ev)
    return out


def valdemoro(html: str, url: str, today: date, municipio: str) -> list:
    s = soup_of(html)
    out = []
    for b in s.select(".tmpl-noticia-listado"):
        a = b.select_one(".title a")
        resumen = text(b.select_one(".summary"))
        if not a or not resumen:
            continue
        # "16 de octubre, 20.00 horas. Musical. Edad recomendada…": la categoría es la 2.ª frase
        categoria = (resumen.split(". ") + [""])[1]
        if es_musica(f"{text(a)} · {categoria}"):
            ev = _evento(parse_fecha_texto(resumen, today), text(a), a["href"], municipio,
                         hora=parse_hora(resumen.split(". ")[0].replace(".", ":")), sala="Teatro Municipal Juan Prado")
            if ev:
                out.append(ev)
    return out


def pinto(html: str, url: str, today: date, municipio: str) -> list:
    """Calendario mensual de Liferay (calendarsuite): cada acto lleva '07 septiembre · 09:00'."""
    s = soup_of(html)
    out = []
    for li in s.select("li.calendar-booking"):
        a = li.select_one("a.title")
        f = li.select_one(".date-event-popover")
        if not (a and f):
            continue
        fh = text(f)
        if es_musica(text(a)):
            ev = _evento(parse_fecha_texto(fh, today), text(a), a.get("href") or url, municipio,
                         hora=parse_hora(fh.split("·")[-1]))
            if ev:
                out.append(ev)
    return out


LECTORES = {"generico": generico, "leganes": leganes, "alcorcon": alcorcon, "boadilla": boadilla,
            "torrejon": torrejon, "valdemoro": valdemoro, "pinto": pinto}


def municipal_parse(html: str, url: str, today, municipio: str, lector: str = "generico") -> list:
    vistos, out = set(), []
    for e in LECTORES[lector](html, url, today, municipio):
        k = (e.fecha, e.artista.casefold())
        if k not in vistos:
            vistos.add(k)
            out.append(e)
    return out


def hacer(municipio: str, url: str, lector: str = "generico"):
    def run(ctx: Ctx):
        yield from municipal_parse(ctx.get(url), url, ctx.today, municipio, lector)
    return run
