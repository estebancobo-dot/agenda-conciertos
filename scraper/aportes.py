"""Datos aportados por lotes (fase D): lo que un chat con buscador encuentra de los artistas y conciertos con huecos,
comprobado aquí contra la página que cita antes de aceptarlo.

Nada se acepta porque lo diga el chat. Cada dato llega con la dirección de una página y la frase exacta que lo dice;
se abre esa página con el mismo lector que las agendas (robots.txt, identificación, ritmo) y solo vale si:

- la página se puede leer y nombra al artista (y, para un concierto, también la fecha);
- la frase citada está en la página (se admiten pequeñas diferencias de espacios o comillas);
- la frase dice de verdad lo que se aporta: el país (un gentilicio o el nombre del país o de una ciudad conocida),
  los estilos (las palabras de estilo están en la frase) o la hora y el precio (están en la página o en sus datos
  de evento del día).

Lo aceptado se guarda en data/aportes.json (rama `aportes`) con la página y la frase, y se aplica en cada lectura solo
donde falte el dato: nunca pisa lo que dicen las webs de música ni las agendas. Lo rechazado se guarda con el motivo."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date
from html import unescape

from .normalize import MESES, canon_sala, norm

VERSION = 1
# webs de música: un estilo que sale de ellas es "conocido"; de cualquier otra página citada, "estimado"
WEBS_MUSICA = ("bandcamp.com", "discogs.com", "musicbrainz.org", "wikipedia.org", "wikidata.org", "last.fm",
               "rateyourmusic.com")
# páginas que piden sesión o no dejan leerse: no se pueden comprobar
NO_COMPROBABLES = ("instagram.com", "facebook.com", "tiktok.com", "twitter.com", "x.com", "threads.net",
                   "linktr.ee", "youtube.com", "youtu.be", "open.spotify.com")

_PAISES = {
    "ES": "espana spain", "AR": "argentina", "MX": "mexico", "CL": "chile", "CO": "colombia", "UY": "uruguay",
    "PE": "peru", "VE": "venezuela", "CU": "cuba", "BR": "brasil brazil", "PT": "portugal", "US": "estados unidos "
    "eeuu ee uu usa united states", "CA": "canada", "GB": "reino unido inglaterra escocia gales united kingdom uk "
    "england scotland wales", "IE": "irlanda ireland", "FR": "francia france", "IT": "italia italy",
    "DE": "alemania germany", "SE": "suecia sweden", "NO": "noruega norway", "FI": "finlandia finland",
    "DK": "dinamarca denmark", "NL": "paises bajos holanda netherlands holland", "BE": "belgica belgium",
    "CH": "suiza switzerland", "AT": "austria", "GR": "grecia greece", "PL": "polonia poland", "RU": "rusia russia",
    "UA": "ucrania ukraine", "JP": "japon japan", "AU": "australia", "IS": "islandia iceland", "IL": "israel",
    "TR": "turquia turkey", "SN": "senegal", "ML": "mali", "MA": "marruecos morocco", "ZA": "sudafrica south africa",
    "NZ": "nueva zelanda new zealand", "CZ": "republica checa chequia czech republic czechia",
    "HU": "hungria hungary", "EC": "ecuador", "BO": "bolivia", "PY": "paraguay", "DO": "republica dominicana "
    "dominican republic", "PR": "puerto rico", "GT": "guatemala", "CR": "costa rica", "PA": "panama",
    "SV": "el salvador", "HN": "honduras", "NI": "nicaragua", "KR": "corea del sur south korea", "CN": "china",
    "IN": "india", "EE": "estonia", "LV": "letonia latvia", "LT": "lituania lithuania", "RO": "rumania romania",
    "BG": "bulgaria", "RS": "serbia", "HR": "croacia croatia", "SI": "eslovenia slovenia", "SK": "eslovaquia slovakia",
    "LU": "luxemburgo luxembourg", "CV": "cabo verde cape verde", "NG": "nigeria", "GH": "ghana", "DZ": "argelia "
    "algeria", "TN": "tunez tunisia", "EG": "egipto egypt", "IR": "iran", "LB": "libano lebanon",
}
_CIUDADES = {
    "ES": "madrid barcelona valencia sevilla bilbao zaragoza malaga granada vigo coruna gijon oviedo murcia alicante "
          "valladolid pamplona santander salamanca cordoba cadiz almeria leon burgos logrono toledo san sebastian "
          "donostia vitoria castellon tarragona girona lleida palma ibiza tenerife las palmas alcala de henares "
          "getafe mostoles fuenlabrada leganes alcorcon",
    "AR": "buenos aires rosario mendoza la plata", "MX": "ciudad de mexico guadalajara monterrey "
    "tijuana", "CL": "santiago de chile valparaiso", "CO": "bogota medellin cali barranquilla", "PE": "lima",
    "UY": "montevideo", "VE": "caracas", "CU": "la habana havana", "US": "nueva york new york los angeles chicago "
    "nashville austin seattle san francisco boston detroit memphis new orleans portland atlanta brooklyn",
    "GB": "londres london manchester liverpool glasgow edimburgo edinburgh bristol birmingham sheffield leeds",
    "FR": "paris lyon marsella marseille burdeos bordeaux", "DE": "berlin hamburgo hamburg munich colonia cologne",
    "IT": "roma rome milan milano napoles naples turin torino bolonia bologna", "SE": "estocolmo stockholm gotemburgo "
    "gothenburg", "NO": "oslo bergen", "DK": "copenhague copenhagen", "NL": "amsterdam rotterdam", "IE": "dublin",
    "PT": "lisboa lisbon oporto porto", "AU": "sidney sydney melbourne", "CA": "toronto montreal vancouver",
    "JP": "tokio tokyo osaka", "BE": "bruselas brussels amberes antwerp", "FI": "helsinki", "IS": "reikiavik reykjavik",
}


# gentilicios en francés, italiano, portugués y alemán (páginas de Wikipedia o de prensa de esos países)
_GENT_OTROS = {
    "FR": "francais francaise francaises franzosisch franzosische francese", "ES": "espagnol espagnole espanhol "
    "espanhola spanisch spanische spagnolo spagnola", "IT": "italien italienne italienisch italienische italiano "
    "italiana", "DE": "allemand allemande deutsch deutsche deutscher tedesco tedesca alemao alema", "PT": "portugais "
    "portugaise portugues portuguesa portoghese", "GB": "britannique anglais anglaise britisch britische britannico "
    "inglese britanico", "US": "americain americaine amerikanisch amerikanische statunitense",
    "AR": "argentin argentine argentinisch argentino argentina", "MX": "mexicain mexicaine mexikanisch messicano",
    "BE": "belge belgisch belga", "CH": "suisse schweizer svizzero suico", "NL": "neerlandais niederlandisch "
    "olandese holandes", "SE": "suedois suedoise schwedisch svedese sueco", "NO": "norvegien norvegienne norwegisch "
    "norvegese noruegues", "DK": "danois danoise danisch danese dinamarques", "FI": "finlandais finnisch finlandese",
    "IE": "irlandais irlandaise irisch irlandese", "CA": "canadien canadienne kanadisch canadese canadense",
    "BR": "bresilien bresilienne brasilianisch brasiliano brasileiro brasileira", "CL": "chilien chilienne chilenisch",
    "CO": "colombien colombienne kolumbianisch", "CU": "cubain cubaine kubanisch", "JP": "japonais japonaise "
    "japanisch giapponese japones", "GR": "grec grecque griechisch greco", "PL": "polonais polonaise polnisch polacco",
}


def _gentilicios() -> dict[str, str]:
    from .origen import _GENT_EN, _GENT_ES
    out = {norm(k): v for k, v in _GENT_EN.items() if v}
    out.update({norm(k): v for k, v in _GENT_ES.items() if v})
    for iso, palabras in _GENT_OTROS.items():
        out.update({w: iso for w in palabras.split() if w not in out})
    return out


def paises_en_cita(cita: str) -> set[str]:
    """Países que una frase menciona: gentilicio, nombre del país o una ciudad conocida."""
    t = f" {norm(cita)} "
    out = {v for k, v in _gentilicios().items() if f" {k} " in t}
    for iso, lista in list(_PAISES.items()) + list(_CIUDADES.items()):
        if any(f" {n} " in t for n in _NOMBRES_COMPLETOS[lista]):
            out.add(iso)
    return out


def _nombres_completos() -> dict[str, set[str]]:
    # cada lista se escribe con los nombres separados por espacios; los de varias palabras se reconocen aquí
    multi = ("estados unidos", "ee uu", "united states", "reino unido", "united kingdom", "paises bajos",
             "south africa", "nueva zelanda", "new zealand", "republica checa", "czech republic", "republica dominicana",
             "dominican republic", "puerto rico", "costa rica", "el salvador", "corea del sur", "south korea",
             "cabo verde", "cape verde", "alcala de henares", "san sebastian", "las palmas", "buenos aires",
             "la plata", "ciudad de mexico", "santiago de chile", "la habana", "nueva york", "new york", "los angeles",
             "san francisco", "new orleans")
    out = {}
    for lista in list(_PAISES.values()) + list(_CIUDADES.values()):
        nombres = set()
        resto = f" {lista} "
        for m in multi:
            if f" {m} " in resto:
                nombres.add(m)
                resto = resto.replace(f" {m} ", " ")
        nombres.update(w for w in resto.split() if len(w) >= 4 or w in ("uk", "usa", "eeuu", "peru", "mali", "cuba"))
        out[lista] = nombres
    return out


_NOMBRES_COMPLETOS = _nombres_completos()


# ------------------------------------------------------------------ comprobaciones sobre la página
def plano(t: str) -> str:
    """Minúsculas y sin tildes, pero con los signos (€, :, /): para fechas, horas y precios."""
    import unicodedata
    t = "".join(c for c in unicodedata.normalize("NFKD", unescape(t or "")) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t.lower()).strip()


def texto_de(html: str) -> str:
    """El texto de la página (sin scripts ni estilos) más el título y la descripción, con signos."""
    from bs4 import BeautifulSoup
    s = BeautifulSoup(html, "html.parser")
    extra = []
    for m in s.find_all("meta", attrs={"content": True}):
        if (m.get("property") or m.get("name") or "").lower() in ("og:title", "og:description", "description",
                                                                   "twitter:description"):
            extra.append(m["content"])
    # los datos de evento de la página (JSON-LD) también son texto de la página: nombre, descripción, lugar
    import json as _json
    for sc in s.select('script[type="application/ld+json"]'):
        try:
            datos = _json.loads(sc.string or sc.get_text() or "")
        except ValueError:
            continue
        pila = [datos]
        while pila:
            x = pila.pop()
            if isinstance(x, list):
                pila.extend(x)
            elif isinstance(x, dict):
                extra += [str(x[k]) for k in ("name", "description", "headline", "startDate") if isinstance(x.get(k), str)]
                pila.extend(v for v in x.values() if isinstance(v, (dict, list)))
    for x in s(["script", "style", "noscript", "svg"]):
        x.decompose()
    return plano(" ".join(extra + [s.get_text(" ")]))


def contiene(texto: str, frase: str, minimo: int = 90) -> bool:
    """La frase (normalizada) está en el texto, con margen para espacios, comillas o una palabra cortada."""
    f = norm(frase)
    if not f:
        return False
    if f in texto:
        return True
    from rapidfuzz import fuzz
    return len(f) >= 20 and fuzz.partial_ratio(f, texto) >= minimo


def nombra(texto: str, nombre: str) -> bool:
    n = norm(nombre)
    return bool(n) and re.search(rf"(?<![a-z0-9]){re.escape(n)}(?![a-z0-9])", texto) is not None


def fecha_en(texto: str, fecha: str, html: str = "") -> bool:
    """La fecha del concierto aparece en la página: 18/10/2026, 18-10, 18 de octubre, 18 oct, October 18, 2026-10-18."""
    y, m, d = (int(x) for x in fecha.split("-"))
    if fecha in html or fecha in texto:
        return True
    nombres = [k for k, v in MESES.items() if v == m]
    pats = [rf"\b0?{d}\s*[/.-]\s*0?{m}(?:\s*[/.-]\s*(?:{y}|{y % 100}))?\b"]
    for n in nombres:
        pats.append(rf"\b0?{d}(?:\s+de)?\s+{n}\b")
        pats.append(rf"\b{n}\s+0?{d}\b")
    return any(re.search(p, texto) for p in pats)


def cerca_de(texto: str, nombres: list[str], radio: int = 600) -> str:
    """Los trozos del texto (con signos) alrededor de cada vez que sale el artista: la fecha, la hora y el precio de
    su concierto tienen que estar ahí, no en otro concierto de la misma página."""
    trozos = []
    for n in nombres:
        palabras = re.findall(r"[a-z0-9]+", plano(n))
        if not palabras:
            continue
        for m in re.finditer(r"(?<![a-z0-9])" + r"[^a-z0-9]+".join(map(re.escape, palabras)) + r"(?![a-z0-9])", texto):
            trozos.append(texto[max(0, m.start() - radio):m.end() + radio])
    return " … ".join(trozos)


def fecha_del_evento(html: str, fecha: str) -> bool | None:
    """Con datos de evento (JSON-LD): True si alguno es de esa fecha, False si los hay y ninguno lo es; None si no hay."""
    from bs4 import BeautifulSoup
    from .entradas import _eventos_jsonld
    evs = _eventos_jsonld(BeautifulSoup(html, "html.parser"))
    fechas = {str(e.get("startDate") or "")[:10] for e in evs if e.get("startDate")}
    if not fechas:
        return None
    return fecha in fechas


def hora_en(texto: str, hora: str) -> bool:
    h, mi = (int(x) for x in hora.split(":"))
    pats = [rf"(?<!\d)0?{h}\s*[:.h]\s*{mi:02d}(?!\d)"]
    if mi == 0:
        pats += [rf"\b0?{h}\s*h(?:oras|rs)?\b", rf"\b{h % 12 or 12}\s*(?:pm|p m)\b" if h >= 12 else rf"\b{h}\s*am\b"]
    return any(re.search(p, texto) for p in pats)


def precio_en(texto: str, precio: str) -> bool:
    """Las cifras del precio aportado ("12 €", "desde 15,50 €", "entrada libre") están en la página junto a €."""
    p = norm(precio)
    if re.search(r"\b(gratis|gratuit[oa]|entrada libre|libre hasta completar aforo|free)\b", p):
        return re.search(r"\b(gratis|gratuit[oa]|entrada libre|acceso libre|libre hasta completar aforo|free entry)\b",
                         texto) is not None
    for num in re.findall(r"\d+(?:[.,]\d{1,2})?", precio):
        ent, _, dec = num.replace(",", ".").partition(".")
        variantes = [ent] if not dec or int(dec) == 0 else []
        variantes += [f"{ent}[.,]{dec.ljust(2, '0')}"] if dec else [f"{ent}[.,]00"]
        if any(re.search(rf"(?:€|eur|euros?)\s*{v}\b|\b{v}\s*(?:€|eur\b|euros?\b)", texto) for v in variantes):
            return True
    return False


def dominio(url: str | None) -> str:
    from .entradas import dominio as _d
    return _d(url)


def _no_comprobable(url: str) -> str | None:
    d = dominio(url)
    if not url or not url.startswith("http"):
        return "sin dirección de página"
    if any(d == x or d.endswith("." + x) for x in NO_COMPROBABLES):
        return f"{d} no se puede leer sin sesión: hace falta otra página (web oficial, Bandcamp, prensa, sala…)"
    return None


class Lector:
    """Abre cada página una vez (con robots.txt) y recuerda el texto o el motivo por el que no se pudo."""

    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.paginas: dict[str, tuple[str, str, str] | str] = {}

    def leer(self, url: str) -> tuple[str, str, str] | str:
        if url in self.paginas:
            return self.paginas[url]
        motivo = _no_comprobable(url)
        if motivo:
            self.paginas[url] = motivo
            return motivo
        from .fetch import RobotsBlocked
        try:
            html = self.fetcher.get(url)
            p = texto_de(html)
            r = (html, p, norm(p))
        except RobotsBlocked:
            r = "su robots.txt no deja leerla, así que no se puede comprobar"
        except Exception as e:  # noqa: BLE001
            r = f"no se pudo abrir ({type(e).__name__})"
        self.paginas[url] = r
        return r


# ------------------------------------------------------------------ artistas
# el ciclo delante no es parte del artista: "Inverfest. Marwan" y "Marwan" son la misma clave
_PREFIJO_CICLO = re.compile(r"^inverfest(?: \d{4})? (?=\S)")


def clave_artista(nombre: str) -> str:
    return _PREFIJO_CICLO.sub("", norm(nombre))


def normalizar_claves(apo: dict) -> dict:
    """Rehace las claves guardadas con clave_artista (las antiguas podían llevar el ciclo delante). Si dos claves
    quedan iguales se conserva la que ya estaba limpia."""
    for campo in ("artistas", "ocultos", "mostrar"):
        d = apo.get(campo)
        if isinstance(d, dict):
            nuevo: dict = {}
            for k, v in d.items():
                nk = clave_artista(k)
                if nk not in nuevo or nk == k:
                    nuevo[nk] = v
            apo[campo] = nuevo
    d = apo.get("consultados")
    if isinstance(d, dict):
        nuevo = {}
        for k, v in d.items():
            nk = "a:" + clave_artista(k[2:]) if k.startswith("a:") else k
            if nk not in nuevo or nk == k:
                nuevo[nk] = v
        apo["consultados"] = nuevo
    return apo


def verificar_artista(item: dict, pedido: dict, lector: Lector) -> dict:
    """item: lo que devuelve el chat; pedido: lo que se le preguntó (nombre y contexto). Devuelve
    {"nombre", "aceptado": {...}, "rechazado": [motivos]}."""
    from .clasificar import categorias_de
    from .origen import pais_en_texto
    nombre = pedido["nombre"]
    out: dict = {"nombre": nombre, "aceptado": {}, "rechazado": []}
    ident = str(item.get("identidad") or "").lower()
    if ident.startswith(("dudos", "varios", "no es")):
        # sin identidad segura no se acepta nada: podría ser otro artista con el mismo nombre
        if ident.startswith(("dudos", "varios")):
            out["rechazado"].append("el chat no pudo identificar al artista con seguridad")
        return out
    # el nombre real del artista ("Fabio Lione") si el pedido es el título del concierto ("FABIO LIONE’S DAWN OF
    # VICTORY"): solo si está dentro de ese título, para no cambiar de artista
    real = str(item.get("nombre_real") or "").strip()
    from rapidfuzz import fuzz
    parecido_real = bool(real) and len(norm(real)) >= 3 and (
        norm(real) in norm(nombre) or fuzz.ratio(norm(real), norm(nombre)) >= 85        # "FAHMI ALQHI" → "Fahmi Alqhai"
        or fuzz.partial_ratio(norm(real), norm(nombre)) >= 90 and len(norm(real)) >= 8)
    nombres = [nombre] + ([real] if parecido_real else [])

    def comprobar(url: str, cita: str, dice) -> tuple[str | None, str]:
        """(frase aceptada, motivo del rechazo). Vale la frase citada si está en la página y dice el dato; si no,
        lo que la propia página dice junto al nombre del artista (a 150 letras como mucho)."""
        r = lector.leer(url) if url else "sin página"
        if isinstance(r, str):
            return None, r
        if not any(nombra(r[2], n) for n in nombres):
            return None, f"la página citada no nombra a {nombres[-1]}"
        if cita and contiene(r[2], cita) and dice(cita):
            return cita[:300], ""
        for trozo in cerca_de(r[1], nombres, 150).split(" … "):
            if trozo and dice(trozo):
                return trozo.strip()[:300], ""
        return None, ("la frase citada no está en la página y la página no lo dice junto al nombre" if cita and
                      not contiene(r[2], cita) else "ni la frase citada ni la página lo dicen junto al nombre")

    # país
    pais = str(item.get("pais") or "").strip().upper()[:2]
    if pais and pais.isalpha():
        url = str(item.get("pais_url") or "")
        frase, motivo = comprobar(url, str(item.get("pais_cita") or ""),
                                  lambda t: pais_en_texto(t, nombres[-1])[0] == pais or pais in paises_en_cita(t))
        if not frase:
            out["rechazado"].append(f"país {pais}: {motivo}")
        else:
            ac = {"valor": pais, "url": url, "cita": frase}
            if item.get("ciudad"):
                ac["ciudad"] = str(item["ciudad"])[:60]
            out["aceptado"]["pais"] = ac
    # estilos
    estilos = [str(e).strip().lower() for e in item.get("estilos") or [] if str(e).strip()][:6]
    if estilos:
        url = str(item.get("estilos_url") or "")
        usables = lambda t: [e for e in estilos if norm(e) and norm(e) in norm(t) and categorias_de(e)]  # noqa: E731
        frase, motivo = comprobar(url, str(item.get("estilos_cita") or ""), lambda t: bool(usables(t)))
        if not frase or not usables(frase):  # la zona citada tiene que decir alguno de esos estilos
            out["rechazado"].append(f"estilos: {motivo or 'la frase no dice ninguno de esos estilos'}")
        else:
            d = dominio(url)
            out["aceptado"]["estilos"] = {"valores": usables(frase), "url": url, "cita": frase,
                                          "web_musica": any(d == w or d.endswith("." + w) for w in WEBS_MUSICA)}
    # enlaces del artista (web oficial, Bandcamp, Discogs…): se guardan los que se pueden leer y lo nombran
    enl = []
    for u in [str(x) for x in item.get("enlaces") or []][:5]:
        r = lector.leer(u)
        if not isinstance(r, str) and any(nombra(r[2], n) for n in nombres):
            enl.append(u)
    if enl:
        out["aceptado"]["enlaces"] = enl
    return out


# ------------------------------------------------------------------ conciertos
def id_concierto(r: dict) -> str:
    base = f"{r['fecha']}|{norm(r.get('artista') or '')}|{norm(canon_sala(r.get('sala') or ''))}"
    return hashlib.sha1(base.encode()).hexdigest()[:8]


def verificar_concierto(item: dict, rec: dict, lector: Lector, web_sala: str | None = None) -> dict:
    """item: lo que devuelve el chat de un concierto; rec: el concierto. Acepta la página si nombra al artista y la
    fecha; de ella, la hora y el precio si están en la página (o en sus datos de evento de ese día), el enlace de
    compra si es una ticketera, la confirmación si es la web de la sala y la cancelación si la página la dice."""
    from .entradas import leer_pagina, ticketera
    from .nombres import claves_ficha
    out: dict = {"aceptado": {}, "rechazado": []}
    url = str(item.get("url") or "")
    r = lector.leer(url) if url else "sin página"
    if isinstance(r, str):
        out["rechazado"].append(r)
        return out
    html, texto, tnorm = r
    nombres = [n for n in dict.fromkeys([rec.get("artista") or "", *claves_ficha(rec)]) if n]
    if not any(nombra(tnorm, n) for n in nombres):
        out["rechazado"].append("la página citada no nombra al artista")
        return out
    zona = cerca_de(texto, nombres)
    ev = fecha_del_evento(html, rec["fecha"])
    if ev is False or (ev is None and not fecha_en(zona, rec["fecha"])):
        out["rechazado"].append(f"la página citada no anuncia al artista el {rec['fecha']}")
        return out
    ld = leer_pagina(html, url, rec["fecha"])
    base = {"url": url}
    hora = str(item.get("hora") or "").strip()
    if re.fullmatch(r"\d{1,2}:\d{2}", hora):
        hora = hora.zfill(5)
        if ld.get("hora") == hora or (not ld.get("hora") and hora_en(zona, hora)):
            out["aceptado"]["hora"] = {"valor": hora, **base}
        else:
            out["rechazado"].append(f"hora {hora}: no está en la página")
    precio = str(item.get("precio") or "").strip()
    if precio:
        if precio_en(zona, precio) or (ld.get("precio") and precio_en(plano(ld["precio"]), precio)):
            out["aceptado"]["precio"] = {"valor": precio[:40], **base}
        else:
            out["rechazado"].append(f"precio {precio}: no está en la página")
    if ticketera(url):
        out["aceptado"]["entradas"] = {"url": url, "nombre": ticketera(url)}
    if web_sala and dominio(url) == dominio(web_sala):
        out["aceptado"]["sala_oficial"] = {"url": url}
    estado = norm(str(item.get("estado") or ""))
    if estado.startswith(("cancel", "aplaz", "suspend")):
        tipo = "aplazado" if estado.startswith("aplaz") else "cancelado"
        if re.search(r"\b(cancelad[oa]s?|suspendid[oa]s?|aplazad[oa]s?|cancelled|canceled|postponed)\b", tnorm):
            out["aceptado"]["estado"] = {"valor": tipo, **base}
        else:
            out["rechazado"].append(f"{tipo}: la página no lo dice")
    if not out["aceptado"] and not out["rechazado"]:
        out["rechazado"].append("la página confirma el concierto pero no aporta nada que falte")
        out["aceptado"]["pagina"] = base
    return out


# ------------------------------------------------------------------ aplicar a los conciertos
def _fuente(url: str) -> str:
    return f"página citada y comprobada ({dominio(url)})"


# Lo que por el título no es un concierto (partidos, sesiones de DJ, exposiciones, foros, karaoke, humor, cine,
# presentaciones de libros…). Se oculta con su motivo en la lista revisable (ocultos.json); un falso positivo se
# vuelve a mostrar con tools/lotes.py mostrar, que lo apunta en aportes["mostrar"]. Un título que dice "concierto"
# nunca se oculta por estas reglas.
_NO_CONCIERTO = [
    (re.compile(r"\bvs\.?(\s+kids)?\s*$|\b(partido|euroliga|euroleague|liga endesa|nba|harlem globetrotters)\b"),
     "partido o evento deportivo"),
    # "Real Madrid vs. Partizan Mozzart Bet Belgrade", "Movistar Estudiantes vs. Inveready Askatuak Gipuzkoa": un "vs."
    # con un equipo o una competición ("Queen vs. ABBA. Candlelight" o "The Beatles VS The Rolling Stones" no)
    (re.compile(r"\bvs\.?\s.*\b(real madrid|estudiantes|basket|baloncesto|futbol|fc|cf|cd|bc|euroliga|euroleague|acb|"
                r"partizan|olympiacos|panathinaikos|fenerbahce|maccabi|zalgiris|baskonia|unicaja|gipuzkoa|belgrade|"
                r"mozzart|atletico|getafe|rayo vallecano|leganes)\b|\b(real madrid|estudiantes|basket|baloncesto|fc|cf|"
                r"atletico|getafe|rayo vallecano|leganes)\b.*\bvs\.?\s"), "partido o evento deportivo"),
    (re.compile(r"^dj\s+\S|\S\s+djs?$"), "sesión de DJ"),
    (re.compile(r"\b(fast expo|exposicion)\b"), "exposición"),
    (re.compile(r"\b(foro|congreso|conferencia|charla|coloquio)\b"), "foro, charla o conferencia"),
    (re.compile(r"\b(karaoke|podcast|bingo|quiz)\b"), "karaoke, podcast o juego"),
    (re.compile(r"\b(comedy|monologos?|stand.?up)\b"), "humor"),
    (re.compile(r"\bpresentacion (del? )?(libro|la novela|novela)\b"), "presentación de un libro"),
    (re.compile(r"^presentacion\b"), "presentación (no concierto)"),
    (re.compile(r"\b(cortometrajes?|proyeccion|pelicula)\b"), "cine"),
    (re.compile(r"\b(feria del disco|mercadillo)\b"), "feria o mercadillo"),
    # "AFROJAM HALLOWEEN PARTY", "Halloween Party con Gastón & Tony Karate" (DJ), "Halloween Takeover 2026"; una
    # "fiesta de Halloween con X" no, que suele decir qué grupo toca
    (re.compile(r"\b(halloween|jalog\w*)\b.*\b(party|takeover)\b|\b(party|takeover)\b.*\b(halloween|jalog\w*)\b|"
                r"^(?!.*\scon\s).*(\b(halloween|jalog\w*)\b.*\bfiesta\b|\bfiesta\b.*\b(halloween|jalog\w*)\b)"),
     "fiesta de Halloween"),
]


def no_es_concierto(titulo: str) -> str | None:
    t = unicodedata.normalize("NFKD", titulo.lower()).encode("ascii", "ignore").decode()
    t = re.sub(r"\s+", " ", t).strip()
    if not t or re.search(r"\bconciertos?\b|\ben directo\b|\blive\b", t):
        return None
    for patron, motivo in _NO_CONCIERTO:
        if patron.search(t):
            return motivo
    return None


def aplicar_artista(r: dict, aportes: dict) -> None:
    """País y estilos aportados, solo donde no hay dato de una web de música ni de la agenda. Y la marca de oculto
    para lo que no es un concierto (lista revisable "ocultos": la web no lo enseña, los datos lo conservan)."""
    from .clasificar import categorias_de
    from .nombres import claves_ficha
    r.pop("oculto", None)
    ocultos = (aportes or {}).get("ocultos") or {}
    o = next((ocultos[k] for k in (clave_artista(n) for n in [r.get("artista") or "", *claves_ficha(r)]) if k in ocultos),
             None)
    if o and o.get("salas"):
        from .normalize import misma_sala
        if not any(misma_sala(canon_sala(r.get("sala") or ""), canon_sala(x)) for x in o["salas"]):
            o = None  # oculto solo en las salas donde se vio que no era un concierto
    if o:
        r["oculto"] = {"motivo": o.get("motivo") or "no es un concierto", "nombre": o.get("nombre")}
    elif clave_artista(r.get("artista") or "") not in ((aportes or {}).get("mostrar") or {}):
        motivo = no_es_concierto(r.get("artista") or "")
        if motivo:
            r["oculto"] = {"motivo": motivo, "nombre": r.get("artista"), "regla": True}
    arts = (aportes or {}).get("artistas") or {}
    if not arts:
        return
    a = next((arts[k] for k in (clave_artista(n) for n in claves_ficha(r) or [r.get("artista") or ""]) if k in arts),
             None)
    if not a:
        return
    p = a.get("pais")
    if p and not r.get("nacionalidad") and not r.get("origen_no_aplica"):
        r["nacionalidad"], r["nacionalidad_fuente"] = p["valor"], _fuente(p["url"])
        r["nacionalidad_cita"] = {"url": p["url"], "cita": p["cita"]}
        r.pop("nacionalidad_estimada", None)
        r.pop("nacionalidad_estimada_motivo", None)
    e = a.get("estilos")
    actuales = [g for g in r.get("grupos") or [] if g != "sin clasificar"]
    debil = not actuales or r.get("grupos_generico")
    if e and debil and str(r.get("grupos_origen") or "") not in ("Discogs", "MusicBrainz", "Wikipedia", "Wikidata",
                                                                   "Last.fm", "cartel del festival"):
        grupos = list(dict.fromkeys(g for v in e["valores"] for g in categorias_de(v)))
        if grupos:
            r["grupos"], r["categoria"] = grupos, grupos[0]
            r["grupos_generico"] = False
            r["grupos_origen"] = "página citada"
            r["grupos_segun"] = [dominio(e["url"])]
            r["estilos_cita"] = {"url": e["url"], "cita": e["cita"], "web_musica": e.get("web_musica", False)}
            if not r.get("estilos_discogs"):
                r["estilos_discogs"] = e["valores"][:5]


def aplicar_conciertos(recs: list[dict], aportes: dict) -> int:
    """Hora, precio, enlace de compra, confirmación de la sala y cancelación aportados, en los conciertos que
    coinciden (fecha, artista y sala) y solo donde falte el dato. Se llama después de leer las páginas."""
    from .correcciones import coincide
    n = 0
    for c in (aportes or {}).get("conciertos") or []:
        for r in recs:
            if r["fecha"] != c["fecha"] or not coincide({"fecha": c["fecha"], "artistas": c.get("artistas") or [],
                                                         "salas": c.get("salas") or []}, r):
                continue
            hecho = False
            hora_conflicto = any(x.get("campo") == "hora" for x in r.get("conflictos") or [])
            if c.get("hora") and not r.get("hora") and not hora_conflicto:
                r["hora"] = c["hora"]["valor"]
                r["hora_pagina"] = {"hora": c["hora"]["valor"], "nombre": _fuente(c["hora"]["url"]),
                                    "url": c["hora"]["url"]}
                hecho = True
            if c.get("precio") and not r.get("precio"):
                r["precio"] = c["precio"]["valor"]
                r["precio_fuente"] = {"nombre": _fuente(c["precio"]["url"]), "url": c["precio"]["url"], "pagina": True}
                hecho = True
            if c.get("entradas") and not r.get("entradas"):
                r["entradas"] = {"url": c["entradas"]["url"], "nombre": c["entradas"]["nombre"], "via": "página citada"}
                hecho = True
            if c.get("sala_oficial") and not r.get("confirmado_sala"):
                r["confirmado_sala"] = {"nombre": "la web de la sala (página citada y comprobada)",
                                        "url": c["sala_oficial"]["url"]}
                hecho = True
            if c.get("estado") and not r.get("estado_evento"):
                r["estado_evento"] = {"tipo": c["estado"]["valor"], "nombre": _fuente(c["estado"]["url"]),
                                      "url": c["estado"]["url"]}
                hecho = True
            n += hecho
    return n


def vacio() -> dict:
    return {"version": VERSION, "artistas": {}, "conciertos": [], "consultados": {}, "lotes": {}}


def hoy() -> str:
    return date.today().isoformat()
