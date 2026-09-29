"""Nacionalidad desde la API pública de MusicBrainz (máx. 1 petición/segundo, User-Agent propio).

Solo se acepta si hay UNA única coincidencia exacta del nombre del artista; si no, queda null ('sin confirmar').
Se usa la API /ws/2 documentada para uso programático (https://musicbrainz.org/doc/MusicBrainz_API); el
robots.txt de musicbrainz.org se refiere al rastreo de sus páginas web, no a la API."""
from __future__ import annotations

import json
import time
from datetime import date, timedelta
from urllib.parse import quote

from .fetch import USER_AGENT, Fetcher
from .normalize import es_generico, norm

API = "https://musicbrainz.org/ws/2/artist/?query={q}&fmt=json&limit=25"
CADUCIDAD_DIAS = 120


def buscar(fetcher: Fetcher, nombre: str) -> dict:
    q = quote(f'artist:"{nombre}"')
    raw = fetcher.get(API.format(q=q), check_robots=False, headers={"Accept": "application/json",
                                                                     "User-Agent": USER_AGENT})
    data = json.loads(raw)
    exactos = [a for a in data.get("artists", []) if norm(a.get("name")) == norm(nombre)]
    if len(exactos) != 1:
        return {"pais": None, "coincidencias_exactas": len(exactos)}
    a = exactos[0]
    pais = a.get("country") or ((a.get("area") or {}).get("iso-3166-1-codes") or [None])[0]
    return {"pais": pais, "coincidencias_exactas": 1, "mbid": a.get("id")}


def completar(recs: list[dict], cache: dict, hoy: date, fetcher: Fetcher | None, max_consultas: int = 600,
              presupuesto_seg: float = 1500) -> dict:
    """Rellena nacionalidad en los registros que no la traen de la fuente. Devuelve estadísticas."""
    stats = {"consultas": 0, "desde_cache": 0, "asignadas": 0, "sin_confirmar": 0, "pendientes": 0}
    limite = (hoy - timedelta(days=CADUCIDAD_DIAS)).isoformat()
    inicio = time.monotonic()
    # primero los conciertos en foco y más próximos
    orden = sorted([r for r in recs if not r.get("nacionalidad")], key=lambda r: (not r["en_foco"], r["fecha"]))
    for r in orden:
        nombre = r["artista"]
        if es_generico(nombre) or len(norm(nombre)) < 2:
            r["nacionalidad_fuente"] = None
            continue
        k = norm(nombre)
        ent = cache.get(k)
        if ent is None or ent.get("fecha", "") < limite:
            if fetcher is None or stats["consultas"] >= max_consultas or time.monotonic() - inicio > presupuesto_seg:
                stats["pendientes"] += 1
                continue
            try:
                res = buscar(fetcher, nombre)
            except Exception as e:  # noqa: BLE001
                stats.setdefault("errores", []).append(f"{nombre}: {type(e).__name__}")
                continue
            stats["consultas"] += 1
            ent = {**res, "fecha": hoy.isoformat()}
            cache[k] = ent
        else:
            stats["desde_cache"] += 1
        if ent.get("pais"):
            r["nacionalidad"] = ent["pais"]
            r["nacionalidad_fuente"] = "MusicBrainz (coincidencia por nombre)"
            stats["asignadas"] += 1
        else:
            stats["sin_confirmar"] += 1
    return stats


def fetcher_musicbrainz() -> Fetcher:
    return Fetcher(min_interval=1.0)  # norma de MusicBrainz: 1 petición/s; ante 503 el Fetcher frena y reintenta
