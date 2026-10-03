"""Orquestador: rastrea las fuentes, unifica, aplica correcciones y escribe los datos."""
from __future__ import annotations

import csv
import json
import re
import logging
import threading
import time
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import __version__
from .clasificar import categoria_de
from .correcciones import aplicar as aplicar_correcciones
from .entradas import aplicar_entradas
from .fetch import AntiBotBlocked, Fetcher, RobotsBlocked, RobotsUnreachable
from .merge import (Item, agrupar, artistas_coinciden, coinciden_flexible, construir, fusionar_conflictos_sala,
                    hacer_id, marcar_conflictos_cartel, nombres_rec, recalcular_categorias, recalcular_estado,
                    separar_ciclo)
from .model import RawEvent, Source
from .normalize import (DATA, canon_sala, clean, load_json, misma_sala, municipio, norm, parecido_flexible,
                        sala_municipio, tiene_mojibake)
from .registry import FUENTES, NO_USAR, SIN_AGENDA_LEGIBLE
from .sources.base import Ctx, TiempoAgotado

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
    t0 = time.monotonic()
    ctx = Ctx(fetcher=fetcher, today=hoy, horizon=horizonte, estado=estado.setdefault(src.id, {}),
              limite=t0 + src.tope_seg if src.tope_seg else None)
    evs: list[RawEvent] = []
    res = {"funciono": False, "estado": "", "brutos": 0, "paginas": 0, "errores": [], "robots": ""}
    try:
        for e in src.parser(ctx):
            e.fuente = src.id
            evs.append(e)
        res["funciono"] = True
        res["estado"] = "ok" if evs else "ok_sin_resultados"
    except TiempoAgotado:
        # se queda con lo leído hasta ahora; lo demás sale de su última lectura buena (no es una lectura completa)
        res["funciono"] = bool(evs)
        res["estado"] = "tope_de_tiempo"
        res["errores"].append(f"superó su tiempo máximo de lectura ({round(src.tope_seg / 60)} min): se queda con lo "
                              f"leído y el resto sale de su última lectura buena")
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
    if ctx.limite is not None and time.monotonic() > ctx.limite and res["estado"] != "tope_de_tiempo" and ctx.errors:
        # el lector siguió con otras páginas tras el tope (cada una falló al momento): también es tope de tiempo
        res["estado"] = "tope_de_tiempo"
        ctx.errors = [e for e in ctx.errors if "TiempoAgotado" not in e]
        res["errores"].append(f"superó su tiempo máximo de lectura ({round(src.tope_seg / 60)} min): se queda con lo "
                              f"leído y el resto sale de su última lectura buena")
    res["errores"] += ctx.errors[:20]
    # lectura completa: funcionó, dio resultados y sin errores parciales (páginas caídas, tope de tiempo…)
    res["completa"] = res["funciono"] and bool(evs) and not ctx.errors and res["estado"] != "tope_de_tiempo"
    res["paginas"] = ctx.pages
    res["brutos"] = len(evs)
    res["campos"] = campos_leidos(evs)
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
CACHE_PAGINAS = "paginas.json"  # páginas de concierto y de entradas leídas (scraper/entradas.py)
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


def campos_leidos(evs: list[RawEvent]) -> dict:
    """Qué parte de lo leído trae cada dato (hora, sala, estilo) y qué parte cae en el día más repetido: si una
    fuente deja de dar un dato que daba, o de repente pone casi todo el mismo día, su web ha cambiado."""
    if not evs:
        return {}
    n = len(evs)
    dia = max(Counter(e.fecha for e in evs).values())
    return {"hora": round(100 * sum(bool(e.hora) for e in evs) / n), "sala": round(100 * sum(bool(e.sala) for e in evs) / n),
            "estilo": round(100 * sum(bool(e.estilo) for e in evs) / n), "mismo_dia": round(100 * dia / n), "n": n}


CAMPOS_NOMBRE = {"hora": "la hora", "sala": "la sala", "estilo": "el estilo"}


def cambio_de_diseno(antes: dict | None, ahora: dict | None) -> str | None:
    """Aviso si la fuente ha dejado de dar un dato que daba (≥60 % antes, ≤10 % ahora) o pone de golpe casi todo en
    el mismo día (posible lector que ya no entiende las fechas). Solo con lecturas de 10 o más conciertos."""
    if not antes or not ahora or ahora.get("n", 0) < 10 or antes.get("n", 0) < 10:
        return None
    for k, nombre in CAMPOS_NOMBRE.items():
        if antes.get(k, 0) >= 60 and ahora.get(k, 0) <= 10:
            return f"ya no se lee {nombre} (antes en el {antes[k]} % de sus conciertos, ahora en el {ahora[k]} %): posible cambio en la web"
    if ahora.get("mismo_dia", 0) >= 60 and antes.get("mismo_dia", 0) < 30:
        return (f"pone el {ahora['mismo_dia']} % de sus conciertos el mismo día (antes como mucho el {antes['mismo_dia']} %): "
                "posible cambio en cómo da las fechas")
    return None


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
    # nombre mal descodificado que no se ha podido reparar ("M├ČtorHits"): si ese día en esa sala hay otro concierto
    # bien escrito, es el mismo anunciado por otra web y se descarta; si no, se queda (mejor raro que perdido)
    limpios = {(it.ev.fecha, norm(it.ev.sala)) for it in ok if not tiene_mojibake(it.ev.artista)}
    fuera["mal_codificados"] = sum(1 for it in ok if tiene_mojibake(it.ev.artista) and (it.ev.fecha, norm(it.ev.sala)) in limpios)
    ok = [it for it in ok if not (tiene_mojibake(it.ev.artista) and (it.ev.fecha, norm(it.ev.sala)) in limpios)]
    # una sola grafía por sala: "Teatro Salón Cervantes" / "TEATRO SALÓN CERVANTES", "ContraClub" / "Contraclub" (las
    # que solo cambian en mayúsculas, tildes o signos). Se queda la más usada que no esté toda en mayúsculas
    grafias: dict[str, Counter] = {}
    for it in ok:
        if it.ev.sala:
            grafias.setdefault(norm(it.ev.sala), Counter())[it.ev.sala] += 1
    mejor = {k: max(c, key=lambda x: (not x.isupper(), c[x], x)) for k, c in grafias.items() if len(c) > 1}
    for it in ok:
        if it.ev.sala and norm(it.ev.sala) in mejor:
            it.ev.sala = mejor[norm(it.ev.sala)]
    return ok, fuera


def posibles_alias_salas(recs: list[dict], hoy: str) -> list[dict]:
    """Salas que pueden ser la misma escrita de dos formas, para revisarlas y añadir el alias a mano
    (data/salas_alias.json): nombres casi iguales ("Café Libertad 8" / "Libertad 8 Café") o el mismo artista el mismo
    día en dos salas de nombre parecido. No se unen solas: dos salas distintas pueden llamarse casi igual."""
    from itertools import combinations

    from rapidfuzz import fuzz
    fut = [r for r in recs if r["fecha"] >= hoy]
    cuenta = Counter(x for r in fut for x in (r.get("sala") or "").split(" / ") if x)
    out: dict[tuple, dict] = {}
    nombres = sorted(cuenta)
    for a, b in combinations(nombres, 2):
        na, nb = norm(a), norm(b)
        # aunque ya se unan al comparar conciertos (misma_sala), con dos nombres salen como dos salas en la web
        if len(na) >= 5 and len(nb) >= 5 and na != nb and fuzz.token_sort_ratio(na, nb) >= 88:
            out[(a, b)] = {"salas": [a, b], "conciertos": [cuenta[a], cuenta[b]], "motivo": "nombres casi iguales"}
    por_dia: dict[str, list] = {}
    for r in fut:
        for x in (r.get("sala") or "").split(" / "):
            if x:
                por_dia.setdefault(r["fecha"], []).append((x, r))
    for f, l in por_dia.items():
        for (sa, ra), (sb, rb) in combinations(l, 2):
            if sa == sb or ra is rb or misma_sala(sa, sb) or fuzz.token_set_ratio(norm(sa), norm(sb)) < 60:
                continue
            if artistas_coinciden([ra["artista"]], nombres_rec(rb)):
                k = tuple(sorted((sa, sb)))
                out.setdefault(k, {"salas": list(k), "conciertos": [cuenta[k[0]], cuenta[k[1]]],
                                   "motivo": f"{ra['artista']} el {f} en las dos"})
    return list(out.values())[:30]


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
        # el propio artista no es su telonero ("Valkyria" + "VALKYRIA" de otra agenda)
        if not r.get("festival"):  # en un festival sí: "Saurom" toca en el "Saurom Juglar Fest"
            r["invitados"] = [n for n in r["invitados"] if parecido_flexible(n, r["artista"]) < 90]
    return recs


