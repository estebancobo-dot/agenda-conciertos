"""Ficha musical del artista principal: estilo, géneros, origen y foto desde webs de música.

Fuentes verificadas (29-09-2026) desde GitHub Actions:
- Discogs API pública (api.discogs.com), sin clave: búsqueda de artistas, ficha (foto y perfil con el origen) y
  búsqueda de discos 'master' (género y estilos de cada disco). robots.txt lo permite. Máx. 25 peticiones/min.
- Wikipedia en español e inglés (páginas /wiki/, permitidas por robots.txt): ficha con Origen, Género(s) y foto de
  Wikimedia Commons (licencia libre).
- AllMusic bloquea todo acceso automático (403 incluso en robots.txt): solo se ofrece un enlace de búsqueda.

Regla de identidad: un dato solo se usa si el artista se identifica sin ambigüedad (una única coincidencia exacta
del nombre en Discogs; una página de Wikipedia con ese título que sea de un grupo o músico). Si no, no se asigna.
"""
from __future__ import annotations

import json
import re
import time
from collections import Counter
from datetime import date, timedelta
from urllib.parse import quote

from bs4 import BeautifulSoup

from .fetch import Fetcher
from .normalize import clean, es_generico, es_relleno, load_json, norm

DISCOGS = "https://api.discogs.com"
CADUCIDAD_OK = 180      # días que se conserva una ficha encontrada
CADUCIDAD_NO = 30       # días hasta reintentar un artista no encontrado

# ------------------------------------------------------------------ países (nombres en inglés y español → ISO)
PAISES = {
    "spain": "ES", "espana": "ES", "españa": "ES", "espanola": "ES", "espanol": "ES",
    "united kingdom": "GB", "uk": "GB", "england": "GB", "scotland": "GB", "wales": "GB", "northern ireland": "GB",
    "reino unido": "GB", "inglaterra": "GB", "escocia": "GB", "gales": "GB", "britanica": "GB", "britanico": "GB",
    "united states": "US", "usa": "US", "us": "US", "estados unidos": "US", "estadounidense": "US",
    "ireland": "IE", "irlanda": "IE", "sweden": "SE", "suecia": "SE", "norway": "NO", "noruega": "NO",
    "finland": "FI", "finlandia": "FI", "denmark": "DK", "dinamarca": "DK", "iceland": "IS", "islandia": "IS",
    "germany": "DE", "alemania": "DE", "france": "FR", "francia": "FR", "italy": "IT", "italia": "IT",
    "netherlands": "NL", "the netherlands": "NL", "paises bajos": "NL", "holanda": "NL", "belgium": "BE",
    "belgica": "BE", "switzerland": "CH", "suiza": "CH", "austria": "AT", "portugal": "PT", "greece": "GR",
    "grecia": "GR", "poland": "PL", "polonia": "PL", "czech republic": "CZ", "czechia": "CZ", "hungary": "HU",
    "hungria": "HU", "russia": "RU", "rusia": "RU", "ukraine": "UA", "ucrania": "UA", "japan": "JP", "japon": "JP",
    "canada": "CA", "australia": "AU", "new zealand": "NZ", "nueva zelanda": "NZ", "argentina": "AR",
    "mexico": "MX", "chile": "CL", "colombia": "CO", "brazil": "BR", "brasil": "BR", "uruguay": "UY", "cuba": "CU",
    "peru": "PE", "venezuela": "VE", "israel": "IL", "turkey": "TR", "turquia": "TR", "south africa": "ZA",
    "south korea": "KR", "corea del sur": "KR", "estonia": "EE", "latvia": "LV", "lithuania": "LT", "slovenia": "SI",
    "croatia": "HR", "serbia": "RS", "romania": "RO", "rumania": "RO", "bulgaria": "BG", "luxembourg": "LU",
    "malta": "MT", "puerto rico": "PR", "morocco": "MA", "marruecos": "MA",
}
# comunidades y regiones españolas que aparecen como origen
REGIONES_ES = {"madrid", "barcelona", "cataluna", "catalunya", "andalucia", "pais vasco", "euskadi", "galicia",
               "valencia", "comunidad valenciana", "islas canarias", "canarias", "asturias", "aragon", "navarra",
               "castilla y leon", "castilla la mancha", "extremadura", "murcia", "region de murcia", "cantabria",
               "la rioja", "islas baleares", "baleares", "bilbao", "sevilla", "zaragoza", "malaga", "granada",
               "vigo", "gijon", "oviedo", "pamplona", "valladolid", "cadiz", "cordoba", "alicante", "donostia",
               "san sebastian", "vitoria", "leon", "salamanca", "burgos", "toledo", "almeria", "huelva", "jaen"}


