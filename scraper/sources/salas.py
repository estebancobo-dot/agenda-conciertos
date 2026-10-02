"""Webs oficiales de salas y recintos (prioridad 1 en conflictos).

Cada sala tiene su parser verificado contra su HTML real (sep-2026). Las que publican la agenda
como una secuencia de textos 'TÍTULO | FECHA | HORA' usan `secuencia()` con su configuración."""
from __future__ import annotations

import html as htmlmod
import html as html_lib
import json
import re
from datetime import date, timedelta
from urllib.parse import urljoin

from ..normalize import MESES, clean, parse_fecha_texto, parse_hora
from .base import Ctx, jsonld_events, make, soup_of, text

DIAS = r"(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo|lun|mar|mi[eé]|jue|vie|s[aá]b|dom|monday|" \
       r"tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\.?"
_MES = r"(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre|" \
       r"ene|feb|mar|abr|may|jun|jul|ago|sept?|oct|nov|dic|january|february|march|april|june|july|august|" \
       r"september|october|november|december|jan|apr|aug|dec)\.?"
_FECHA_RX = [
    re.compile(rf"(?i)(?:{DIAS}\s*,?\s*)?\b(\d{{1,2}})\s*(?:de\s+)?({_MES})(?:\s*(?:de\s+|,\s*)?(20\d\d))?\b"),
    re.compile(rf"(?i)(?:{DIAS}\s*,?\s*)?\b({_MES})\s+(\d{{1,2}})(?:\s*,?\s*(20\d\d))?\b"),
    re.compile(r"\b(\d{1,2})[/.](\d{1,2})[/.](20\d\d|\d\d)\b"),
]
STOP = re.compile(r"(?i)^(comprar entradas?|entradas?|tickets?|m[aá]s info(rmaci[oó]n)?|ver (evento|m[aá]s)|reserva|"
                  r"reservar|agotad[oa]s?|sold out|info|precio regular|conciertos?|eventos?|pr[oó]ximos conciertos|"
                  r"comprar|leer m[aá]s|\+|·|→|entradas →|m[aá]s info →|compra tu entrada|vac[ií]o|"
                  rf"{DIAS}|\d{{1,2}}|{_MES}|20\d\d|hoy|mañana|puertas.*|apertura.*|\d+[.,]?\d*\s*€.*|€.*)$")


def find_fecha(seg: str, today: date):
    """Busca una fecha en el texto. Devuelve (fecha, inicio, fin) o None."""
    for i, rx in enumerate(_FECHA_RX):
        m = rx.search(seg)
        if not m:
            continue
        if i == 0:
            mes = MESES.get(m.group(2).lower().rstrip("."))
            d, y = int(m.group(1)), m.group(3)
        elif i == 1:
            mes = MESES.get(m.group(1).lower().rstrip("."))
            d, y = int(m.group(2)), m.group(3)
        else:
            mes, d, y = int(m.group(2)), int(m.group(1)), m.group(3)
            if y and len(y) == 2:
                y = "20" + y
        if not mes:
            continue
        f = parse_fecha_texto(f"{d}/{mes}/{y}" if y else f"{d} {list(MESES)[list(MESES.values()).index(mes)]}", today)
        if f:
            return f, m.start(), m.end()
    return None


def titulo_ok(s: str) -> bool:
    s = clean(s)
    return 2 <= len(s) <= 160 and re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]", s) and not STOP.match(s) \
        and not parse_hora(s) == s and not re.fullmatch(r"\d{1,2}[:.]\d{2}\s*h?\.?", s)


