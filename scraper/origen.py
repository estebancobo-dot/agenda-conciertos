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
_QUIEN_ES = (r"soprano|tenor|baritono|mezzosoprano|contralto|directora?|violonchelista|contrabajista|percusionista|"
             r"banda|grupo|formaci[oó]n|conjunto|orquesta|big band|combo|cantante|cantautora?|cantaora?|artista|"
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


_GENT_RE = "|".join(sorted((k for k, v in _GENT_ES.items() if v), key=len, reverse=True))
_TRAS_NOMBRE = re.compile(rf"^\s*,?\s*(?:\([^)]*\)\s*)?(?:es|son|fue|era|eran|,)?\s*(?:un|una|unos|el|la|los|las)?\s*"
                          rf"(?:{_QUIEN_ES})\s+(?:de\s+)?(?:[a-z&-]+\s+){{0,2}}?({_GENT_RE})\b")
_ANTES_NOMBRE = re.compile(rf"\b(?:{_QUIEN_ES})\s+(?:y\s+[a-z]+\s+)?(?:de\s+[a-z&-]+\s+)?({_GENT_RE})\s*(?:de\s+[a-z]+\s*)?"
                           rf"(?:,?\s*(?:mas\s+)?(?:conocid[oa]s?\s+como|alias|llamad[oa]))?,?\s*$")


def paises_junto_al_nombre(frase: str, clave: str) -> set[str]:
    """Países dichos del artista en su misma frase y pegados a su nombre (texto normalizado)."""
    n = norm(frase)
    out: set[str] = set()
    # palabra entera: "martin" no es "martinez"
    for m in re.finditer(rf"(?<![a-z0-9]){re.escape(clave)}(?![a-z0-9])", n) if clave else ():
        i = m.start()
        despues, antes = n[i + len(clave):i + len(clave) + 120], n[max(0, i - 80):i]
        m = _TRAS_NOMBRE.match(despues)
        if m:
            out.add(_GENT_ES[m.group(1)])
        m = _ANTES_NOMBRE.search(antes)
        if m:
            out.add(_GENT_ES[m.group(1)])
        # "Compro Oro nace en Almería", "Thee Nameshakes, procedentes de Glasgow": lugar justo detrás del nombre
        trozo = frase[len(frase) - len(frase.lstrip()):]  # el lugar se lee en el texto original (mayúsculas)
        j = norm(trozo).find(clave)
        if j >= 0:
            from .artistas import pais_de_texto
            m = re.match(r"^[^.;:]{0,60}?\b(?:nace en|nacid[oa]s? en|naci[oó] en|procedentes? de|originari[oa]s? de|"
                         r"natural(?:es)? de|surgid[oa]s? en|formad[oa]s? en|fundad[oa]s? en)\s+([^.;:()\n]{2,60})",
                         trozo[j + len(clave):], re.I)
            if m:
                lugar = re.split(r"\s+(?:y|en|a|con|que|para|el|la|los|las|desde)\s+|,\s*(?=[a-záéíóú])", m.group(1))[0]
                p = pais_de_texto(lugar) or pais_de_texto(lugar.split(",")[-1])
                if p:
                    out.add(p)
    return out


_UNION = {"de", "del", "la", "las", "el", "los", "y", "e", "of", "the", "and", "&", "van", "von", "da", "do", "dos",
          "di", "le", "les", "du"}


def _mayuscula(t: str) -> bool:
    return t[:1].isupper() or t[:1].isdigit()


def nombre_completo_en(frase: str, nombre: str) -> bool:
    """El nombre sale en la frase como nombre propio completo, no como parte de otro: "Megara es un grupo" sí;
    "Diego Martín" (para "Martin"), "Mariah Carey" (para "Carey"), "acid jazz" (para "Jazz"), "Kraak & Smaak" (para
    "Kraak") o "Los Hijos de la Profecía" (para "Profecía") no. Para frases de webs generales (Wikipedia), donde
    un nombre corto aparece en frases de otros artistas."""
    partes = norm(nombre).split()
    if not partes:
        return False
    import html
    frase = html.unescape(frase)  # "Kraak &amp; Smaak"
    toks = re.findall(r"[^\W_]+(?:['’][^\W_]+)*|&|[^\w\s]", frase)
    nt = [norm(t) if re.match(r"[^\W_]", t) else ("and" if t == "&" else None) for t in toks]
    k = len(partes)

    def pegado(desde: int, paso: int) -> bool:
        """¿Hay otra palabra con mayúscula pegada (directamente o tras "de", "la", "&"…)?"""
        j, unido = desde, False
        # "de", "la", "&" y comillas ("Pablo “Tito” Rodríguez") unen el nombre con lo de al lado
        while 0 <= j < len(toks) and ((nt[j] in _UNION and not _mayuscula(toks[j])) or toks[j] in "“”\"«»‘’'"):
            j += paso
            unido = True
        if j < 0 and unido and frase[:1].islower():
            return True  # el extracto empieza a mitad de nombre: "…de la Profecía) fue una banda"
        return 0 <= j < len(toks) and bool(nt[j]) and _mayuscula(toks[j])

    for i in range(len(toks) - k + 1):
        if nt[i:i + k] == partes and _mayuscula(toks[i]) and not pegado(i - 1, -1) and not pegado(i + k, 1):
            return True
    return False


def pais_en_texto(texto: str, nombre: str | None = None, solo_con_nombre: bool = True) -> tuple[str | None, str]:
    """(país, frase) si el texto dice de dónde es el artista y solo da un país; (None, "") si no.

    Con `nombre`, solo cuentan las frases que lo mencionan (una página de agenda puede hablar de varios
    artistas); `solo_con_nombre=False` es para textos que ya son del artista (perfil de Discogs, biografía)."""
    clave = norm(nombre or "")
    halladas: list[tuple[str, str]] = []
    for f in _frases(texto):
        if nombre and solo_con_nombre and clave:
            if clave not in norm(f):
                continue
            # en una página de agenda el gentilicio tiene que ir pegado al nombre: "Mala Luna Band es un grupo
            # madrileño", "la banda madrileña Sho-Hai". "Alchemy Project ... la banda inglesa" (Dire Straits, el
            # grupo homenajeado) no dice de dónde es Alchemy Project
            for p in paises_junto_al_nombre(f, clave):
                halladas.append((p, f))
            continue
        for p in paises_en_frase(f):
            halladas.append((p, f))
    paises = {p for p, _ in halladas}
    if len(paises) != 1:
        return None, ""
    return halladas[0][0], halladas[0][1][:220]


# ------------------------------------------------------------------ estilo dicho en la página del concierto
def _vocabulario() -> list[str]:
    """Estilos y géneros que se reconocen en un texto (los de la taxonomía, sus sinónimos y las palabras clave
    de las etiquetas de agenda), del más largo al más corto para quedarse con "rock alternativo" antes que
    "rock"."""
    from .normalize import load_json
    t, m = load_json("taxonomia.json"), load_json("estilos_map.json")
    voc = {norm(e) for estilos in t["generos"].values() for e in estilos}
    voc |= {norm(k) for k in t.get("sinonimos", {})} | {norm(k) for k in t.get("sinonimos_genero", {})}
    voc |= {norm(k) for k, _ in m["palabras_clave"]}
    voc -= {"club", "dj", "afro", "heavy", "jam", "roots", "oi", "vocal", "instrumental", "experimental", "modern",
            "contemporary", "theme", "score", "beat", "mod", "musical", "teatro", "coro", "rap", "son", "disco"}
    return sorted((v for v in voc if len(v) >= 3), key=len, reverse=True)


_VOC: list[str] | None = None
_TRAS_ESTILO = re.compile(rf"^\s*,?\s*(?:\([^)]*\)\s*)?(?:es|son|fue|era|,)?\s*(?:un|una|unos|el|la|los|las)?\s*"
                          rf"(?:{_QUIEN_ES})\s+(?:de\s+|del\s+)?([^.;:!?()]{{2,70}})")
_ANTES_ESTILO = re.compile(rf"\b(?:{_QUIEN_ES})\s+(?:de\s+|del\s+)?([^.;:!?()]{{2,50}}?)\s*,?\s*$")
_EN_ESTILO = re.compile(r"\b((?:[a-z&'-]+\s+){1,3})(?:band|group|outfit|act|duo|trio|singer|artist|project)\b")


def estilos_en_texto(texto: str, nombre: str) -> list[str]:
    """Estilos que la página del concierto dice del artista, pegados a su nombre: "X es una banda de rock
    alternativo y power pop", "el grupo de soul X", "X, a garage rock band". Sin nombre no se lee nada."""
    global _VOC
    if _VOC is None:
        _VOC = _vocabulario()
    clave = norm(nombre or "")
    if not clave:
        return []
    out: list[str] = []

    def terminos(trozo: str):
        t = f" {trozo} "
        for v in _VOC:
            if f" {v} " in t and v not in out and not any(v in o for o in out):
                out.append(v)
                t = t.replace(f" {v} ", " | ")

    # "JOSH MEADER TRIO (Jazz-Fusión / 21:00 horas / Entrada 16 €)", "Clarence Bekker Band (Soul & Funk)": el
    # estilo entre paréntesis detrás del nombre, como lo ponen muchas salas en su programación
    for linea in (texto or "").split("\n"):
        nl = norm(linea)
        j = nl.find(clave)
        if j >= 0:
            m = re.search(r"\(([^()]{3,90})\)", linea[j:j + len(clave) + 120] if len(nl) == len(linea) else linea)
            if m:
                terminos(norm(m.group(1).split("/")[0]))
    sujeto = False
    for f in _frases(texto):
        n = norm(f)
        # "miaw es un dúo de pop experimental …. Su música … shoegaze, trip-hop": la frase (y la siguiente si
        # habla de "su música") son del artista
        if re.match(rf"^(?:el|la|los|las)?\s*{re.escape(clave)}\s+(?:es|son|fue|era|eran)\b", n):
            terminos(n[len(clave):])
            sujeto = True
        elif sujeto and re.match(r"^su (?:musica|sonido|propuesta|estilo|directo)\b", n):
            terminos(n)
        else:
            sujeto = False
        i = n.find(clave)
        while i >= 0:
            despues, antes = n[i + len(clave):i + len(clave) + 140], n[max(0, i - 90):i]
            m = _TRAS_ESTILO.match(despues)
            if m:
                terminos(m.group(1))
            m = _ANTES_ESTILO.search(antes)
            if m:
                terminos(m.group(1))
            m = _EN_ESTILO.search(despues[:60])
            if m and re.match(r"^\s*,?\s*(?:is|are|was)?\s*(?:a|an|the)?\s*", despues):
                terminos(m.group(1))
            i = n.find(clave, i + 1)
    return out[:5]


# ------------------------------------------------------------------ origen estimado por el nombre
_PALABRAS: tuple[frozenset, frozenset, frozenset] | None = None
_RELLENO = {"dr", "mr", "mc", "dj", "sr", "st", "la", "el", "y", "e", "&", "feat", "ft", "presenta", "presentan", "live",
            "band", "trio", "quartet", "quintet", "orchestra", "project", "experience", "tributo", "tribute",
            "the", "and", "of", "en", "concierto", "madrid", "gira", "tour", "show",
            # palabras del evento, no del artista ("Noches de Piano Jazz", "Concierto inaugural de…")
            "de", "del", "los", "las", "con", "noche", "noches", "conciertos", "espectaculo", "flamenco", "presenta",
            "nueva", "nuevo", "anos", "homenaje", "fiestas", "fiesta", "ciclo", "festival", "verbena", "inaugural",
            "especial", "navidad", "hispanidad", "jazz", "piano", "sesion", "musica", "canciones", "grandes",
            "orquesta", "banda", "grupo", "trio", "cuarteto", "quinteto", "friends", "amigos", "invitados"}


def _palabras() -> tuple[frozenset, frozenset, frozenset]:
    global _PALABRAS
    if _PALABRAS is None:
        from .normalize import load_json
        d = load_json("palabras.json")
        _PALABRAS = frozenset(d["es"]), frozenset(d["es_fuerte"]), frozenset(d["en"])
    return _PALABRAS


def pais_estimado(nombre: str) -> tuple[str | None, str]:
    """("ES", motivo) si el nombre del artista está en español: alguna palabra propia del español ("cuarteto",
    "amados", "rayo", nombres como "Felipe") o letras como la ñ, y ninguna propia del inglés. Es una estimación,
    no un dato: solo se usa cuando ninguna fuente dice de dónde es, y se muestra como tal ("probablemente")."""
    es, fuerte, en = _palabras()
    crudo = (nombre or "").lower()
    tokens = [t for t in re.findall(r"[a-z]+", norm(nombre or "")) if len(t) >= 2]
    contenido = [t for t in tokens if t not in _RELLENO]
    if not contenido:
        return None, ""
    de_es = [t for t in contenido if t in es]
    de_en = [t for t in tokens if t in en and t not in {"dr", "mr"}]
    if de_en:
        return None, ""
    tildes = bool(re.search(r"[ñáéíóú]", crudo))
    claro = tildes or len(de_es) >= 2 or any(t in fuerte for t in de_es)
    if claro and (de_es or tildes) and len(de_es) * 2 >= len(contenido):
        motivo = "nombre en español" + (f" ({', '.join(de_es[:3])})" if de_es else " (con tildes)")
        return "ES", motivo
    return None, ""
