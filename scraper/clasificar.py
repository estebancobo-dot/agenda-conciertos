"""Traducción del estilo que da la fuente a categoría (data/estilos_map.json) y a estilos de Discogs
(data/taxonomia.json). Nunca se deduce un estilo que la fuente no dé."""
from __future__ import annotations

import re
from functools import lru_cache

from .normalize import load_json, norm


@lru_cache(maxsize=1)
def _mapa():
    d = load_json("estilos_map.json")
    exacto = {norm(k): v for k, v in d["exacto"].items()}
    claves = [(norm(k), v) for k, v in d["palabras_clave"]]
    titulo = [norm(x) for x in d["titulo_fuera_de_foco"]]
    return exacto, claves, titulo, d["en_foco"]


@lru_cache(maxsize=1)
def _taxo():
    d = load_json("taxonomia.json")
    estilo_genero = {}
    for g, estilos in d["generos"].items():
        for e in estilos:
            estilo_genero.setdefault(norm(e), (e, g))
    sin = {norm(k): v for k, v in d["sinonimos"].items()}
    return estilo_genero, sin


def partes(estilo: str | None) -> list[str]:
    if not estilo:
        return []
    return [p.strip() for p in re.split(r"\s*[,|/;·]\s*|\s+-\s+", estilo) if p.strip()]


def _v(x):
    return x[0] if isinstance(x, list) else x


def categoria_de(estilo: str | None) -> str | None:
    """Categoría para un texto de estilo de una fuente. None si no se reconoce."""
    if not estilo:
        return None
    exacto, claves, _, _ = _mapa()
    n = norm(estilo)
    if n in exacto:
        return _v(exacto[n])
    # primer componente de listas ('Indie Rock, Indie Pop'): la fuente suele poner primero el principal
    for p in partes(estilo):
        np_ = norm(p)
        if np_ in exacto:
            return _v(exacto[np_])
        for k, v in claves:
            if f" {k} " in f" {np_} ":
                return v
    for k, v in claves:
        if f" {k} " in f" {n} ":
            return v
    return None


def categorias_de(estilo: str | None) -> list[str]:
    """Todas las categorías que aparecen en un texto de estilo (para no perder conciertos en foco)."""
    out = []
    exacto = _mapa()[0]
    if estilo and isinstance(exacto.get(norm(estilo)), list):
        return list(exacto[norm(estilo)])
    for p in partes(estilo) or ([estilo] if estilo else []):
        c = categoria_de(p)
        if c and c not in out:
            out.append(c)
    c0 = categoria_de(estilo)
    if c0 and c0 not in out:
        out.insert(0, c0)
    return out


def titulo_fuera_de_foco(titulo: str) -> bool:
    _, _, titulo_kw, _ = _mapa()
    n = f" {norm(titulo)} "
    return any(f" {k} " in n for k in titulo_kw)


def en_foco(categorias: list[str]) -> bool:
    _, _, _, foco = _mapa()
    return any(c in foco for c in categorias)


def discogs(estilos_fuente: list[str]) -> tuple[list[str], list[str]]:
    """Estilos y géneros de Discogs cuyo nombre coincide literalmente (o por sinónimo declarado) con el estilo de la fuente."""
    estilo_genero, sin = _taxo()
    estilos, generos = [], []
    for e in estilos_fuente:
        ps = partes(e)
        for p in (ps if len(ps) > 1 else [e]):
            n = norm(p)
            nombre = None
            if n in estilo_genero:
                nombre = estilo_genero[n][0]
            elif n in sin and norm(sin[n]) in estilo_genero:
                nombre = estilo_genero[norm(sin[n])][0]
            if nombre and nombre not in estilos:
                estilos.append(nombre)
                g = estilo_genero[norm(nombre)][1]
                if g not in generos:
                    generos.append(g)
    return estilos, generos


# ------------------------------------------------------------------ ficha musical (Discogs / Wikipedia) → grupos de filtro
@lru_cache(maxsize=1)
def _discogs_cat():
    d = load_json("estilos_map.json")
    est = {}
    for cat, lista in d["discogs_a_categoria"].items():
        if cat.startswith("_"):
            continue
        for e in lista:
            est[norm(e)] = cat
    return est, d["genero_a_categoria"]


