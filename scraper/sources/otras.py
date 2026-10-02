"""Resto de fuentes: Metalcry, TodoHeavyMetal, Metal Symphony, Neverland, Rock for Everyone, Rock-Progresivo,
Galileo Galilei, Big Mama, Mutick, Sociedad de Blues de Madrid, Qconciertos y agendas municipales."""
from __future__ import annotations

import html as htmlmod
import re
from datetime import date
from urllib.parse import urljoin

from ..normalize import MESES, MESES_ES, clean, municipio, parse_fecha_texto, parse_hora
from .base import Ctx, jsonld_events, ld_to_raw, make, soup_of, text
from .rock_metal import heading_blocks, parse_linea, split_lista
from .salas import find_fecha, secuencia


# ------------------------------------------------------------------ Metalcry (GigPress). Su hora es 20:00 por defecto: se ignora
def metalcry_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out = []
    for h3 in s.find_all("h3"):
        artista = text(h3)
        if not artista:
            continue
        tabla = h3.find_next_sibling("table", class_="gigpress-table")
        if tabla is None:
            continue
        for row in tabla.select("tr.gigpress-row"):
            d = text(row.select_one(".gigpress-date"))
            ciudad = text(row.select_one(".gigpress-city"))
            sala = text(row.select_one(".gigpress-venue"))
            m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2})", d)
            if not m:
                continue
            try:
                f = date(2000 + int(m.group(3)), int(m.group(2)), int(m.group(1)))
            except ValueError:
                continue
            info = row.find_next_sibling("tr")
            invitados = []
            url = page_url
            if info is not None and "gigpress-info" in (info.get("class") or []):
                for it in info.select(".gigpress-info-item"):
                    t = text(it)
                    if t.startswith("+"):
                        invitados = [clean(x) for x in t.split("+") if clean(x)]
                a = info.find("a", string=re.compile("Noticia relacionada"))
                if a:
                    url = a["href"]
            art, inv = split_lista(artista)
            out.append(make(f, art, url, invitados=(inv + invitados) or None, sala=sala, ciudad=ciudad,
                            hora=None, nota="Metalcry pone 20:00 por defecto: hora ignorada."))
    return out


def metalcry(ctx: Ctx):
    url = "https://metalcry.com/conciertos/"
    yield from metalcry_parse(ctx.get(url), url, ctx.today)


