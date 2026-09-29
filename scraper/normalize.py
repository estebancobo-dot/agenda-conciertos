"""Normalización de texto, salas, municipios, fechas y estilos."""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from functools import lru_cache
from pathlib import Path

from rapidfuzz import fuzz

DATA = Path(__file__).resolve().parent.parent / "data"

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
    "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8, "sep": 9, "sept": 9,
    "set": 9, "oct": 10, "nov": 11, "dic": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "apr": 4, "aug": 8, "dec": 12,
}
MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
            "octubre", "noviembre", "diciembre"]
MONTHS_EN = ["january", "february", "march", "april", "may", "june", "july", "august", "september",
             "october", "november", "december"]


def norm(s: str | None) -> str:
    """Minúsculas, sin tildes ni signos, espacios simples."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", " and ").replace("'", "").replace("’", "")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


def clean(s: str | None) -> str:
    """Limpia espacios y separadores sobrantes sin alterar el texto."""
    if not s:
        return ""
    s = re.sub(r"\s+", " ", str(s).replace("\xa0", " ")).strip()
    return s.strip(" .·|-–,;")


def load_json(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- salas
@lru_cache(maxsize=1)
def _salas():
    d = load_json("salas_alias.json")
    alias, muni, canon = {}, {}, {}
    for s in d["salas"]:
        for a in [s["nombre"], *s.get("alias", [])]:
            alias[norm(a)] = s["nombre"]
        muni[s["nombre"]] = s.get("municipio")
        canon[norm(s["nombre"])] = s["nombre"]
    distintas = [{norm(a) for a in par} for par in d.get("distintas", [])]
    return alias, muni, distintas


_SALA_PREFIX = re.compile(r"^(sala|la sala|club|sala de conciertos|teatro)\s+")


def _sala_key(n: str) -> str:
    return _SALA_PREFIX.sub("", n)


def canon_sala(nombre: str | None) -> str:
    """Nombre canónico de la sala según data/salas_alias.json (o el original limpio)."""
    nombre = clean(nombre)
    if not nombre:
        return ""
    alias, _, _ = _salas()
    n = norm(nombre)
    # quita sufijos de ciudad: "sala x madrid", "sala x (madrid)"
    candidates = [n, re.sub(r"\s+(madrid|de madrid)$", "", n)]
    for c in list(candidates):
        candidates.append(_sala_key(c))
    for c in candidates:
        if c in alias:
            return alias[c]
    # "Sala X" → probar con "sala " delante
    for c in candidates:
        if "sala " + c in alias:
            return alias["sala " + c]
    return nombre


def sala_municipio(sala: str) -> str | None:
    _, muni, _ = _salas()
    return muni.get(sala)


def salas_distintas(a: str, b: str) -> bool:
    _, _, distintas = _salas()
    na, nb = norm(a), norm(b)
    return any(na in par and nb in par and na != nb for par in distintas)


def misma_sala(a: str, b: str) -> bool:
    """True si dos nombres de sala (ya canonizados) son la misma sala."""
    if not a or not b:
        return False
    if a == b:
        return True
    if salas_distintas(a, b):
        return False
    ka, kb = _sala_key(norm(a)), _sala_key(norm(b))
    if not ka or not kb:
        return False
    if ka == kb or fuzz.ratio(ka, kb) >= 90 or ka.replace(" ", "") == kb.replace(" ", ""):
        return True
    ta, tb = _tokens_sala(ka), _tokens_sala(kb)
    return bool(ta) and bool(tb) and fuzz.token_sort_ratio(ta, tb) >= 92


_GENERICAS_SALA = {"sala", "club", "teatro", "recinto", "madrid", "de", "del", "la", "el", "the", "espacio", "and",
                   "y", "hall"}


def _tokens_sala(k: str) -> str:
    return " ".join(w for w in k.split() if w not in _GENERICAS_SALA)


# ---------------------------------------------------------------- municipios
@lru_cache(maxsize=1)
def _municipios():
    d = load_json("municipios.json")
    m = {norm(x): x for x in d["municipios"]}
    for k, v in d["alias"].items():
        m[norm(k)] = v
    for b in d["barrios_madrid"]:
        m.setdefault(norm(b), "Madrid")
    # variantes con artículo pospuesto: "Rozas de Madrid, Las"
    for x in d["municipios"]:
        parts = x.split(" ", 1)
        if parts[0] in ("La", "El", "Los", "Las") and len(parts) == 2:
            m.setdefault(norm(f"{parts[1]}, {parts[0]}"), x)
            m.setdefault(norm(parts[1]), x)
    return m, set(d["municipios"])


def municipio(texto: str | None) -> str | None:
    """Devuelve el municipio oficial de la Comunidad de Madrid o None si no lo es."""
    if not texto:
        return None
    m, _ = _municipios()
    n = norm(texto)
    if n in m:
        return m[n]
    # "Leganés (Madrid)", "Madrid, Madrid", "Coslada - Madrid"
    for part in re.split(r"[(),/\-–]| - ", str(texto)):
        p = norm(part)
        if p in m:
            return m[p]
    return None


def es_municipio_madrid(nombre: str | None) -> bool:
    _, oficiales = _municipios()
    return nombre in oficiales


# ---------------------------------------------------------------- fechas y horas
def parse_hora(texto: str | None) -> str | None:
    if not texto:
        return None
    m = re.search(r"(?<!\d)([01]?\d|2[0-3])\s*[:.h]\s*([0-5]\d)(?!\d)", str(texto))
    if m:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    m = re.search(r"(?<!\d)([01]?\d|2[0-3])\s*(?:h\b|hrs?\b|horas\b)", str(texto), re.I)
    if m:
        return f"{int(m.group(1)):02d}:00"
    return None


def infer_year(day: int, month: int, today: date, back_days: int = 45) -> int:
    """Año de una fecha sin año: el más cercano que no quede más de back_days en el pasado."""
    for y in (today.year, today.year + 1):
        try:
            d = date(y, month, day)
        except ValueError:
            continue
        if (d - today).days >= -back_days:
            return y
    return today.year + 1


def parse_fecha_texto(texto: str, today: date, year: int | None = None) -> date | None:
    """Reconoce '17 de octubre de 2026', '17 Oct 2026', '17/10/2026', '2026-10-17', 'sábado 17 octubre'."""
    if not texto:
        return None
    t = norm(texto)
    m = re.search(r"(20\d\d)-(\d{1,2})-(\d{1,2})", texto)
    if m:
        return _mk(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](20\d\d|\d\d)\b", texto)
    if m:
        y = int(m.group(3))
        return _mk(y + 2000 if y < 100 else y, int(m.group(2)), int(m.group(1)))
    for m in re.finditer(r"\b(\d{1,2})\s+(?:de\s+)?([a-z]+)(?:\s+(?:de\s+)?(20\d\d))?\b", t):
        mes = MESES.get(m.group(2))
        if mes:
            d = int(m.group(1))
            y = int(m.group(3)) if m.group(3) else (year or infer_year(d, mes, today))
            return _mk(y, mes, d)
    # formato inglés: "Oct 17, 2026"
    m = re.search(r"\b([a-z]+)\s+(\d{1,2})(?:\s+(20\d\d))?\b", t)
    if m and MESES.get(m.group(1)):
        d = int(m.group(2))
        mes = MESES[m.group(1)]
        y = int(m.group(3)) if m.group(3) else (year or infer_year(d, mes, today))
        return _mk(y, mes, d)
    return None


def _mk(y: int, m: int, d: int) -> date | None:
    try:
        return date(y, m, d)
    except ValueError:
        return None


# ---------------------------------------------------------------- artistas
_SPLIT = re.compile(r"\s+\+\s+|\s*\+\s*(?=[A-ZÁÉÍÓÚÑ0-9])|\s+&\s+(?=.*\+)|\s+y\s+(?=.*\+)|\s*,\s+(?=.*\+)")


def split_artistas(texto: str) -> tuple[str, list[str]]:
    """Separa 'A + B + C' en artista principal e invitados (solo con el separador '+' que usa la fuente)."""
    texto = clean(texto)
    if "+" not in texto:
        return texto, []
    parts = [clean(p) for p in re.split(r"\s*\+\s*", texto) if clean(p)]
    if not parts:
        return texto, []
    return parts[0], parts[1:]


COUNTRY_TAG = re.compile(r"\s*\(([A-Za-zÁÉÍÓÚáéíóúñÑ .]{2,20})\)\s*$")
PAISES_ES = {"eeuu": "US", "ee uu": "US", "usa": "US", "estados unidos": "US", "reino unido": "GB", "uk": "GB",
             "inglaterra": "GB", "escocia": "GB", "gales": "GB", "irlanda": "IE", "suecia": "SE", "noruega": "NO",
             "finlandia": "FI", "dinamarca": "DK", "alemania": "DE", "francia": "FR", "italia": "IT",
             "paises bajos": "NL", "holanda": "NL", "belgica": "BE", "suiza": "CH", "austria": "AT",
             "portugal": "PT", "grecia": "GR", "polonia": "PL", "japon": "JP", "canada": "CA", "australia": "AU",
             "nueva zelanda": "NZ", "argentina": "AR", "mexico": "MX", "chile": "CL", "colombia": "CO",
             "brasil": "BR", "uruguay": "UY", "cuba": "CU", "islandia": "IS", "rusia": "RU", "ucrania": "UA",
             "hungria": "HU", "republica checa": "CZ", "chequia": "CZ", "israel": "IL", "turquia": "TR",
             "sudafrica": "ZA", "corea del sur": "KR", "estonia": "EE", "letonia": "LV", "lituania": "LT",
             "eslovenia": "SI", "croacia": "HR", "serbia": "RS", "rumania": "RO", "bulgaria": "BG", "espana": "ES"}
ISO_FIX = {"UK": "GB", "USA": "US", "EEUU": "US", "ENG": "GB", "ING": "GB", "SUE": "SE", "ALE": "DE", "FRA": "FR",
           "ITA": "IT", "HOL": "NL", "BEL": "BE", "SUI": "CH", "NOR": "NO", "DIN": "DK", "FIN": "FI", "AUS": "AU",
           "CAN": "CA", "ARG": "AR", "MEX": "MX", "ESP": "ES", "POR": "PT", "IRL": "IE", "JPN": "JP", "JAP": "JP",
           "BRA": "BR", "CHI": "CL", "COL": "CO", "GRE": "GR", "POL": "PL", "RUS": "RU", "AUT": "AT", "EUA": "US"}
ISO2 = set("AD AE AR AT AU BE BG BR CA CH CL CN CO CU CZ DE DK EE ES FI FR GB GR HR HU IE IL IN IS IT JP KR LT LU LV MA MX NL NO NZ PE PL PT RO RS RU SE SI SK TR UA US UY VE ZA".split())


def extrae_pais(nombre: str) -> tuple[str, str | None]:
    """'Samm (BE)' → ('Samm', 'BE'). Solo si la propia fuente pone el código de país entre paréntesis."""
    m = COUNTRY_TAG.search(nombre or "")
    if not m:
        return nombre, None
    raw = m.group(1)
    code = PAISES_ES.get(norm(raw))
    if not code and len(raw) <= 3:
        code = ISO_FIX.get(raw.upper(), raw.upper())
    if code in ISO2:
        return clean(nombre[: m.start()]), code
    return nombre, None


def cabeza(nombre: str) -> str:
    """Parte principal del nombre para comparar ('Hällas - Gira 2026' → 'hallas')."""
    n = norm(nombre)
    n = re.split(r"\b(presenta|presentan|presentando|en concierto|tour|gira|live in|en madrid|world tour)\b", n)[0]
    return n.strip()


_CORTES = re.compile(r"\s*(?:[.:|–—]|\s-\s|\bby\b|\bpresenta(?:n|ndo)?\b|\bcon\b|\ben concierto\b|\+)\s*", re.I)


def variantes(nombre: str) -> set[str]:
    """Formas del nombre para comparar: completo, cabeza y trozos separados por '.', ':', '–', 'by'..."""
    out = {norm(nombre), cabeza(nombre)}
    for p in _CORTES.split(nombre or ""):
        n = norm(p)
        if len(n) >= 4:
            out.add(n)
    return {x for x in out if x}


def contiene(corto: str, largo: str) -> bool:
    """True si la secuencia de palabras 'corto' aparece completa dentro de 'largo'."""
    if len(corto) < 4 or corto == largo:
        return corto == largo and bool(corto)
    return f" {corto} " in f" {largo} "


def parecido_flexible(a: str, b: str) -> float:
    """Para comparar dentro de la misma fecha y sala: admite prefijos de ciclo y subtítulos
    ('Las Noches de Río Babel. Los Vinagres' ~ 'LOS VINAGRES', 'Aciz – Soul Castizo' ~ 'Aciz')."""
    r = parecido(a, b)
    if r >= 90:
        return r
    va, vb = variantes(a), variantes(b)
    for x in va:
        for y in vb:
            if len(x) >= 4 and len(y) >= 4 and fuzz.ratio(x, y) >= 90:
                return 90.0
    na, nb = norm(a), norm(b)
    corto, largo = sorted((na, nb), key=len)
    if contiene(corto, largo) and len(corto.replace(" ", "")) >= 5:
        return 90.0
    return r


def parecido(a: str, b: str) -> float:
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    r = fuzz.ratio(na, nb)
    ha, hb = cabeza(a), cabeza(b)
    if ha and hb:
        r = max(r, fuzz.ratio(ha, hb))
    # "Deep Purple" vs "Deep Purple + Jayler" / "Hällas. Tour" : prefijo completo de otra
    short, long_ = sorted((na, nb), key=len)
    if len(short) >= 5 and long_.startswith(short + " ") and len(short) / len(long_) >= 0.35:
        r = max(r, 90.0)
    return r


GENERICOS = {norm(x) for x in [
    "concierto de blues", "concierto de jazz", "jam session", "jam session blues", "blues jam session",
    "concierto de versiones", "open mic", "after church open mic", "the fucking jam", "sesion dj",
    "concierto", "conciertos", "candlelight", "tributo", "fiesta", "karaoke"]}


_RELLENO = re.compile(
    r"^(y |mas |\+ )?((artistas?|bandas?|grupos?|dj s?) )?(invitad[oa]s?|sorpresa|por (confirmar|anunciar|determinar)|tba)"
    r"( especiales?| sorpresa| por confirmar)?$"
    r"|^(y |\+ )?mas( artistas| bandas| grupos| invitados| sorpresas)?$"
    r"|^(y |\+ )?(muchos|otros) mas$|^y otros$|^etc$|^djs?$|^dj set$"
    r"|\boferta\b|\bentradas?\b|\bdescuento\b|\bpromocion\b")


def es_relleno(nombre: str) -> bool:
    """Textos que las fuentes ponen en el cartel pero no son artistas: 'invitados especiales', 'y más',
    'banda invitada', 'por confirmar', 'DJ', ofertas de entradas…"""
    return bool(_RELLENO.search(norm(nombre)))


def es_generico(nombre: str) -> bool:
    n = norm(nombre)
    return n in GENERICOS or len(n) < 3
