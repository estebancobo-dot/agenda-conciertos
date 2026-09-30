"""País de origen leído en un texto que habla del artista: la página del concierto en la agenda, el perfil de
Discogs o la biografía de Last.fm.

Solo frases explícitas y sin ambigüedad: "la banda madrileña X", "el cantautor argentino", "procedentes de
Glasgow", "Spanish rock band from Bilbao", "X is an American singer". Si el texto da más de un país (una gira
con teloneros de varios sitios, "hispano-argentina"…), no se decide nada. Nunca se deduce del idioma ni del
nombre.

sin_artista(titulo): jam sessions, micros abiertos, karaoke o "Concierto de blues": no hay un artista del que
buscar el origen (como en los espectáculos, el origen no aplica).
"""
from __future__ import annotations

import re

from .normalize import norm

# gentilicios en español (forma normalizada, sin tildes; masculino/femenino/plural) y en inglés
_GENT_ES = {
    "espanol": "ES", "espanola": "ES", "espanoles": "ES", "espanolas": "ES",
    "madrileno": "ES", "madrilena": "ES", "madrilenos": "ES", "madrilenas": "ES",
    "barcelones": "ES", "barcelonesa": "ES", "barceloneses": "ES", "catalan": "ES", "catalana": "ES",
    "catalanes": "ES", "vasco": "ES", "vasca": "ES", "vascos": "ES", "gallego": "ES", "gallega": "ES",
    "gallegos": "ES", "andaluz": "ES", "andaluza": "ES", "andaluces": "ES", "asturiano": "ES", "asturiana": "ES",
    "asturianos": "ES", "valenciano": "ES", "valenciana": "ES", "valencianos": "ES", "canario": "ES",
    "canaria": "ES", "canarios": "ES", "sevillano": "ES", "sevillana": "ES", "sevillanos": "ES",
    "gaditano": "ES", "gaditana": "ES", "granadino": "ES", "granadina": "ES", "malagueno": "ES", "malaguena": "ES",
    "bilbaino": "ES", "bilbaina": "ES", "zaragozano": "ES", "zaragozana": "ES", "murciano": "ES", "murciana": "ES",
    "extremeno": "ES", "extremena": "ES", "aragones": "ES", "aragonesa": "ES", "navarro": "ES", "navarra": "ES",
    "cantabro": "ES", "cantabra": "ES", "manchego": "ES", "manchega": "ES", "castellano": "ES", "castellana": "ES",
    "alcalaino": "ES", "alcalaina": "ES", "mostoleno": "ES", "getafense": "ES", "leganense": "ES",
    "argentino": "AR", "argentina": "AR", "argentinos": "AR", "argentinas": "AR", "porteno": "AR", "portena": "AR",
    "mexicano": "MX", "mexicana": "MX", "mexicanos": "MX", "chileno": "CL", "chilena": "CL", "chilenos": "CL",
    "colombiano": "CO", "colombiana": "CO", "colombianos": "CO", "uruguayo": "UY", "uruguaya": "UY",
    "peruano": "PE", "peruana": "PE", "venezolano": "VE", "venezolana": "VE", "cubano": "CU", "cubana": "CU",
    "cubanos": "CU", "brasileno": "BR", "brasilena": "BR", "brasilenos": "BR", "portugues": "PT",
    "portuguesa": "PT", "portugueses": "PT", "estadounidense": "US", "estadounidenses": "US",
    "norteamericano": "US", "norteamericana": "US", "norteamericanos": "US", "neoyorquino": "US",
    "neoyorquina": "US", "canadiense": "CA", "canadienses": "CA", "britanico": "GB", "britanica": "GB",
    "britanicos": "GB", "ingles": "GB", "inglesa": "GB", "ingleses": "GB", "escoces": "GB", "escocesa": "GB",
    "escoceses": "GB", "gales": "GB", "galesa": "GB", "irlandes": "IE", "irlandesa": "IE", "irlandeses": "IE", "frances": "FR",
    "francesa": "FR", "franceses": "FR", "italiano": "IT", "italiana": "IT", "italianos": "IT", "aleman": "DE",
    "alemana": "DE", "alemanes": "DE", "sueco": "SE", "sueca": "SE", "suecos": "SE", "noruego": "NO",
    "noruega": "NO", "noruegos": "NO", "finlandes": "FI", "finlandesa": "FI", "finlandeses": "FI", "danes": "DK",
    "danesa": "DK", "daneses": "DK", "holandes": "NL", "holandesa": "NL", "holandeses": "NL", "neerlandes": "NL",
    "belga": "BE", "belgas": "BE", "suizo": "CH", "suiza": "CH", "suizos": "CH", "austriaco": "AT",
    "austriaca": "AT", "griego": "GR", "griega": "GR", "griegos": "GR", "polaco": "PL", "polaca": "PL",
    "ruso": "RU", "rusa": "RU", "rusos": "RU", "ucraniano": "UA", "ucraniana": "UA", "japones": "JP",
    "japonesa": "JP", "japoneses": "JP", "australiano": "AU", "australiana": "AU", "australianos": "AU",
    "islandes": "IS", "islandesa": "IS", "israeli": "IL", "turco": "TR", "turca": "TR", "senegales": "SN",
    "senegalesa": "SN", "maliense": "ML", "marroqui": "MA", "sudafricano": "ZA", "sudafricana": "ZA",
    "neozelandes": "NZ", "neozelandesa": "NZ", "checo": "CZ", "checa": "CZ", "hungaro": "HU", "hungara": "HU",
}
_GENT_EN = {
    "spanish": "ES", "argentinian": "AR", "argentine": "AR", "mexican": "MX", "chilean": "CL", "colombian": "CO",
    "uruguayan": "UY", "peruvian": "PE", "venezuelan": "VE", "cuban": "CU", "brazilian": "BR", "portuguese": "PT",
    "american": "US", "canadian": "CA", "british": "GB", "english": "GB", "scottish": "GB", "welsh": "GB",
    "irish": "IE", "french": "FR", "italian": "IT", "german": "DE", "swedish": "SE", "norwegian": "NO",
    "finnish": "FI", "danish": "DK", "dutch": "NL", "belgian": "BE", "swiss": "CH", "austrian": "AT",
    "greek": "GR", "polish": "PL", "russian": "RU", "ukrainian": "UA", "japanese": "JP", "australian": "AU",
    "icelandic": "IS", "israeli": "IL", "turkish": "TR", "senegalese": "SN", "malian": "ML", "moroccan": "MA",
    "south african": "ZA", "new zealand": "NZ", "czech": "CZ", "hungarian": "HU",
}
# qué es el artista: el gentilicio tiene que ir pegado a una de estas palabras ("la banda madrileña", "el
# cantautor argentino", "Spanish rock band"), no suelto ("cocina italiana", "la escena madrileña")
_QUIEN_ES = (r"banda|grupo|formaci[oó]n|conjunto|orquesta|big band|combo|cantante|cantautora?|cantaora?|artista|"
             r"m[uú]sic[oa]|compositora?|productora?|rapera?|trapera?|dj|pianista|guitarrista|bater[ií]a|saxofonista|"
             r"trompetista|violinista|bajista|vocalista|int[eé]rprete|d[uú]o|tr[ií]o|cuarteto|quinteto|sexteto|"
             r"septeto|colectivo|proyecto|solista|bandas|grupos|m[uú]sicos|artistas")