# ------------------------------------------------------------------ TodoHeavyMetal (AMP)
def thm_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    content = s.select_one(".amp-wp-article-content") or s.body

    def is_head(e):
        if e.name != "p":
            return False
        st = e.find("strong")
        return st is not None and text(st) == text(e)

    out = []
    for head, el, lines in heading_blocks(content, is_head, lambda e: [text(e)] if e.name == "li" else []):
        head = re.sub(r"\s*\+\s*", " + ", head)
        art, inv = split_lista(head)
        for ln in lines:
            m = re.match(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(20\d\d)\s+(.+)$", ln)
            if not m or not MESES.get(m.group(2).lower()):
                continue
            f = parse_fecha_texto(f"{m.group(1)} de {m.group(2)} de {m.group(3)}", today)
            resto = m.group(4)
            # 'Sala X, Ciudad (Provincia)': la ciudad va al final
            sala, _, ciudad = resto.rpartition(",")
            if not sala:
                sala, ciudad = "", resto
            ciudad = re.sub(r"\s*\([^)]*\)", "", ciudad)
            out.append(make(f, art, page_url, invitados=inv or None, sala=clean(sala), ciudad=clean(ciudad)))
    return out


def thm(ctx: Ctx):
    url = "https://www.todoheavymetal.com/index.php/agenda/amp"
    yield from thm_parse(ctx.get(url), url, ctx.today)


# ------------------------------------------------------------------ artículos de agenda (Metal Symphony, Rock for Everyone)
def articulo_agenda_parse(html: str, page_url: str, today: date) -> list:
    """Artículos con bloques 'Artista' + líneas de fecha/lugar, o tablas fecha|artista|ciudad|sala|hora."""
    s = soup_of(html)
    content = (s.select_one(".td-post-content") or s.select_one(".entry-content") or s.find("article") or s.body)
    out = []
    # tablas
    for tr in content.find_all("tr"):
        cells = [text(td) for td in tr.find_all(["td", "th"])]
        if len(cells) < 3:
            continue
        f = find_fecha(cells[0], today)
        if not f:
            continue
        resto = cells[1:]
        ciudad_idx = next((i for i, c in enumerate(resto) if municipio(c) or c.lower() in (
            "barcelona", "bilbao", "valencia", "sevilla", "zaragoza", "murcia", "málaga", "granada", "pamplona")), None)
        if ciudad_idx is None:
            continue
        artista = " + ".join(resto[:ciudad_idx]) if ciudad_idx > 0 else ""
        sala = resto[ciudad_idx + 1] if ciudad_idx + 1 < len(resto) else ""
        hora = next((parse_hora(c) for c in resto[ciudad_idx + 1:] if parse_hora(c)), None)
        if artista:
            out.append(make(f[0], artista, page_url, sala=sala, ciudad=resto[ciudad_idx], hora=hora))
    if out:
        return out

    # bloques cabecera + líneas
    def is_head(e):
        if e.name in ("h2", "h3", "h4"):
            return True
        if e.name == "p":
            st = e.find(["strong", "b"])
            return st is not None and text(st) == text(e) and not find_fecha(text(e), today)
        return False

    def lines_of(e):
        if e.name in ("li",):
            return [text(e)]
        if e.name == "p" and not is_head(e):
            return [clean(x) for x in e.get_text("\n").split("\n") if clean(x)]
        return []

    for head, el, lines in heading_blocks(content, is_head, lines_of):
        head = re.sub(r"(?i)^(conciertos? de|gira de)\s+", "", head)
        art, inv = split_lista(head)
        for ln in lines:
            f, ciudad, sala, extra = parse_linea(ln, today)
            if not f:
                # 'Madrid: 17 de octubre – Sala Nazca' / 'Madrid, 17/10 – Sala X'
                m = re.match(r"([A-ZÁÉÍÓÚ][\wáéíóúñ -]+?)\s*[:,–-]\s*(.+)$", ln)
                if m and municipio(m.group(1)):
                    f2 = find_fecha(m.group(2), today)
                    if f2:
                        f, ciudad = f2[0], m.group(1)
                        sala = clean(m.group(2)[f2[2]:].strip(" -–,:()"))
            if f:
                out.append(make(f, art, page_url, invitados=(inv + extra) or None, sala=sala, ciudad=ciudad))
    return out


def metalsymphony(ctx: Ctx):
    """El artículo de agenda de temporada más reciente."""
    s = ctx.soup("https://www.metalsymphony.com/agenda/")
    art = None
    for a in s.find_all("a", href=True):
        if re.search(r"metalsymphony\.com/conciertos-de-rock-y-metal-en-espana-[a-z0-9-]+/?$", a["href"]):
            art = a["href"]
            break
    if not art:
        ctx.errors.append("no se encontró el artículo de agenda de temporada")
        return
    yield from articulo_agenda_parse(ctx.get(art), art, ctx.today)


def neverland(ctx: Ctx):
    url = "https://www.metalsymphony.com/neverland-concerts-agenda-rock-progresivo-2026-2027/"
    yield from articulo_agenda_parse(ctx.get(url), url, ctx.today)


def rfe_parse(html: str, page_url: str, today: date) -> list:
    """Líneas '17 de octubre. La Pestilencia (gira despedida). Sala Gruta 77 a las 21:30. Precio: 40 euros.'"""
    s = soup_of(html)
    content = s.select_one(".entry-content") or s.find("article") or s.body
    out = []
    for li in content.find_all("li"):
        t = text(li)
        m = re.match(r"(\d{1,2})(?:\s*y\s*(\d{1,2}))?\s+de\s+([a-záéíóú]+)\.\s*(.+)$", t)
        if not m or not MESES.get(m.group(3).lower()):
            continue
        resto = re.sub(r"\.\s+ala\s+", ". Sala ", m.group(4))  # errata frecuente: 'ala Wagon'
        precio = None
        mp = re.search(r"\.?\s*Precio[^:]*:\s*(.+)$", resto)
        if mp:
            precio, resto = clean(mp.group(1)).rstrip("."), resto[: mp.start()]
        partes = [clean(x) for x in re.split(r"\.\s+(?=[A-ZÁÉÍÓÚ])", resto) if clean(x)]
        if not partes:
            continue
        artistas = re.sub(r"\s*\((?:gira|tour)[^)]*\)", "", partes[0])
        lugar = partes[1] if len(partes) > 1 else ""
        mh = re.search(r"\s+a las\s+(\d{1,2}[:.]\d{2})", lugar)
        hora = parse_hora(mh.group(1)) if mh else None
        sala = clean(lugar[: mh.start()] if mh else lugar)
        if re.search(r"(?i)precio|abono", sala):
            sala = ""
        for dd in filter(None, [m.group(1), m.group(2)]):
            f = parse_fecha_texto(f"{dd} de {m.group(3)}", today)
            if f:
                out.append(make(f, artistas, page_url, sala=sala, ciudad="Madrid", hora=hora, precio=precio))
    return out


def rockforeveryone(ctx: Ctx):
    """Artículo mensual 'agenda de conciertos heavy en Madrid en <mes> de <año>'."""
    for y, m in _meses(ctx):
        url = f"https://rockforeveryone.es/agenda-de-conciertos-heavy-en-madrid-en-{MESES_ES[m - 1]}-de-{y}/"
        try:
            html = ctx.get(url)
        except Exception as e:  # noqa: BLE001
            if "404" in str(e):
                continue
            raise
        yield from rfe_parse(html, url, ctx.today)


def _meses(ctx: Ctx):
    from .base import months_in_window
    return months_in_window(ctx.today, ctx.horizon)


_MES_EN = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def rockprog_cal_parse(html: str, page_url: str, today: date, y: int, m: int) -> list:
    """Calendario mensual: celdas td.day-with-date con 'Título (Ciudad)'. Sin ciudad no se puede ubicar y se omite."""
    s = soup_of(html)
    out = []
    for td in s.select("td.day-with-date"):
        dia = td.find("span")
        if not dia or not text(dia).isdigit():
            continue
        for a in td.select(".calnk a"):
            t = text(a.select_one(".event-title")) or text(a)
            mc = re.match(r"(.+?)\s*\(([^)]+)\)\s*$", t)
            if not mc:
                continue
            try:
                f = date(y, m, int(text(dia)))
            except ValueError:
                continue
            nombre = mc.group(1).replace("/", " / ")
            out.append(make(f, nombre, a.get("href") or page_url, ciudad=mc.group(2),
                            nota="Del calendario de Rock-Progresivo.com (no indica sala)."))
    return out


def rockprog_agenda(ctx: Ctx):
    base = "https://www.rock-progresivo.com/agenda-de-conciertos-de-rock-progresivo/"
    for y, m in _meses(ctx):
        url = f"{base}?calendar_month={_MES_EN[m - 1]}&calendar_yr={y}"
        yield from rockprog_cal_parse(ctx.get(url), url, ctx.today, y, m)


# ------------------------------------------------------------------ Galileo Galilei (Modern Events Calendar)
def galileo_parse(html: str, page_url: str, today: date) -> list:
    out = []
    for m in re.finditer(r'data-sort-masonry="(\d{4})-(\d{2})-(\d{2})"(.*?)(?=data-sort-masonry=|$)', html, re.S):
        bloque = m.group(4)
        t = re.search(r'mec-event-title"><a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', bloque, re.S)
        alt = re.search(r'wp-post-image" alt="([^"]*)"', bloque)
        if not t and not alt:
            continue
        titulo = htmlmod.unescape(re.sub(r"<[^>]+>", "", t.group(2) if t else alt.group(1)))
        hora = re.search(r'mec-event-detail">\s*(\d{1,2}:\d{2})', bloque)
        info = re.search(r'href="(https://salagalileo\.es/programacion/[^"]+)"', bloque)
        f = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        out.append(make(f, clean(titulo), info.group(1) if info else page_url, sala="Galileo Galilei",
                        ciudad="Madrid", hora=hora.group(1) if hora else None))
    return out


def galileo(ctx: Ctx):
    url = "https://salagalileo.es/"
    yield from galileo_parse(ctx.get(url), url, ctx.today)


# ------------------------------------------------------------------ Big Mama Ballroom (página de blues)
def bigmama(ctx: Ctx):
    url = "https://bigmamaballroom.com/conciertos-blues/"
    yield from secuencia(ctx.get(url), url, ctx.today, orden="despues", sala="Big Mama Ballroom",
                         estilo_fijo="Blues (página de conciertos de blues de la sala)")


# ------------------------------------------------------------------ Mutick / The Flying Pig (MomentaZos)
def mutick_evento_parse(html: str, url: str, today: date) -> list:
    out = []
    for ev in jsonld_events(soup_of(html)):
        ev = dict(ev)
        nombre = clean(ev.get("name"))
        nombre = re.sub(r"(?i)^(entradas\s+)?(momentazos:\s*)", "", nombre)
        nombre = re.sub(r"(?i)\s+en\s+(madrid|leganés|leganes|alcal[aá].*|[A-Z][a-z]+)\s*(20\d\d)?$", "", nombre)
        ev["name"] = nombre
        ev["performer"] = None
        r = ld_to_raw(ev, today, url)
        if r:
            desc = ev.get("description") or ""
            mh = re.search(r"(\d{1,2}[:.]\d{2})h?\.?\s*concierto", desc)
            if mh:
                r.hora = parse_hora(mh.group(1))
            out.append(r)
    return out


def mutick(ctx: Ctx):
    base = "https://mutick.com"
    urls = []
    for page in ("https://mutick.com", "https://mutick.com/o/the-flying-pig"):
        try:
            s = ctx.soup(page)
        except Exception as e:  # noqa: BLE001
            ctx.errors.append(f"{page}: {e}")
            continue
        for a in s.find_all("a", href=True):
            h = urljoin(base, a["href"])
            if re.search(r"mutick\.com/e/[^/]*(madrid|momentazos|leganes|alcala|getafe|mostoles|rivas)", h) and h not in urls:
                urls.append(h)
    for h in urls[:60]:
        try:
            yield from mutick_evento_parse(ctx.get(h), h, ctx.today)
        except Exception as e:  # noqa: BLE001
            ctx.errors.append(f"{h}: {e}")


# ------------------------------------------------------------------ Sociedad de Blues de Madrid
def sbm_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out = []
    for art in s.find_all(["article", "div"], class_=re.compile(r"\bpost\b|type-post")):
        h = art.find(["h1", "h2", "h3"])
        if not h:
            continue
        t = art.get_text(" ", strip=True)
        pub = re.search(r"on\s+(\d{1,2}/\d{1,2}/20\d\d)", t)
        ref = parse_fecha_texto(pub.group(1), today) if pub else today
        m = re.search(r"(?i)(?:el\s+)?(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)?\s*(\d{1,2}) de "
                      r"([a-záéíóú]+)(?: de (20\d\d))?", t)
        if not m or not MESES.get(m.group(2).lower()):
            continue
        f = parse_fecha_texto(f"{m.group(1)} de {m.group(2)} {m.group(3) or ''}", ref or today)
        artista = re.search(r"(?i)actuaci[oó]n de:?\s*(.+?)(?:\s+[A-ZÁÉÍÓÚ]\w+ [A-ZÁÉÍÓÚ]\w+ \(|\s+Desde|\s+Entradas|$)", t)
        lugar = re.search(r"(?i)\ben (el|la) ((?:Centro|Sala|Bar|Caf[eé]|Club|Teatro)[^,.]{2,60}?)(?: con | a las |,|\.)", t)
        if not artista:
            continue
        a = h.find("a", href=True)
        out.append(make(f, clean(artista.group(1)), a["href"] if a else page_url,
                        sala=clean(lugar.group(2)) if lugar else "", ciudad="Madrid",
                        hora=parse_hora(re.search(r"(?i)desde las ([\d:.-]+\s*h)", t).group(1))
                        if re.search(r"(?i)desde las ([\d:.-]+\s*h)", t) else None,
                        estilo="Blues (ciclo de la Sociedad de Blues de Madrid)", nota=f"Anuncio: {text(h)}"))
    return out


def sbm(ctx: Ctx):
    url = "https://www.sociedaddebluesdemadrid.com/"
    yield from sbm_parse(ctx.get(url), url, ctx.today)


# ------------------------------------------------------------------ Qconciertos (country y provincia de Madrid)
def qconciertos_parse(html: str, page_url: str, today: date, estilo: str | None) -> list:
    s = soup_of(html)
    for x in s(["script", "style", "nav", "footer"]):
        x.decompose()
    segs = [clean(x) for x in s.body.get_text("\n", strip=True).split("\n") if clean(x)]
    links = {text(a): urljoin(page_url, a["href"]) for a in s.find_all("a", href=True) if text(a)}
    out = []
    for i, sg in enumerate(segs[:-2]):
        m = re.fullmatch(r"(\d{2})/(\d{2})/(20\d\d)", sg)
        if not m:
            continue
        titulo, lugar = segs[i + 1], segs[i + 2]
        mt = re.match(r"(.+?) en (.+?) \(([^)]+)\)", titulo)
        if not mt:
            continue
        sala, _, loc = lugar.partition(" · ")
        ciudad = loc.split(",")[0] if loc else mt.group(3)
        f = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        out.append(make(f, mt.group(1), links.get(titulo, page_url), sala=clean(sala) or mt.group(2), ciudad=ciudad,
                        estilo=estilo))
    return out


def qconciertos(ctx: Ctx):
    for url, estilo in (("https://qconciertos.es/estilo/country/", "Country"),
                        ("https://qconciertos.es/estilo/folk/", "Folk"),
                        ("https://qconciertos.es/conciertos-en-madrid-provincia/", None)):
        yield from qconciertos_parse(ctx.get(url), url, ctx.today, estilo)