def secuencia(html: str, page_url: str, today: date, *, orden: str = "antes", scope: str | None = None,
              sala: str = "", ciudad: str = "Madrid", estilo_fijo: str | None = None, link_rx: str | None = None):
    """Empareja cada fecha con el título más cercano (antes o después) en la secuencia de textos de la página."""
    s = soup_of(html)
    for x in s(["script", "style", "noscript", "nav", "footer", "header"]):
        x.decompose()
    root = s.select_one(scope) if scope else s.body
    if root is None:
        return []
    segs = [clean(x) for x in root.get_text("\n", strip=True).split("\n")]
    segs = [x for x in segs if x]
    links = {}
    if link_rx:
        for a in root.find_all("a", href=True):
            if re.search(link_rx, a["href"]) and titulo_ok(text(a)):
                links.setdefault(text(a), urljoin(page_url, a["href"]))
    out, usados = [], set()
    i = 0
    while i < len(segs):
        seg = segs[i]
        found, k = find_fecha(seg, today), 1
        if not found and i + 2 < len(segs):
            joined = " ".join(segs[i:i + 3])
            f2 = find_fecha(joined, today)
            if f2 and f2[1] < len(seg) + 1 and f2[2] > len(seg):
                found, k = f2, 3 if f2[2] > len(seg) + len(segs[i + 1]) + 1 else 2
                seg = joined
        if not found:
            i += 1
            continue
        fecha, a, b = found
        titulo = None
        antes, despues = clean(seg[:a]).strip(" -–·|:"), clean(seg[b:]).strip(" -–·|:")
        if titulo_ok(antes) and not find_fecha(antes, today):
            titulo = antes
        if titulo is None:
            rng = range(i - 1, max(-1, i - 5), -1) if orden == "antes" else range(i + k, min(len(segs), i + k + 5))
            for j in rng:
                if j in usados:
                    break
                if find_fecha(segs[j], today):
                    break
                if titulo_ok(segs[j]):
                    titulo = segs[j]
                    usados.add(j)
                    break
        hora = parse_hora(despues) or next((parse_hora(x) for x in segs[i + k:i + k + 3] if parse_hora(x)), None)
        if titulo:
            titulo = re.sub(r"(?i)\s*\((sold out|agotad[oa]s?|segunda fecha|nueva fecha)\)|\s*-\s*agotad[oa]s?$", "", titulo)
            titulo = re.sub(r"(?i)\s+en madrid\b.*$", "", titulo)
            titulo = re.split(r"\s+[-–]\s+(?=(?:gira|tour|rock|20\d\d|presenta|\")|[^+]*$)", titulo)[0] \
                if re.search(r"\s[-–]\s", titulo) else titulo
            out.append(make(fecha, titulo, links.get(titulo, page_url), sala=sala, ciudad=ciudad, hora=hora,
                            estilo=estilo_fijo))
        i += k
    return out


# ------------------------------------------------------------------ Gruta 77 (EventON + JSON-LD por evento)
def gruta77_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out = []
    for ev in s.select(".eventon_list_event"):
        st = ev.select_one("meta[itemprop=startDate]")
        raw = str(ev)
        mname = re.search(r'"name":\s*"((?:[^"\\]|\\.)*)"', raw)
        if not st or not mname:
            continue
        m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})T(\d{1,2}):(\d{2})", st["content"])
        if not m:
            continue
        fecha = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        hora = f"{int(m.group(4)):02d}:{m.group(5)}"
        nombre = htmlmod.unescape(mname.group(1).encode().decode("unicode_escape", "ignore")
                                  if "\\u" in mname.group(1) else mname.group(1))
        nombre = htmlmod.unescape(nombre)
        cartel, _, subt = nombre.partition(";")
        sala = "Gruta 77"
        msala = re.search(r"(?i)\s+(?:en (?:la )?|[-–]\s*)(sala [^;+]+)$", cartel)
        if msala:
            sala, cartel = clean(msala.group(1)), cartel[: msala.start()]
        t = ev.get_text(" | ", strip=True)
        mst = re.search(r"Tipo de m[uú]sica:\s*\|\s*([^|]+)", t)
        estilo = clean(mst.group(1)).rstrip(",") if mst else None
        url_el = ev.select_one("a[itemprop=url]")
        pr = re.search(r"Precio de las entradas:\s*\|?\s*([^|]+)", t)
        e = make(fecha, cartel, url_el["href"] if url_el else page_url, sala=sala, ciudad="Madrid", hora=hora,
                 estilo=estilo, precio=clean(pr.group(1)) if pr else None,
                 nota=f"Título en la web de la sala: {clean(nombre)}" if subt else None)
        out.append(e)
    return out