_QUIEN_EN = (r"band|group|singer|songwriter|singer-songwriter|artist|musician|composer|producer|rapper|dj|duo|trio|"
             r"quartet|quintet|outfit|act|collective|project|pianist|guitarist|orchestra|ensemble|combo|"
             r"(?:[a-z&'-]+ ){0,3}(?:band|group|singer|act|outfit|duo|trio|artist|musician|project)")
_ES_ANTES = re.compile(rf"\b(?:{_QUIEN_ES})\s+(?:de\s+)?(?:[a-z&-]+\s+){{0,2}}?({'|'.join(sorted(_GENT_ES, key=len, reverse=True))})\b")
_QUIEN = re.compile(rf"\b(?:{_QUIEN_ES}|{_QUIEN_EN})\b", re.I)
_EN_ANTES = re.compile(rf"\b({'|'.join(sorted(_GENT_EN, key=len, reverse=True))})\s+(?:[a-z&'-]+\s+){{0,3}}?(?:{_QUIEN_EN})\b")
# "procedentes de Glasgow", "originaria de Bogotá", "nacido en Rosario", "from Bilbao, Spain". Dónde vive o
# está afincado no es su origen ("banda británica afincada en Madrid"): no cuenta
_LUGAR = re.compile(r"\b(?:procedentes? de|originari[oa]s? de|nacid[oa]s? en|natural(?:es)? de|"
                    r"llegad[oa]s? (?:desde|de)|venid[oa]s? (?:desde|de)|desde (?:la ciudad de )?"
                    r"(?=[A-ZÁÉÍÓÚ])|from|hailing from|born in)\s+([^.;:!?()\n]{2,60})")