def pais_de_texto(texto: str | None) -> str | None:
    """'Hertford, Inglaterra, Reino Unido' → 'GB'; 'La Palma, Islas Canarias, España' → 'ES'."""
    if not texto:
        return None
    partes = [norm(p) for p in re.split(r"[,(/)]", texto) if norm(p)]
    for p in reversed(partes):
        if p in PAISES:
            return PAISES[p]
    for p in reversed(partes):
        if p in REGIONES_ES:
            return "ES"
    return None


# ------------------------------------------------------------------ Discogs
def _sin_sufijo(nombre: str) -> str:
    return re.sub(r"\s*\(\d+\)\s*$", "", nombre or "").rstrip("*").strip()


def discogs_identificar(resultados: list[dict], nombre: str) -> tuple[dict | None, int]:
    """Única coincidencia exacta del nombre (Discogs añade '(2)', '(3)'… a los homónimos)."""
    arts = [r for r in resultados if r.get("type") == "artist"]
    # primero, coincidencia literal (respetando tildes y diéresis: 'Hällas' no es 'Hallas')
    literales = [r for r in arts if _sin_sufijo(r.get("title")).casefold() == nombre.strip().casefold()]
    if len(literales) == 1:
        return literales[0], 1
    exactos = [r for r in arts if norm(_sin_sufijo(r.get("title"))) == norm(nombre)]
    return (exactos[0] if len(exactos) == 1 else None), len(exactos)


def discogs_pais(perfil: str | None) -> str | None:
    """Del perfil: '... band from England, United Kingdom.' → GB."""
    if not perfil:
        return None
    m = re.search(r"\bfrom ([A-Z][^.\n\[]{2,80}?)(?:\.|\n|$)", perfil)
    return pais_de_texto(m.group(1)) if m else None


def discogs_estilos(masters: list[dict]) -> tuple[list[str], list[str]]:
    """Géneros y estilos más repetidos en los discos del artista (ordenados por frecuencia)."""
    g, s = Counter(), Counter()
    for m in masters:
        g.update(set(m.get("genre") or []))
        s.update(set(m.get("style") or []))
    n = max(1, len(masters))
    generos = [x for x, c in g.most_common() if c / n >= 0.25][:3]
    estilos = [x for x, c in s.most_common() if c / n >= 0.2][:5]
    return generos, estilos


def buscar_discogs(f: Fetcher, nombre: str) -> dict:
    q = quote(nombre)
    res = json.loads(f.get(f"{DISCOGS}/database/search?q={q}&type=artist&per_page=50"))
    cand, n = discogs_identificar(res.get("results", []), nombre)
    if not cand:
        return {"encontrado": False, "motivo": "sin coincidencia exacta" if n == 0 else f"{n} artistas homónimos"}
    art = json.loads(f.get(cand["resource_url"]))
    masters = json.loads(f.get(f"{DISCOGS}/database/search?artist={quote(_sin_sufijo(art.get('name')))}"
                               f"&type=master&per_page=25")).get("results", [])
    # solo discos de este artista exacto (la búsqueda por 'artist' también devuelve colaboraciones)
    masters = [m for m in masters if norm(_sin_sufijo(m.get("title", "").split(" - ")[0])) == norm(nombre)] or masters
    generos, estilos = discogs_estilos(masters)
    img = next((i.get("uri") for i in art.get("images", []) if i.get("type") == "primary"), None) or \
        next((i.get("uri") for i in art.get("images", [])), None)
    return {"encontrado": True, "id": art.get("id"), "nombre": art.get("name"), "url": art.get("uri"),
            "generos": generos, "estilos": estilos, "discos_analizados": len(masters),
            "pais": discogs_pais(art.get("profile")), "imagen": img,
            "perfil": clean((art.get("profile") or "").split("\n")[0])[:240]}


# ------------------------------------------------------------------ Wikipedia
MUSICA_CAT = re.compile(r"(?i)grupos? de|cantantes?|m[uú]sicos?|raperos?|cantautor|d[uú]os de m[uú]sica|bandas? de|"
                        r"musical groups|bands|singers|musicians|rappers|songwriters|music(al)? duos")
CAMPOS = {"origen": "origen", "origin": "origen", "nacimiento": "nacimiento", "born": "nacimiento",
          "nacionalidad": "nacionalidad", "genero": "generos", "generos": "generos", "genero s": "generos",
          "genres": "generos", "genre": "generos"}