def etiquetas_por_fuente(r: dict) -> list[list[str]]:
    por: dict[str, list[str]] = {}
    for e in r.get("estilo_fuente", []):
        grupo = e["fuente"].split(" (")[0]  # las variantes de una misma web cuentan una vez
        if e["estilo"] not in por.setdefault(grupo, []):
            por[grupo].append(e["estilo"])
    if (r.get("estilo_texto") or {}).get("estilos"):  # lo que dice el texto de la página: una agenda más
        por["texto de la agenda"] = list(r["estilo_texto"]["estilos"])
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


def _lecturas_agenda(r: dict, cache: dict) -> list[dict]:
    """Lo leído en la página del concierto para este artista (por cada nombre probado y por el título)."""
    from .artistas import clave_agenda
    from .nombres import claves_ficha
    out = []
    for k in [norm(n) for n in claves_ficha(r)] + [clave_agenda(r["artista"])]:
        ent = cache.get(k) or {}
        if (ent.get("agenda") or {}).get("encontrado"):
            out.append(ent)
    return out


def estilos_de_agenda(r: dict, cache: dict) -> None:
    """Estilos que dice la página del concierto ("X es un grupo de rock alternativo"): cuentan como la etiqueta
    de una agenda más, así que concretan las etiquetas paraguas ("Pop / Rock") y dan estilo a quien no lo tiene."""
    estilos, url = [], None
    for ent in _lecturas_agenda(r, cache):
        for e in ent["agenda"].get("estilos") or []:
            if e not in estilos:
                estilos.append(e)
                url = url or ent["agenda"].get("url_estilos") or ent["agenda"].get("url")
    if estilos:
        r["estilo_texto"] = {"estilos": estilos[:5], "url": url}
    else:
        r.pop("estilo_texto", None)


def origen_por_agenda(r: dict, cache: dict) -> None:
    """El origen que dice la página de la agenda, aunque el artista no esté en ninguna web de música (grupos
    locales) o no se busque en ellas (tributos, espectáculos con intérprete)."""
    from .artistas import agenda_valida
    if r.get("nacionalidad"):
        return
    for ent in _lecturas_agenda(r, cache):
        ag = ent["agenda"]
        if agenda_valida(ag, ent.get("nombre")):
            r["nacionalidad"] = ag["pais"]
            r["nacionalidad_fuente"] = f"la agenda ({ag['url'].split('/')[2]}): «{ag.get('frase', '')[:160]}»"
            r["origen_no_aplica"] = None
            return


def tributo_y_estimacion(r: dict, cache: dict) -> None:
    """Dos cosas que se completan al final, cuando ya se sabe todo lo demás:

    - Tributos: a quién homenajean y de dónde es ("THE RUMORS: TRIBUTO FLEETWOOD MAC" → Fleetwood Mac, Reino
      Unido). El origen del concierto sigue siendo el de la banda tributo; el del homenajeado se muestra aparte.
      Si el tributo no tiene estilo, se usa el del homenajeado (un tributo a Queen es hard rock).
    - Origen estimado: si ninguna fuente dice de dónde es el artista y su nombre está en español, "probablemente
      España" (se muestra como estimación, no como dato). No se estima en latina ni urbana, donde es habitual
      que sean de Latinoamérica."""
    from .artistas import ficha, nombre_en_titulo
    from .clasificar import grupos_de_evidencias
    from .nombres import claves_ficha, homenajeado
    from .origen import pais_estimado
    h = homenajeado(r["artista"])
    r.pop("homenaje", None)
    if h:
        hf = ficha(cache.get(norm(h)))
        r["homenaje"] = {"artista": h, "pais": (hf or {}).get("pais")}
        if hf and hf.get("evidencias"):
            cats, estilos = grupos_de_evidencias(hf["evidencias"])
            previos = [g for g in r.get("grupos") or [] if g not in ("sin clasificar", "tributos y versiones")]
            if cats and not previos or r.get("grupos_generico"):
                r["grupos"] = ["tributos y versiones"] + [g for g in cats if g != "tributos y versiones"]
                r["categoria"] = r["grupos"][0]
                r["grupos_generico"] = False
                r["grupos_segun"] = [f"estilo de {h} (homenajeado)"]
            if not r.get("estilos_discogs") and estilos:
                r["estilos_discogs"] = estilos[:5]
    r.pop("nacionalidad_estimada", None)
    r.pop("nacionalidad_estimada_motivo", None)
    if r.get("nacionalidad") or r.get("origen_no_aplica"):
        return
    if {"latina", "urbana y hip hop"} & set(r.get("grupos") or []):
        return
    nombre = nombre_en_titulo(r["artista"]) if h else (claves_ficha(r)[1:2] or [r["artista"]])[0]
    # "McEnroe presenta «La vida libre»", "DEPEDRO presentando su nuevo disco": solo el nombre, no el del disco
    nombre = re.split(r"\s+(?:presenta\w*|en concierto|nuevo disco|su disco|gira|tour)\b|[«\"“]", nombre, flags=re.I)[0]
    if re.search(r"\b(festival|fest|certamen|ciclo|concierto de|conciertos|versiones|jam|vermu|tardeo|apertura|clausura|"
                 r"fiestas?|muestra|encuentro|gala|noche de|programa|foro|jornadas?|congreso|feria|expo)\b", norm(nombre)):
        return  # un festival o un ciclo no es un artista: no se estima nada
    pais, motivo = pais_estimado(nombre)
    if pais:
        r["nacionalidad_estimada"], r["nacionalidad_estimada_motivo"] = pais, motivo


