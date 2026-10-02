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
        if not estilos:  # lo que dice el título o, si no, el principio de la descripción
            for rx, est in ESTILO_TEXTO:
                if rx.search(titulo) or rx.search(descripcion[:300]):
                    estilos.append(est)
                    break
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
