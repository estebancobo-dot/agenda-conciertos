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
import logging
import re
import time
from collections import Counter
from datetime import date, timedelta
from urllib.parse import quote

from bs4 import BeautifulSoup

from .fetch import Fetcher
from .normalize import clean, es_generico, es_relleno, load_json, norm

log = logging.getLogger(__name__)
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


def discogs_ficha(f: Fetcher, art: dict, nombre: str, via: str) -> dict:
    masters = json.loads(f.get(f"{DISCOGS}/database/search?artist={quote(_sin_sufijo(art.get('name')))}"
                               f"&type=master&per_page=25")).get("results", [])
    # solo discos de este artista exacto (la búsqueda por 'artist' también devuelve colaboraciones)
    masters = [m for m in masters if norm(_sin_sufijo(m.get("title", "").split(" - ")[0])) == norm(nombre)] or masters
    generos, estilos = discogs_estilos(masters)
    img = next((i.get("uri") for i in art.get("images", []) if i.get("type") == "primary"), None) or \
        next((i.get("uri") for i in art.get("images", [])), None)
    return {"encontrado": True, "id": art.get("id"), "nombre": art.get("name"), "url": art.get("uri"),
            "generos": generos, "estilos": estilos, "discos_analizados": len(masters),
            "pais": discogs_pais(art.get("profile")), "imagen": img, "identificado_por": via,
            "perfil": clean((art.get("profile") or "").split("\n")[0])[:240]}


def buscar_discogs(f: Fetcher, nombre: str, discogs_id: str | None = None) -> dict:
    """Con el identificador de Wikidata no hay ambigüedad; sin él, única coincidencia exacta del nombre."""
    if discogs_id:
        import requests
        try:
            art = json.loads(f.get(f"{DISCOGS}/artists/{discogs_id}"))
            return discogs_ficha(f, art, nombre, "identificador de Discogs en Wikidata")
        except requests.HTTPError as e:
            # Wikidata puede apuntar a una ficha de Discogs borrada o fusionada: se busca por nombre
            if e.response is None or e.response.status_code != 404:
                raise
    q = quote(nombre)
    res = json.loads(f.get(f"{DISCOGS}/database/search?q={q}&type=artist&per_page=50"))
    cand, n = discogs_identificar(res.get("results", []), nombre)
    if not cand:
        return {"encontrado": False, "motivo": "sin coincidencia exacta" if n == 0 else f"{n} artistas homónimos"}
    art = json.loads(f.get(cand["resource_url"]))
    return discogs_ficha(f, art, nombre, "única coincidencia exacta del nombre en Discogs")


class _FetcherDiscogs(Fetcher):
    """Discogs indica en cada respuesta cuántas peticiones quedan en el minuto: si se acaban, se espera."""

    def after_response(self, r) -> None:
        try:
            quedan = int(r.headers.get("X-Discogs-Ratelimit-Remaining", "99"))
        except ValueError:
            return
        if quedan <= 2:
            time.sleep(10)


def fetcher_discogs() -> Fetcher:
    """Límite publicado por Discogs: 60 peticiones/min con DISCOGS_TOKEN (gratuito), 25 sin él."""
    import os
    token = os.environ.get("DISCOGS_TOKEN", "").strip()
    f = _FetcherDiscogs(min_interval=1.0 if token else 2.4)
    if token:
        f.session.headers["Authorization"] = f"Discogs token={token}"
    return f


def fetcher_wikimedia() -> Fetcher:
    """Wikipedia y Wikidata no publican un límite de lectura: piden User-Agent identificable y peticiones
    en serie (una tras otra), que es como van siempre las de una misma web."""
    return Fetcher(min_interval=0.2)


def fetcher_lastfm() -> Fetcher:
    return Fetcher(min_interval=0.25)  # Last.fm: máximo 5 peticiones/s