def aplicar_cartel(r: dict, cache: dict) -> None:
    """Fichas de los artistas del cartel (invitados, teloneros, artistas de un festival): país y grupos de cada uno.

    - r["cartel"]: [{nombre, pais?, grupos?, estilos?}] con lo que dicen sus fichas (solo si alguno tiene ficha).
    - r["grupos_cartel"]: {grupo: [artistas]} de los grupos del cartel que no son los del concierto. Con ellos un
      concierto sale también al filtrar por el género de su telonero (y la web dice por quién).
    - Un festival sin estilo propio (su nombre no se busca como artista y las agendas dicen "Festival" o nada)
      toma los grupos que más se repiten en su cartel."""
    from .artistas import ficha
    from .clasificar import NO_GRUPO_CONCIERTO, contexto_de_fuentes, en_foco, grupos_de_evidencias
    r.pop("cartel", None)
    r.pop("grupos_cartel", None)
    if not r.get("invitados") or str(r.get("grupos_origen") or "").startswith("agenda (espect"):
        return
    from .clasificar import grupos_de_agenda, pesos_de_agenda
    contexto = contexto_de_fuentes([x.get("id") for x in r.get("fuentes", [])])
    # las etiquetas del concierto, como con el cabeza de cartel: descartan homónimos (un DJ de techno con el
    # nombre de un cantante latino) y pesan como una web más
    etiquetas = etiquetas_por_fuente(r)
    g_agenda, p_agenda = grupos_de_agenda(etiquetas)[0], pesos_de_agenda(etiquetas)
    cartel = []
    for n in r["invitados"][:40]:
        f = ficha(cache.get(norm(n)))
        x: dict = {"nombre": n}
        if f and f.get("evidencias"):
            gs, est = grupos_de_evidencias(f["evidencias"], g_agenda, p_agenda, contexto)
            gs = [g for g in gs if g not in NO_GRUPO_CONCIERTO]
            if gs:
                x["grupos"], x["estilos"] = gs[:2], est[:3]
        if f and f.get("pais"):
            x["pais"] = f["pais"]
        cartel.append(x)
    if not any(len(x) > 1 for x in cartel):
        return
    r["cartel"] = cartel
    cuenta: dict[str, list[str]] = {}
    for x in cartel:
        for g in x.get("grupos", [])[:1]:  # su grupo principal (el segundo puede venir de un homónimo)
            cuenta.setdefault(g, []).append(x["nombre"])
    if r.get("festival") and (r.get("grupos") in (None, [], ["sin clasificar"]) or r.get("grupos_generico")):
        top = max(len(v) for v in cuenta.values()) if cuenta else 0
        propios = [g for g, v in sorted(cuenta.items(), key=lambda kv: -len(kv[1])) if len(v) >= max(1, top / 2)][:3]
        if propios:
            r["grupos"], r["grupos_origen"], r["grupos_generico"] = propios, "cartel del festival", False
            r["grupos_segun"] = ["fichas de los artistas del cartel"]
            r["categoria"], r["en_foco"] = propios[0], en_foco(propios)
    extra = {g: v for g, v in cuenta.items() if g not in (r.get("grupos") or [])}
    if extra:
        r["grupos_cartel"] = extra


def aplicar_ficha(r: dict, f: dict | None) -> None:
    """Grupos de filtro, estilos, nacionalidad y foto.

    1. Si la agenda lo presenta como teatro, musical, danza… no es un concierto: no se usa la ficha de ningún
       "artista" (evita homónimos como el musical "Los Miserables" y el grupo punk chileno).
    2. Si hay ficha de webs de música, los grupos salen del consenso ponderado de todas (Discogs, MusicBrainz,
       Last.fm, Wikipedia) y de las etiquetas concretas de las agendas: el principal y los que tengan un peso
       comparable, no todos los que aparezcan.
    3. Si no, de las etiquetas de las agendas. Las genéricas ("Pop / Rock") se marcan como tales."""
    from .clasificar import (contexto_de_fuentes, en_foco, es_espectaculo, grupos_de_agenda, grupos_de_evidencias,
                             grupo_de_titulo, pesos_de_agenda, revisar_homonimos)
    etiquetas = etiquetas_por_fuente(r)
    generico, estilos, segun = False, [], []
    r.pop("estilo_descartado", None)
    r.pop("homonimo_descartado", None)
    if es_espectaculo([e for es in etiquetas for e in es]):
        f, cats, origen = None, ["musicales y espectáculos"], "agenda (espectáculo, no concierto)"
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
    if grupo_de_titulo(r["artista"]):
        cats, generico = [grupo_de_titulo(r["artista"])], False
    r["ficha"] = f
    r["grupos"], r["grupos_origen"], r["grupos_generico"], r["grupos_segun"] = cats, origen, generico, segun
    r["categoria"] = cats[0]
    r["en_foco"] = en_foco(cats)
    if not estilos and origen.startswith("agenda"):
        # sin ficha: los estilos de Discogs que nombran las propias etiquetas ("Jazz/Swing" → Swing, "rock
        # alternativo" → Alternative Rock), solo los de los grupos asignados
        from .clasificar import discogs, grupo_de
        estilos = [e for e in discogs([x for es in etiquetas for x in es])[0] if grupo_de(e, "estilo") in cats]
    r["estilos_discogs"] = estilos[:5]
    from .clasificar import grupo_de
    r["genero_discogs"] = [g for g in ((f or {}).get("generos") or []) if grupo_de(g, "genero") in cats] \
        if not origen.startswith("agenda") else []
    if origen != "agenda":
        r.pop("estilo_descartado", None)
    # el origen leído en textos (página de la agenda, Last.fm) se vuelve a calcular siempre con la regla actual
    fuente_nac = str(r.get("nacionalidad_fuente") or "")
    if fuente_nac.startswith(("Last.fm", "la agenda (", "Wikipedia (artículo")) and \
            not fuente_nac.startswith("la agenda (en el título)"):
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
    from .clasificar import grupo_de_titulo as _gt
    r["origen_no_aplica"] = (origen.startswith("agenda (espect") or (sin_artista(r["artista"]) and not r.get("nacionalidad"))
                             or (_gt(r["artista"]) == "musicales y espectáculos" and not r.get("nacionalidad"))) or None


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


def _ms(a: str, b: str) -> bool:
    """Misma sala, con los nombres llevados antes a su forma canónica: un registro anterior puede tener el nombre
    de antes de un alias nuevo ("El Perro de la parte de atrás del coche" = "El Perro Club")."""
    return misma_sala(a, b) or misma_sala(canon_sala(a), canon_sala(b))


def _match_prev(r: dict, prev: list[dict], flexible: bool = False) -> dict | None:
    """El registro de la ejecución anterior que es este concierto. `flexible`: segunda vuelta para los que han
    cambiado de título (ciclo o festival separado del artista, "JAZZ CON SABOR A CLUB 26: X (Festival JazzMadrid)"
    → "X"; el mismo festival con otro nombre): conservan su id, su enlace y su fecha de primera vez."""
    from .cartel import mismo_festival
    for p in prev:
        if p["fecha"] != r["fecha"]:
            continue
        sa, sb = [x for x in r["sala"].split(" / ") if x], [x for x in p["sala"].split(" / ") if x]
        if sa and sb and not any(_ms(x, y) for x in sa for y in sb):
            continue
        if artistas_coinciden([r["artista"]], nombres_rec(p)) or artistas_coinciden([p["artista"]], nombres_rec(r)):
            return p
        if flexible and (coinciden_flexible([p["artista"]], nombres_rec(r)) or
                         coinciden_flexible([r["artista"]], nombres_rec(p)) or
                         artistas_coinciden([_titulo_actual(p)], nombres_rec(r)) or mismo_festival(p["artista"], r["artista"])):
            return p
    return None


