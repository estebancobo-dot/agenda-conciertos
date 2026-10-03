"""Nombre del artista para buscar su ficha, a partir del título que da la agenda.

Las agendas mezclan en el título el nombre del artista con el del ciclo, festival o gira ("Fiestas de Boadilla
del Monte 2026. Siloé", "JAZZ CON SABOR A CLUB 26: P.H.A.T. (ITALIA) (Festival JazzMadrid)", "THE SILENCERS (UK)
en Madrid - CAMBIA A NAZCA") o con varios artistas ("LA BANDA EN OBRAS & MC CLAN"). Buscado tal cual, ninguna web
de música lo encuentra y el concierto se queda sin estilo ni origen.

claves_ficha(r) da los nombres a probar, en orden: el título limpio y, si son varios artistas, el primero (el
cabeza de cartel). pais_del_titulo(r) lee el país que a veces pone la propia agenda entre paréntesis: "(UK)",
"(USA)", "(ITALIA)"… Nada se deduce: o lo dice la agenda o lo dice una web de música.
"""
from __future__ import annotations

import re

from .normalize import clean, norm

# partes del título que son ciclo, festival, gira o aviso, no el artista
_NO_ARTISTA = re.compile(
    r"\b(fiestas?|festival|fest|ciclo|jazz con sabor|noches?|temporada|presenta|gira|tour|en concierto|"
    r"aniversario|aniv|concierto|sesion|live|world tour|jazzmadrid|inverfest|radar joven|cambia a|nueva fecha|"
    r"aplazado|entradas|sold out|agotad[oa]s?|brunch|halloween|especial|hispanidad|navidad|espectaculo|tardeo|"
    r"certamen|clausura|inaugural|musica|musica antigua|dia de la|homenaje|[ivxlc]+ edicion)\b|^[ivxlc]{2,}\b")
# formación detrás del nombre: "INOIDEL GONZÁLEZ QUARTET" se busca también como "INOIDEL GONZÁLEZ"
_FORMACION = re.compile(r"(?i)\s+(?:quartet|quintet|sextet|trio|tr[ií]o|cuarteto|quinteto|sexteto|group|ensemble|"
                        r"orquesta|big band|combo)$")
_PAIS_TIT = {
    "usa": "US", "us": "US", "eeuu": "US", "ee uu": "US", "estados unidos": "US", "uk": "GB", "gb": "GB",
    "reino unido": "GB", "inglaterra": "GB", "escocia": "GB", "gales": "GB", "irlanda": "IE", "ie": "IE",
    "fr": "FR", "francia": "FR", "it": "IT", "ita": "IT", "italia": "IT", "de": "DE", "alemania": "DE",
    "ger": "DE", "ar": "AR", "arg": "AR", "argentina": "AR", "mx": "MX", "mex": "MX", "mexico": "MX",
    "cl": "CL", "chile": "CL", "co": "CO", "colombia": "CO", "br": "BR", "brasil": "BR", "pt": "PT",
    "portugal": "PT", "se": "SE", "suecia": "SE", "swe": "SE", "no": "NO", "noruega": "NO", "nor": "NO",
    "fi": "FI", "fin": "FI", "finlandia": "FI", "dk": "DK", "dinamarca": "DK", "nl": "NL", "holanda": "NL",
    "paises bajos": "NL", "be": "BE", "belgica": "BE", "ch": "CH", "suiza": "CH", "at": "AT", "austria": "AT",
    "ca": "CA", "can": "CA", "canada": "CA", "au": "AU", "aus": "AU", "australia": "AU", "jp": "JP",
    "japon": "JP", "gr": "GR", "grecia": "GR", "pl": "PL", "polonia": "PL", "cu": "CU", "cuba": "CU",
    "uy": "UY", "uruguay": "UY", "pe": "PE", "peru": "PE", "ve": "VE", "venezuela": "VE", "es": "ES",
    "esp": "ES", "espana": "ES", "is": "IS", "islandia": "IS", "nz": "NZ", "nueva zelanda": "NZ",
    "za": "ZA", "sudafrica": "ZA", "il": "IL", "israel": "IL", "tr": "TR", "turquia": "TR", "ru": "RU",
    "rusia": "RU", "ua": "UA", "ucrania": "UA", "cz": "CZ", "republica checa": "CZ", "hu": "HU", "hungria": "HU",
}
_TRIBUTO = re.compile(r"\b(tributo|tribute|trib|homenaje|versiones|covers?|musica de|revival band|the music of)\b")
_PARENTESIS = re.compile(r"\(([^()]{2,22})\)")
_VARIOS = re.compile(r"\s+(?:&|\+|y|and|con|feat\.?|ft\.?|x|vs\.?)\s+|\s*,\s+|\s*/\s*", re.I)


def pais_del_titulo(titulo: str) -> str | None:
    """País que la agenda pone entre paréntesis en el título ("THE SILENCERS (UK)"). Solo si hay uno."""
    paises = {_PAIS_TIT[norm(m)] for m in _PARENTESIS.findall(titulo or "") if norm(m) in _PAIS_TIT}
    return paises.pop() if len(paises) == 1 else None