# ------------------------------------------------------------------ Sala Villanos
def villanos_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out = []
    for a in s.find_all("a", class_="row"):
        h4 = a.find("h4")
        h3 = a.find("h3")
        if not h4 or not h3:
            continue
        found = find_fecha(text(h4), today)
        if not found:
            continue
        cont = h4.find_parent("div")
        hora = parse_hora(text(cont)) if cont else None
        tags = [text(x) for x in a.select(".tag") if text(x)]
        tags = [x for x in tags if x != text(h3) and x.lower() not in ("concierto", "club", "evento")]
        out.append(make(found[0], text(h3), urljoin(page_url, a.get("href", "")), sala="Sala Villanos",
                        ciudad="Madrid", hora=hora, estilo=", ".join(dict.fromkeys(tags)) or None))
    return out


# ------------------------------------------------------------------ Wurlitzer Ballroom
def wurlitzer_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out = []
    for art in s.select("article.flyer"):
        segs = [clean(x) for x in art.get_text("\n", strip=True).split("\n") if clean(x)]
        found = find_fecha(" ".join(segs[:3]), today)
        h3 = art.find("h3")
        if not found or not h3:
            continue
        titulo = text(h3)
        # etiquetas de estilo: textos cortos en minúsculas/mayúsculas tras el título y antes de 'Puertas'
        idx = segs.index(titulo) if titulo in segs else 3
        estilos = []
        for x in segs[idx + 1:]:
            if re.match(r"(?i)puertas|after dj|entradas|m[aá]s info", x):
                break
            if x != "+" and len(x) < 30 and not re.search(r"\d", x):
                estilos.append(x)
        # el título puede venir partido: 'HUBRIS | + | NUEVOS MUNDOS'
        cartel = [titulo]
        j = idx + 1
        while j + 1 < len(segs) and segs[j] == "+":
            cartel.append(segs[j + 1])
            if segs[j + 1] in estilos:
                estilos.remove(segs[j + 1])
            j += 2
        hora = next((parse_hora(x) for x in segs if x.lower().startswith("puertas")), None)
        link = art.find("a", href=re.compile(r"/agenda/|/eventos?/|/conciertos?/"))
        out.append(make(found[0], " + ".join(cartel), urljoin(page_url, link["href"]) if link else page_url,
                        sala="Wurlitzer Ballroom", ciudad="Madrid", hora=hora,
                        estilo=", ".join(estilos) or None))
    return out


# ------------------------------------------------------------------ RockVille
def rockville_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out = []
    mes_actual = None
    for el in s.find_all(["h2", "h3", "h4", "p", "li", "strong"]):
        t = text(el)
        mm = re.fullmatch(r"(?i)([a-záéíóú]+)\s+(20\d\d)", t)
        if mm and MESES.get(mm.group(1).lower()):
            mes_actual = (int(mm.group(2)), MESES[mm.group(1).lower()])
            continue
        if el.name != "li" or not mes_actual:
            continue
        m = re.match(r"\[[A-Z](\d{1,2})\]\s*(.+?)\s*\((.+)\)\s*$", t)
        if not m:
            continue
        try:
            fecha = date(mes_actual[0], mes_actual[1], int(m.group(1)))
        except ValueError:
            continue
        info = [clean(x) for x in m.group(3).split("/")]
        estilo = info[0] if info else None
        hora = parse_hora(m.group(3))
        precio = next((x for x in info if "€" in x or "ratuit" in x), None)
        a = el.find("a", href=True)
        out.append(make(fecha, m.group(2), a["href"] if a else page_url, sala="Rockville", ciudad="Madrid",
                        hora=hora, estilo=estilo, precio=precio))
    return out