_SIN_ARTISTA = re.compile(
    r"^\s*(jam session|jam( de [\w ]+)?$|open mic|micro abierto|karaoke|concierto de (blues|jazz|rock|"
    r"flamenco|soul|swing|musica)$|sesion (de )?dj|dj set|noche de (jazz|blues|swing|rock)$|musica en directo|"
    r"live music|concierto sorpresa|actuacion sorpresa|concierto benefico|ensayo abierto)\b")


def sin_artista(titulo: str) -> bool:
    """El título no es un artista: jam sessions, micro abierto, karaoke, "Concierto de blues"…"""
    t = norm(titulo or "")
    return bool(_SIN_ARTISTA.match(t) or re.search(r"\b(jam session|open mic|micro abierto|karaoke)\b", t)
                or re.search(r"\bjam\s*!", (titulo or "").lower()))


def _frases(texto: str) -> list[str]:
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+|\n+", texto or "") if len(f.strip()) > 10]


def paises_en_frase(frase: str) -> set[str]:
    """Países que la frase atribuye a alguien de forma explícita."""
    from .artistas import pais_de_texto
    out: set[str] = set()
    n = norm(frase)
    for m in _ES_ANTES.finditer(n):
        p = _GENT_ES.get(m.group(1))
        if p:
            out.add(p)
    for m in _EN_ANTES.finditer(frase.lower()):
        out.add(_GENT_EN[m.group(1)])
    for m in _LUGAR.finditer(frase) if _QUIEN.search(frase) else ():  # "Live from Madrid" no dice de dónde es nadie
        lugar = re.split(r"\s+(?:y|and|con|with|que|who|para|a|en|in|el|la|los|las|the)\s+", m.group(1))[0]
        p = pais_de_texto(lugar) or pais_de_texto(lugar.split(",")[-1])
        if p:
            out.add(p)
    return out


def pais_en_texto(texto: str, nombre: str | None = None, solo_con_nombre: bool = True) -> tuple[str | None, str]:
    """(país, frase) si el texto dice de dónde es el artista y solo da un país; (None, "") si no.

    Con `nombre`, solo cuentan las frases que lo mencionan (una página de agenda puede hablar de varios
    artistas); `solo_con_nombre=False` es para textos que ya son del artista (perfil de Discogs, biografía)."""
    clave = norm(nombre or "")
    halladas: list[tuple[str, str]] = []
    for f in _frases(texto):
        if nombre and solo_con_nombre and clave and clave not in norm(f):
            continue
        for p in paises_en_frase(f):
            halladas.append((p, f))
    paises = {p for p, _ in halladas}
    if len(paises) != 1:
        return None, ""
    return halladas[0][0], halladas[0][1][:220]
