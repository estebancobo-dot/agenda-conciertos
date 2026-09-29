"""Blogs de giras con lectura incremental: solo se leen las entradas nuevas desde la última ejecución.

De cada entrada nueva se extraen las fechas en Madrid y municipios de la Comunidad. Los conciertos
encontrados se guardan en data/estado.json para no perderlos en los días siguientes (las entradas
antiguas no se vuelven a leer)."""
from __future__ import annotations

import re
from datetime import date

from ..model import RawEvent
from ..normalize import MESES, clean, municipio, parse_fecha_texto
from .base import Ctx, make, soup_of, text
from .rock_metal import parse_linea, split_lista

_VERBOS = (r"\s+(?:llega|llegan|presenta|presentan|anuncia|anuncian|confirma|confirman|vuelve|vuelven|regresa|"
           r"regresan|girar[aá]n?|visitar[aá]n?|traen?|actuar[aá]n?|estar[aá]n?|celebra|celebran|ofrecer[aá]n?|"
           r"desembarca|desembarcan|de gira|en gira|gira|tour|en madrid|en espa[ñn]a|pasar[aá]n?|recalar[aá]n?|"
           r"har[aá]n?|tocar[aá]n?|publica|publican|lanza|lanzan|y su|con su|con )\b")


def artista_de_titular(titulo: str) -> str:
    """Nombre del grupo tomado del titular de la entrada (lo que precede al verbo o a los dos puntos)."""
    t = clean(titulo)
    m = re.match(r"^((?:[A-Z0-9ÁÉÍÓÚÜÑ'&.\-]+\s*){1,6})(?=\s+[a-záéíóúñ«“\"]|$)", t)
    if m and len(clean(m.group(1))) >= 2 and clean(m.group(1)).upper() == clean(m.group(1)):
        return clean(m.group(1))
    t = re.split(r"\s*[:|–—]\s+|\s+-\s+", t)[0]
    t = re.split(_VERBOS, t, flags=re.I)[0]
    return clean(t.strip(" «»“”\"'"))


_PROSA = re.compile(
    r"(\d{1,2})\s+de\s+([a-záéíóú]+)(?:\s+de\s+(20\d\d))?[^.;\n]{0,25}?\ben\s+(?:la\s+|el\s+)?(?:sala\s+)?"
    r"([A-ZÁÉÍÓÚÑ0-9][^,(.;\n]{1,40}?)\s*\(([^)]{3,40})\)", re.I)
_PROSA2 = re.compile(
    r"(\d{1,2})\s+de\s+([a-záéíóú]+)(?:\s+de\s+(20\d\d))?[^.;\n]{0,30}?\b(Madrid|[A-ZÁÉÍÓÚ][a-záéíóúñ]+(?:[- ]"
    r"[A-Za-záéíóúñ]+){0,4})\s*[\(,–-]\s*(?:sala\s+)?([^)\n.;,]{2,40})\)?", re.I)


def extrae_fechas_madrid(cuerpo: str, ref: date, today: date) -> list[tuple[date, str, str]]:
    """Devuelve (fecha, municipio, sala) solo para fechas en la Comunidad de Madrid."""
    out = []
    lines = [clean(x) for x in cuerpo.split("\n") if clean(x)]
    for ln in lines:
        f, ciudad, sala, _ = parse_linea(ln.replace("|", " - "), ref)
        if f and municipio(ciudad):
            out.append((f, municipio(ciudad), sala))
            continue
        for rx in (_PROSA, _PROSA2):
            for m in rx.finditer(ln):
                mes = MESES.get(m.group(2).lower())
                if not mes:
                    continue
                a, b = clean(m.group(4)), clean(m.group(5))
                if municipio(b) and not municipio(a):
                    muni, sala = municipio(b), a
                elif municipio(a):
                    muni, sala = municipio(a), b
                else:
                    continue
                f = parse_fecha_texto(f"{m.group(1)} de {m.group(2)} {m.group(3) or ''}", ref)
                if f:
                    out.append((f, muni, re.sub(r"(?i)^sala\s+", "Sala ", sala)))
    seen, res = set(), []
    for x in out:
        if x[0] not in seen:
            seen.add(x[0])
            res.append(x)
    return res