# ------------------------------------------------------------------ Honky Tonk (día de la semana + número)
def honky_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out = []
    dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    for it in s.select("div.item"):
        segs = [clean(x) for x in it.get_text("\n", strip=True).split("\n") if clean(x)]
        if len(segs) < 3:
            continue
        from ..normalize import norm
        dname = norm(segs[0])
        if dname not in dias or not segs[1].isdigit():
            continue
        wd, dd = dias.index(dname), int(segs[1])
        # la página no indica el mes: se toma la fecha más cercana a hoy con ese día y día de la semana
        fecha = None
        for k in sorted(range(-60, 120), key=abs):
            c = today + timedelta(days=k)
            if c.day == dd and c.weekday() == wd:
                fecha = c
                break
        if not fecha:
            continue
        titulo = segs[2]
        a = it.find("a", href=True)
        out.append(make(fecha, re.sub(r"\s*\[[^\]]*\]\s*", " ", titulo), a["href"] if a else page_url,
                        sala="Honky Tonk", ciudad="Madrid", hora=parse_hora(" ".join(segs[3:4]))))
    return out


# ------------------------------------------------------------------ Sala El Sol (Events Manager)
def elsol_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out, seen = [], set()
    for it in s.select(".em-event.em-item"):
        more = it.select_one("a.em-item-read-more")
        url = more["href"] if more else None
        if not url or url in seen:
            continue
        seen.add(url)
        img = it.select_one(".em-item-image img[alt]")
        titulo = clean(img["alt"]) if img else ""
        dt = text(it.select_one(".em-event-date"))
        found = find_fecha(dt.split("–")[0], today)
        cats = [text(x) for x in it.select(".event-categories a")]
        if not found or not titulo or any(c.lower() == "clubbing" for c in cats):
            continue
        titulo = re.sub(r"\s*\[[^\]]*\]", "", titulo)
        out.append(make(found[0], titulo, url, sala="Sala El Sol", ciudad="Madrid",
                        hora=parse_hora(text(it.select_one(".em-event-time"))), estilo=None))
    return out


# ------------------------------------------------------------------ Silikona (The Events Calendar)
def silikona_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out = []
    for meta in s.select(".fusion-events-meta"):
        a = meta.select_one("h2 a")
        d = meta.select_one(".tribe-event-date-start")
        if not a or not d:
            continue
        found = find_fecha(text(d), today)
        if not found:
            continue
        titulo = re.sub(r"(?i)\s+en concierto$", "", text(a))
        titulo = re.split(r"\s+[–-]\s+", titulo)[0]
        out.append(make(found[0], titulo, a["href"], sala="Silikona", ciudad="Madrid", hora=parse_hora(text(d))))
    return out


# ------------------------------------------------------------------ Revi Live / Revi Space
def revi_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out = []
    for p in s.find_all("p"):
        t = p.get_text("\n", strip=True)
        if "Fecha:" not in t or "Evento:" not in t:
            continue
        campos = dict(re.findall(r"(Evento|Bandas|Fecha|Sala):\s*(.*)", t))
        f = find_fecha(campos.get("Fecha", ""), today)
        if not f:
            continue
        sala = "Revi Live"
        nxt = p.find_next("p")
        sala_txt = clean(campos.get("Sala", ""))
        if not sala_txt and nxt is not None and text(nxt).startswith("Sala:"):
            sala_txt = clean(text(nxt)[5:])
        if not sala_txt:
            # la sala aparece a veces en un bloque aparte tras el evento
            sib = p.find_next(string=re.compile(r"^\s*Sala:\s*$"))
            if sib is not None and sib.find_parent("p") is not None and sib.find_parent("p").find_previous("p") is p:
                sala_txt = clean(text(sib.find_parent("p"))[5:])
        if sala_txt and "space" in sala_txt.lower():
            sala = "Revi Space"
        bandas = campos.get("Bandas") or campos.get("Evento")
        a = p.find("a", href=True)
        out.append(make(f[0], bandas, a["href"] if a else page_url, sala=sala, ciudad="Madrid",
                        nota=f"Evento: {clean(campos.get('Evento', ''))}" if campos.get("Evento") else None))
    return out


