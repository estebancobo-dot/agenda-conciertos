"""Webs especializadas en rock, metal, hard rock, AOR y progresivo."""
from __future__ import annotations

import json
import re
from datetime import date
from urllib.parse import urljoin

from ..normalize import MESES, clean, municipio, parse_fecha_texto, parse_hora
from .base import Ctx, jsonld_events, ld_to_raw, make, soup_of, text

_DATE_START = re.compile(
    r"^\s*(?:(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\s*,?\s*)?"
    r"(\d{1,2})(?:\s*(?:y|&|-)\s*\d{1,2})?\s*(?:de\s+)?([A-Za-zñÑ]+)\.?(?:\s+(?:de\s+)?(20\d\d))?"
    r"|^\s*(\d{1,2})/(\d{1,2})/(20\d\d|\d\d)", re.I)


def parse_linea(linea: str, today: date) -> tuple[date | None, str, str, list[str]]:
    """'Viernes 2 de octubre de 2026 - Madrid (Revi Live)' | '28/11/2026 – Madrid – La Cubierta' |
    '28 Noviembre - Leganés (Madrid) - La Cubierta' → (fecha, ciudad, sala, invitados de esa fecha)."""
    linea = clean(linea.replace("\xa0", " "))
    m = _DATE_START.match(linea)
    if not m:
        return None, "", "", []
    if m.group(4):
        y = int(m.group(6))
        try:
            f = date(y + 2000 if y < 100 else y, int(m.group(5)), int(m.group(4)))
        except ValueError:
            return None, "", "", []
    else:
        mes = MESES.get(m.group(2).lower())
        if not mes:
            return None, "", "", []
        f = parse_fecha_texto(f"{m.group(1)} {m.group(2)} {m.group(3) or ''}", today)
    resto = linea[m.end():].strip(" -–—,:|.")
    resto = re.sub(r"(?i)\s*\|?\s*(entradas\b|sold out|cancelad[oa]|aplazad[oa]).*$", "", resto)
    extra = []
    mx = re.search(r"\)\s*\+\s*(.+)$", resto)
    if mx:
        extra = [clean(x) for x in mx.group(1).split("+") if clean(x)]
        resto = resto[: mx.start() + 1]
    resto = re.sub(r"\s*\|[^()]*\)", ")", resto)  # '(sala X | Nueva sala)' → '(sala X)'
    ciudad, sala = "", ""
    parts = [clean(p) for p in re.split(r"\s+[-–—|]\s+|\s*[–—]\s*|\s+-$", resto) if clean(p)]
    if parts:
        first = parts[0]
        mp = re.match(r"(.*?)\s*\(([^)]*)\)\s*$", first)
        if mp:
            antes, dentro = clean(mp.group(1)), clean(mp.group(2))
            if municipio(dentro) and municipio(dentro) != "Madrid" and "," not in dentro and len(parts) == 1:
                ciudad, sala = dentro, antes  # 'Nazca (Madrid)' raro; se prefiere ciudad conocida
            if "," in dentro and municipio(dentro.split(",")[0]):
                ciudad, sala = dentro.split(",")[0], clean(dentro.split(",", 1)[1])  # Madrid (Leganés, La Cubierta)
            elif municipio(antes) and (dentro.lower() in ("madrid",) or not municipio(dentro)):
                ciudad = antes
                sala = dentro if not municipio(dentro) else (parts[1] if len(parts) > 1 else "")
            else:
                ciudad, sala = antes, dentro
        else:
            if "," in first and len(parts) == 1:
                ciudad, sala = [clean(x) for x in first.split(",", 1)]
            else:
                ciudad = first
                sala = parts[1] if len(parts) > 1 else ""
    sala = re.sub(r"(?i)^sala\s+(?=[a-z])", "Sala ", sala)
    sala = clean(re.sub(r"(?i)\s*\(con [^)]*\)", "", sala))
    if re.fullmatch(r"(?i)festival|por confirmar|tba|-|espa[ñn]a|spain", sala or "") or municipio(sala):
        sala = ""
    return f, ciudad, sala, extra


def split_lista(nombre: str) -> tuple[str, list[str]]:
    """'A + B', 'A, B y C' o 'A y B' (ambos en mayúsculas, como escriben los nombres de grupo estas webs)."""
    nombre = clean(nombre)
    if "+" in nombre:
        parts = [clean(p) for p in nombre.split("+") if clean(p)]
        return parts[0], parts[1:]
    m = re.match(r"^(.+?)((?:,\s*[^,]+)+)\s+y\s+(.+)$", nombre)
    if m:
        parts = [m.group(1)] + [clean(x) for x in m.group(2).split(",") if clean(x)] + [m.group(3)]
        return clean(parts[0]), [clean(p) for p in parts[1:]]
    m = re.match(r"^(.+?)\s+y\s+(.+)$", nombre)
    if m and m.group(1).upper() == m.group(1) and m.group(2).upper() == m.group(2):
        return clean(m.group(1)), [clean(m.group(2))]
    return nombre, []