# ------------------------------------------------------------------ Wikidata (Special:EntityData, permitido por robots.txt)
WIKIDATA = "https://www.wikidata.org/wiki/Special:EntityData/{q}.json"
Q_PAIS = {"Q29": "ES", "Q145": "GB", "Q21": "GB", "Q22": "GB", "Q25": "GB", "Q26": "GB", "Q30": "US", "Q34": "SE",
          "Q183": "DE", "Q142": "FR", "Q38": "IT", "Q55": "NL", "Q29999": "NL", "Q31": "BE", "Q39": "CH", "Q40": "AT",
          "Q45": "PT", "Q20": "NO", "Q33": "FI", "Q35": "DK", "Q27": "IE", "Q16": "CA", "Q408": "AU", "Q17": "JP",
          "Q414": "AR", "Q96": "MX", "Q298": "CL", "Q739": "CO", "Q155": "BR", "Q36": "PL", "Q41": "GR", "Q159": "RU",
          "Q212": "UA", "Q189": "IS", "Q213": "CZ", "Q28": "HU", "Q664": "NZ", "Q801": "IL", "Q43": "TR", "Q258": "ZA",
          "Q884": "KR", "Q77": "UY", "Q241": "CU", "Q419": "PE", "Q717": "VE", "Q218": "RO", "Q219": "BG", "Q224": "HR",
          "Q403": "RS", "Q215": "SI", "Q191": "EE", "Q211": "LV", "Q37": "LT", "Q32": "LU", "Q233": "MT", "Q1183": "PR"}
WD_IDS = {"P1953": "discogs", "P1728": "allmusic", "P1902": "spotify", "P434": "musicbrainz", "P3192": "lastfm"}


def wikidata_parse(data: dict) -> dict:
    ent = next(iter(data.get("entities", {}).values()), {})
    claims = ent.get("claims", {})

    def valores(p):
        out = []
        for c in claims.get(p, []):
            v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
            if isinstance(v, dict) and "id" in v:
                v = v["id"]
            if v and c.get("rank") != "deprecated":
                out.append(v)
        return out

    ids = {n: valores(p)[0] for p, n in WD_IDS.items() if valores(p)}
    paises = [Q_PAIS[q] for q in valores("P495") + valores("P27") if q in Q_PAIS]
    img = valores("P18")
    return {"encontrado": True, "id": ent.get("id"), "ids": ids,
            "pais": paises[0] if paises and len(set(paises)) == 1 else None,
            "imagen_commons": img[0] if img else None}


