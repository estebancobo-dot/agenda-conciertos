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