def wikipedia_parse(html: str, url: str) -> dict:
    s = BeautifulSoup(html, "lxml")
    if s.select_one("#disambigbox, .mw-disambig, .dablink") and not s.select_one("table.infobox"):
        return {"encontrado": False, "motivo": "página de desambiguación"}
    cats = [c.get_text() for c in s.select("#mw-normal-catlinks a")]
    ib = s.select_one("table.infobox")
    if not ib or not any(MUSICA_CAT.search(c) for c in cats):
        return {"encontrado": False, "motivo": "no es la página de un grupo o músico"}
    datos = {}
    for tr in ib.find_all("tr"):
        th, td = tr.find("th"), tr.find("td")
        if not th or not td:
            continue
        k = CAMPOS.get(norm(th.get_text(" ")).strip())
        if not k:
            continue
        if k == "generos":
            for sup in td.find_all("sup"):
                sup.decompose()
            items = [clean(li.get_text(" ")) for li in td.find_all("li")] or \
                    [clean(a.get_text(" ")) for a in td.find_all("a")] or [clean(td.get_text(" "))]
            datos[k] = [re.sub(r"\s*\(.*?\)", "", x) for x in items if x and len(x) < 40]
        else:
            datos[k] = clean(td.get_text(", ", strip=True))
    pais = None
    for k in ("nacionalidad", "origen", "nacimiento"):
        pais = pais or pais_de_texto(datos.get(k))
    img = ib.find("img")
    imagen = imagen_pagina = None
    if img and img.get("src") and int(img.get("width") or 100) >= 60:
        imagen = "https:" + img["src"].split("?")[0] if img["src"].startswith("//") else img["src"].split("?")[0]
        a = img.find_parent("a")
        imagen_pagina = ("https://" + url.split("/")[2] + a["href"]) if a and a.get("href", "").startswith("/") \
            else (a.get("href") if a else None)
    canon = s.find("link", rel="canonical")
    return {"encontrado": True, "url": canon["href"] if canon else url, "generos": datos.get("generos", [])[:6],
            "origen": datos.get("origen") or datos.get("nacimiento"), "pais": pais, "imagen": imagen,
            "imagen_pagina": imagen_pagina}


def buscar_wikipedia(f: Fetcher, nombre: str) -> dict:
    titulo = nombre.strip().replace(" ", "_")
    intentos = []
    for lang, sufijos in (("es", ["", "_(banda)", "_(grupo_musical)", "_(cantante)"]),
                          ("en", ["", "_(band)"])):
        for suf in sufijos:
            url = f"https://{lang}.wikipedia.org/wiki/{quote(titulo + suf)}"
            try:
                html = f.get(url)
            except Exception as e:  # noqa: BLE001 - 404 = no existe esa página
                intentos.append(f"{lang}{suf or ''}: {'no existe' if '404' in str(e) else type(e).__name__}")
                continue
            r = wikipedia_parse(html, url)
            # el título de la página debe corresponder al nombre (evita redirecciones a otra cosa)
            if r["encontrado"]:
                tit = norm(re.sub(r"\s*\(.*?\)\s*$", "", r["url"].rsplit("/", 1)[-1].replace("_", " ")))
                if tit != norm(nombre) and not norm(nombre).startswith(tit):
                    intentos.append(f"{lang}{suf}: redirige a otra página")
                    continue
                r["idioma"] = lang
                return r
            intentos.append(f"{lang}{suf or ''}: {r['motivo']}")
            if suf == "" and r["motivo"] == "no es la página de un grupo o músico":
                continue
    return {"encontrado": False, "motivo": "; ".join(intentos[:4])}


# ------------------------------------------------------------------ orquestación
def nombre_consultable(nombre: str) -> bool:
    n = norm(nombre)
    return bool(n) and not es_generico(nombre) and not es_relleno(nombre) and len(n) >= 2 and len(nombre) <= 60 \
        and not re.search(r"(?i)tributo|candlelight|jam session|concierto de|festival|fest\b|musical|flamenco|"
                          r"sesi[oó]n|open mic|karaoke|homenaje|aniversario|fiesta|party|noche de", nombre)


