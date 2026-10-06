"""Nivel del concierto: no es lo mismo un grupo local en un bar que Muse en el Movistar Arena. Solo información
(no filtra nada), calculada con dos señales medibles y con su porqué a la vista:

- el tipo de recinto (data/salas_tipo.json: gran recinto, teatro o auditorio, sala grande, sala, club o bar…);
- cuánto se escucha al artista: oyentes en Last.fm, solo si la identidad es segura (por identificador de
  MusicBrainz; por el nombre solo, no: un homónimo con millones de oyentes no convierte en gran concierto a un
  grupo local con el mismo nombre).

Niveles: "gran formato" (gran recinto, o artista con 1 millón de oyentes o más), "formato medio" (teatro,
auditorio o sala grande, o artista con 100.000 o más), "formato íntimo" (sala, club, tablao, hotel o centro
cultural o iglesia, con un artista con menos de 100.000 oyentes o sin datos). Los oyentes solo suben el nivel:
pocos oyentes en Last.fm no prueban nada (se usa poco en España). Sin sala con tipo ni artista con 100.000 oyentes
o más no hay nivel: no se adivina. No se calcula para tributos, festivales ni lo que no tiene un artista (jams, Candlelight): ahí los
oyentes no serían los del concierto; solo cuenta el recinto.
"""
from __future__ import annotations

import re
from functools import lru_cache

from .normalize import canon_sala, load_json, norm

FORMATO_RECINTO = {"gran recinto": 3, "teatro o auditorio": 2, "sala grande": 2, "sala": 1, "club o bar": 1,
                   "tablao": 1, "hotel": 1, "centro cultural": 1, "iglesia": 1}
# las que no están en la lista, por lo que dice su nombre (solo nombres que no dejan duda del tipo de sitio)
POR_NOMBRE = [(re.compile(r"^(centro (socio)?cultural|biblioteca)\b", re.I), "centro cultural"),
              (re.compile(r"^(teatro|auditorio|cine ?& ?teatro)\b", re.I), "teatro o auditorio"),
              (re.compile(r"^(bas[ií]lica|parroquia|iglesia|catedral|convento|monasterio|ermita)\b", re.I), "iglesia")]
NIVELES = {3: "gran formato", 2: "formato medio", 1: "formato íntimo"}
MUY_ESCUCHADO, CONOCIDO, MINORITARIO = 1_000_000, 100_000, 10_000


@lru_cache(maxsize=1)
def _tipos() -> dict[str, str]:
    d = load_json("salas_tipo.json")
    return {canon_sala(s): t for t, salas in d.items() if not t.startswith("_") for s in salas}


def tipo_recinto(sala: str | None) -> str | None:
    """Tipo de la sala ("La Sala del Movistar Arena / Movistar Arena" → el de la primera que tenga tipo)."""
    for parte in (sala or "").split(" / "):
        nombre = canon_sala(parte.strip())
        t = _tipos().get(nombre) or next((t for rx, t in POR_NOMBRE if rx.search(nombre or "")), None)
        if t:
            return t
    return None


def etiqueta_oyentes(n: int) -> str:
    return ("muy escuchado" if n >= MUY_ESCUCHADO else "conocido" if n >= CONOCIDO
            else "minoritario" if n >= MINORITARIO else "poco escuchado")


def oyentes_txt(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}".replace(".", ",").replace(",0", "") + " M de oyentes"
    if n >= 1000:
        return f"{round(n / 1000)} mil oyentes"
    return f"{n} oyentes"


def audiencia_segura(ent: dict | None) -> dict | None:
    """Los oyentes de Last.fm del artista, solo si Last.fm lo identificó por su identificador de MusicBrainz (el
    de Wikidata o el del único artista con ese nombre en MusicBrainz). Por el nombre solo no cuenta: un homónimo
    famoso daría a un grupo local millones de oyentes que no son suyos."""
    aud = (ent or {}).get("audiencia") or {}
    via = aud.get("identificado_por")
    if not aud.get("encontrado") or not aud.get("oyentes") or via in (None, "", "coincidencia por nombre"):
        return None
    # el identificador del único artista con ese nombre en MusicBrainz vale si otra web de música lo encuentra
    if "nombre" in via and not any((ent.get(k) or {}).get("encontrado") for k in ("discogs", "wikipedia", "wikidata")):
        return None
    return aud


def nivel(r: dict, cache: dict) -> dict | None:
    """{"nivel", "recinto", "oyentes", "artista", "motivo"} o None si no hay ninguna señal."""
    from .nombres import claves_ficha
    from .origen import sin_artista
    recinto = tipo_recinto(r.get("sala"))
    p_recinto = FORMATO_RECINTO.get(recinto or "", 0)
    aud, quien = None, None
    con_artista = not (r.get("festival") or r.get("origen_no_aplica") or sin_artista(r.get("artista") or "")
                       or "tributos y versiones" in (r.get("grupos") or []))
    if con_artista:
        for k in claves_ficha(r) or [r.get("artista") or ""]:
            aud = audiencia_segura(cache.get(norm(k)))
            if aud:
                quien = aud.get("nombre") or k
                break
    n = (aud or {}).get("oyentes") or 0
    # los oyentes solo suben el nivel, nunca lo bajan: Last.fm se usa poco en España y se queda corto con artistas
    # españoles y latinos (flamenco, copla, pop latino), así que pocos oyentes no prueban un concierto pequeño
    p_art = 3 if n >= MUY_ESCUCHADO else 2 if n >= CONOCIDO else 0
    p = max(p_recinto, p_art)
    if not p:
        return None
    partes = []
    if recinto:
        partes.append(f"{r.get('sala')}: {recinto}")
    if aud and (p_art or recinto):
        # por debajo de 100.000 solo la cifra: "poco escuchado" sería injusto con quien no está en Last.fm
        partes.append(f"{quien}: {oyentes_txt(n)} en Last.fm" + (f" ({etiqueta_oyentes(n)})" if p_art else ""))
    out = {"nivel": NIVELES[p], "motivo": " · ".join(partes)}
    if recinto:
        out["recinto"] = recinto
    if aud:
        out["oyentes"] = n
    return out