def _titulo_actual(p: dict) -> str:
    """El título de un registro anterior tal como se escribiría hoy (sin el ciclo o el festival delante o entre
    paréntesis): "JAZZ CON SABOR A CLUB 26: ACIZ (Festival JazzMadrid)" → "ACIZ"."""
    q = {"artista": p["artista"], "ciclo": None}
    separar_ciclo(q)
    return q["artista"]


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
    # primero los que casan por el nombre; después, los que han cambiado de título
    previo: dict[int, dict] = {}
    for flexible in (False, True):
        for i, r in enumerate(recs):
            if i in previo:
                continue
            p = _match_prev(r, [x for x in prev_por_fecha.get(r["fecha"], []) if x["id"] not in usados], flexible)
            if p:
                usados.add(p["id"])
                previo[i] = p
    for i, r in enumerate(recs):
        p = previo.get(i)
        if p:
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
    from .cartel import mismo_festival
    arrastrados, desaparecidos = [], []
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
        if any(r["fecha"] == p["fecha"] and (
                mismo_festival(p["artista"], r["artista"]) or  # el mismo festival, aunque una agenda no dé bien la sala
                (not r["sala"] or not p["sala"] or any(_ms(x, y) for x in r["sala"].split(" / ")
                                                       for y in p["sala"].split(" / ")))
                and (coinciden_flexible([p["artista"]], nombres_rec(r)) or
                     artistas_coinciden([_titulo_actual(p)], nombres_rec(r))))
               for r in recs):
            continue
        # el mismo día, el mismo artista y en las mismas webs, pero en otra sala que ya estaba en la agenda: es un
        # cambio de sala de una lectura anterior (ItineruM, de Revi Space a Revi Live), no una cancelación. (Si el
        # de la otra sala es nuevo hoy, lo empareja abajo el cambio de sala, que conserva el enlace y el historial.)
        fp = {f["id"] for f in p["fuentes"]}
        if any(i in previo and r["fecha"] == p["fecha"] and fp & {f["id"] for f in r["fuentes"]}
               and artistas_coinciden([p["artista"]], [r["artista"]]) for i, r in enumerate(recs)):
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
            desaparecidos.append(p)
            continue
        arrastrados.append(p)
    # cambio de fecha: el concierto que deja de anunciarse en su día y aparece, en las mismas webs, otro día en la
    # misma sala con el mismo artista; o el mismo día en otra sala (cambio de sala: de Revi Space a Revi Live).
    # Solo si la pareja es única (un artista con dos fechas en la sala no se toca).
    nuevos = [i for i in range(len(recs)) if i not in previo]
    pareja: dict[str, list[int]] = {}
    for p in desaparecidos:
        fp = {f["id"] for f in p["fuentes"]}
        pareja[p["id"]] = [i for i in nuevos if recs[i]["fecha"] >= hoy_s
                           and fp & {f["id"] for f in recs[i]["fuentes"]}
                           and (recs[i]["fecha"] != p["fecha"]) == _misma_sala_rec(recs[i], p)
                           and artistas_coinciden([p["artista"]], nombres_rec(recs[i]))]
    usados_nuevos = Counter(i for c in pareja.values() for i in c)
    for p in desaparecidos:
        c = pareja[p["id"]]
        if len(c) == 1 and usados_nuevos[c[0]] == 1:
            r = recs[c[0]]
            ids.discard(r["id"])
            r["id"], r["primera_vez_visto"] = p["id"], p.get("primera_vez_visto") or hoy_s
            ids.add(r["id"])
            antes = f"el {p['fecha']}" if p["fecha"] != r["fecha"] else f"en {p['sala']}"
            r["notas"] = list(r.get("notas") or []) + [f"Antes se anunciaba {antes} (cambio visto el {hoy_s})."]
            continue
        if p["estado"] != "posiblemente cancelado":
            p["estado"] = "posiblemente cancelado"
            p["notas"].append(f"Ya no aparece en ninguna de sus fuentes (comprobado el {hoy_s}); "
                              f"visto por última vez el {p.get('ultima_vez_visto')}.")
        arrastrados.append(p)
    return recs + arrastrados


def _misma_sala_rec(a: dict, b: dict) -> bool:
    sa, sb = [x for x in (a.get("sala") or "").split(" / ") if x], [x for x in (b.get("sala") or "").split(" / ") if x]
    return bool(sa and sb and any(_ms(x, y) for x in sa for y in sb))


# ---------------------------------------------------------------- confirmación de cada concierto (fase A)
# Cuánto se puede fiar uno de que el concierto existe tal cual: no se exige un número de webs (muchos conciertos
# pequeños solo los anuncia un sitio, y no se pierden), se dice quién lo confirma. Puntos:
#   - la web oficial de la sala o el programa municipal lo anuncia: 4
#   - se vende en una ticketera (fuente o enlace de compra hallado en la página del concierto): 2
#   - agendas y blogs independientes: la primera según su fiabilidad (alta 2, media 1, baja 0) y +1 por cada otra
#     (hasta 3)
#   - las webs no coinciden (hora, sala o cartel): -2; la web de la sala, leída entera, no lo anuncia: -2
# Nivel: 4 o más "confirmado"; 2-3 "probable"; 0-1 "sin confirmar". Cancelado o "¿cancelado?": "sin confirmar".
CONFIANZA = (("confirmado", 4), ("probable", 2), ("sin confirmar", -99))


def puntuar_confianza(r: dict, fuentes: dict[str, Source]) -> dict:
    """Nivel de confirmación de un concierto según quién lo anuncia (ver CONFIANZA). Si todas las webs que lo anuncian
    han fallado hoy y se usa su última lectura buena, se dice y no pasa de "probable"."""
    puntos, motivos = 0, []
    ids = [f["id"] for f in r.get("fuentes") or [] if f.get("id") in fuentes]
    oficial = [fuentes[i] for i in ids if fuentes[i].tipo in ("sala", "institucional") and fuentes[i].prioridad == 1]
    if oficial or r.get("confirmado_sala"):
        puntos += 4
        motivos.append(f"Lo anuncia {oficial[0].nombre.split(' (')[0] if oficial else 'la web oficial de la sala'}"
                       + (" (programa municipal)" if oficial and oficial[0].tipo == "institucional" else ""))
    grupos_agenda = {fuentes[i].grupo for i in ids if fuentes[i].tipo in ("agregador", "blog")}
    # la ticketera de una web cuya agenda ya cuenta (entradas.conciertos.club y conciertos.club) no confirma más
    tick = [fuentes[i] for i in ids if fuentes[i].tipo in ("ticketera", "promotora") and fuentes[i].grupo not in grupos_agenda]
    # un enlace de compra de la misma web que una agenda ya contada (entradas.conciertos.club) no confirma más
    ent = r.get("entradas") or {}
    agendas = {norm(fuentes[i].nombre.split(" (")[0]) for i in ids if fuentes[i].tipo in ("agregador", "blog")}
    if ent and not tick and any(norm(ent.get("nombre") or "").split(" ")[0] in a for a in agendas if a):
        ent = {}
    if tick or ent:
        puntos += 2
        quien = ent.get("nombre") or (tick[0].nombre.split(" (")[0] if tick else "una ticketera")
        motivos.append(f"A la venta en {quien}")
    grupos_ag: dict[str, Source] = {}
    for i in ids:
        sr = fuentes[i]
        if sr.tipo in ("agregador", "blog") and sr.grupo not in grupos_ag:
            grupos_ag[sr.grupo] = sr
    if grupos_ag:
        mejor = max({"alta": 2, "media": 1, "baja": 0}.get(sr.fiabilidad, 1) for sr in grupos_ag.values())
        puntos += mejor + min(len(grupos_ag) - 1, 3)
        motivos.append(f"En {len(grupos_ag)} agenda{'s' if len(grupos_ag) > 1 else ''} o blog{'s' if len(grupos_ag) > 1 else ''}"
                       f" ({', '.join(sr.nombre.split(' (')[0] for sr in list(grupos_ag.values())[:3])}"
                       f"{'…' if len(grupos_ag) > 3 else ''})")
    if r.get("conflictos"):
        puntos -= 2
        campos = sorted({c.get("campo") for c in r["conflictos"] if c.get("campo")})
        fecha_sala = next((v for c in r["conflictos"] if c.get("campo") == "fecha" for v in c.get("versiones", [])[:1]), None)
        if fecha_sala:
            motivos.append(f"La web de la sala lo anuncia el {fecha_sala['valor']}")
        resto = [c for c in campos if c != "fecha"]
        if resto:
            motivos.append("Las webs no coinciden en " + " y ".join(resto))
    if r.get("ausente_web_sala"):
        puntos -= 2
        motivos.append(f"La web de la sala ({r['ausente_web_sala']}) no anuncia nada ese día")
    nivel = next(n for n, minimo in CONFIANZA if puntos >= minimo)
    cache = [f["cache"] for f in r.get("fuentes") or [] if f.get("id") in fuentes and f.get("cache")]
    vivas = {f["id"] for f in r.get("fuentes") or [] if f.get("id") in fuentes and not f.get("cache")}
    if ids and cache and not vivas:
        motivos.append("Las webs que lo anuncian han fallado hoy: se usa su última lectura"
                       + (f" (del {max(cache)[:10]})" if any(cache) else ""))
        if nivel == "confirmado":
            nivel = "probable"
    ev = (r.get("estado_evento") or {}).get("tipo")
    if ev or r.get("estado") == "posiblemente cancelado":
        nivel = "sin confirmar"
        motivos.append("Cancelado o aplazado según la web" if ev else "Ya no aparece en las webs donde se anunciaba")
    return {"nivel": nivel, "puntos": puntos, "motivos": motivos}