@lru_cache(maxsize=1)
def _generos_sin():
    t = load_json("taxonomia.json")
    g = {norm(k): v for k, v in t.get("sinonimos_genero", {}).items()}
    for gen in list(t["generos"]) + t.get("otros_generos", []):
        g[norm(gen)] = gen
    return g


def genero_de_estilo(estilo: str) -> str | None:
    estilo_genero, sin = _taxo()
    n = norm(estilo)
    if n in estilo_genero:
        return estilo_genero[n][1]
    if n in sin and norm(sin[n]) in estilo_genero:
        return estilo_genero[norm(sin[n])][1]
    return None


def generos_de_texto(textos: list[str]) -> list[str]:
    """Géneros de Discogs para textos como 'Rock', 'Hip hop', 'Música latina' (traducción literal declarada)."""
    g = _generos_sin()
    out = []
    for t in textos:
        x = g.get(norm(t))
        if x and x not in out:
            out.append(x)
    return out


def categorias_de_ficha(generos: list[str], estilos: list[str]) -> list[str]:
    """Grupos de filtro a partir del género y los estilos de Discogs (o traducidos desde Wikipedia)."""
    por_estilo, por_genero = _discogs_cat()
    cats = []
    for e in estilos:
        c = por_estilo.get(norm(e)) or por_genero.get(genero_de_estilo(e) or "", None)
        if c is None and genero_de_estilo(e) is None:
            continue
        c = c or "fuera de foco"
        if c not in cats:
            cats.append(c)
    for g in generos:
        c = por_genero.get(g, "fuera de foco")
        if c not in cats and (not estilos or c == "fuera de foco" and not any(
                por_genero.get(genero_de_estilo(e) or "") for e in estilos)):
            cats.append(c)
    return cats


# ------------------------------------------------------------------ clasificación por consenso
# Umbral para que un grupo secundario cuente: al menos la mitad de la puntuación del principal y una quinta
# parte del total. Así un artista de pop latino con "rock" al final de su lista no aparece en "Rock y metal".
UMBRAL_PRINCIPAL, UMBRAL_TOTAL = 0.6, 0.25

# Etiquetas de agenda que indican que no es un concierto (obra de teatro, musical…): no se busca al "artista"
# en las webs de música, porque un título como "Los Miserables" coincide con un grupo real (punk chileno).
NO_CONCIERTO = re.compile(r"\b(teatro|musicales?|artes escenicas|danza|ballet|humor|monologos?|comedia|infantil|"
                          r"familiar|magia|circo|cine|zarzuela)\b")


def grupo_de(nombre: str, tipo: str) -> str | None:
    cats = categorias_de_ficha([nombre], []) if tipo == "genero" else categorias_de_ficha([], [nombre])
    return cats[0] if cats else None


def por_consenso(pesos: dict[str, float]) -> list[str]:
    if not pesos:
        return []
    total, maximo = sum(pesos.values()), max(pesos.values())
    return [g for g, p in sorted(pesos.items(), key=lambda x: -x[1])
            if p >= UMBRAL_PRINCIPAL * maximo and p >= UMBRAL_TOTAL * total]


def grupos_de_evidencias(evs: list[dict], grupos_agenda: list[str] | None = None) -> tuple[list[str], list[str]]:
    """Grupos por consenso ponderado y los estilos que los sostienen, ordenados por peso.

    Las evidencias débiles (Last.fm identificado solo por el nombre) valen la mitad; si son las únicas, solo
    cuentan los grupos en los que coinciden con la agenda (si la agenda no dice nada, no se usan): así un
    título genérico como "Eternal" no se convierte en un grupo de doom metal."""
    fuertes = [e for e in evs if not e.get("debil")]
    debiles = [e for e in evs if e.get("debil")]

    def puntuar(lista, factor_debil):
        pesos: dict[str, float] = {}
        por_estilo: dict[str, float] = {}
        for e in lista:
            g = grupo_de(e["nombre"], e["tipo"])
            if not g:
                continue
            p = e["peso"] * (factor_debil if e.get("debil") else 1.0)
            pesos[g] = pesos.get(g, 0) + p
            if e["tipo"] == "estilo":
                por_estilo[e["nombre"]] = por_estilo.get(e["nombre"], 0) + p
        return pesos, por_estilo

    if fuertes:
        pesos, por_estilo = puntuar(fuertes + debiles, 0.5)
        grupos = por_consenso(pesos)
    else:
        pesos, por_estilo = puntuar(debiles, 1.0)
        grupos = [g for g in por_consenso(pesos) if g in (grupos_agenda or [])]
    estilos = [x for x, _ in sorted(por_estilo.items(), key=lambda x: -x[1]) if grupo_de(x, "estilo") in grupos]
    return grupos, estilos