def _limpio(titulo: str) -> list[str]:
    t = _PARENTESIS.sub(" ", titulo or "")           # "(UK)", "(Festival JazzMadrid)", "(Muse Tribute)"…
    t = re.sub(r"(?i)\s+en madrid\b", "", t)          # "… en Madrid - 2026"
    t = re.sub(r"(?i)\s+\d+\s*[º°]?\s*aniversario\b.*$|\s+(?:gira|tour)\b.*$", "", t)  # "ACCEPT 50º ANIVERSARIO"
    # trozos separados por ". ", ": ", " - ", " – ", " | ": se queda el que no es ciclo, festival, gira ni aviso
    t = re.sub(r"^\s*[A-ZÁÉÍÓÚÑ]{3,}!\s+", "", t)    # "HALLOWEEN! FRUIT TONES"
    trozos = [clean(x) for x in re.split(r"\s*[:|]\s+|\.\s+|\s+[-–—]\s+", t) if clean(x)]
    # "'Apolo Brass', presenta 'Aires de América'": el artista es lo de antes de "presenta"
    trozos = [clean(re.split(r"(?i)\s*,?\s+presenta\w*\b", x)[0]).strip(" '\"«»“”‘’,") or x for x in trozos]
    buenos = [x for x in trozos if not _NO_ARTISTA.search(norm(x)) and not re.fullmatch(r"\d{2,4}", x)]
    return buenos or [clean(t)]


def claves_ficha(r: dict) -> list[str]:
    """Nombres con los que buscar la ficha del artista, del más fiable al menos."""
    titulo = r.get("artista") or ""
    if r.get("festival"):
        return []  # el nombre de un festival no es un artista: su estilo sale de su cartel y de las agendas
    out = [titulo]
    from .clasificar import titulo_fuera_de_foco
    if _TRIBUTO.search(norm(titulo)) or "tributos y versiones" in (r.get("categorias") or []) or \
            re.search(r"(?i)candlelight", titulo):
        # una banda tributo no es el artista homenajeado, y un Candlelight "Queen vs. ABBA" no es Queen ni ABBA:
        # solo su propio nombre
        return out
    if titulo_fuera_de_foco(titulo):
        # "ESPECTÁCULO FLAMENCO: CLAUDIA CRUZ": el intérprete sí se busca, no el título entero
        from .artistas import nombre_en_titulo
        n = re.sub(r"(?i)\s+al baile$", "", nombre_en_titulo(titulo)).strip()
        partes = [p for p in _VARIOS.split(n) if len(norm(p)) >= 4]
        return [titulo] + [x for x in dict.fromkeys([n] + partes[:1]) if norm(x) != norm(titulo)]
    limpios = _limpio(titulo)[:2]
    out += limpios
    partes = [p for p in _VARIOS.split(limpios[0]) if len(norm(p)) >= 3] if limpios else []
    if re.search(r"(?i)\by sus?\b", limpios[0] if limpios else ""):
        partes = []  # "PEPE Y SU TUMBAO" es un solo nombre: "PEPE" a secas sería otro
    if len(partes) > 1:
        out.append(partes[0])  # cabeza de cartel
    for x in list(out[1:] or out):
        sin = _FORMACION.sub("", re.sub(r"[’']s$", "", x)).strip()
        if sin and len(norm(sin)) >= 4 and norm(sin) != norm(x):
            out.append(sin)
    vistos, unicos = set(), []
    for x in out:
        if norm(x) and norm(x) not in vistos:
            vistos.add(norm(x))
            unicos.append(x)
    return unicos


_HOMENAJE = [
    re.compile(r"\b(?:tributo|homenaje|tribute)\s+(?:a|al|to|de)\s+(.+)$", re.I),
    re.compile(r"\btrib\.?\s+(?:a\s+)?(.+?)\)?$", re.I),
    re.compile(r"^(?:the\s+)?(.+?)(?:\s+the)?\s+(?:tribute|tributo)(?:\s+(?:band|show|banda))?$", re.I),
    re.compile(r"\b(?:tributo|tribute)\s+(.+)$", re.I),
    re.compile(r"\b(?:the music of|la musica de|lo mejor de)\s+(.+)$", re.I),
]
_NO_HOMENAJEADO = {"band", "banda", "festival", "fest", "show", "night", "noche", "concierto", "concert", "party",
                   "fiesta", "night live", "rock", "metal", "pop", "bands", "bandas"}


def homenajeado(titulo: str) -> str | None:
    """Artista al que homenajea un tributo: "THE RUMORS: TRIBUTO FLEETWOOD MAC" → "FLEETWOOD MAC", "LA VAN GOGH
    (TRIB. LA OREJA DE VAN GOGH)" → "LA OREJA DE VAN GOGH", "Queen Tribute Band" → "Queen". None si no lo dice."""
    if not _TRIBUTO.search(norm(titulo or "")):
        return None
    t = re.sub(r"\.\s*candlelight.*$", "", titulo or "", flags=re.I)
    t = re.sub(r"\btrib\.\s*", "tributo ", t, flags=re.I)  # "(TRIB. LA OREJA DE VAN GOGH)"
    trozos = [x.strip(" .:-–\"'«»") for x in re.split(r"[()]|\s*[:|]\s+|\s+[-–—]\s+|\.\s+", t) if x and x.strip()]
    for parte in [x for x in trozos if _TRIBUTO.search(norm(x))]:
        for rx in _HOMENAJE:
            m = rx.search(parte)
            if m:
                x = re.split(r"\s*,\s+|\s+(?:en|el|por|con)\s+(?=[a-záéíóú])", m.group(1).strip(" .:-–\"'«»()"))[0].strip()
                if len(norm(x)) >= 3 and not _TRIBUTO.search(norm(x)) and norm(x) not in _NO_HOMENAJEADO:
                    return x
    return None