def ausencias_web_sala(recs: list[dict], resultados: dict, fuentes: dict[str, Source], eventos: dict, hoy: str,
                      historial: dict | None = None) -> dict:
    """Contrasta cada concierto con la web oficial de su sala, cuando se ha leído entera hoy:
    - la web anuncia al mismo artista otro día (±45 días) y nada el día del concierto: conflicto de fecha, con las dos
      versiones a la vista (r["conflictos"], campo "fecha");
    - la web no anuncia nada ese día: r["ausente_web_sala"] (baja la confirmación). Si anuncia otro concierto ese día no
      se marca: suele ser el mismo con otro nombre ("CARO CAXI" / "CARO TAXI").
    Solo hasta la última fecha que publica esa web (muchas solo anuncian unas semanas), solo en las salas de las que esa
    web anuncia al menos 5 conciertos (la suya, no otras que mencione) y nunca si hoy da muchos menos conciertos de lo
    habitual (lectura incompleta o diseño cambiado: no sería culpa de los conciertos). Devuelve lo marcado por fuente."""
    from .merge import mismo_acto_en_sala
    historial = historial or {}
    marcados: dict[str, dict] = {}
    for r in recs:
        r.pop("ausente_web_sala", None)
        r["conflictos"] = [c for c in r.get("conflictos") or [] if c.get("campo") != "fecha"]
    for sid, evs in eventos.items():
        sr = fuentes.get(sid)
        res = resultados.get(sid, {})
        if not sr or sr.tipo != "sala" or not res.get("completa") or res.get("no_leida") or res.get("desde_cache"):
            continue
        antes = (historial.get(sid) or {}).get("ultimo_conteo") or 0
        if antes >= 10 and len(evs) < 0.5 * antes:
            continue
        cuenta = Counter(canon_sala(e.sala) for e in evs if e.sala)
        salas = [x for x, n in cuenta.items() if n >= 5]
        if not salas or not evs:
            continue
        # hasta dónde publica cada sala: una fuente puede leer varias webs (Intruso publica una semana; Moe, un mes)
        hasta_sala: dict[str, str] = {}
        for e in evs:
            k = canon_sala(e.sala) if e.sala else ""
            hasta_sala[k] = max(hasta_sala.get(k, ""), e.fecha.isoformat())
        dias = {e.fecha.isoformat() for e in evs}
        m = marcados.setdefault(sid, {"ausentes": 0, "otra_fecha": 0})
        pendientes = []
        for r in recs:
            if r["fecha"] < hoy or r["fecha"] in dias or any(f["id"] == sid for f in r.get("fuentes") or []):
                continue
            if r.get("estado") == "posiblemente cancelado":
                continue
            suyas = [sa for x in (r.get("sala") or "").split(" / ") if x for sa in salas if _ms(x, sa)]
            if not suyas or r["fecha"] > max(hasta_sala.get(sa, "") for sa in suyas):
                continue
            f0 = date.fromisoformat(r["fecha"])
            otra = sorted((e for e in evs if abs((e.fecha - f0).days) <= 45
                           and (artistas_coinciden([r["artista"]], [e.artista]) or mismo_acto_en_sala(r["artista"], e.artista, r.get("sala") or ""))),
                          key=lambda e: abs((e.fecha - f0).days))
            if len({e.fecha for e in otra}) > 1:
                continue  # una serie (jam semanal, ciclo): la web la anuncia varios días, no es otra fecha del mismo
            pendientes.append((r, otra))
        # la web de la sala no lista todo lo que hay en ella (solo lo de su promotora, o una parte): si le falta un
        # concierto que anuncian 3 o más webs independientes, su silencio no dice nada de los demás (Vistalegre y
        # Papa Roach, en 8 webs)
        fuertes = [r for r, otra in pendientes if not otra and
                   len({fuentes[f["id"]].grupo for f in r.get("fuentes") or [] if f.get("id") in fuentes}) >= 3]
        if fuertes:
            m["incompleta"] = f"no anuncia {fuertes[0]['artista']} ({fuertes[0]['fecha']}), que dan 3 o más webs"
            pendientes = [(r, otra) for r, otra in pendientes if otra]
        nombre = sr.nombre.split(" (")[0]
        for r, otra in pendientes:
            if otra:
                agendas = list(dict.fromkeys(f["nombre"] for f in r.get("fuentes") or []))
                r["conflictos"].append({"campo": "fecha", "versiones": [
                    {"valor": otra[0].fecha.isoformat(), "fuentes": [sr.nombre]},
                    {"valor": r["fecha"], "fuentes": agendas}]})
                if r.get("estado") != "posiblemente cancelado":
                    r["estado"] = "conflicto"
                m["otra_fecha"] += 1
            else:
                r["ausente_web_sala"] = nombre
                m["ausentes"] += 1
    return {k: v for k, v in marcados.items() if v["ausentes"] or v["otra_fecha"] or v.get("incompleta")}


# ---------------------------------------------------------------- historial de cambios de cada concierto
# Lo que cambia de un concierto entre una lectura y la siguiente (fase 7): fecha, hora, precio, cancelado o aplazado,
# entradas agotadas, artistas que aparecen en el cartel, deja de anunciarse o vuelve. Cada cambio lleva el día en
# que se vio. Solo se apunta lo que dicen las webs: un dato que pasa de nada a algo (una hora que aparece) es dato
# nuevo, no un cambio; una hora o un precio que sale de otra web (la página de entradas en vez de la agenda) tampoco.
CAMBIOS_MAX = 12
OSCILA_DIAS = 3  # una hora o un precio que vuelve a su valor anterior en estos días: no cambió, era ruido
# versión de las reglas: los cambios apuntados con reglas anteriores se descartan (el primer día, 3-10-2026, apuntó
# como cambios lo que solo aportaban las salas recién añadidas)
REGLAS_CAMBIOS = 2


def _precios(p: str | None) -> list[float]:
    return sorted({float(x.replace(",", ".")) for x in re.findall(r"\d+(?:[.,]\d+)?", p or "")})


def foto_cambios(recs: list[dict]) -> dict[str, dict]:
    """Lo que hace falta de cada concierto para ver después qué ha cambiado (se toma antes de tocarlos)."""
    return {r["id"]: {"fecha": r["fecha"], "sala": r.get("sala") or "", "hora": r.get("hora"),
                      "hora_pagina": bool(r.get("hora_pagina")), "precio": r.get("precio"),
                      "precio_pagina": bool((r.get("precio_fuente") or {}).get("pagina")),
                      "evento": (r.get("estado_evento") or {}).get("tipo"), "agotado": bool(r.get("agotado")),
                      "estado": r.get("estado"), "invitados": list(r.get("invitados") or []),
                      "fuentes": sorted({f.get("id") for f in r.get("fuentes") or []}),
                      "cambios": list(r.get("cambios") or [])}
            for r in recs if r.get("id")}


