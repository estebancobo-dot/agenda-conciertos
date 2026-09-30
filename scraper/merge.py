"""Deduplicación y fusión de conciertos, detección de conflictos y resolución por prioridad de fuente.

Mismo concierto = misma fecha + misma sala normalizada + artista con similitud >= 90 (rapidfuzz),
comparando también el artista con los invitados. Si dos fuentes no coinciden en hora, sala o cartel
no se elige: se guardan ambas versiones y se marca 'conflicto', salvo que la fuente de mayor prioridad
confirme un dato, en cuyo caso el conflicto queda resuelto y se anota."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from .clasificar import categoria_de, categorias_de, discogs, en_foco, titulo_fuera_de_foco
from .model import RawEvent, Source
from .normalize import clean, contiene, es_generico, es_relleno, misma_sala, norm, parecido, parecido_flexible

UMBRAL = 90


@dataclass
class Item:
    ev: RawEvent
    src: Source

    @property
    def nombres(self) -> list[str]:
        return [self.ev.artista, *self.ev.invitados]


@dataclass
class Cluster:
    fecha: str
    items: list[Item] = field(default_factory=list)

    @property
    def salas(self) -> list[str]:
        return [i.ev.sala for i in self.items if i.ev.sala]

    @property
    def nombres(self) -> list[str]:
        out = []
        for i in self.items:
            out.extend(i.nombres)
        return out


def artistas_coinciden(a: list[str], b: list[str]) -> bool:
    """True si algún nombre de a coincide (>= 90) con alguno de b. Nombres genéricos solo casan entre sí exactos."""
    for x in a:
        for y in b:
            if es_generico(x) or es_generico(y):
                if norm(x) == norm(y):
                    return True
                continue
            if parecido(x, y) >= UMBRAL:
                return True
    return False


def coinciden_flexible(a: list[str], b: list[str]) -> bool:
    for x in a:
        for y in b:
            if es_generico(x) or es_generico(y):
                nx, ny = norm(x), norm(y)
                corto, largo = sorted((nx, ny), key=len)
                if nx == ny or contiene(corto, largo):
                    return True
                continue
            if parecido_flexible(x, y) >= UMBRAL:
                return True
    return False


def principal_coincide(a: Item | Cluster, b: list[str]) -> bool:
    """Coincidencia del cabeza de cartel de a con cualquier nombre de b (evita fusionar por un telonero común).
    Se usa dentro de la misma fecha y sala, por eso admite prefijos de ciclo y subtítulos."""
    first = a.ev.artista if isinstance(a, Item) else a.items[0].ev.artista
    return coinciden_flexible([first], b) or coinciden_flexible(b[:1], a.nombres)


_SESIONES = re.compile(r"\b(tributo|homenaje|candlelight|ballet|musical|espectaculo|sesion|matinal|infantil|"
                       r"familiar|cabaret|opera|zarzuela|orquesta|sinfonic[oa])\b")


def _con_sesiones(nombre: str) -> bool:
    """Espectáculos que se repiten el mismo día (varias sesiones)."""
    return titulo_fuera_de_foco(nombre) or bool(_SESIONES.search(norm(nombre)))


def agrupar(items: list[Item]) -> list[Cluster]:
    """Agrupa eventos de un mismo día en conciertos."""
    clusters: list[Cluster] = []
    # primero los de mayor prioridad y con sala conocida
    for it in sorted(items, key=lambda i: (i.src.prioridad, not i.ev.sala)):
        destino = None
        for c in clusters:
            salas_c = c.salas
            if it.ev.sala and salas_c and not any(misma_sala(it.ev.sala, s) for s in salas_c):
                continue
            # dos sesiones del mismo espectáculo el mismo día (misma fuente, distinta hora) no se fusionan. Solo en
            # espectáculos (Candlelight, tributos, ballet…): un concierto anunciado dos veces con horas distintas
            # en la misma web (Devin Townsend a las 20:30 y a las 21:00) es uno solo con la hora en conflicto
            if it.ev.hora and _con_sesiones(it.ev.artista) and any(
                    o.src.id == it.src.id and o.ev.hora and o.ev.hora != it.ev.hora for o in c.items):
                continue
            if principal_coincide(it, c.nombres):
                destino = c
                break
        if destino is None:
            destino = Cluster(it.ev.fecha.isoformat())
            clusters.append(destino)
        destino.items.append(it)
    return clusters


def _mejor_grafia(nombres: list[tuple[str, int]]) -> str:
    """Entre variantes del mismo nombre, la de mayor prioridad que no esté toda en mayúsculas (si existe)."""
    nombres = sorted(nombres, key=lambda x: x[1])
    base = nombres[0][0]
    for n, _ in nombres:
        if norm(n) == norm(base) and not (n.isupper() and len(n) > 4):
            return n
    return base


def _fuentes(items: list[Item]) -> list[dict]:
    out, seen = [], set()
    for it in sorted(items, key=lambda i: i.src.prioridad):
        k = (it.src.id, it.ev.url)
        if k in seen:
            continue
        seen.add(k)
        out.append({"nombre": it.src.nombre, "id": it.src.id, "url": it.ev.url, "prioridad": it.src.prioridad})
    return out


def _versiones(items: list[Item], campo) -> dict[str, list[Item]]:
    v: dict[str, list[Item]] = {}
    for it in items:
        val = campo(it)
        if val:
            v.setdefault(val, []).append(it)
    return v


def resolver(nombre_campo: str, versiones: dict[str, list[Item]], notas: list[str], conflictos: list[dict],
             igual=lambda a, b: a == b):
    """Devuelve el valor acordado o None si hay conflicto (y lo registra)."""
    if not versiones:
        return None
    # fusiona valores equivalentes (p. ej. variantes del nombre de la sala)
    claves = list(versiones)
    grupos: list[list[str]] = []
    for k in claves:
        for g in grupos:
            if igual(g[0], k):
                g.append(k)
                break
        else:
            grupos.append([k])
    if len(grupos) == 1:
        return max(grupos[0], key=lambda k: -min(i.src.prioridad for i in versiones[k]))
    por_grupo = {}
    for g in grupos:
        its = [i for k in g for i in versiones[k]]
        valor = min(g, key=lambda k: min(i.src.prioridad for i in versiones[k]))
        por_grupo[valor] = its
    desc = "; ".join(f"{v} según {', '.join(sorted({i.src.nombre for i in its}))}" for v, its in por_grupo.items())
    top = min(i.src.prioridad for its in por_grupo.values() for i in its)
    con_top = [v for v, its in por_grupo.items() if any(i.src.prioridad == top for i in its)]
    if len(con_top) == 1:
        notas.append(f"{nombre_campo.capitalize()}: {desc}. Resuelto por prioridad de fuente "
                     f"(la fuente de mayor prioridad confirma {con_top[0]}).")
        return con_top[0]
    notas.append(f"Conflicto de {nombre_campo}: {desc}.")
    conflictos.append({"campo": nombre_campo, "versiones": [
        {"valor": v, "fuentes": sorted({i.src.nombre for i in its})} for v, its in por_grupo.items()]})
    return None


def construir(cluster: Cluster, municipio_de) -> dict:
    items = cluster.items
    notas: list[str] = []
    conflictos: list[dict] = []
    # artista principal: el de la fuente de mayor prioridad, con mejor grafía
    top = min(items, key=lambda i: i.src.prioridad)
    variantes = [(top.ev.artista, top.src.prioridad)] + [
        (i.ev.artista, i.src.prioridad) for i in items if i is not top and parecido(i.ev.artista, top.ev.artista) >= UMBRAL]
    artista = _mejor_grafia(variantes)
    if artista.isupper() and len(artista) > 4:
        alt = [(n, p) for n, p in variantes if not n.isupper()]
        if alt:
            artista = sorted(alt, key=lambda x: x[1])[0][0]
    invitados: list[str] = []
    for it in sorted(items, key=lambda i: i.src.prioridad):
        for n in [it.ev.artista, *it.ev.invitados]:
            if parecido_flexible(n, artista) >= UMBRAL or es_generico(n) or es_relleno(n):
                continue
            if any(parecido_flexible(n, x) >= UMBRAL for x in invitados):
                continue
            invitados.append(n)
    # sala
    sala = resolver("sala", _versiones(items, lambda i: i.ev.sala), notas, conflictos, igual=misma_sala)
    if sala is None and conflictos and conflictos[-1]["campo"] == "sala":
        sala_txt = " / ".join(v["valor"] for v in conflictos[-1]["versiones"])
    else:
        sala_txt = sala or ""
    # hora
    hora = resolver("hora", _versiones(items, lambda i: i.ev.hora), notas, conflictos)
    # municipio
    munis = [m for m in (municipio_de(i) for i in items) if m]
    municipio = munis[0] if munis else None
    # precio: el de la fuente de mayor prioridad que lo dé (y se guarda cuál es)
    it_precio = next((i for i in sorted(items, key=lambda i: i.src.prioridad) if i.ev.precio), None)
    precio = it_precio.ev.precio if it_precio else None
    precio_fuente = {"nombre": it_precio.src.nombre, "url": it_precio.ev.url} if it_precio else None
    it_img = next((i for i in sorted(items, key=lambda i: i.src.prioridad) if i.ev.imagen), None)
    imagen_evento = {"url": it_img.ev.imagen, "credito": it_img.src.nombre, "enlace": it_img.ev.url} if it_img else None
    oficial = next((i for i in items if i.src.tipo == "sala"), None)
    # estilos tal como los dan las fuentes
    estilos, cats = [], []
    for it in sorted(items, key=lambda i: i.src.prioridad):
        if it.ev.estilo and not any(e["estilo"] == it.ev.estilo and e["fuente"] == it.src.nombre for e in estilos):
            estilos.append({"estilo": it.ev.estilo, "fuente": it.src.nombre})
            for c in categorias_de(it.ev.estilo):
                if c not in cats:
                    cats.append(c)
    if not cats:
        cats = ["sin clasificar"]
    categoria = next((categoria_de(e["estilo"]) for e in estilos if categoria_de(e["estilo"])), None) or cats[0]
    if titulo_fuera_de_foco(artista):  # Candlelight, musicales…: fuera de foco aunque la fuente diga 'tributo'
        cats, categoria = ["fuera de foco"], "fuera de foco"
    estilos_d, generos_d = discogs([e["estilo"] for e in estilos])
    # nacionalidad solo si la da la fuente
    nac = next(((i.ev.nacionalidad, i.src.nombre) for i in sorted(items, key=lambda i: i.src.prioridad)
                if i.ev.nacionalidad), (None, None))
    grupos = {i.src.grupo for i in items}
    for it in items:
        n = it.ev.nota
        if not n or n in notas or n.startswith("Entradas:") or n.startswith("Metalcry pone"):
            continue
        if it.src.fiabilidad == "baja" and len(grupos) > 1:
            continue  # la nota de fiabilidad baja solo importa si es la única fuente
        if n.startswith("Evento: ") and parecido_flexible(n[8:], " + ".join([artista] + invitados)) >= UMBRAL:
            continue
        notas.append(n)
    if conflictos:
        estado = "conflicto"
    elif len(grupos) >= 2:
        estado = "contrastado"
    else:
        estado = "1_fuente"
        if all(i.src.fiabilidad == "baja" for i in items):
            if "fiabilidad baja" not in " ".join(notas).lower():
                notas.append("Solo aparece en una fuente de fiabilidad baja.")
    return {
        "id": None,
        "fecha": cluster.fecha,
        "hora": hora,
        "artista": artista,
        "invitados": invitados,
        "sala": sala_txt,
        "municipio": municipio,
        "precio": precio,
        "precio_fuente": precio_fuente,
        "imagen_evento": imagen_evento,
        "confirmado_sala": {"nombre": oficial.src.nombre, "url": oficial.ev.url} if oficial else None,
        "ciclo": None,
        "estilo_fuente": estilos,
        "categoria": categoria,
        "categorias": cats,
        "genero_discogs": generos_d,
        "estilos_discogs": estilos_d,
        "nacionalidad": nac[0],
        "nacionalidad_fuente": nac[1],
        "fuentes": _fuentes(items),
        "estado": estado,
        "conflictos": conflictos,
        "notas": notas,
        "en_foco": en_foco(cats),
        "primera_vez_visto": None,
        "ultima_vez_visto": None,
    }


def hacer_id(rec: dict) -> str:
    base = f"{rec['fecha']}|{norm(rec['sala'].split(' / ')[0])}|{norm(rec['artista'])}"
    return hashlib.sha1(base.encode()).hexdigest()[:12]


def nombres_rec(r: dict) -> list[str]:
    return [r["artista"], *r.get("invitados", [])]


def fusionar_conflictos_sala(recs: list[dict]) -> list[dict]:
    """Mismo día, mismo artista (no genérico) y distinta sala → un solo registro con conflicto de sala
    (salvo que la fuente de mayor prioridad lo resuelva)."""
    out: list[dict] = []
    por_fecha: dict[str, list[dict]] = {}
    for r in recs:
        por_fecha.setdefault(r["fecha"], []).append(r)
    for fecha, rs in por_fecha.items():
        usados = set()
        for i, a in enumerate(rs):
            if i in usados:
                continue
            for j in range(i + 1, len(rs)):
                b = rs[j]
                if j in usados or not a["sala"] or not b["sala"] or misma_sala(a["sala"], b["sala"]):
                    continue
                # si la misma fuente lo anuncia en dos salas, son dos eventos (p. ej. Candlelight en varias sedes)
                if {f["id"] for f in a["fuentes"]} & {f["id"] for f in b["fuentes"]}:
                    continue
                if es_generico(a["artista"]) or es_generico(b["artista"]):
                    continue
                if not (artistas_coinciden([a["artista"]], nombres_rec(b)) or
                        artistas_coinciden([b["artista"]], nombres_rec(a))):
                    continue
                pa = min(f["prioridad"] for f in a["fuentes"])
                pb = min(f["prioridad"] for f in b["fuentes"])
                desc = (f"{a['sala']} según {', '.join(sorted({f['nombre'] for f in a['fuentes']}))}; "
                        f"{b['sala']} según {', '.join(sorted({f['nombre'] for f in b['fuentes']}))}")
                a["fuentes"] = a["fuentes"] + [f for f in b["fuentes"] if f not in a["fuentes"]]
                a["invitados"] += [x for x in b["invitados"] if all(parecido(x, y) < UMBRAL for y in a["invitados"])]
                for n in b["notas"]:
                    if n not in a["notas"]:
                        a["notas"].append(n)
                for e in b["estilo_fuente"]:
                    if e not in a["estilo_fuente"]:
                        a["estilo_fuente"].append(e)
                if pa != pb:
                    ganador = a if pa < pb else b
                    a["notas"].append(f"Sala: {desc}. Resuelto por prioridad de fuente (la de mayor prioridad "
                                      f"confirma {ganador['sala']}).")
                    a["sala"], a["municipio"] = ganador["sala"], ganador["municipio"]
                    a["hora"] = ganador["hora"] or a["hora"]
                else:
                    a["conflictos"].append({"campo": "sala", "versiones": [
                        {"valor": a["sala"], "fuentes": sorted({f["nombre"] for f in a["fuentes"] if f not in b["fuentes"]})},
                        {"valor": b["sala"], "fuentes": sorted({f["nombre"] for f in b["fuentes"]})}]})
                    a["notas"].append(f"Conflicto de sala: {desc}.")
                    a["sala"] = f"{a['sala']} / {b['sala']}"
                    a["estado"] = "conflicto"
                usados.add(j)
            out.append(a)
    return out


def marcar_conflictos_cartel(recs: list[dict]) -> None:
    """Misma fecha, misma sala y misma hora, artistas distintos, uno de la web oficial de la sala y otro de
    fuentes que no son la sala: la web oficial y la otra fuente no coinciden en el cartel."""
    por_clave: dict[tuple, list[dict]] = {}
    for r in recs:
        if r["hora"] and r["sala"] and " / " not in r["sala"]:
            por_clave.setdefault((r["fecha"], norm(r["sala"]), r["hora"]), []).append(r)
    for rs in por_clave.values():
        if len(rs) < 2:
            continue
        oficiales = [r for r in rs if any(f["prioridad"] == 1 for f in r["fuentes"])]
        otros = [r for r in rs if not any(f["prioridad"] == 1 for f in r["fuentes"])]
        if not oficiales or not otros:
            continue
        for o in otros:
            of = oficiales[0]
            desc = (f"{of['artista']}{' + ' + ' + '.join(of['invitados']) if of['invitados'] else ''} según "
                    f"{', '.join(sorted({f['nombre'] for f in of['fuentes']}))}; "
                    f"{o['artista']}{' + ' + ' + '.join(o['invitados']) if o['invitados'] else ''} según "
                    f"{', '.join(sorted({f['nombre'] for f in o['fuentes']}))}")
            for r in (of, o):
                nota = f"Conflicto de cartel a las {r['hora']} en {r['sala']}: {desc}."
                if nota not in r["notas"]:
                    r["notas"].append(nota)
                r["estado"] = "conflicto"
                if not any(c["campo"] == "cartel" for c in r["conflictos"]):
                    r["conflictos"].append({"campo": "cartel", "versiones": [
                        {"valor": of["artista"], "fuentes": sorted({f["nombre"] for f in of["fuentes"]})},
                        {"valor": o["artista"], "fuentes": sorted({f["nombre"] for f in o["fuentes"]})}]})


def recalcular_estado(r: dict, grupos_de) -> None:
    if r["estado"] == "posiblemente cancelado":
        return
    if r["conflictos"]:
        r["estado"] = "conflicto"
    elif len({grupos_de(f["id"]) for f in r["fuentes"]}) >= 2:
        r["estado"] = "contrastado"
    else:
        r["estado"] = "1_fuente"


def recalcular_categorias(r: dict) -> None:
    """Tras fusionar registros (correcciones), recalcula categoría y foco a partir de los estilos de las fuentes."""
    cats = []
    for e in r["estilo_fuente"]:
        for c in categorias_de(e["estilo"]):
            if c not in cats:
                cats.append(c)
    if not cats:
        cats = ["sin clasificar"]
    if titulo_fuera_de_foco(r["artista"]):
        cats = ["fuera de foco"]
    r["categorias"] = cats
    if r.get("categoria") not in cats:
        r["categoria"] = cats[0]
    r["en_foco"] = en_foco(cats)
    r["estilos_discogs"], r["genero_discogs"] = discogs([e["estilo"] for e in r["estilo_fuente"]])


_CICLO = re.compile(r"(?i)^\s*((?:radar joven|las noches de r[ií]o babel|villanos del jazz|momentazos|jazzmadrid|"
                    r"festival [^:.]{2,40}|ciclo [^:.]{2,40}|madrid en vivo[^:]*|club 77)[^:.]*?)\s*[:.\-–]\s+(.{2,})$")


def separar_ciclo(r: dict) -> None:
    """'Radar Joven. Kris Tena' → artista 'Kris Tena', ciclo 'Radar Joven'. El texto original se conserva en notas."""
    m = _CICLO.match(r["artista"])
    if m and len(m.group(2)) >= 2:
        ciclo, resto = clean(m.group(1)), clean(m.group(2))
        # 'RADAR JOVEN 2026 - MADRID EN VIVO 25 AÑOS: TOLDOS VERDES' tiene dos niveles de ciclo
        m2 = _CICLO.match(resto)
        if m2:
            ciclo, resto = f"{ciclo} · {clean(m2.group(1))}", clean(m2.group(2))
        r["ciclo"] = ciclo
        r["artista"] = resto
    else:
        mt = re.search(r"(?i)\s*[-–(]\s*club 77\)?\s*$", r["artista"])
        if mt:
            r["ciclo"], r["artista"] = "Club 77", r["artista"][: mt.start()].strip()