# ------------------------------------------------------------------ Movistar Arena
def movistar_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out, seen = [], set()
    for ev in s.select(".hero__event, .event-card, [class*='event-card']"):
        segs = [clean(x) for x in ev.get_text("\n", strip=True).split("\n") if clean(x)]
        joined = " ".join(segs)
        m = re.search(rf"(?i)\b({_MES})\s+(\d{{1,2}})\b", joined)
        f = parse_fecha_texto(f"{m.group(2)} {m.group(1)}", today) if m else None
        h = ev.find(["h2", "h3"])
        if not f or not h:
            continue
        sala = "La Sala del Movistar Arena" if re.search(r"(?i)la sala movistar|la sala del movistar", joined) \
            else "Movistar Arena"
        k = (f, text(h))
        if k in seen:
            continue
        seen.add(k)
        a = ev.find("a", href=True) or (ev.find_parent("article").find("a", href=True) if ev.find_parent("article") else None)
        out.append(make(f, text(h), urljoin(page_url, a["href"]) if a else page_url, sala=sala, ciudad="Madrid",
                        hora=parse_hora(joined), estilo=None,
                        nota=None))
    return out


# ------------------------------------------------------------------ Siroco
def siroco_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out = []
    for ev in s.select(".eventos-agenda"):
        segs = [clean(x) for x in ev.get_text("\n", strip=True).split("\n") if clean(x)]
        if len(segs) < 5:
            continue
        f = find_fecha(segs[0], today)
        if not f:
            continue
        tipo = segs[1]
        if tipo.lower() == "clubbing":
            continue
        titulo = segs[4] if len(segs) > 4 else segs[-1]
        out.append(make(f[0], titulo, page_url, sala="Sala Siroco", ciudad="Madrid", hora=parse_hora(segs[3]),
                        estilo=None))
    return out


# ------------------------------------------------------------------ La Riviera
def riviera_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out = []
    for art in s.select("article.act-post"):
        h = art.select_one("h2.entry-title")
        segs = [clean(x) for x in art.get_text("\n", strip=True).split("\n") if clean(x)]
        f = next((find_fecha(x, today) for x in segs if re.search(r"\d{4}", x) and find_fecha(x, today)), None)
        if not h or not f:
            continue
        hora = None
        for x in segs:
            m = re.fullmatch(r"(?i)(\d{1,2}):(\d{2})\s*(am|pm)", x)
            if m:
                hh = int(m.group(1)) % 12 + (12 if m.group(3).lower() == "pm" else 0)
                hora = f"{hh:02d}:{m.group(2)}"
                break
        titulo = re.sub(r"(?i)\s*\((sold out|segunda fecha|nueva fecha|[^)]*fecha)\)", "", text(h))
        a = h.find("a", href=True)
        out.append(make(f[0], titulo, a["href"] if a else page_url, sala="La Riviera", ciudad="Madrid", hora=hora))
    return out


# ------------------------------------------------------------------ Fun House (tarjetas)
def funhouse_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out = []
    for c in s.select(".card-body"):
        h = c.find(["h1", "h2", "h3", "h5"])
        segs = [clean(x) for x in c.get_text("\n", strip=True).split("\n") if clean(x)]
        f = find_fecha(segs[0], today) if segs else None
        if not h or not f:
            continue
        a = h.find("a", href=True)
        out.append(make(f[0], text(h), urljoin(page_url, a["href"]) if a else page_url, sala="Fun House",
                        ciudad="Madrid", hora=parse_hora(segs[0])))
    return out


# ------------------------------------------------------------------ Moby Dick (bloques TÍTULO | FECHA HORA | PRECIO)
def mobydick_parse(html: str, page_url: str, today: date) -> list:
    out = secuencia(html, page_url, today, orden="antes", sala="Moby Dick Club")
    for e in out:
        e.artista = re.sub(r"\s*\.$", "", e.artista)
    return out