def registrar_cambios(recs: list[dict], antes: dict[str, dict], hoy: str) -> int:
    """Añade a cada concierto (r["cambios"]) lo que ha cambiado desde `antes` (foto_cambios). Devuelve cuántos."""
    nuevos = 0
    for r in recs:
        p = antes.get(r.get("id"))
        if not p:
            continue
        cambios = [dict(c) for c in (r.get("cambios") or p["cambios"]) if c.get("r") == REGLAS_CAMBIOS]
        hechos: list[dict] = []
        # hora, precio y cartel solo si lo dicen las mismas webs antes y después: si se suma o falta una web (una sala
        # recién añadida, una lectura incompleta), la diferencia es de quién lo cuenta, no un cambio del concierto
        mismas = p["fuentes"] == sorted({f.get("id") for f in r.get("fuentes") or []})

        def anota(campo: str, **kw) -> None:
            hechos.append({"dia": hoy, "campo": campo, "r": REGLAS_CAMBIOS, **kw})

        if p["fecha"] != r["fecha"]:
            anota("fecha", antes=p["fecha"], despues=r["fecha"])
        sa, sb = [x for x in p["sala"].split(" / ") if x], [x for x in (r.get("sala") or "").split(" / ") if x]
        if sa and sb and not any(_ms(x, y) for x in sa for y in sb):
            anota("sala", antes=p["sala"], despues=r["sala"])
        if mismas and p["hora"] and r.get("hora") and p["hora"] != r["hora"] and \
                p["hora_pagina"] == bool(r.get("hora_pagina")):
            anota("hora", antes=p["hora"], despues=r["hora"])
        pa, pb = _precios(p["precio"]), _precios(r.get("precio"))
        # "8 €" → "8-10 €" es más detalle, no otro precio: solo si ninguno contiene al otro
        if mismas and pa and pb and not set(pa) <= set(pb) and not set(pb) <= set(pa) and \
                p["precio_pagina"] == bool((r.get("precio_fuente") or {}).get("pagina")):
            anota("precio", antes=p["precio"], despues=r["precio"])
        ev = r.get("estado_evento") or {}
        if ev.get("tipo") and ev["tipo"] != p["evento"]:
            anota("evento", despues=ev["tipo"], fuente=ev.get("nombre"), url=ev.get("url"))
        if r.get("agotado") and not p["agotado"]:
            ag = r["agotado"] if isinstance(r["agotado"], dict) else {}
            anota("agotado", fuente=ag.get("nombre"), url=ag.get("url"))
        if r.get("estado") == "posiblemente cancelado" and p["estado"] != "posiblemente cancelado":
            anota("desaparece")
        elif p["estado"] == "posiblemente cancelado" and r.get("estado") != "posiblemente cancelado":
            anota("reaparece")
        ya = {norm(x) for x in p["invitados"]} | {norm(r["artista"])} | \
             {norm(n) for c in cambios if c["campo"] == "cartel" for n in c.get("nombres", [])}
        # un nombre que es el del cabeza escrito de otra forma ("RADAR JOVEN 2026: ASHLEYS", "GRUMPYS") no es otro
        # artista en el cartel
        base = [r["artista"], *p["invitados"]]
        nuevos_cartel = [x for x in r.get("invitados") or [] if norm(x) not in ya
                         and not coinciden_flexible([x], base) and not any(norm(b) and norm(b) in norm(x) for b in base)]
        if mismas and nuevos_cartel:
            anota("cartel", nombres=nuevos_cartel[:6])
        for h in hechos:
            ultimo = next((c for c in reversed(cambios) if c["campo"] == h["campo"]), None)
            reciente = ultimo and (date.fromisoformat(hoy) - date.fromisoformat(ultimo["dia"])).days <= OSCILA_DIAS
            if h["campo"] in ("hora", "precio", "fecha", "sala") and reciente and ultimo.get("antes") == h.get("despues"):
                cambios.remove(ultimo)  # ida y vuelta en pocos días: no hubo cambio
                continue
            if h["campo"] == "reaparece":
                ultimo = next((c for c in reversed(cambios) if c["campo"] == "desaparece"), None)
                if ultimo and (date.fromisoformat(hoy) - date.fromisoformat(ultimo["dia"])).days <= OSCILA_DIAS:
                    cambios.remove(ultimo)  # faltó en una lectura y volvió: no dejó de anunciarse
                    continue
            if h["campo"] in ("evento", "agotado") and any(c["campo"] == h["campo"] and c.get("despues") == h.get("despues")
                                                           for c in cambios):
                continue  # ya apuntado (la página se volvió a leer)
            cambios.append(h)
            nuevos += 1
        if cambios:
            r["cambios"] = cambios[-CAMBIOS_MAX:]
        else:
            r.pop("cambios", None)
    return nuevos


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
        if res.get("estado") == "bloqueado_robots" and h.get("ultimo_conteo", 0) > 0:
            # no es un cambio de diseño: la sala ha cambiado su robots.txt (se respeta). Hay que decidir si se quita
            alt = ALTERNATIVAS.get(s.id)
            aviso = (f"su robots.txt ya no permite leerla (último éxito {h.get('ultima_ok')}, daba {h['ultimo_conteo']}): "
                     f"se respeta; sus conciertos salen de su última lectura y de otras agendas"
                     + (f", y de {alt}" if alt else ""))
        elif res and (not res.get("funciono") or res.get("brutos", 0) == 0) and h.get("ultimo_conteo", 0) > 0:
            aviso = f"posible cambio en la web: antes daba {h['ultimo_conteo']} conciertos (último éxito {h.get('ultima_ok')})"
            if h.get("ultima_ok"):
                dias = (hoy - date.fromisoformat(h["ultima_ok"])).days
                if dias >= DIAS_ALERTA:
                    aviso = f"lleva {dias} días sin leerse bien (último éxito {h['ultima_ok']}, daba {h['ultimo_conteo']})"
        elif res.get("funciono") and not res.get("no_leida") and cambio_de_diseno(h.get("campos"), res.get("campos")):
            aviso = cambio_de_diseno(h.get("campos"), res.get("campos"))
        elif (res.get("funciono") and not res.get("no_leida") and h.get("ultimo_conteo", 0) >= 10
              and len(mios) < 0.3 * h["ultimo_conteo"]):
            # lee algo, pero muchos menos de lo habitual: suele ser un cambio de diseño que el lector no entiende
            aviso = f"da muchos menos conciertos de lo habitual ({len(mios)} frente a {h['ultimo_conteo']}): posible cambio en la web"
        metricas = metricas_fuente(s, mios, grupo)
        salud = salud_fuente(historial.setdefault("_dias", {}).setdefault(s.id, {}), res, len(mios), hoy)
        out.append({**s.meta(), "funciono": res.get("funciono", False), "estado": res.get("estado", "no ejecutada"),
                    "metricas": metricas, "salud": salud,
                    "conciertos": len(mios), "nuevos": len(nuevos), "solo_en_esta": len(solo),
                    "eventos_brutos": res.get("brutos", 0), "paginas": res.get("paginas", 0),
                    "errores": res.get("errores", []), "robots": res.get("robots", ""),
                    "robots_bloquea": res.get("estado") == "bloqueado_robots", "aviso": aviso,
                    "segundos": res.get("segundos"), "reintento": res.get("reintento"),
                    "desde_cache": res.get("desde_cache", 0), "cache_fecha": res.get("cache_fecha"),
                    "no_leida": res.get("no_leida", False)})
        if res.get("funciono") and res.get("brutos", 0) > 0 and not res.get("no_leida"):
            historial[s.id] = {"ultima_ok": hoy.isoformat(), "ultimo_conteo": len(mios), "campos": res.get("campos")}
    return out


