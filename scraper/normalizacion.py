"""N3 y N4: estado explícito del estilo y del origen de cada concierto.

Nada queda "sin procesar": cada dato termina en uno de cuatro estados, con su porqué.

- conocido: lo dice una web de música (Discogs, MusicBrainz, Wikipedia, Wikidata, Last.fm por su identificador) o,
  para el origen, la propia agenda o la sala con una frase que lo dice. Con la fuente.
- estimado: no hay dato directo; se deduce de algo que se dice (la etiqueta de la agenda, el homenajeado de un
  tributo, un artista identificado solo por su nombre, un nombre en español). Con el motivo. Se muestra como tal.
- no_aplica: no hay un artista del que decirlo (musicales, jam sessions, micro abierto, festivales con varios).
- desconocido: se ha buscado y no se ha encontrado. Con dónde se ha buscado y qué respondió cada sitio.

Solo describe lo que ya hay en el concierto y en las fichas guardadas: no busca ni cambia nada."""
from __future__ import annotations

from .normalize import norm

ESTADOS = ("conocido", "estimado", "no_aplica", "desconocido")
_WEBS_MUSICA = ("Discogs", "MusicBrainz", "Wikipedia", "Wikidata", "Last.fm")
_PASOS = (("discogs", "Discogs"), ("musicbrainz", "MusicBrainz"), ("wikipedia", "Wikipedia"),
          ("wikidata", "Wikidata"), ("lastfm", "Last.fm"), ("lastfm_bio", "biografía de Last.fm"),
          ("agenda", "página de la agenda"), ("wikipedia_texto", "texto de Wikipedia"))
# el origen o el estilo de un artista encontrado solo por su nombre puede ser el de un homónimo ("LANDA" → un
# músico checo): no se da por conocido
_SOLO_NOMBRE = ("coincidencia por nombre", "identificado por su nombre")


def buscado_en(r: dict, cache: dict) -> list[str]:
    """Dónde se ha buscado al artista del concierto y qué respondió cada sitio ("Discogs: sin coincidencia
    exacta"). Vacío si aún no se ha buscado."""
    from .nombres import claves_ficha
    out, vistos = [], set()
    for k in claves_ficha(r):
        ent = cache.get(norm(k))
        if not ent:
            continue
        for paso, nombre in _PASOS:
            p = ent.get(paso)
            if not isinstance(p, dict) or nombre in vistos:
                continue
            vistos.add(nombre)
            if p.get("encontrado"):
                out.append(f"{nombre}: encontrado")
            else:
                out.append(f"{nombre}: {str(p.get('motivo') or 'sin resultado').split(';')[0][:70]}")
    return out


def _sin_artista(r: dict) -> str | None:
    from .clasificar import grupo_de_titulo
    from .origen import sin_artista
    if r.get("festival") and not r.get("cartel"):
        return "festival o ciclo con varios artistas"
    if sin_artista(r.get("artista") or ""):
        return "no hay un artista (jam session, micro abierto, sesión…)"
    if grupo_de_titulo(r.get("artista") or "") == "musicales y espectáculos" or \
            str(r.get("grupos_origen") or "").startswith("agenda (espect"):
        return "espectáculo (musical, teatro, danza…), no un concierto de un artista"
    return None


def estado_estilo(r: dict, cache: dict) -> dict:
    origen = str(r.get("grupos_origen") or "")
    grupos = [g for g in r.get("grupos") or [] if g != "sin clasificar"]
    segun = ", ".join(r.get("grupos_segun") or [])
    if origen.startswith("agenda (espect"):
        return {"estado": "no_aplica", "motivo": "espectáculo, no un concierto de un artista"}
    if grupos and origen in _WEBS_MUSICA:
        ent_lf = _lastfm_por_nombre(r, cache) if origen == "Last.fm" else False
        if ent_lf:
            return {"estado": "estimado", "fuente": "Last.fm",
                    "motivo": "etiquetas de Last.fm de un artista identificado solo por su nombre"}
        return {"estado": "conocido", "fuente": origen}
    if grupos and origen == "cartel del festival":
        return {"estado": "conocido", "fuente": "fichas de los artistas del cartel"}
    if grupos and segun.startswith("estilo de ") and "homenajeado" in segun:
        return {"estado": "estimado", "fuente": segun, "motivo": "un tributo suena como el artista homenajeado"}
    if grupos:
        return {"estado": "estimado", "fuente": "la agenda",
                "motivo": "etiqueta de la agenda" + (f" ({segun})" if segun else "")
                          + (": genérica" if r.get("grupos_generico") else "")}
    sin = _sin_artista(r)
    if sin:
        return {"estado": "no_aplica", "motivo": sin}
    return {"estado": "desconocido", "buscado": buscado_en(r, cache) or ["aún no se ha buscado: entra en la próxima pasada de fichas de artista"]}


def _lastfm_por_nombre(r: dict, cache: dict) -> bool:
    from .nombres import claves_ficha
    for k in claves_ficha(r):
        lf = (cache.get(norm(k)) or {}).get("lastfm") or {}
        if lf.get("encontrado"):
            return any(s in str(lf.get("identificado_por") or "") for s in _SOLO_NOMBRE)
    return False