# ------------------------------------------------------------------ La Nueva Cubierta (Leganés)
def cubierta_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out, seen = [], set()
    for h in s.find_all(["h2", "h3", "h4"]):
        a = h.find("a", href=True)
        if not a or not re.search(r"lanuevacubierta\.com/", a["href"]):
            continue
        box = h.find_parent(["article", "div"])
        for _ in range(4):
            if box is not None and re.search(rf"(?i){_MES}\s+\d{{1,2}},\s*20\d\d", box.get_text(" ")):
                break
            box = box.parent if box is not None else None
        if box is None:
            continue
        m = re.search(rf"(?i)({_MES})\s+(\d{{1,2}}),\s*(20\d\d)", box.get_text(" "))
        f = parse_fecha_texto(f"{m.group(2)} {m.group(1)} {m.group(3)}", today) if m else None
        if not f or (a["href"], f) in seen:
            continue
        seen.add((a["href"], f))
        titulo = re.sub(r"(?i)\s+(madrid|leganes|leganés)?\s*20\d\d$", "", text(h))
        if not re.search(r"[A-Za-z]{3}", titulo):
            continue
        out.append(make(f, titulo, a["href"], sala="La Nueva Cubierta", ciudad="Leganés"))
    return out


# ------------------------------------------------------------------ salas con The Events Calendar (WordPress)
# Muchas salas publican su agenda con este plugin, que tiene una API pública de eventos: fecha y hora, título,
# enlace, precio, categorías e imagen, sin tener que entender el diseño de la página. Lo que la sala marca como
# fiesta o sesión de DJ ("Clubbing") no es un concierto. "Matasuegras – Tributo Pop-Rock": el artista y, aparte,
# lo que es (la etiqueta de estilo).
TRIBE_API = "wp-json/tribe/events/v1/events"
TRIBE_NO = re.compile(r"(?i)^(clubbing|club|fiesta|fiestas|dj|djs|sesi[oó]n(es)? dj|literatura|cine|teatro|humor|"
                      r"monólogos?|talleres?|exposici[oó]n(es)?)$")
_TRIBE_COLA = re.compile(r"\s+[–—-]\s+((?:tributo|versiones|homenaje|covers?)\b.*)$", re.I)


def _tribe_precio(e: dict) -> str | None:
    vals = []
    for v in (e.get("cost_details") or {}).get("values") or []:
        try:
            vals.append(float(str(v).replace(",", ".")))
        except ValueError:
            pass
    if not vals:
        vals = [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:[.,]\d+)?", str(e.get("cost") or ""))
                if float(x.replace(",", ".")) < 500]
    if not vals:
        return "Gratis" if re.search(r"(?i)libre|gratis|gratuit", str(e.get("cost") or "")) else None
    a, b = min(vals), max(vals)
    f = lambda x: f"{x:g}".replace(".", ",")  # noqa: E731
    return f"{f(a)} €" if a == b else f"{f(a)}-{f(b)} €"


def tribe_parse(datos: dict, sala: str, ciudad: str, hoy: date, horizonte: date, solo: str | None = None) -> list:
    """`solo`: categoría que deben tener (Café La Palma marca así los conciertos; el resto son fiestas, alquiler
    del local…)."""
    out = []
    for e in (datos or {}).get("events") or []:
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})(?: (\d{2}):(\d{2}))?", str(e.get("start_date") or ""))
        if not m:
            continue
        f = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if not (hoy <= f <= horizonte):
            continue
        cats = [clean(html_lib.unescape(c.get("name") or "")) for c in e.get("categories") or [] if c.get("name")]
        if cats and all(TRIBE_NO.match(c) for c in cats):
            continue
        if solo and not any(re.match(solo, c, re.I) for c in cats):
            continue
        titulo = clean(html_lib.unescape(re.sub(r"<[^>]+>", " ", str(e.get("title") or ""))))
        if not titulo:
            continue
        estilos = [c for c in cats if not TRIBE_NO.match(c) and not re.match(r"(?i)^conciertos?$", c)]
        mc = _TRIBE_COLA.search(titulo)
        if mc:
            titulo, estilos = titulo[: mc.start()], [mc.group(1)] + estilos
        hora = f"{m.group(4)}:{m.group(5)}" if m.group(4) and not e.get("all_day") else None
        img = (e.get("image") or {}).get("url") if isinstance(e.get("image"), dict) else None
        out.append(make(f, titulo, str(e.get("url") or ""), sala=sala, ciudad=ciudad, hora=hora,
                        precio=_tribe_precio(e), estilo=", ".join(dict.fromkeys(estilos)) or None, imagen=img))
    return out