# fuentes bloqueadas (robots.txt) y la vía permitida por la que siguen llegando sus conciertos
ALTERNATIVAS = {"villanos": "su venta de entradas en Enterticket (fuente Enterticket)"}

DIAS_SALUD = 14  # días de historial de cada fuente en la página de Fuentes


def _pct(n: int, d: int) -> int | None:
    return round(100 * n / d) if d else None


def metricas_fuente(s: Source, mios: list[dict], grupo: dict) -> dict:
    """Lo que aporta y lo fiable que resulta cada fuente, medido sobre sus conciertos próximos:
    - otra_web: % que confirma al menos otra web independiente;
    - coincide: de los que comparte con otras webs, % en que no lleva la contraria (cuando hay un conflicto de
      hora, sala o cartel, su versión es la que dan más webs, o no hay conflicto);
    - hora, precio, estilo: % en que ella da ese dato."""
    otras = [r for r in mios if len({grupo.get(f["id"], f["id"]) for f in r["fuentes"]}) > 1]
    en_contra = 0
    for r in otras:
        for c in r.get("conflictos") or []:
            vs = c.get("versiones") or []
            mayor = max((len(v.get("fuentes") or []) for v in vs), default=0)
            if any(s.nombre in (v.get("fuentes") or []) and len(v.get("fuentes") or []) < mayor for v in vs):
                en_contra += 1
                break
    def da(r, campo):
        if campo == "estilo":
            return any(e.get("fuente") == s.nombre for e in r.get("estilo_fuente") or [])
        if campo == "precio":
            return (r.get("precio_fuente") or {}).get("nombre") == s.nombre
        return bool(r.get("hora"))  # la hora no guarda de qué fuente viene: la del concierto
    return {"otra_web": _pct(len(otras), len(mios)), "coincide": _pct(len(otras) - en_contra, len(otras)),
            "comparte": len(otras), "precio": _pct(sum(da(r, "precio") for r in mios), len(mios)),
            "estilo": _pct(sum(da(r, "estilo") for r in mios), len(mios)),
            "hora": _pct(sum(da(r, "hora") for r in mios), len(mios))}


def salud_fuente(dias: dict, res: dict, n: int, hoy: date) -> list[dict]:
    """Historial de los últimos 14 días de una fuente: por día, cuántas lecturas fueron bien de cuántas y con
    cuántos conciertos. Las ejecuciones que no la leen (reintentos de otras, lectura aparte) no cuentan."""
    hoy_s = hoy.isoformat()
    if res and not res.get("no_leida"):
        d = dias.setdefault(hoy_s, {"ok": 0, "n": 0})
        d["n"] += 1
        bien = bool(res.get("funciono")) and res.get("brutos", 0) > 0
        d["ok"] += bien
        d["c"] = n
        d["e"] = res.get("estado") if not bien else ("parcial" if not res.get("completa") else "ok")
    limite = (hoy - timedelta(days=DIAS_SALUD - 1)).isoformat()
    for k in [k for k in dias if k < limite]:
        del dias[k]
    return [{"fecha": k, **dias[k]} for k in sorted(dias)]


def salas_sin_fuente(recs: list[dict], hoy: date, minimo: int = 4) -> list[dict]:
    """Salas con conciertos próximos cuya web oficial no leemos (ningún concierto suyo lo confirma la sala): son
    candidatas a fuente nueva, o su web no tiene agenda legible (se dice por qué)."""
    from .normalize import load_json
    from .registry import SIN_AGENDA_LEGIBLE
    alias = {norm(x["nombre"]): x for x in load_json("salas_alias.json").get("salas", [])}
    por: dict[str, list[dict]] = {}
    for r in recs:
        # solo conciertos (los musicales y espectáculos de los teatros, con dos funciones al día, no cuentan)
        if (r["fecha"] >= hoy.isoformat() and r.get("sala") and " / " not in r["sala"]
                and not set(r.get("grupos") or []) & {"musicales y espectáculos", "fuera de foco"}):
            por.setdefault(r["sala"], []).append(r)
    out = []
    for sala, rs in por.items():
        if len(rs) < minimo or any(r.get("confirmado_sala") for r in rs):
            continue
        motivo = next((v for k, v in SIN_AGENDA_LEGIBLE.items() if norm(sala) in norm(k) or norm(k.split(" (")[0]) in norm(sala)), None)
        out.append({"sala": sala, "conciertos": len(rs), "municipio": rs[0].get("municipio"),
                    "web": (alias.get(norm(sala)) or {}).get("web"), "motivo": motivo})
    return sorted(out, key=lambda x: -x["conciertos"])


DIAS_ALERTA = 3  # días seguidos sin leer bien una fuente para avisar
PRESUPUESTO_FICHAS = 2400  # tope de la ejecución diaria para fichas (los pendientes siguen cada 2 horas)