def enriquecer(recs: list[dict], cache: dict, hoy: date, presupuesto_seg: float = 1200,
               fetcher_dc: Fetcher | None = None, fetcher_wp: Fetcher | None = None) -> dict:
    """Completa cache[norm(artista)] para los artistas principales, priorizando los conciertos en foco y próximos."""
    fetcher_dc = fetcher_dc or Fetcher(min_interval=2.6)   # 25 peticiones/min sin clave
    fetcher_wp = fetcher_wp or Fetcher()
    stats = {"consultados": 0, "desde_cache": 0, "discogs": 0, "wikipedia": 0, "sin_ficha": 0, "pendientes": 0,
             "errores": []}
    inicio = time.monotonic()
    vistos, pendientes = set(), []
    for r in sorted(recs, key=lambda r: (not r["en_foco"], r["fecha"])):
        nombre = r["artista"]
        k = norm(nombre)
        if k in vistos or not nombre_consultable(nombre):
            continue
        vistos.add(k)
        ent = cache.get(k)
        cad = CADUCIDAD_OK if ent and (ent.get("discogs", {}).get("encontrado") or
                                       ent.get("wikipedia", {}).get("encontrado")) else CADUCIDAD_NO
        if ent and ent.get("fecha", "") >= (hoy - timedelta(days=cad)).isoformat():
            stats["desde_cache"] += 1
            continue
        pendientes.append((k, nombre))

    def consultar(par):
        k, nombre = par
        if time.monotonic() - inicio > presupuesto_seg:
            return k, None
        ent = {"nombre": nombre, "fecha": hoy.isoformat()}
        for clave, fn, fx in (("wikipedia", buscar_wikipedia, fetcher_wp), ("discogs", buscar_discogs, fetcher_dc)):
            try:
                ent[clave] = fn(fx, nombre)
            except Exception as e:  # noqa: BLE001
                ent[clave] = {"encontrado": False, "motivo": f"error: {type(e).__name__}"}
                if len(stats["errores"]) < 20:
                    stats["errores"].append(f"{nombre} ({clave}): {type(e).__name__}: {str(e)[:80]}")
        return k, ent

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as ex:
        for k, ent in ex.map(consultar, pendientes):
            if ent is None:
                stats["pendientes"] += 1
            else:
                cache[k] = ent
                stats["consultados"] += 1
    for k in vistos:
        ent = cache.get(k) or {}
        if ent.get("discogs", {}).get("encontrado"):
            stats["discogs"] += 1
        if ent.get("wikipedia", {}).get("encontrado"):
            stats["wikipedia"] += 1
        if ent and not ent.get("discogs", {}).get("encontrado") and not ent.get("wikipedia", {}).get("encontrado"):
            stats["sin_ficha"] += 1
    return stats


# ------------------------------------------------------------------ aplicar la ficha al concierto
def _estilos_discogs_de_wikipedia(generos: list[str]) -> list[str]:
    """Traduce los géneros de Wikipedia al nombre de estilo de Discogs (solo traducción literal declarada)."""
    from .clasificar import discogs
    est, _ = discogs(generos)
    return est


def ficha(ent: dict | None) -> dict | None:
    """Resumen de la ficha musical para la web y para los filtros."""
    if not ent:
        return None
    dc, wp = ent.get("discogs") or {}, ent.get("wikipedia") or {}
    if not dc.get("encontrado") and not wp.get("encontrado"):
        return None
    from .clasificar import genero_de_estilo
    estilos = list(dc.get("estilos") or []) if dc.get("encontrado") else []
    fuente_estilo = "Discogs" if estilos else None
    wp_est = _estilos_discogs_de_wikipedia(wp.get("generos") or []) if wp.get("encontrado") else []
    if not estilos and wp_est:
        estilos, fuente_estilo = wp_est, "Wikipedia"
    if not fuente_estilo and dc.get("encontrado") and dc.get("generos"):
        fuente_estilo = "Discogs"
    if not fuente_estilo and wp.get("encontrado") and wp.get("generos"):
        fuente_estilo = "Wikipedia"
    from .clasificar import generos_de_texto
    generos = list(dc.get("generos") or []) if dc.get("encontrado") else []
    if not generos and wp.get("encontrado"):
        generos = generos_de_texto(wp.get("generos") or [])
    for e in estilos:
        g = genero_de_estilo(e)
        if g and g not in generos:
            generos.append(g)
    pais, fuente_pais = None, None
    if wp.get("encontrado") and wp.get("pais"):
        pais, fuente_pais = wp["pais"], "Wikipedia"
    elif dc.get("encontrado") and dc.get("pais"):
        pais, fuente_pais = dc["pais"], "Discogs"
    imagen = None
    if wp.get("encontrado") and wp.get("imagen"):
        imagen = {"url": wp["imagen"], "credito": "Wikimedia Commons", "enlace": wp.get("imagen_pagina") or wp["url"]}
    elif dc.get("encontrado") and dc.get("imagen"):
        imagen = {"url": dc["imagen"], "credito": "Discogs", "enlace": "https://www.discogs.com" + (
            dc.get("url") or "") if (dc.get("url") or "").startswith("/") else dc.get("url")}
    enlaces = []
    if dc.get("encontrado"):
        u = dc["url"] if dc["url"].startswith("http") else "https://www.discogs.com" + dc["url"]
        enlaces.append({"nombre": "Discogs", "url": u})
    if wp.get("encontrado"):
        enlaces.append({"nombre": f"Wikipedia ({wp.get('idioma', 'es')})", "url": wp["url"]})
    return {"generos": generos, "estilos": estilos, "fuente_estilo": fuente_estilo,
            "generos_wikipedia": wp.get("generos") or [], "pais": pais, "fuente_pais": fuente_pais,
            "imagen": imagen, "enlaces": enlaces, "perfil": dc.get("perfil") if dc.get("encontrado") else None}
