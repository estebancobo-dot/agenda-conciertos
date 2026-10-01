"""Orquestador: rastrea las fuentes, unifica, aplica correcciones y escribe los datos."""
from __future__ import annotations

import csv
import json
import re
import logging
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import __version__
from .clasificar import categoria_de
from .correcciones import aplicar as aplicar_correcciones
from .fetch import AntiBotBlocked, Fetcher, RobotsBlocked, RobotsUnreachable
from .merge import (Item, agrupar, artistas_coinciden, coinciden_flexible, construir, fusionar_conflictos_sala,
                    hacer_id, marcar_conflictos_cartel, nombres_rec, recalcular_categorias, recalcular_estado,
                    separar_ciclo)
from .model import RawEvent, Source
from .normalize import DATA, canon_sala, clean, load_json, misma_sala, municipio, norm, sala_municipio
from .registry import FUENTES, NO_USAR, SIN_AGENDA_LEGIBLE
from .sources.base import Ctx

log = logging.getLogger("agenda")
HORIZONTE_DIAS = 120
HISTORIA_DIAS = 31


def _read(name: str, default):
    p = DATA / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            return default
    return default


def _write(name: str, obj) -> None:
    # escritura atómica: si el proceso se corta a mitad, el archivo anterior queda intacto
    tmp = DATA / (name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(DATA / name)


# ---------------------------------------------------------------- rastreo
# Fallos que merece la pena reintentar: la web no respondió, bloqueó (403, antirobots) o dio error.
# Un "robots.txt lo prohíbe" no se reintenta: es una decisión de la web.
REINTENTABLES = {"error", "bloqueado_403", "bloqueado_antibots"}
PAUSA_REINTENTO_SEG = 90


def leer_fuente(src: Source, fetcher: Fetcher, hoy: date, horizonte: date, estado: dict) -> tuple[list, dict]:
    ctx = Ctx(fetcher=fetcher, today=hoy, horizon=horizonte, estado=estado.setdefault(src.id, {}))
    t0 = time.monotonic()
    evs: list[RawEvent] = []
    res = {"funciono": False, "estado": "", "brutos": 0, "paginas": 0, "errores": [], "robots": ""}
    try:
        for e in src.parser(ctx):
            e.fuente = src.id
            evs.append(e)
        res["funciono"] = True
        res["estado"] = "ok" if evs else "ok_sin_resultados"
    except AntiBotBlocked as e:
        res["estado"] = "bloqueado_antibots"
        res["errores"].append(str(e))
    except RobotsUnreachable as e:
        res["estado"] = "error"
        res["errores"].append(str(e))
    except RobotsBlocked as e:
        res["estado"] = "bloqueado_robots"
        res["errores"].append(f"robots.txt prohíbe {e}")
    except Exception as e:  # noqa: BLE001
        msg = f"{type(e).__name__}: {e}"
        res["estado"] = "bloqueado_403" if "403" in msg else "error"
        res["errores"].append(msg[:400])
        log.debug(traceback.format_exc())
    res["errores"] += ctx.errors[:20]
    # lectura completa: funcionó, dio resultados y sin errores parciales (páginas caídas, tope de tiempo…)
    res["completa"] = res["funciono"] and bool(evs) and not ctx.errors
    res["paginas"] = ctx.pages
    res["brutos"] = len(evs)
    res["segundos"] = round(time.monotonic() - t0, 1)
    try:
        res["robots"] = fetcher.robots_status(src.url)
    except Exception:  # noqa: BLE001
        res["robots"] = ""
    log.info("%-22s %-18s %4d eventos %3d páginas %5.1fs", src.id, res["estado"], len(evs), ctx.pages,
             res["segundos"])
    return evs, res


def rastrear(fuentes: list[Source], fetcher: Fetcher, hoy: date, horizonte: date, estado: dict,
             max_workers: int = 16, pausa_reintento: float = PAUSA_REINTENTO_SEG) -> tuple[dict, dict]:
    """Lee todas las fuentes en paralelo (una petición a la vez por servidor) y reintenta una vez, tras una
    pausa, las que fallaron. Devuelve los eventos y el resultado de cada fuente."""
    resultados: dict[str, dict] = {}
    eventos: dict[str, list] = {}
    # primero las lentas (Madrid en Vivo, conciertos.club…): así el resto se lee mientras tanto
    orden = sorted(fuentes, key=lambda s: -float((estado.get("_duracion") or {}).get(s.id, 0)))
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for src, (evs, res) in zip(orden, ex.map(lambda s: leer_fuente(s, fetcher, hoy, horizonte, estado), orden)):
            eventos[src.id], resultados[src.id] = evs, res
    fallidas = [s for s in fuentes if resultados[s.id]["estado"] in REINTENTABLES]
    if fallidas:
        log.info("Reintento de %d fuentes dentro de %d s: %s", len(fallidas), pausa_reintento,
                 ", ".join(s.id for s in fallidas))
        time.sleep(pausa_reintento)
        for s in fallidas:
            fetcher.olvidar(s.url)
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            for src, (evs, res) in zip(fallidas, ex.map(lambda s: leer_fuente(s, fetcher, hoy, horizonte, estado),
                                                        fallidas)):
                if res["funciono"]:
                    res["reintento"] = "funcionó en el 2.º intento"
                    eventos[src.id], resultados[src.id] = evs, res
                else:
                    resultados[src.id]["reintento"] = "falló también en el 2.º intento"
    estado["_duracion"] = {s: r.get("segundos", 0) for s, r in resultados.items()}
    return eventos, resultados


# ---------------------------------------------------------------- caché de la última lectura buena de cada fuente
CACHE_FUENTES = "fuentes_cache.json"
CACHE_MAX_DIAS = 14  # más antigua no se usa: la fuente puede haber cambiado o desaparecido


def completar_con_cache(fuentes: list[Source], eventos: dict, resultados: dict, hoy: date, horizonte: date,
                        cache: dict, no_leidas: set[str] = frozenset()) -> None:
    """Si una fuente no se ha podido leer entera, se completan sus conciertos con los de su última lectura
    completa (máx. 14 días): así no se pierden ni sus conciertos ni lo que aporta a los que comparte con otras.
    Las fuentes leídas por completo actualizan la caché. `no_leidas`: fuentes que esta ejecución no intentó
    leer (reintento parcial); sus conciertos de la caché entran sin aviso."""
    hoy_s = hoy.isoformat()
    for s in fuentes:
        res = resultados.setdefault(s.id, {})
        evs = eventos.setdefault(s.id, [])
        if s.id not in no_leidas and res.get("completa"):
            cache[s.id] = {"fecha": hoy_s, "eventos": [e.to_dict() for e in evs if e.fecha >= hoy]}
            continue
        c = cache.get(s.id)
        if not c or c.get("fecha", "") < (hoy - timedelta(days=CACHE_MAX_DIAS)).isoformat():
            continue
        ya = {(e.fecha, norm(e.artista)) for e in evs}
        anadidos = []
        for d in c.get("eventos", []):
            e = RawEvent.from_dict(d)
            if not (hoy <= e.fecha <= horizonte) or (e.fecha, norm(e.artista)) in ya:
                continue
            if s.id not in no_leidas:
                e.nota = clean(f"{e.nota or ''} Dato de la última lectura completa de {s.nombre} ({c['fecha']}): "
                               f"hoy no se pudo leer.")
            anadidos.append(e)
        evs.extend(anadidos)
        if s.id not in no_leidas and anadidos:
            res["desde_cache"] = len(anadidos)
            res["cache_fecha"] = c["fecha"]


# ---------------------------------------------------------------- normalización y ámbito
def municipio_item(it: Item) -> str | None:
    ev = it.ev
    ciudad_m = municipio(ev.ciudad) if ev.ciudad else None
    if ev.ciudad and not ciudad_m:
        return None  # la fuente da una ciudad fuera de la Comunidad de Madrid (p. ej. Granada)
    return sala_municipio(ev.sala) or ciudad_m or it.src.municipio_defecto


def preparar(items: list[Item], hoy: date, horizonte: date) -> tuple[list[Item], dict]:
    fuera = {"fuera_de_ventana": 0, "fuera_de_ambito": 0, "ejemplos_fuera_de_ambito": []}
    ok = []
    for it in items:
        ev = it.ev
        if not ev.artista or not (hoy <= ev.fecha <= horizonte):
            fuera["fuera_de_ventana"] += 1
            continue
        ev.sala = canon_sala(ev.sala)
        if not municipio_item(it):
            fuera["fuera_de_ambito"] += 1
            if len(fuera["ejemplos_fuera_de_ambito"]) < 25:
                fuera["ejemplos_fuera_de_ambito"].append(
                    f"{ev.fecha} {ev.artista} @ {ev.sala or '?'} ({ev.ciudad or 'sin ciudad'}) [{it.src.nombre}]")
            continue
        ok.append(it)
    return ok, fuera


# ---------------------------------------------------------------- unificación
def unificar(items: list[Item]) -> list[dict]:
    por_fecha: dict[date, list[Item]] = {}
    for it in items:
        por_fecha.setdefault(it.ev.fecha, []).append(it)
    recs = []
    for f in sorted(por_fecha):
        for cl in agrupar(por_fecha[f]):
            try:
                recs.append(construir(cl, municipio_item))
            except Exception:  # noqa: BLE001 - un registro raro no debe tumbar toda la ejecución
                log.error("No se pudo construir %s %s:\n%s", f, [i.ev.artista for i in cl.items],
                          traceback.format_exc())
    recs = fusionar_conflictos_sala(recs)
    marcar_conflictos_cartel(recs)
    for r in recs:
        separar_ciclo(r)
    return recs


def etiquetas_por_fuente(r: dict) -> list[list[str]]:
    por: dict[str, list[str]] = {}
    for e in r.get("estilo_fuente", []):
        grupo = e["fuente"].split(" (")[0]  # las variantes de una misma web cuentan una vez
        if e["estilo"] not in por.setdefault(grupo, []):
            por[grupo].append(e["estilo"])
    return list(por.values())


def ficha_de(r: dict, cache: dict) -> dict | None:
    """Ficha del artista: la del título tal cual o, si no la hay, la del nombre limpio (sin ciclo, festival ni gira)
    o la del cabeza de cartel (scraper/nombres.py)."""
    from .artistas import ficha
    from .nombres import claves_ficha
    for n in claves_ficha(r):
        f = ficha(cache.get(norm(n)))
        if f:
            return f
    return None


def origen_por_agenda(r: dict, cache: dict) -> None:
    """Tributos y espectáculos que no se buscan en webs de música: el origen que dice la página de la agenda."""
    from .artistas import agenda_valida, clave_agenda
    if r.get("nacionalidad"):
        return
    ent = cache.get(clave_agenda(r["artista"])) or {}
    ag = ent.get("agenda") or {}
    if agenda_valida(ag, ent.get("nombre")):
        r["nacionalidad"] = ag["pais"]
        r["nacionalidad_fuente"] = f"la agenda ({ag['url'].split('/')[2]}): «{ag.get('frase', '')[:160]}»"
        r["origen_no_aplica"] = None


def aplicar_ficha(r: dict, f: dict | None) -> None:
    """Grupos de filtro, estilos, nacionalidad y foto.

    1. Si la agenda lo presenta como teatro, musical, danza… no es un concierto: no se usa la ficha de ningún
       "artista" (evita homónimos como el musical "Los Miserables" y el grupo punk chileno).
    2. Si hay ficha de webs de música, los grupos salen del consenso ponderado de todas (Discogs, MusicBrainz,
       Last.fm, Wikipedia) y de las etiquetas concretas de las agendas: el principal y los que tengan un peso
       comparable, no todos los que aparezcan.
    3. Si no, de las etiquetas de las agendas. Las genéricas ("Pop / Rock") se marcan como tales."""
    from .clasificar import (contexto_de_fuentes, en_foco, es_espectaculo, grupos_de_agenda, grupos_de_evidencias,
                             pesos_de_agenda, revisar_homonimos, titulo_fuera_de_foco)
    etiquetas = etiquetas_por_fuente(r)
    generico, estilos, segun = False, [], []
    r.pop("estilo_descartado", None)
    r.pop("homonimo_descartado", None)
    if es_espectaculo([e for es in etiquetas for e in es]):
        f, cats, origen = None, ["fuera de foco"], "agenda (espectáculo, no concierto)"
        # el origen que viniera de buscar el título como artista (Wikidata, MusicBrainz…) tampoco vale
        if str(r.get("nacionalidad_fuente") or "").startswith(("Wikidata", "Wikipedia", "Discogs", "MusicBrainz")):
            r["nacionalidad"], r["nacionalidad_fuente"] = None, None
    else:
        cats, origen = [], "agenda"
        grupos_agenda, generico_agenda = grupos_de_agenda(etiquetas)
        if f and f.get("evidencias"):
            contexto = contexto_de_fuentes([x.get("id") for x in r.get("fuentes", [])])
            p_agenda = pesos_de_agenda(etiquetas)
            _, homonimo = revisar_homonimos(f["evidencias"], p_agenda)
            if homonimo:
                r["homonimo_descartado"] = homonimo
            cats, estilos = grupos_de_evidencias(f["evidencias"], grupos_agenda, p_agenda, contexto)
            if cats:
                pesos: dict[str, float] = {}
                for e in f["evidencias"]:
                    pesos[e["fuente"]] = pesos.get(e["fuente"], 0) + e["peso"]
                segun = [x for x, _ in sorted(pesos.items(), key=lambda x: -x[1])]
                if any(g in p_agenda for g in cats):
                    segun.append("agenda")
                origen = segun[0]
        if not cats:
            if f and f.get("evidencias"):
                # la única web de música que lo nombra es Last.fm por coincidencia de nombre y no concuerda
                # con lo que dice la agenda: puede ser otro artista con el mismo nombre
                r["estilo_descartado"] = [e["nombre"] for e in f["evidencias"]
                                          if e.get("debil") and e["fuente"] == "Last.fm"][:3] or None
                if not r["estilo_descartado"]:
                    r.pop("estilo_descartado")
            cats, generico = grupos_de_agenda(etiquetas)
            origen = "agenda"
            estilos = []
        if not cats:
            cats = ["sin clasificar"]
    if "tributos y versiones" in r.get("categorias", []) and "tributos y versiones" not in cats:
        cats.append("tributos y versiones")
    if titulo_fuera_de_foco(r["artista"]):
        cats, generico = ["fuera de foco"], False
    r["ficha"] = f
    r["grupos"], r["grupos_origen"], r["grupos_generico"], r["grupos_segun"] = cats, origen, generico, segun
    r["categoria"] = cats[0]
    r["en_foco"] = en_foco(cats)
    r["estilos_discogs"] = estilos[:5]
    from .clasificar import grupo_de
    r["genero_discogs"] = [g for g in ((f or {}).get("generos") or []) if grupo_de(g, "genero") in cats] \
        if not origen.startswith("agenda") else []
    if origen != "agenda":
        r.pop("estilo_descartado", None)
    # el origen leído en textos (página de la agenda, Last.fm) se vuelve a calcular siempre con la regla actual
    fuente_nac = str(r.get("nacionalidad_fuente") or "")
    if fuente_nac.startswith(("Last.fm", "la agenda (")) and not fuente_nac.startswith("la agenda (en el título)"):
        r["nacionalidad"], r["nacionalidad_fuente"] = None, None
    if f and f.get("pais") and (not r.get("nacionalidad") or
                                str(r.get("nacionalidad_fuente", "")).startswith("MusicBrainz")):
        r["nacionalidad"], r["nacionalidad_fuente"] = f["pais"], f["fuente_pais"]
    r["imagen"] = (f or {}).get("imagen") or r.get("imagen_evento")
    # la agenda a veces pone el país en el título: "THE SILENCERS (UK)"
    from .nombres import pais_del_titulo
    if not r.get("nacionalidad") and pais_del_titulo(r["artista"]):
        r["nacionalidad"], r["nacionalidad_fuente"] = pais_del_titulo(r["artista"]), "la agenda (en el título)"
    # teatro, musicales, danza…: no es un artista, el origen no aplica (no cuenta como "origen sin confirmar")
    # y jam sessions, micros abiertos, "Concierto de blues": no hay un artista del que decir el origen
    from .origen import sin_artista
    r["origen_no_aplica"] = (origen.startswith("agenda (espect") or (sin_artista(r["artista"]) and not r.get("nacionalidad"))) or None


def cambios_grupos(previos: dict[str, list[str]], recs: list[dict], hoy: str) -> dict:
    """Conciertos futuros por grupo y cuántos han entrado o salido de cada grupo respecto a la ejecución anterior
    (solo los que ya existían: así se ve si un cambio de clasificación ha movido muchos conciertos de golpe)."""
    out: dict[str, dict] = {}
    for r in recs:
        if r["fecha"] < hoy:
            continue
        ahora = r.get("grupos") or []
        for g in ahora:
            out.setdefault(g, {"total": 0, "entran": 0, "salen": 0, "ejemplos_entran": [], "ejemplos_salen": []})
            out[g]["total"] += 1
        if r["id"] not in previos:
            continue
        antes = previos[r["id"]]
        for g, tipo in [(g, "entran") for g in ahora if g not in antes] + [(g, "salen") for g in antes if g not in ahora]:
            d = out.setdefault(g, {"total": 0, "entran": 0, "salen": 0, "ejemplos_entran": [], "ejemplos_salen": []})
            d[tipo] += 1
            if len(d["ejemplos_" + tipo]) < 8 and r["artista"] not in d["ejemplos_" + tipo]:
                d["ejemplos_" + tipo].append(r["artista"])
    return out


def _grupos_previos(recs: list[dict]) -> dict[str, list[str]]:
    return {r["id"]: list(r.get("grupos") or []) for r in recs}


def _match_prev(r: dict, prev: list[dict]) -> dict | None:
    for p in prev:
        if p["fecha"] != r["fecha"]:
            continue
        sa, sb = [x for x in r["sala"].split(" / ") if x], [x for x in p["sala"].split(" / ") if x]
        if sa and sb and not any(misma_sala(x, y) for x in sa for y in sb):
            continue
        if artistas_coinciden([r["artista"]], nombres_rec(p)) or artistas_coinciden([p["artista"]], nombres_rec(r)):
            return p
    return None


def _fuera_de_cobertura(p: dict, srcs: list[str]) -> bool:
    """Registro que solo venía de Madrid en Vivo y en estilos que ya no se leen (teatro, musicales, DJ)."""
    from .sources.agregadores import MEV_EXCLUIDOS
    if not srcs or set(srcs) != {"madridenvivo"}:
        return False
    est = [e["estilo"] for e in p.get("estilo_fuente", []) if "Madrid en Vivo" in e.get("fuente", "")]
    return bool(est) and all(e in MEV_EXCLUIDOS for e in est)


# restos de leer UTF-8 con otra codificación ("├", "Ã©", "â€™"): nunca aparecen en un nombre real
MOJIBAKE = re.compile(r"[├┤┬┴┼╢╣║╗╝]|Ã[\x80-\xbf©±³º¡\u0152-\u2122]|â€")


def conciliar(recs: list[dict], anteriores: list[dict], hoy: date, resultados: dict, fuentes: dict[str, Source]):
    """Asigna ids estables, fechas de primera/última vez y marca 'posiblemente cancelado'."""
    hoy_s = hoy.isoformat()
    prev_por_fecha: dict[str, list[dict]] = {}
    for p in anteriores:
        prev_por_fecha.setdefault(p["fecha"], []).append(p)
    usados = set()
    ids = set()
    for r in recs:
        p = _match_prev(r, [x for x in prev_por_fecha.get(r["fecha"], []) if x["id"] not in usados])
        if p:
            usados.add(p["id"])
            r["id"] = p["id"]
            r["primera_vez_visto"] = p.get("primera_vez_visto") or hoy_s
        else:
            r["id"] = hacer_id(r)
            r["primera_vez_visto"] = hoy_s
        while r["id"] in ids:
            r["id"] = r["id"][:10] + format(len(ids) % 256, "02x")
        ids.add(r["id"])
        r["ultima_vez_visto"] = hoy_s
    limite_hist = (hoy - timedelta(days=HISTORIA_DIAS)).isoformat()
    arrastrados = []
    for p in anteriores:
        if p["id"] in usados or p["id"] in ids:
            continue
        if p["fecha"] < limite_hist:
            continue
        if MOJIBAKE.search(p["artista"]):
            continue  # nombre mal descodificado en una lectura anterior ("Brujer├Ła"): no es un concierto aparte
        if p["fecha"] < hoy_s:
            arrastrados.append(p)  # ya pasó: se conserva como histórico del mes
            continue
        # absorbido por un registro actual (mismo día y sala, nombre equivalente): no es una cancelación
        if any(r["fecha"] == p["fecha"] and (not r["sala"] or not p["sala"] or
                                             any(misma_sala(x, y) for x in r["sala"].split(" / ")
                                                 for y in p["sala"].split(" / ")))
               and coinciden_flexible([p["artista"]], nombres_rec(r)) for r in recs):
            continue
        srcs = [f["id"] for f in p["fuentes"] if f["id"] in fuentes]
        if _fuera_de_cobertura(p, srcs):
            continue  # la fuente ya no lee ese tipo de actos (p. ej. teatro en Madrid en Vivo): no es una cancelación
        reconf = [s for s in srcs if fuentes[s].reconfirma]
        if not reconf:
            arrastrados.append(p)
            continue
        caidas = [s for s in reconf if not resultados.get(s, {}).get("completa")]
        if caidas:
            nota = ("No se pudo reconfirmar hoy: no se leyó por completo " +
                    ", ".join(fuentes[s].nombre for s in caidas) + ". Se mantiene el dato anterior.")
            p["notas"] = [n for n in p["notas"] if not n.startswith("No se pudo reconfirmar hoy")] + [nota]
        else:
            if p["estado"] != "posiblemente cancelado":
                p["estado"] = "posiblemente cancelado"
                p["notas"].append(f"Ya no aparece en ninguna de sus fuentes (comprobado el {hoy_s}); "
                                  f"visto por última vez el {p.get('ultima_vez_visto')}.")
        arrastrados.append(p)
    return recs + arrastrados


# ---------------------------------------------------------------- salidas
CSV_COLS = ["id", "fecha", "hora", "artista", "invitados", "ciclo", "sala", "municipio", "precio", "precio_segun",
            "grupo", "estilos", "generos", "estilo_segun", "etiqueta_agenda", "nacionalidad", "nacionalidad_segun",
            "estado", "confirmado_por_la_sala", "en_foco", "fuentes", "urls", "notas", "primera_vez_visto",
            "ultima_vez_visto"]


def escribir_csv(recs: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(CSV_COLS)
        for r in recs:
            w.writerow([
                r["id"], r["fecha"], r["hora"] or "", r["artista"], " + ".join(r["invitados"]), r.get("ciclo") or "",
                r["sala"], r["municipio"] or "", r["precio"] or "", (r.get("precio_fuente") or {}).get("nombre", ""),
                r["categoria"], ", ".join(r.get("estilos_discogs") or []), ", ".join(r.get("genero_discogs") or []),
                r.get("grupos_origen") or "",
                " | ".join(f"{e['estilo']} ({e['fuente']})" for e in r["estilo_fuente"]),
                r["nacionalidad"] or "sin confirmar", r["nacionalidad_fuente"] or "", r["estado"],
                "sí" if r.get("confirmado_sala") else "no",
                "sí" if r["en_foco"] else "no", " | ".join(f["nombre"] for f in r["fuentes"]),
                " | ".join(f["url"] for f in r["fuentes"]), " | ".join(r["notas"]),
                r["primera_vez_visto"] or "", r["ultima_vez_visto"] or ""])


def informe_fuentes(fuentes: list[Source], resultados: dict, recs: list[dict], anteriores_ids: set,
                    historial: dict, hoy: date) -> list[dict]:
    grupo = {s.id: s.grupo for s in fuentes}
    out = []
    for s in fuentes:
        res = resultados.get(s.id, {})
        mios = [r for r in recs if r["fecha"] >= hoy.isoformat() and any(f["id"] == s.id for f in r["fuentes"])]
        solo = [r for r in mios if {grupo.get(f["id"], f["id"]) for f in r["fuentes"]} == {s.grupo}]
        nuevos = [r for r in mios if r["id"] not in anteriores_ids]
        h = historial.get(s.id, {})
        aviso = None
        if res and (not res.get("funciono") or res.get("brutos", 0) == 0) and h.get("ultimo_conteo", 0) > 0:
            aviso = f"posible cambio en la web: antes daba {h['ultimo_conteo']} conciertos (último éxito {h.get('ultima_ok')})"
            if h.get("ultima_ok"):
                dias = (hoy - date.fromisoformat(h["ultima_ok"])).days
                if dias >= DIAS_ALERTA:
                    aviso = f"lleva {dias} días sin leerse bien (último éxito {h['ultima_ok']}, daba {h['ultimo_conteo']})"
        elif (res.get("funciono") and not res.get("no_leida") and h.get("ultimo_conteo", 0) >= 10
              and len(mios) < 0.3 * h["ultimo_conteo"]):
            # lee algo, pero muchos menos de lo habitual: suele ser un cambio de diseño que el lector no entiende
            aviso = f"da muchos menos conciertos de lo habitual ({len(mios)} frente a {h['ultimo_conteo']}): posible cambio en la web"
        out.append({**s.meta(), "funciono": res.get("funciono", False), "estado": res.get("estado", "no ejecutada"),
                    "conciertos": len(mios), "nuevos": len(nuevos), "solo_en_esta": len(solo),
                    "eventos_brutos": res.get("brutos", 0), "paginas": res.get("paginas", 0),
                    "errores": res.get("errores", []), "robots": res.get("robots", ""),
                    "robots_bloquea": res.get("estado") == "bloqueado_robots", "aviso": aviso,
                    "segundos": res.get("segundos"), "reintento": res.get("reintento"),
                    "desde_cache": res.get("desde_cache", 0), "cache_fecha": res.get("cache_fecha"),
                    "no_leida": res.get("no_leida", False)})
        if res.get("funciono") and res.get("brutos", 0) > 0 and not res.get("no_leida"):
            historial[s.id] = {"ultima_ok": hoy.isoformat(), "ultimo_conteo": len(mios)}
    return out


DIAS_ALERTA = 3  # días seguidos sin leer bien una fuente para avisar
PRESUPUESTO_FICHAS = 2400  # tope de la ejecución diaria para fichas (los pendientes siguen cada 2 horas)


def ejecutar(hoy: date | None = None, solo: list[str] | None = None, fetcher: Fetcher | None = None,
             musicbrainz: bool = True, max_mb: int = 700, reintentar: bool = False,
             pausa_reintento: float = PAUSA_REINTENTO_SEG) -> dict | None:
    """Ejecución completa. Con `solo` o `reintentar`, se leen solo algunas fuentes y las demás entran con su
    última lectura completa (caché), así que la agenda publicada nunca pierde conciertos de las no leídas.
    `reintentar`: vuelve a leer las fuentes que fallaron en la última ejecución; si ninguna responde, no
    cambia nada y devuelve None."""
    hoy = hoy or datetime.now(timezone.utc).astimezone().date()
    horizonte = hoy + timedelta(days=HORIZONTE_DIAS)
    fetcher = fetcher or Fetcher()
    estado = _read("estado.json", {})
    if reintentar:
        solo = estado.get("fuentes_fallidas") or []
        if not solo:
            log.info("Reintento: ninguna fuente falló en la última ejecución")
            return None
    fuentes = [s for s in FUENTES if not solo or s.id in solo]
    no_leidas = {s.id for s in FUENTES} - {s.id for s in fuentes}
    anteriores = _read("concerts.json", {}).get("conciertos", [])
    anteriores_ids = {p["id"] for p in anteriores}
    # los grupos de la ejecución anterior se copian ya: los registros anteriores se reutilizan (y se modifican)
    # al conciliar, así que al final ya tendrían los grupos nuevos
    grupos_previos = _grupos_previos(anteriores)
    t0 = time.monotonic()
    # Las fichas de artista usan otras webs (Discogs, Wikipedia…): se buscan mientras se leen las agendas,
    # empezando por los artistas de la ejecución anterior; al terminar se completan los nuevos.
    cache_art = _read("artistas.json", {})
    cache_mb = _read("musicbrainz_cache.json", {})

    def guardar_fichas():
        _write("artistas.json", cache_art)
        _write("musicbrainz_cache.json", cache_mb)

    parar, hilo, previas = threading.Event(), None, {}
    if musicbrainz and anteriores and not no_leidas:
        from .artistas import enriquecer
        hilo = threading.Thread(target=lambda: previas.update(
            enriquecer([p for p in anteriores if p["fecha"] >= hoy.isoformat()], cache_art, hoy,
                       presupuesto_seg=PRESUPUESTO_FICHAS, parar=parar, guardar=guardar_fichas,
                       mb_cache=cache_mb)), daemon=True)
        hilo.start()
    eventos, resultados = rastrear(fuentes, fetcher, hoy, horizonte, estado.setdefault("fuentes", {}),
                                   pausa_reintento=pausa_reintento)
    if reintentar and not any(r["funciono"] for r in resultados.values()):
        log.info("Reintento: ninguna de las fuentes fallidas ha respondido; no se cambia nada")
        if hilo:
            parar.set()
        return None
    previos = estado.get("resultados", {})
    for sid in no_leidas:  # su estado es el de la última vez que se leyeron
        resultados[sid] = {**previos.get(sid, {}), "no_leida": True}
    cache_fuentes = _read(CACHE_FUENTES, {})
    completar_con_cache(FUENTES, eventos, resultados, hoy, horizonte, cache_fuentes, no_leidas)
    por_id = {s.id: s for s in FUENTES}
    items = [Item(e, por_id[sid]) for sid, evs in eventos.items() if sid in por_id for e in evs]
    items, fuera = preparar(items, hoy, horizonte)
    recs = unificar(items)
    recs = conciliar(recs, anteriores, hoy, resultados, {s.id: s for s in FUENTES})
    correcciones = load_json("correcciones.json")["correcciones"]
    recs, res_corr = aplicar_correcciones(recs, correcciones, hoy.isoformat())
    grupo = {s.id: s.grupo for s in FUENTES}
    for r in recs:
        recalcular_categorias(r)
        recalcular_estado(r, lambda i: grupo.get(i, i))
    # ficha musical del artista principal (Wikidata, Discogs, Wikipedia, Last.fm)
    art_stats = {"desactivado": True}
    if musicbrainz:  # misma bandera: sin red externa en pruebas
        from .artistas import enriquecer
        if hilo:
            parar.set()
            hilo.join()
        resto = max(PRESUPUESTO_FICHAS - (time.monotonic() - t0), 300)
        art_stats = enriquecer(recs, cache_art, hoy, presupuesto_seg=resto, guardar=guardar_fichas,
                               mb_cache=cache_mb)
        art_stats["durante_agendas"] = {k: previas.get(k, 0) for k in ("consultados", "completados")}
        guardar_fichas()
    from .artistas import ficha
    for r in recs:
        aplicar_ficha(r, ficha_de(r, cache_art))
        origen_por_agenda(r, cache_art)
    # MusicBrainz (solo para los que siguen sin nacionalidad)
    mb_stats = {"desactivado": True}
    if musicbrainz:
        from .musicbrainz import completar, fetcher_musicbrainz
        mb_stats = completar(recs, cache_mb, hoy, fetcher_musicbrainz(), max_consultas=max_mb)
        _write("musicbrainz_cache.json", cache_mb)
    recs.sort(key=lambda r: (r["fecha"], r["hora"] or "99", norm(r["artista"])))
    # estilos que no se han podido traducir a categoría
    sin_mapear = sorted({e["estilo"] + " (" + e["fuente"] + ")" for r in recs for e in r["estilo_fuente"]
                         if categoria_de(e["estilo"]) is None})
    historial = estado.setdefault("historial_fuentes", {})
    inf_fuentes = informe_fuentes(FUENTES, resultados, recs, anteriores_ids, historial, hoy)
    futuros = [r for r in recs if r["fecha"] >= hoy.isoformat()]
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    informe = {
        "version": __version__,
        "generado": ahora,
        "modo": ("reintento de " + ", ".join(sorted(s.id for s in fuentes))) if no_leidas else "completa",
        "hoy": hoy.isoformat(),
        "horizonte": horizonte.isoformat(),
        "duracion_seg": round(time.monotonic() - t0),
        "totales": {
            "conciertos": len(futuros),
            "en_foco": sum(r["en_foco"] for r in futuros),
            "contrastados": sum(r["estado"] == "contrastado" for r in futuros),
            "una_fuente": sum(r["estado"] == "1_fuente" for r in futuros),
            "conflictos": sum(r["estado"] == "conflicto" for r in futuros),
            "posiblemente_cancelados": sum(r["estado"] == "posiblemente cancelado" for r in futuros),
            "nuevos_hoy": sum(r["id"] not in anteriores_ids for r in futuros),
            "fuentes_ok": sum(f["funciono"] for f in inf_fuentes),
            "fuentes_total": len(inf_fuentes),
            "peticiones_http": fetcher.requests_count,
            **fuera,
        },
        "fuentes": inf_fuentes,
        "sin_agenda_legible": SIN_AGENDA_LEGIBLE,
        "no_usar": NO_USAR,
        "correcciones": res_corr,
        "musicbrainz": mb_stats,
        "artistas": art_stats,
        "estilos_sin_mapear": sin_mapear[:300],
        "grupos": cambios_grupos(grupos_previos, recs, hoy.isoformat()),
        # lo que requiere mirar a mano (se abre también un issue en GitHub, ver .github/workflows)
        "alertas": [f"{f['nombre']}: {f['aviso']}" for f in inf_fuentes if f.get("aviso")],
    }
    # la ejecución completa del día queda registrada aunque luego los reintentos rehagan el informe
    if no_leidas:
        informe["ultima_completa"] = _read("informe.json", {}).get("ultima_completa")
    else:
        informe["ultima_completa"] = {"generado": ahora, "duracion_seg": informe["duracion_seg"],
                                      "fuentes_ok": informe["totales"]["fuentes_ok"],
                                      "fuentes_total": informe["totales"]["fuentes_total"],
                                      "peticiones_http": informe["totales"]["peticiones_http"]}
    _write("concerts.json", {"generado": ahora, "hoy": hoy.isoformat(), "horizonte": horizonte.isoformat(),
                             "conciertos": recs})
    escribir_csv(recs, DATA / "concerts.csv")
    _write("informe.json", informe)
    _write(CACHE_FUENTES, cache_fuentes)
    estado["fuentes_fallidas"] = sorted(sid for sid, r in resultados.items() if r.get("estado") in REINTENTABLES)
    estado["resultados"] = {sid: {k: r.get(k) for k in ("estado", "funciono", "completa", "brutos", "paginas",
                                                        "errores", "robots", "segundos")}
                            for sid, r in resultados.items()}
    estado["ultima_ejecucion"] = ahora
    _write("estado.json", estado)
    return informe


def ejecutar_fichas(hoy: date | None = None, presupuesto_seg: float = 3000) -> dict:
    """Solo fichas de artista: no vuelve a leer las agendas. Completa los artistas pendientes de
    data/concerts.json y actualiza concerts.json, concerts.csv y el bloque 'artistas' del informe."""
    from .artistas import enriquecer, ficha
    hoy = hoy or datetime.now(timezone.utc).astimezone().date()
    datos = _read("concerts.json", {})
    recs = datos.get("conciertos", [])
    cache_art = _read("artistas.json", {})
    cache_mb = _read("musicbrainz_cache.json", {})

    def guardar_fichas():
        _write("artistas.json", cache_art)
        _write("musicbrainz_cache.json", cache_mb)

    stats = enriquecer(recs, cache_art, hoy, presupuesto_seg=presupuesto_seg, guardar=guardar_fichas,
                       mb_cache=cache_mb)
    if not stats["consultados"] and not stats["completados"]:
        return stats  # nada pendiente: no se toca ningún archivo (ni commit ni nueva publicación)
    _write("musicbrainz_cache.json", cache_mb)
    _write("artistas.json", cache_art)
    previos = _grupos_previos(recs)
    for r in recs:
        aplicar_ficha(r, ficha_de(r, cache_art))
        origen_por_agenda(r, cache_art)
    _write("concerts.json", datos)
    escribir_csv(recs, DATA / "concerts.csv")
    informe = _read("informe.json", {})
    informe["grupos"] = cambios_grupos(previos, recs, hoy.isoformat())
    stats["ultima_carga_fichas"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    informe["artistas"] = stats
    informe["version_fichas"] = __version__  # la clasificación publicada es la de esta versión
    _write("informe.json", informe)
    return stats


def reaplicar_fichas() -> None:
    """Aplica a data/concerts.json las fichas de data/artistas.json (tras unir datos de dos ejecuciones)."""
    from .artistas import ficha
    datos = _read("concerts.json", {})
    recs = datos.get("conciertos", [])
    if not recs:
        return
    cache = _read("artistas.json", {})
    for r in recs:
        aplicar_ficha(r, ficha_de(r, cache))
        origen_por_agenda(r, cache)
    _write("concerts.json", datos)
    escribir_csv(recs, DATA / "concerts.csv")