def parse_articulo(html: str, url: str, today: date) -> list[RawEvent]:
    s = soup_of(html)
    h1 = s.find("h1", class_=re.compile("title|entry")) or s.find("h1")
    titulo = text(h1) if h1 else ""
    pub = s.find("meta", property="article:published_time")
    ref = today
    if pub and pub.get("content"):
        ref = parse_fecha_texto(pub["content"][:10], today) or today
    body = (s.select_one(".entry-content") or s.select_one(".td-post-content") or s.select_one(".post-content")
            or s.find("article") or s.body)
    for x in body.select("script, style, .sharedaddy, .jp-relatedposts, .comments-area"):
        x.decompose()
    cuerpo = body.get_text("\n", strip=True)
    nombre = artista_de_titular(titulo)
    if not nombre:
        return []
    art, inv = split_lista(nombre)
    evs = []
    for f, muni, sala in extrae_fechas_madrid(cuerpo, ref, today):
        evs.append(make(f, art, url, invitados=inv or None, sala=sala, ciudad=muni,
                        nota="Artista tomado del titular de la entrada del blog."))
    return evs


def blog_incremental(ctx: Ctx, list_url: str, art_pattern: str, max_pages: int = 3, page_fmt: str = "{base}page/{n}/"):
    """Lee el listado del blog, procesa solo entradas no vistas y reemite los conciertos guardados."""
    st = ctx.estado
    vistos = st.setdefault("vistos", [])
    guardados = st.setdefault("eventos", [])
    nuevos_urls = []
    for n in range(1, max_pages + 1):
        url = list_url if n == 1 else page_fmt.format(base=list_url, n=n)
        s = ctx.soup(url)
        links = []
        for a in s.find_all("a", href=True):
            h = a["href"].split("#")[0].split("?")[0]
            if re.search(art_pattern, h) and h not in links:
                links.append(h)
        nuevos = [h for h in links if h not in vistos and h not in nuevos_urls]
        nuevos_urls.extend(nuevos)
        if not vistos or len(nuevos) < len(links):  # primera ejecución: solo 1 página; después hasta lo ya visto
            break
    for h in nuevos_urls:
        try:
            for e in parse_articulo(ctx.get(h), h, ctx.today):
                d = e.to_dict()
                guardados.append(d)
        except Exception as ex:  # noqa: BLE001
            ctx.errors.append(f"{h}: {type(ex).__name__}: {ex}")
        vistos.append(h)
    st["vistos"] = vistos[-600:]
    st["ultima_entrada"] = nuevos_urls[0] if nuevos_urls else st.get("ultima_entrada")
    # conserva solo los futuros
    hoy = ctx.today.isoformat()
    st["eventos"] = [d for d in guardados if d["fecha"] >= hoy]
    for d in st["eventos"]:
        yield RawEvent(**{**d, "fecha": date.fromisoformat(d["fecha"])})


def dirtyrock(ctx: Ctx):
    yield from blog_incremental(ctx, "https://www.dirtyrock.info/category/giras/",
                                r"dirtyrock\.info/20\d\d/\d\d/[^/]+/?$")


def viriaor(ctx: Ctx):
    yield from blog_incremental(ctx, "https://viriaor.wordpress.com/category/agenda-de-conciertos/",
                                r"viriaor\.wordpress\.com/20\d\d/\d\d/\d\d/[^/]+/?$")


def diariorockero(ctx: Ctx):
    yield from blog_incremental(ctx, "https://www.diariodeunrockero.es/category/conciertos/",
                                r"diariodeunrockero\.es/conciertos/[a-z0-9-]{10,}/?$")  # anuncios: /conciertos/<entrada>/


def rockprog(ctx: Ctx):
    yield from blog_incremental(ctx, "https://www.rock-progresivo.com/seccion/cronicas-conciertos/previas-de-conciertos/",
                                r"rock-progresivo\.com/[a-z0-9-]{12,}/20\d\d/\d\d/?$")  # entradas: /<entrada>/AAAA/MM/


def force(ctx: Ctx):
    yield from blog_incremental(ctx, "https://forcemagazine.es/agenda-force/",
                                r"forcemagazine\.es/(?!agenda|calendario|tienda|revista|mi-cuenta|carrito|category)"
                                r"[a-z0-9-]{15,}/?$", max_pages=2)