def heading_blocks(soup, is_heading, lines_of) -> list[tuple[str, str, list[str]]]:
    """Recorre el documento: cada 'cabecera' (artista) va seguida de líneas con fecha y lugar."""
    out = []
    cur = None
    for el in soup.find_all(True):
        if is_heading(el):
            cur = (text(el), el, [])
            out.append(cur)
            continue
        if cur is None:
            continue
        for ln in lines_of(el):
            cur[2].append(ln)
    return [(h, el, ls) for h, el, ls in out]


def _events_from_blocks(blocks, url_of, today, nombre_de=lambda h: h, nota=None):
    evs = []
    for head, el, lines in blocks:
        nombre = nombre_de(head)
        if not nombre:
            continue
        for ln in lines:
            f, ciudad, sala, extra = parse_linea(ln, today)
            if f:
                art, inv = split_lista(nombre)
                evs.append(make(f, art, url_of(el), invitados=(inv + extra) or None, sala=sala, ciudad=ciudad,
                                nota=nota))
    return evs


# ------------------------------------------------------------------ Metal Legion
def metallegion_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    content = s.select_one(".entry-content") or s.body
    blocks = heading_blocks(content, lambda e: e.name == "h3",
                            lambda e: [text(e)] if e.name == "li" else [])
    return _events_from_blocks(blocks, lambda el: page_url, today)


def metallegion(ctx: Ctx):
    url = "https://metallegion.es/conciertos/"
    yield from metallegion_parse(ctx.get(url), url, ctx.today)


# ------------------------------------------------------------------ Hellpress
def _hellpress_nombre(h: str) -> str:
    m = re.match(r"(?i)(?:conciertos?|gira|fechas)\s+de\s+(.+)$", h)
    if not m:
        return ""
    n = m.group(1)
    n = re.split(r"(?i)\s+en\s+(?=(?:20\d\d|espa|madrid|barcelona|[A-ZÁÉÍÓÚ][a-záéíóú]+[,\s]))|\s+[“\"«]", n)[0]
    return clean(n)


def hellpress_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    content = s.select_one(".td-post-content") or s.select_one(".tdb_single_content") or s.body
    blocks = heading_blocks(content, lambda e: e.name == "h3",
                            lambda e: [text(e)] if e.name == "li" else [])
    evs = []
    for head, el, lines in blocks:
        nombre = _hellpress_nombre(head)
        if not nombre:
            continue
        artista, invitados = split_lista(nombre)
        mcon = re.match(r"(?i)(.+?)\s+con\s+(.+)$", nombre)
        if mcon:
            artista = mcon.group(1)
            invitados = [clean(x) for x in re.split(r"\s*,\s*|\s+y\s+", mcon.group(2)) if clean(x)]
        link = el.find_next("a", href=re.compile(r"hellpress\.com/(noticias|conciertos)/"))
        url = link["href"] if link else page_url
        for ln in lines:
            f, ciudad, sala, extra = parse_linea(ln, today)
            if f:
                evs.append(make(f, artista, url, invitados=(invitados + extra) or None, sala=sala, ciudad=ciudad))
    return evs


def hellpress(ctx: Ctx):
    url = "https://www.hellpress.com/agenda-conciertos/"
    yield from hellpress_parse(ctx.get(url), url, ctx.today)


def hellpress_melodico(ctx: Ctx):
    """Sección rock melódico: lista de noticias; se leen las entradas nuevas y se extraen fechas."""
    from .blogs import blog_incremental
    yield from blog_incremental(ctx, "https://www.hellpress.com/tag/rock-melodico/",
                                r"hellpress\.com/noticias/[^/]+/?$", max_pages=1)


# ------------------------------------------------------------------ MariskalRock (fiabilidad baja)
NOTA_BAJA = "Fuente de fiabilidad baja (mantiene fechas antiguas); año deducido: la fuente no indica año."


def mariskal_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    content = s.select_one(".elementor-widget-theme-post-content") or s.body

    def is_head(e):
        if e.name != "p":
            return False
        st = e.find("strong")
        return st is not None and text(st) == text(e) and not _DATE_START.match(text(e))

    blocks = heading_blocks(content, is_head,
                            lambda e: [text(e)] if e.name == "p" and not e.find("strong") else [])
    return _events_from_blocks(blocks, lambda el: page_url, today, nota=NOTA_BAJA)