def buscar_wikidata(f: Fetcher, qid: str) -> dict:
    return wikidata_parse(json.loads(f.get(WIKIDATA.format(q=qid))))


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
    mq = re.search(r'"wgWikibaseItemId":"(Q\d+)"', html)
    return {"encontrado": True, "url": canon["href"] if canon else url, "generos": datos.get("generos", [])[:6],
            "wikidata": mq.group(1) if mq else None,
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
                if suf == "" and "404" in str(e):
                    # si ni siquiera existe la página con el nombre, no hay homónimo que obligue a usar
                    # "(banda)"; se ahorran 3 peticiones por artista desconocido
                    break
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


# ------------------------------------------------------------------ Last.fm (clave gratuita LASTFM_KEY, opcional)
LASTFM = "https://ws.audioscrobbler.com/2.0/"


def lastfm_key() -> str:
    import os
    return os.environ.get("LASTFM_KEY", "").strip()


def lastfm_parse(data: dict, nombre: str, por_mbid: bool) -> dict:
    """Etiquetas de los oyentes traducidas a estilos de Discogs (solo equivalencias declaradas en taxonomia.json)."""
    if "error" in data:
        return {"encontrado": False, "motivo": data.get("message", "no encontrado")}
    tt = data.get("toptags", {})
    artista = tt.get("@attr", {}).get("artist", "")
    if not por_mbid and artista.casefold() != nombre.casefold():
        return {"encontrado": False, "motivo": f"Last.fm devuelve otro nombre ({artista})"}
    etiquetas = [t["name"] for t in tt.get("tag", []) if int(t.get("count", 0)) >= 25][:10]
    from .clasificar import discogs, generos_de_texto
    estilos, generos = discogs(etiquetas)
    for g in generos_de_texto(etiquetas):
        if g not in generos:
            generos.append(g)
    return {"encontrado": True, "nombre": artista, "etiquetas": etiquetas, "estilos": estilos[:5],
            "generos": generos[:3], "url": f"https://www.last.fm/music/{quote(artista.replace(' ', '+'))}",
            "identificado_por": "identificador de MusicBrainz en Wikidata" if por_mbid else "coincidencia por nombre"}


def buscar_lastfm(f: Fetcher, nombre: str, mbid: str | None, key: str) -> dict:
    import requests
    q = f"mbid={mbid}" if mbid else f"artist={quote(nombre)}&autocorrect=0"
    try:
        txt = f.get(f"{LASTFM}?method=artist.gettoptags&{q}&api_key={key}&format=json")
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in (400, 404):
            try:
                return lastfm_parse(e.response.json(), nombre, bool(mbid))
            except ValueError:
                pass
        raise
    r = lastfm_parse(json.loads(txt), nombre, bool(mbid))
    if not r["encontrado"] and mbid:  # Last.fm no siempre conoce el identificador: se prueba por nombre
        return buscar_lastfm(f, nombre, None, key)
    return r


# ------------------------------------------------------------------ orquestación
def nombre_consultable(nombre: str) -> bool:
    n = norm(nombre)
    return bool(n) and not es_generico(nombre) and not es_relleno(nombre) and len(n) >= 2 and len(nombre) <= 60 \
        and not re.search(r"(?i)tributo|candlelight|jam session|concierto de|festival|fest\b|musical|flamenco|"
                          r"sesi[oó]n|open mic|karaoke|homenaje|aniversario|fiesta|party|noche de", nombre)


def _tiene_estilo(ent: dict) -> bool:
    return bool((ent.get("discogs", {}).get("encontrado") and ent["discogs"].get("estilos")) or
                (ent.get("wikipedia", {}).get("encontrado") and _estilos_discogs_de_wikipedia(ent["wikipedia"].get("generos") or [])))


def _pasos_con_error(ent: dict) -> list[str]:
    return [k for k in ("wikipedia", "wikidata", "discogs", "lastfm")
            if str((ent.get(k) or {}).get("motivo", "")).startswith("error")]


def _encontrado(ent: dict) -> bool:
    return any((ent.get(k) or {}).get("encontrado") for k in ("discogs", "wikipedia", "lastfm"))


def enriquecer(recs: list[dict], cache: dict, hoy: date, presupuesto_seg: float = 1200,
               fetcher_dc: Fetcher | None = None, fetcher_wp: Fetcher | None = None,
               fetcher_lf: Fetcher | None = None, clave_lastfm: str | None = None, parar=None,
               guardar=None) -> dict:
    """Completa cache[norm(artista)] para los artistas principales, priorizando los conciertos en foco y próximos.

    Cada artista se consulta una vez; la ficha se renueva a los 180 días (30 si no se encontró). Si una ficha
    antigua no tiene un paso añadido después (Wikidata, Last.fm), solo se completa ese paso."""
    fetcher_dc = fetcher_dc or fetcher_discogs()
    fetcher_wp = fetcher_wp or fetcher_wikimedia()
    clave_lastfm = lastfm_key() if clave_lastfm is None else clave_lastfm
    fetcher_lf = fetcher_lf or fetcher_lastfm()
    stats = {"consultados": 0, "completados": 0, "desde_cache": 0, "discogs": 0, "wikipedia": 0, "wikidata": 0,
             "lastfm": 0, "sin_ficha": 0, "pendientes": 0, "errores": [],
             "discogs_con_token": "Authorization" in fetcher_dc.session.headers, "lastfm_activo": bool(clave_lastfm)}
    inicio = time.monotonic()
    vistos, pendientes = set(), []
    for r in sorted(recs, key=lambda r: (not r["en_foco"], r["fecha"])):
        nombre = r["artista"]
        k = norm(nombre)
        if k in vistos or not nombre_consultable(nombre):
            continue
        vistos.add(k)
        ent = cache.get(k)
        cad = CADUCIDAD_OK if ent and _encontrado(ent) else CADUCIDAD_NO
        if not ent or ent.get("fecha", "") < (hoy - timedelta(days=cad)).isoformat():
            pendientes.append((k, nombre, None))
            continue
        falta_wd = ent.get("wikipedia", {}).get("wikidata") and "wikidata" not in ent
        falta_lf = clave_lastfm and "lastfm" not in ent and not _tiene_estilo(ent)
        if falta_wd or falta_lf or _pasos_con_error(ent):
            pendientes.append((k, nombre, ent))
        else:
            stats["desde_cache"] += 1

    def consultar(par):
        k, nombre, previa = par
        if time.monotonic() - inicio > presupuesto_seg or (parar is not None and parar.is_set()):
            return k, None
        ent = dict(previa) if previa else {"nombre": nombre, "fecha": hoy.isoformat()}
        for clave in _pasos_con_error(ent):  # un error (red, ficha borrada…) no se guarda 180 días: se repite
            ent.pop(clave)

        def paso(clave, fn, *args):
            try:
                ent[clave] = fn(*args)
            except Exception as e:  # noqa: BLE001
                ent[clave] = {"encontrado": False, "motivo": f"error: {type(e).__name__}"}
                msg = str(e)[:120].replace(clave_lastfm, "***") if clave_lastfm else str(e)[:120]
                if len(stats["errores"]) < 20:
                    stats["errores"].append(f"{nombre} ({clave}): {type(e).__name__}: {msg}")

        if "wikipedia" not in ent:
            paso("wikipedia", buscar_wikipedia, fetcher_wp, nombre)
        qid = ent["wikipedia"].get("wikidata") if ent["wikipedia"].get("encontrado") else None
        if qid and "wikidata" not in ent:
            paso("wikidata", buscar_wikidata, fetcher_wp, qid)
            dc = ent.get("discogs") or {}
            dc_id = (ent.get("wikidata") or {}).get("ids", {}).get("discogs")
            if previa and dc_id and str(dc.get("id")) != str(dc_id):
                ent.pop("discogs", None)  # Wikidata identifica otro artista de Discogs (homónimo): se corrige
        if "discogs" not in ent:
            dc_id = (ent.get("wikidata") or {}).get("ids", {}).get("discogs")
            paso("discogs", buscar_discogs, fetcher_dc, nombre, dc_id)
        if clave_lastfm and "lastfm" not in ent and not _tiene_estilo(ent):
            mbid = (ent.get("wikidata") or {}).get("ids", {}).get("musicbrainz")
            paso("lastfm", buscar_lastfm, fetcher_lf, nombre, mbid, clave_lastfm)
        return k, ent

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as ex:
        for (k, ent), (_, _, previa) in zip(ex.map(consultar, pendientes), pendientes):
            if ent is None:
                stats["pendientes"] += 1
            else:
                cache[k] = ent
                stats["completados" if previa else "consultados"] += 1
                # se guarda cada 50 fichas: si la ejecución se corta (tiempo máximo, caída), no se pierde lo hecho
                if guardar and (stats["consultados"] + stats["completados"]) % 50 == 0:
                    try:
                        guardar()
                    except Exception as e:  # noqa: BLE001
                        log.warning("no se pudo guardar artistas.json: %s", e)
    for k in vistos:
        ent = cache.get(k) or {}
        for fuente in ("discogs", "wikipedia", "wikidata", "lastfm"):
            if ent.get(fuente, {}).get("encontrado"):
                stats[fuente] += 1
        if ent and not _encontrado(ent):
            stats["sin_ficha"] += 1
    stats["duracion_seg"] = round(time.monotonic() - inicio)
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
    dc, wp, wd = ent.get("discogs") or {}, ent.get("wikipedia") or {}, ent.get("wikidata") or {}
    lf = ent.get("lastfm") or {}
    if not lf.get("encontrado") or not (lf.get("estilos") or lf.get("generos")):
        lf = {}
    if not dc.get("encontrado") and not wp.get("encontrado") and not lf:
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
    lf_usado = False
    if not estilos and lf.get("estilos"):
        estilos, fuente_estilo, lf_usado = list(lf["estilos"]), "Last.fm", True
    elif not fuente_estilo and lf.get("generos"):
        fuente_estilo, lf_usado = "Last.fm", True
    if lf_usado and lf.get("identificado_por") == "coincidencia por nombre":
        fuente_estilo = "Last.fm (etiquetas de oyentes, coincidencia por nombre)"
    elif lf_usado:
        fuente_estilo = "Last.fm (etiquetas de oyentes)"
    from .clasificar import generos_de_texto
    generos = list(dc.get("generos") or []) if dc.get("encontrado") else []
    if not generos and wp.get("encontrado"):
        generos = generos_de_texto(wp.get("generos") or [])
    if not generos and lf_usado:
        generos = list(lf.get("generos") or [])
    for e in estilos:
        g = genero_de_estilo(e)
        if g and g not in generos:
            generos.append(g)
    pais, fuente_pais = None, None
    if wd.get("encontrado") and wd.get("pais"):
        pais, fuente_pais = wd["pais"], "Wikidata"
    elif wp.get("encontrado") and wp.get("pais"):
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
    ids = wd.get("ids", {}) if wd.get("encontrado") else {}
    if ids.get("allmusic"):
        enlaces.append({"nombre": "AllMusic", "url": f"https://www.allmusic.com/artist/{ids['allmusic']}"})
    if ids.get("spotify"):
        enlaces.append({"nombre": "Spotify", "url": f"https://open.spotify.com/artist/{ids['spotify']}"})
    if ids.get("musicbrainz"):
        enlaces.append({"nombre": "MusicBrainz", "url": f"https://musicbrainz.org/artist/{ids['musicbrainz']}"})
    if ids.get("lastfm"):
        enlaces.append({"nombre": "Last.fm", "url": f"https://www.last.fm/music/{ids['lastfm']}"})
    elif lf:
        enlaces.append({"nombre": "Last.fm", "url": lf["url"]})
    if imagen is None and wd.get("imagen_commons"):
        nom = quote(wd["imagen_commons"].replace(" ", "_"))
        imagen = {"url": f"https://commons.wikimedia.org/wiki/Special:FilePath/{nom}?width=640",
                  "credito": "Wikimedia Commons", "enlace": f"https://commons.wikimedia.org/wiki/File:{nom}"}
    identidad = dc.get("identificado_por") if dc.get("encontrado") else None
    if identidad is None and lf_usado:
        identidad = f"Last.fm por {lf.get('identificado_por')}"
    if wp.get("encontrado"):
        identidad = "página de Wikipedia del grupo" + (" y Wikidata" if wd.get("encontrado") else "")
        if dc.get("encontrado"):
            identidad += f"; Discogs por {dc.get('identificado_por', 'coincidencia exacta')}"
    return {"identidad": identidad,"generos": generos, "estilos": estilos, "fuente_estilo": fuente_estilo,
            "generos_wikipedia": wp.get("generos") or [], "pais": pais, "fuente_pais": fuente_pais,
            "imagen": imagen, "enlaces": enlaces, "perfil": dc.get("perfil") if dc.get("encontrado") else None,
            "tiene_allmusic": bool(ids.get("allmusic"))}