def _tribe(base: str, sala: str, ciudad: str = "Madrid", solo: str | None = None):
    def run(ctx: Ctx):
        pagina = 1
        while pagina <= 10:
            url = (f"{base}{TRIBE_API}?per_page=50&page={pagina}&start_date={ctx.today.isoformat()}"
                   f"&end_date={ctx.horizon.isoformat()}")
            datos = json.loads(ctx.get(url))
            yield from tribe_parse(datos, sala, ciudad, ctx.today, ctx.horizon, solo)
            if pagina >= int(datos.get("total_pages") or 1):
                break
            pagina += 1
    return run


# ------------------------------------------------------------------ registro de salas
def _sec(url, sala, ciudad="Madrid", **kw):
    def run(ctx: Ctx):
        yield from secuencia(ctx.get(url), url, ctx.today, sala=sala, ciudad=ciudad, **kw)
    return run


def _one(url, fn):
    def run(ctx: Ctx):
        yield from fn(ctx.get(url), url, ctx.today)
    return run


PARSERS = {
    "gruta77": _one("https://gruta77.com/events/", gruta77_parse),
    "movistar": _one("https://www.movistararena.es/", movistar_parse),
    "riviera": _one("https://salariviera.com/conciertos/", riviera_parse),
    "nazca": _sec("https://www.salanazcaconciertos.com/conciertos", "Sala Nazca"),
    "wagon": _sec("https://www.wagon.live/", "Sala Wagon"),
    "revi": _one("https://revi.live/eventos/", revi_parse),
    "chango": _sec("https://www.salachango.es/", "Sala Changó", orden="antes"),
    "salabut": _sec("https://www.salabut.es/agenda-conciertos/", "Sala But"),
    "elsol": _one("https://salaelsol.com/agenda/", elsol_parse),
    "villanos": _one("https://salavillanos.es/agenda/", villanos_parse),
    "rockville": _one("https://rockville.es/programacion/", rockville_parse),
    "funhouse": _one("https://www.funhousemusicbar.com/conciertos/", funhouse_parse),
    "wurlitzer": _one("https://wurlitzerballroom.com/agenda", wurlitzer_parse),
    "honky": _one("https://clubhonky.com/programacion/", honky_parse),
    "silikona": _one("https://silikona.es/", silikona_parse),
    "clamores": _sec("https://www.salaclamores.es/", "Sala Clamores"),
    "siroco": _one("https://siroco.es/", siroco_parse),
    "mobydick": _one("https://www.mobydickclub.com/", mobydick_parse),
    "independance": _sec("https://independanceclub.com/collections/conciertos", "Independance Club"),
    "salab": _sec("https://www.salabmadrid.com/", "Sala B"),
    "nuevacubierta": _one("https://lanuevacubierta.com/eventos/", cubierta_parse),
    "cafelapalma": _tribe("https://cafelapalma.com/", "Café La Palma", solo=r"conciertos?$"),
    "cadillac": _tribe("https://cadillacsolitario.com/", "Cadillac Solitario"),
    "dimequemequieres": _tribe("https://conciertos.dimequemequieresbardecopas.com/", "Dime que me Quieres"),
}
