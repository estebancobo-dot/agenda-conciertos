"""Acierto de la hora de cada agenda, medido contra las webs oficiales de las salas, y conflictos de hora resueltos
con él.

Medido el 10/10/2026 (tools/desfase_horas.py): ninguna agenda tiene un desfase fijo (en todas, lo más frecuente es
que coincida con la sala), pero unas aciertan mucho más que otras: Madrid en Vivo, La Ganzúa, Total Stage y
conciertos.club coinciden con la sala en el 69-79 % de los conciertos; Songkick (40 %) y JacksOnLive (52 %) dan a
menudo una hora anterior (la apertura de puertas). Por eso no se corrige ninguna hora: si en un conflicto de hora una
versión la da una agenda que acierta mucho y todas las demás solo agendas que aciertan poco, la hora es la de la que
acierta; la otra versión sigue a la vista en la ficha, con su porqué (como "resuelto por prioridad"). El acierto se
mide en cada lectura, así que la regla se ajusta sola si una agenda mejora o empeora.
"""
from __future__ import annotations

from collections import Counter, defaultdict

ALTO, BAJO = 0.65, 0.55   # acierta mucho / acierta poco (y nada entre medias decide)
MINIMO = 20               # conciertos comparables para que la medida cuente
PUERTAS = 0.3             # da una hora anterior en al menos este tanto: "suele dar la apertura de puertas"


def minutos(h) -> int | None:
    try:
        a, b = str(h).split(":")
        return int(a) * 60 + int(b)
    except (ValueError, TypeError):
        return None


def _campo(e, k):
    return e.get(k) if isinstance(e, dict) else getattr(e, k, None)


def diferencias(eventos: dict, tipo_de: dict[str, str]) -> dict[str, Counter]:
    """{agenda: Counter(minutos de diferencia, agenda − web de la sala)} en los conciertos que dan las dos con hora
    (mismo día, misma sala, mismo artista)."""
    from .merge import artistas_coinciden
    from .normalize import canon_sala
    oficiales = defaultdict(list)
    for sid, evs in eventos.items():
        if tipo_de.get(sid) != "sala":
            continue
        for e in evs or []:
            m = minutos(_campo(e, "hora"))
            if m is not None and _campo(e, "sala"):
                oficiales[(str(_campo(e, "fecha")), canon_sala(_campo(e, "sala")))].append((_campo(e, "artista"), m))
    out: dict[str, Counter] = defaultdict(Counter)
    for sid, evs in eventos.items():
        if tipo_de.get(sid) in (None, "sala"):
            continue
        vistos = set()
        for e in evs or []:
            m = minutos(_campo(e, "hora"))
            if m is None or not _campo(e, "sala"):
                continue
            k = (str(_campo(e, "fecha")), canon_sala(_campo(e, "sala")))
            par = next((mo for a, mo in oficiales.get(k, []) if artistas_coinciden([a], [_campo(e, "artista")])), None)
            clave = (k, str(_campo(e, "artista")).lower())
            if par is not None and clave not in vistos:
                vistos.add(clave)
                out[sid][m - par] += 1
    return out


def medir(eventos: dict, tipo_de: dict[str, str], previo: dict | None, hoy: str) -> dict[str, dict]:
    """{agenda: {"n", "coinciden", "antes", "despues", "fecha"}}: lo medido hoy si hay al menos MINIMO conciertos
    comparables; si no, la última medida buena (previo)."""
    out = {k: v for k, v in (previo or {}).items() if isinstance(v, dict)}
    for sid, c in diferencias(eventos, tipo_de).items():
        n = sum(c.values())
        if n >= MINIMO:
            out[sid] = {"n": n, "coinciden": c[0], "antes": sum(v for d, v in c.items() if d < 0),
                        "despues": sum(v for d, v in c.items() if d > 0), "fecha": hoy}
    return out


def tasa(a: dict | None) -> float | None:
    return a["coinciden"] / a["n"] if a and a.get("n", 0) >= MINIMO else None


def _pct(x: float) -> str:
    return f"{round(100 * x)} %"


def resolver(recs: list[dict], acierto: dict[str, dict], id_de_nombre: dict[str, str]) -> int:
    """Resuelve los conflictos de hora en los que una versión la da una agenda que acierta mucho y todas las demás solo
    agendas que aciertan poco. Devuelve cuántos ha resuelto."""
    hechos = 0
    for r in recs:
        conf = [c for c in r.get("conflictos") or [] if c.get("campo") == "hora"]
        if len(conf) != 1:
            continue
        vs = conf[0].get("versiones") or []
        mejor = []
        for v in vs:
            tasas = [(t, f) for f in v.get("fuentes") or [] if (t := tasa(acierto.get(id_de_nombre.get(f, "")))) is not None]
            mejor.append(max(tasas) if tasas else None)
        fiables = [i for i, m in enumerate(mejor) if m and m[0] >= ALTO]
        if len(fiables) != 1 or any(m is None or m[0] > BAJO for i, m in enumerate(mejor) if i != fiables[0]):
            continue
        elegida = vs[fiables[0]]
        descartadas = []
        for i, v in enumerate(vs):
            if i == fiables[0]:
                continue
            t, f = mejor[i]
            a = acierto[id_de_nombre[f]]
            motivo = f"{f.split(' (')[0]} coincide con la web de la sala en el {_pct(t)} de los conciertos"
            if a["antes"] / a["n"] >= PUERTAS and (minutos(v["valor"]) or 0) < (minutos(elegida["valor"]) or 0):
                motivo += f" y en el {_pct(a['antes'] / a['n'])} da una hora anterior (suele ser la apertura de puertas)"
            descartadas.append({"valor": v["valor"], "fuentes": v["fuentes"], "motivo": motivo})
        tf, ff = mejor[fiables[0]]
        r["hora"] = elegida["valor"]
        r["hora_descartada"] = descartadas
        r["conflictos"] = [c for c in r["conflictos"] if c is not conf[0]]
        r["notas"] = [n for n in r.get("notas") or [] if not n.startswith("Conflicto de hora")]
        r["notas"].append(f"Hora: {elegida['valor']} según {', '.join(elegida['fuentes'])}; "
                          + "; ".join(f"{d['valor']} según {', '.join(d['fuentes'])}" for d in descartadas)
                          + f". Resuelto por acierto medido ({ff.split(' (')[0]} coincide con la web de la sala en el "
                          + f"{_pct(tf)} de los conciertos; " + "; ".join(d["motivo"] for d in descartadas) + ").")
        hechos += 1
    return hechos