def mariskal(ctx: Ctx):
    url = "https://mariskalrock.com/guia-de-conciertos/"
    yield from mariskal_parse(ctx.get(url), url, ctx.today)


# ------------------------------------------------------------------ Rockgle (fiabilidad baja)
def rockgle_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    content = s.select_one(".post-body") or s.body
    lines = [clean(x) for x in content.get_text("\n").split("\n") if clean(x)]
    evs, cur = [], None
    for ln in lines:
        f, ciudad, sala, _ = parse_linea(ln, today)
        if f and cur:
            evs.append(make(f, cur, page_url, sala=sala, ciudad=ciudad, nota=NOTA_BAJA))
        elif not f and len(ln) < 120 and ln.upper() == ln and re.search(r"[A-Z]", ln):
            cur = ln
    return evs


def rockgle(ctx: Ctx):
    url = "https://www.rockgle.es/p/agenda-de-conciertos_07.html?m=0"
    yield from rockgle_parse(ctx.get(url), url, ctx.today)


# ------------------------------------------------------------------ Madness Live (promotora)
def madness_parse(raw: str, page_url: str, today: date) -> list:
    try:
        html = json.loads(raw).get("rendered_products", "")
    except ValueError:
        html = raw
    s = soup_of(html)
    evs = []
    for art in s.select("article.product-miniature, article"):
        title = art.select_one(".product-title a, h2 a, h3 a, h5 a")
        if not title:
            continue
        nombre = re.sub(r"\s*\((?:Madrid|[^)]*)\)\s*$", "", text(title))
        desc = art.select_one(".product-description-short, .product-description") or art
        t = desc.get_text(" | ", strip=True)
        f = parse_fecha_texto(t, today)
        if not f:
            continue
        m = re.search(r"20\d\d\s*\|\s*([^|(]+?)\s*\|\s*\(\s*\|\s*([^|]*)\|", t)
        sala = clean(m.group(1)) if m else ""
        direccion = clean(m.group(2)) if m else ""
        ciudad = "Madrid"
        md = re.search(r",\s*([A-ZÁÉÍÓÚ][\wáéíóúñ\s-]+)$", direccion)
        if md and municipio(md.group(1)):
            ciudad = municipio(md.group(1))
        hora = None
        mh = re.search(r"(?i)(?:inicio|hora|comienzo)[^|]*?(\d{1,2}[:.]\d{2})", t)
        if mh:
            hora = parse_hora(mh.group(1))
        precio = None
        pr = art.select_one(".product-price")
        if pr:
            precio = text(pr)
        evs.append(make(f, nombre, title["href"], sala=sala, ciudad=ciudad, hora=hora, precio=precio,
                        nota=None))
    return evs


def madness(ctx: Ctx):
    base = "https://www.madnesslive.es/es/14-conciertos-en-madrid"
    for page in range(1, 10):
        url = base if page == 1 else f"{base}?page={page}"
        evs = madness_parse(ctx.get(url), url, ctx.today)
        if not evs:
            break
        yield from evs
        if len(evs) < 20:
            break


# ------------------------------------------------------------------ Get Rock (promotora)
def getrock_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    evs = []
    for a in s.select("a.ticket-container"):
        d = text(a.select_one(".date-day"))
        mth = text(a.select_one(".date-month"))
        y = text(a.select_one(".date-year"))
        f = parse_fecha_texto(f"{d} {mth} {y}", today)
        if not f:
            continue
        nombre = text(a.select_one(".event-title"))
        invitados = [clean(x.get_text(" ", strip=True).strip(" ·")) for x in a.select(".event-artists > span")]
        loc = [text(x) for x in a.select(".location-text")]
        ciudad = loc[0] if loc else None
        sala = loc[1] if len(loc) > 1 else ""
        hora = parse_hora(text(a.select_one(".date-time")))
        evs.append(make(f, nombre, urljoin("https://www.getrock.es/", a.get("href", "")), invitados=invitados,
                        sala=sala, ciudad=ciudad, hora=hora))
    return evs


def getrock(ctx: Ctx):
    seen = set()
    for url in ("https://www.getrock.es/conciertos", "https://www.getrock.es/"):
        try:
            html = ctx.get(url)
        except Exception as e:  # noqa: BLE001
            ctx.errors.append(f"{url}: {e}")
            continue
        for e in getrock_parse(html, url, ctx.today):
            k = (e.url, e.fecha)
            if k not in seen:
                seen.add(k)
                yield e


# ------------------------------------------------------------------ genérico JSON-LD (webs con eventos schema.org)
def jsonld_page(ctx: Ctx, url: str, **kw):
    for ev in jsonld_events(ctx.soup(url)):
        r = ld_to_raw(ev, ctx.today, url, **kw)
        if r:
            yield r