def ejecutar(hoy: date | None = None, solo: list[str] | None = None, fetcher: Fetcher | None = None,
             musicbrainz: bool = True, max_mb: int = 700, reintentar: bool = False,
             pausa_reintento: float = PAUSA_REINTENTO_SEG, sin: list[str] | None = None,
             presupuesto_fichas: float | None = None) -> dict | None:
    """Ejecución completa. Con `solo` o `reintentar`, se leen solo algunas fuentes y las demás entran con su
    última lectura completa (caché), así que la agenda publicada nunca pierde conciertos de las no leídas.
    `reintentar`: vuelve a leer las fuentes que fallaron en la última ejecución; si ninguna responde, no
    cambia nada y devuelve None.
    `sin`: todas menos estas (Madrid en Vivo se lee aparte cada noche: tarda 38 de los 45 minutos de la lectura).
    Si las que faltan solo son esas, la lectura cuenta como completa: entran con su lectura de unas horas antes.
    `presupuesto_fichas`: segundos para fichas de artista (por defecto PRESUPUESTO_FICHAS)."""
    hoy = hoy or datetime.now(timezone.utc).astimezone().date()
    horizonte = hoy + timedelta(days=HORIZONTE_DIAS)
    fetcher = fetcher or Fetcher()
    estado = _read("estado.json", {})
    if reintentar:
        solo = estado.get("fuentes_fallidas") or []
        if not solo:
            log.info("Reintento: ninguna fuente falló en la última ejecución")
            return None
    fuentes = [s for s in FUENTES if (not solo or s.id in solo) and s.id not in (sin or [])]
    no_leidas = {s.id for s in FUENTES} - {s.id for s in fuentes}
    completa = not reintentar and not solo and no_leidas <= set(sin or [])
    tope_fichas = PRESUPUESTO_FICHAS if presupuesto_fichas is None else presupuesto_fichas
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
    if musicbrainz and anteriores and completa:
        from .artistas import enriquecer
        hilo = threading.Thread(target=lambda: previas.update(
            enriquecer([p for p in anteriores if p["fecha"] >= hoy.isoformat()], cache_art, hoy,
                       presupuesto_seg=tope_fichas, parar=parar, guardar=guardar_fichas,
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
    antes_cambios = foto_cambios(anteriores)  # antes de conciliar, que actualiza los anteriores
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
        resto = max(tope_fichas - (time.monotonic() - t0), min(300, tope_fichas))
        art_stats = enriquecer(recs, cache_art, hoy, presupuesto_seg=resto, guardar=guardar_fichas,
                               mb_cache=cache_mb)
        art_stats["durante_agendas"] = {k: previas.get(k, 0) for k in ("consultados", "completados")}
        guardar_fichas()
    for r in recs:
        estilos_de_agenda(r, cache_art)
        aplicar_ficha(r, ficha_de(r, cache_art))
        origen_por_agenda(r, cache_art)
        tributo_y_estimacion(r, cache_art)
        aplicar_cartel(r, cache_art)
    stats_entradas = aplicar_entradas(recs, _read(CACHE_PAGINAS, {}))
    # MusicBrainz (solo para los que siguen sin nacionalidad)
    mb_stats = {"desactivado": True}
    if musicbrainz:
        from .musicbrainz import completar, fetcher_musicbrainz
        mb_stats = completar(recs, cache_mb, hoy, fetcher_musicbrainz(), max_consultas=max_mb)
        _write("musicbrainz_cache.json", cache_mb)
    n_cambios = registrar_cambios(recs, antes_cambios, hoy.isoformat())
    contraste_sala = ausencias_web_sala(recs, resultados, por_id, eventos, hoy.isoformat(),
                                        estado.get("historial_fuentes", {}))
    n_ausentes = sum(v["ausentes"] for v in contraste_sala.values())  # (las de listado incompleto no marcan)
    from .normalizacion import normalizar, resumen as resumen_normalizacion
    for r in recs:
        r["confianza"] = puntuar_confianza(r, por_id)
        normalizar(r, cache_art)
    recs.sort(key=lambda r: (r["fecha"], r["hora"] or "99", norm(r["artista"])))
    # estilos que no se han podido traducir a categoría
    sin_mapear = sorted({e["estilo"] + " (" + e["fuente"] + ")" for r in recs for e in r["estilo_fuente"]
                         if categoria_de(e["estilo"]) is None})
    historial = estado.setdefault("historial_fuentes", {})
    inf_fuentes = informe_fuentes(FUENTES, resultados, recs, anteriores_ids, historial, hoy)
    for f in inf_fuentes:  # auditoría: qué contradice la web de cada sala
        if f["id"] in contraste_sala:
            f["contraste_sala"] = contraste_sala[f["id"]]
    futuros = [r for r in recs if r["fecha"] >= hoy.isoformat()]
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    informe = {
        "version": __version__,
        "generado": ahora,
        "modo": ("completa" + (f" ({', '.join(sorted(no_leidas))} de su lectura aparte)" if no_leidas else "")) if completa
        else (("solo " if solo and not reintentar else "reintento de ") + ", ".join(sorted(s.id for s in fuentes))),
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
            "cambios_hoy": n_cambios,
            "ausentes_web_sala": n_ausentes,
            "otra_fecha_web_sala": sum(v["otra_fecha"] for v in contraste_sala.values()),
            "confianza": dict(Counter(r["confianza"]["nivel"] for r in futuros)),
            "normalizacion": resumen_normalizacion(recs, hoy.isoformat()),
            "fuentes_ok": sum(f["funciono"] for f in inf_fuentes),
            "fuentes_total": len(inf_fuentes),
            "peticiones_http": fetcher.requests_count,
            **fuera,
        },
        "fuentes": inf_fuentes,
        "sin_agenda_legible": SIN_AGENDA_LEGIBLE,
        "salas_sin_fuente": salas_sin_fuente(recs, hoy),
        "salas_alias_propuestas": posibles_alias_salas(recs, hoy.isoformat()),
        "no_usar": NO_USAR,
        "correcciones": res_corr,
        "musicbrainz": mb_stats,
        "artistas": art_stats,
        "entradas": stats_entradas,
        "estilos_sin_mapear": sin_mapear[:300],
        "grupos": cambios_grupos(grupos_previos, recs, hoy.isoformat()),
        # lo que requiere mirar a mano (se abre también un issue en GitHub, ver .github/workflows)
        "alertas": [f"{f['nombre']}: {f['aviso']}" for f in inf_fuentes if f.get("aviso")],
    }
    # la ejecución completa del día queda registrada aunque luego los reintentos rehagan el informe
    if not completa:
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
    from .artistas import enriquecer
    hoy = hoy or datetime.now(timezone.utc).astimezone().date()
    datos = _read("concerts.json", {})
    recs = datos.get("conciertos", [])
    cache_art = _read("artistas.json", {})
    cache_mb = _read("musicbrainz_cache.json", {})

    def guardar_fichas():
        _write("artistas.json", cache_art)
        _write("musicbrainz_cache.json", cache_mb)

    t0 = time.monotonic()
    stats = enriquecer(recs, cache_art, hoy, presupuesto_seg=presupuesto_seg, guardar=guardar_fichas,
                       mb_cache=cache_mb)
    # con el tiempo que sobra: páginas de concierto y de entradas (hora, precio, agotado, enlace, cartel)
    from .entradas import leer_entradas
    cache_pag = _read(CACHE_PAGINAS, {})
    resto = presupuesto_seg - (time.monotonic() - t0) - 120
    ent = leer_entradas(recs, cache_pag, Fetcher(), hoy, resto) if resto > 60 else {}
    _write(CACHE_PAGINAS, cache_pag)
    stats["paginas"] = ent
    if not stats["consultados"] and not stats["completados"] and not ent.get("leidas") and \
            _read("informe.json", {}).get("version_fichas") == __version__:
        return stats  # nada pendiente: no se toca ningún archivo (ni commit ni nueva publicación)
    # con una versión nueva se vuelve a aplicar todo aunque no haya fichas nuevas: las reglas pueden haber cambiado
    # (p. ej. un país de Wikipedia que la regla nueva ya no acepta)
    _write("musicbrainz_cache.json", cache_mb)
    _write("artistas.json", cache_art)
    previos = _grupos_previos(recs)
    antes_cambios = foto_cambios(recs)
    for r in recs:
        estilos_de_agenda(r, cache_art)
        aplicar_ficha(r, ficha_de(r, cache_art))
        origen_por_agenda(r, cache_art)
        tributo_y_estimacion(r, cache_art)
        aplicar_cartel(r, cache_art)
    stats["entradas"] = aplicar_entradas(recs, cache_pag)
    stats["cambios"] = registrar_cambios(recs, antes_cambios, hoy.isoformat())
    por_id = {s.id: s for s in FUENTES}
    from .normalizacion import normalizar, resumen as resumen_normalizacion
    for r in recs:  # las páginas de entradas pueden haber añadido dónde se vende
        r["confianza"] = puntuar_confianza(r, por_id)
        normalizar(r, cache_art)
    _write("concerts.json", datos)
    escribir_csv(recs, DATA / "concerts.csv")
    informe = _read("informe.json", {})
    informe["grupos"] = cambios_grupos(previos, recs, hoy.isoformat())
    informe.setdefault("totales", {})["normalizacion"] = resumen_normalizacion(recs, hoy.isoformat())
    stats["ultima_carga_fichas"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    informe["artistas"] = stats
    informe["version_fichas"] = __version__  # la clasificación publicada es la de esta versión
    _write("informe.json", informe)
    return stats


def reaplicar_fichas() -> None:
    """Aplica a data/concerts.json las fichas de data/artistas.json (tras unir datos de dos ejecuciones)."""
    datos = _read("concerts.json", {})
    recs = datos.get("conciertos", [])
    if not recs:
        return
    cache = _read("artistas.json", {})
    for r in recs:
        estilos_de_agenda(r, cache)
        aplicar_ficha(r, ficha_de(r, cache))
        origen_por_agenda(r, cache)
        tributo_y_estimacion(r, cache)
        aplicar_cartel(r, cache)
    aplicar_entradas(recs, _read(CACHE_PAGINAS, {}))
    from .normalizacion import normalizar
    for r in recs:
        normalizar(r, cache)
    _write("concerts.json", datos)
    escribir_csv(recs, DATA / "concerts.csv")