def es_espectaculo(etiquetas: list[str]) -> bool:
    """La agenda lo presenta como teatro, musical, danza, humor… y ninguna etiqueta indica un concierto."""
    if not etiquetas:
        return False
    no = [e for e in etiquetas if NO_CONCIERTO.search(norm(e))]
    si = [e for e in etiquetas if e not in no and any(c not in ("fuera de foco", "sin clasificar")
                                                     for c in categorias_de(e))]
    return bool(no) and not si


def grupos_de_agenda(etiquetas_por_fuente: list[list[str]]) -> tuple[list[str], bool]:
    """Grupos a partir de las etiquetas de las agendas. Las etiquetas "paraguas" ("Pop / Rock", "Músicas negras")
    no dicen cuál de los dos es: solo cuentan si no hay otra más concreta, y entonces el resultado es genérico."""
    exacto = _mapa()[0]
    pesos: dict[str, float] = {}
    paraguas: list[str] = []
    for etiquetas in etiquetas_por_fuente:
        for e in etiquetas:
            if isinstance(exacto.get(norm(e)), list):
                paraguas += [c for c in exacto[norm(e)] if c not in paraguas]
                continue
            for i, c in enumerate(categorias_de(e)):
                if c != "sin clasificar":
                    pesos[c] = pesos.get(c, 0) + PESO_RANGO_AGENDA[min(i, 3)]
    if pesos:
        return por_consenso(pesos), False
    if paraguas:
        return paraguas, True
    return [], False


PESO_RANGO_AGENDA = [1.0, 0.75, 0.55, 0.45]


# Géneros de MusicBrainz sin equivalencia literal en Discogs: su vocabulario es cerrado ("melodic metalcore",
# "rock en español"…), así que se traducen por la palabra que define la familia. Solo se usa con MusicBrainz.
_FAMILIAS_MB = [
    (r"\bmetal(core)?\b", "Heavy Metal", "estilo"), (r"\bgrindcore\b", "Grindcore", "estilo"),
    (r"\bpunk\b", "Punk", "estilo"), (r"\bhardcore\b", "Hardcore", "estilo"), (r"\bgarage\b", "Garage Rock", "estilo"),
    (r"\bshoegaze\b", "Shoegaze", "estilo"), (r"\bpsych", "Psychedelic Rock", "estilo"),
    (r"\bblues\b", "Blues", "genero"), (r"\bcountry\b", "Country", "estilo"), (r"\bbluegrass\b", "Bluegrass", "estilo"),
    (r"\bfolk\b", "Folk", "estilo"), (r"\bjazz\b", "Jazz", "genero"),
    (r"\b(hip hop|rap|trap|drill|grime)\b", "Hip Hop", "genero"),
    (r"\b(house|techno|trance|edm|electro\w*|dubstep|drum and bass|synth\w*|ambient|idm)\b", "Electronic", "genero"),
    (r"\b(reggaeton|cumbia|salsa|bachata|latin|flamenco|rumba|bolero|tango|son)\b", "Latin", "genero"),
    (r"\b(soul|funk|r&b|rnb|disco)\b", "Funk / Soul", "genero"), (r"\b(reggae|dub|dancehall)\b", "Reggae", "genero"),
    (r"\b(classical|orchestral|opera|baroque|romantic|symphon\w*|choral)\b", "Classical", "genero"),
    (r"\bpop\b", "Pop", "genero"), (r"\brock\b", "Rock", "genero"),
]


def traducir_musicbrainz(genero: str) -> list[tuple[str, str]]:
    """[(nombre, 'estilo'|'genero')] de Discogs para un género de MusicBrainz."""
    est, _ = discogs([genero])
    if est:
        return [(e, "estilo") for e in est]
    gen = generos_de_texto([genero])
    if gen:
        return [(g, "genero") for g in gen]
    n = norm(genero)
    for rx, nombre, tipo in _FAMILIAS_MB:
        if re.search(rx, n) and grupo_de(nombre, tipo):
            return [(nombre, tipo)]
    return []