def estado_nacionalidad(r: dict, cache: dict) -> dict:
    fuente = str(r.get("nacionalidad_fuente") or "")
    if r.get("nacionalidad"):
        if any(s in fuente for s in _SOLO_NOMBRE):
            return {"estado": "estimado", "valor": r["nacionalidad"], "fuente": fuente,
                    "motivo": "artista identificado solo por su nombre (podría ser un homónimo)"}
        out = {"estado": "conocido", "valor": r["nacionalidad"], "fuente": fuente}
        otros = paises_contradictorios(r, cache)
        if otros:
            out["contradice"] = otros
        return out
    if r.get("origen_no_aplica"):
        return {"estado": "no_aplica", "motivo": _sin_artista(r) or "no hay un artista del que decir el origen"}
    sin = _sin_artista(r)
    if sin:
        return {"estado": "no_aplica", "motivo": sin}
    if r.get("nacionalidad_estimada"):
        return {"estado": "estimado", "valor": r["nacionalidad_estimada"],
                "motivo": r.get("nacionalidad_estimada_motivo") or ""}
    return {"estado": "desconocido", "buscado": buscado_en(r, cache) or ["aún no se ha buscado: entra en la próxima pasada de fichas de artista"]}


def paises_contradictorios(r: dict, cache: dict) -> list[dict]:
    """Otras webs que dan para el mismo artista un país distinto del elegido (solo de webs que lo identifican por
    algo más que el nombre): se muestran, no se elige."""
    from .nombres import claves_ficha
    ks = claves_ficha(r)[:1]
    ent = cache.get(norm(ks[0])) if ks else None
    if not ent:
        return []
    vistos = {}
    for paso, nombre in (("discogs", "Discogs"), ("musicbrainz", "MusicBrainz"), ("wikidata", "Wikidata")):
        p = ent.get(paso) or {}
        pais = p.get("pais") if p.get("encontrado") else None
        if pais and pais != r["nacionalidad"]:
            vistos.setdefault(pais, []).append(nombre)
    return [{"valor": k, "fuentes": v} for k, v in vistos.items()]


def _webs(r: dict) -> list[str]:
    return list(dict.fromkeys(f.get("nombre", "").split(" (")[0] for f in r.get("fuentes") or [] if f.get("nombre")))


def estado_hora(r: dict) -> dict:
    """N5: la hora de comienzo. Conocida (la dan las webs, o la página del concierto), estimada si las webs no
    coinciden (se enseñan las dos) o desconocida (ninguna de sus webs la da)."""
    versiones = [v.get("valor") for c in r.get("conflictos") or [] if c.get("campo") == "hora"
                 for v in c.get("versiones") or []]
    if versiones and not r.get("hora"):
        return {"estado": "estimado", "motivo": "las webs no coinciden: " + " o ".join(dict.fromkeys(versiones))}
    if r.get("hora"):
        pag = r.get("hora_pagina") or {}
        return {"estado": "conocido", "fuente": pag.get("nombre") or ", ".join(_webs(r)[:3])}
    return {"estado": "desconocido", "buscado": [f"{w}: no la da" for w in _webs(r)] or ["sin webs"]}


def estado_precio(r: dict) -> dict:
    p = str(r.get("precio") or "")
    if p:
        pf = r.get("precio_fuente") or {}
        return {"estado": "conocido", "fuente": (pf.get("nombre") if isinstance(pf, dict) else None)
                or ", ".join(_webs(r)[:3])}
    return {"estado": "desconocido", "buscado": [f"{w}: no lo da" for w in _webs(r)] or ["sin webs"]}


def estado_sala(r: dict) -> dict:
    if r.get("sala"):
        return {"estado": "conocido"}
    return {"estado": "desconocido", "buscado": [f"{w}: no la da" for w in _webs(r)] or ["sin webs"]}


def normalizar(r: dict, cache: dict) -> None:
    r["normalizacion"] = {"estilo": estado_estilo(r, cache), "origen": estado_nacionalidad(r, cache),
                          "hora": estado_hora(r), "precio": estado_precio(r), "sala": estado_sala(r)}


def resumen(recs: list[dict], hoy: str) -> dict:
    """Cuántos conciertos próximos hay en cada estado (para el informe y la página de Fuentes)."""
    from collections import Counter
    out = {}
    for campo in ("estilo", "origen", "hora", "precio", "sala"):
        c = Counter((r.get("normalizacion") or {}).get(campo, {}).get("estado", "sin_estado")
                    for r in recs if r["fecha"] >= hoy)
        out[campo] = {e: c.get(e, 0) for e in ESTADOS + ("sin_estado",) if c.get(e, 0) or e in ESTADOS}
    out["contradicciones_origen"] = sum(1 for r in recs if r["fecha"] >= hoy
                                        and (r.get("normalizacion") or {}).get("origen", {}).get("contradice"))
    return out
