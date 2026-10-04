"""Lotes para completar datos con un chat que busca en internet (fase D).

    python tools/lotes.py generar [--tipo auto|artistas|conciertos] [--n N] [--salida lote.md]
        Elige lo que más falta (artistas sin origen o sin estilo; conciertos sin hora, sin precio o sin confirmar),
        escribe el lote con las instrucciones para el chat y lo apunta como pendiente en data/aportes.json.
    python tools/lotes.py importar respuesta.txt [--informe informe.md]
        Lee la respuesta del chat (el bloque JSON), comprueba cada dato en la página que cita y guarda lo aceptado.
    python tools/lotes.py estado
        Cuánto queda y cuánto se ha aportado.

Los datos de partida son los de data/ (concerts.json de la rama `datos`); lo aportado vive en data/aportes.json, que en
GitHub se guarda en la rama `aportes`."""
from __future__ import annotations

import argparse
import json
from html import unescape
import re
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from scraper import aportes as ap  # noqa: E402
from scraper.normalize import canon_sala, norm  # noqa: E402

DATA = RAIZ / "data"
APORTES = DATA / "aportes.json"
N_ARTISTAS, N_CONCIERTOS = 20, 15
REPETIR_DIAS = 30           # lo ya preguntado no se vuelve a preguntar en un mes
DIAS_CONCIERTOS = 90        # conciertos de los próximos 3 meses
# tributos, Candlelight, jams y sesiones fijas: el origen o el estilo del "artista" no aportan (o no hay artista)
_NO_PREGUNTAR = re.compile(r"\b(candlelight|tributo|tribute|homenaje|versiones|covers?|jam|jams|open mic|micro abierto|"
                           r"karaoke|lunes|martes|miercoles|jueves|viernes|sabados?|domingos?|big band night|vs|expo|certamen|titeres)\b")
DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def cargar(p: Path, defecto):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defecto


def guardar(p: Path, datos) -> None:
    p.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def conciertos(hoy: str) -> list[dict]:
    d = cargar(DATA / "concerts.json", {})
    recs = d.get("conciertos", d) if isinstance(d, dict) else d
    return [r for r in recs if r["fecha"] >= hoy]


def _estado(r: dict, campo: str) -> str:
    return ((r.get("normalizacion") or {}).get(campo) or {}).get("estado", "")


def _reciente(apo: dict, clave: str, hoy: str) -> bool:
    c = apo.get("consultados", {}).get(clave)
    return bool(c) and c.get("fecha", "") >= (date.fromisoformat(hoy) - timedelta(days=REPETIR_DIAS)).isoformat()


def _webs_sala() -> dict[str, str]:
    d = cargar(DATA / "salas_alias.json", {})
    return {s["nombre"]: s["web"] for s in d.get("salas", []) if s.get("web")}


# ------------------------------------------------------------------ elegir
def candidatos_artistas(recs: list[dict], apo: dict, hoy: str) -> list[dict]:
    from scraper.nombres import claves_ficha
    from scraper.normalize import es_generico
    from scraper.origen import sin_artista
    from scraper.registry import FUENTES
    institucional = {f.id: f.tipo == "institucional" for f in FUENTES}
    por: dict[str, dict] = {}
    for r in recs:
        if r.get("festival") or _estado(r, "origen") == "no_aplica" and _estado(r, "estilo") == "no_aplica":
            continue
        claves = claves_ficha(r) or [r["artista"]]
        # "ESPECTÁCULO FLAMENCO: CLARA GUTIERREZ" → "CLARA GUTIERREZ"
        nombre = claves[1] if ":" in claves[0] and len(claves) > 1 else claves[0]
        k = ap.clave_artista(nombre)
        o, e = _estado(r, "origen"), _estado(r, "estilo")
        titulo = norm(r["artista"])
        if not k or o == "no_aplica" or es_generico(nombre) or sin_artista(nombre) or sin_artista(r["artista"]) \
                or _NO_PREGUNTAR.search(titulo) or k in (apo.get("artistas") or {}) or _reciente(apo, "a:" + k, hoy):
            continue
        # el origen: si no se sabe, o si sale de un artista identificado solo por su nombre (podría ser un homónimo);
        # el estilo: si no se sabe o si la agenda solo da una etiqueta genérica ("Varios", "Música en directo")
        solo_nombre = "nombre" in str((r.get("normalizacion") or {}).get("origen", {}).get("motivo", ""))
        falta = {"origen": o == "desconocido" or solo_nombre,
                 "estilo": e == "desconocido" or (e == "estimado" and bool(r.get("grupos_generico")))}
        if not any(falta.values()):
            continue
        x = por.setdefault(k, {"nombre": nombre, "conciertos": [], "falta": set(), "peso": 0, "etiquetas": set(),
                               "webs": [], "sabemos": {}})
        x["conciertos"].append(r)
        x["falta"].update(c for c, v in falta.items() if v)
        # antes los de agendas y salas de música: las agendas municipales traen muchas actividades que no son conciertos
        musica = any(institucional.get(f.get("id")) is False for f in r.get("fuentes") or [])
        x["peso"] = max(x["peso"], 3 * (o == "desconocido") + 2 * solo_nombre + 2 * (e == "desconocido") + falta["estilo"]
                        + 3 * musica)
        x["etiquetas"].update(str(ef.get("estilo")) for ef in r.get("estilo_fuente") or [] if ef.get("estilo"))
        x["webs"] += [f["url"] for f in r.get("fuentes") or [] if f.get("url", "").startswith("http")]
        if r.get("nacionalidad_estimada"):
            x["sabemos"]["origen_estimado"] = r["nacionalidad_estimada"]
        if r.get("nacionalidad"):
            x["sabemos"]["origen"] = r["nacionalidad"]
        if r.get("spotify"):
            x["sabemos"]["spotify"] = f"https://open.spotify.com/artist/{r['spotify']}"
    out = sorted(por.values(), key=lambda x: (-x["peso"], -min(len(x["conciertos"]), 3),
                                              min(c["fecha"] for c in x["conciertos"])))
    return out


def candidatos_conciertos(recs: list[dict], apo: dict, hoy: str) -> list[dict]:
    limite = (date.fromisoformat(hoy) + timedelta(days=DIAS_CONCIERTOS)).isoformat()
    ya = {c.get("id") for c in apo.get("conciertos") or []}
    out = []
    for r in recs:
        if r["fecha"] > limite or r.get("festival") or not r.get("sala") or \
                norm(r["sala"]) in (norm(r.get("municipio") or ""), "madrid", "cadiz", "unknown venue"):
            continue
        i = ap.id_concierto(r)
        if i in ya or _reciente(apo, "c:" + i, hoy):
            continue
        falta = {"hora": _estado(r, "hora") == "desconocido", "precio": _estado(r, "precio") == "desconocido",
                 "confirmacion": (r.get("confianza") or {}).get("nivel") == "sin confirmar",
                 "entradas": not r.get("entradas")}
        peso = 3 * falta["confirmacion"] + 2 * falta["hora"] + falta["precio"]
        if peso:
            out.append({"r": r, "id": i, "falta": falta, "peso": peso})
    return sorted(out, key=lambda x: (-x["peso"], x["r"]["fecha"]))


# ------------------------------------------------------------------ escribir el lote
INSTR_ARTISTAS = """Eres un documentalista musical. Para cada artista de la lista de abajo, busca en internet (usa la búsqueda web)
de qué país es y qué estilos toca. Son artistas que tocan en Madrid en las fechas y salas que se indican: úsalas para no
confundirlos con otro artista que se llame igual.

Reglas (muy importantes, todo se comprueba automáticamente abriendo las páginas que cites):
1. Cada dato tiene que venir de una página que se pueda abrir sin iniciar sesión: web oficial del artista, Bandcamp,
   Wikipedia, Discogs, MusicBrainz, Last.fm, prensa o blogs musicales, la web de la sala o de la venta de entradas.
   NO sirven Instagram, Facebook, TikTok, X/Twitter, YouTube, Spotify ni Linktree (no se pueden comprobar).
2. Copia en "pais_cita" y "estilos_cita" una frase LITERAL de esa página, sin traducir ni resumir, que diga el dato
   (por ejemplo: "banda madrileña de punk rock formada en 2015" o "Danish jazz duo"). La frase tiene que nombrar el
   país, un gentilicio o la ciudad, y las palabras de estilo que pongas en "estilos".
3. Si no lo encuentras o no estás seguro de que es el mismo artista, deja el campo en null. No deduzcas nada del
   nombre ni de la sala. Es mejor null que un dato dudoso.
4. "identidad": "seguro" si los datos de la página encajan con el contexto (ciudad, estilo, sala); "dudoso" si hay
   varios artistas con ese nombre y no sabes cuál es; "no encontrado" si no hay nada; "no es musica" si lo que
   aparece no es un artista o grupo musical (un partido, cine, teatro, una exposición…), y explica qué es en "nota".
5. "nombre_real": el nombre del artista o grupo si en la lista aparece con más cosas o mal escrito (por ejemplo
   "Fabio Lione" para "FABIO LIONE’S DAWN OF VICTORY" o "Fahmi Alqhai" para "FAHMI ALQHI").
6. "pais": código de dos letras (ES, AR, MX, US, GB, FR…). "estilos": de 1 a 4 estilos concretos en minúsculas
   tal como los dice la página (por ejemplo "punk rock", "indie pop", "flamenco fusión", "stoner rock").

Responde SOLO con un bloque de código JSON con esta forma (un objeto por artista, con su "id"):
```json
{"lote": "%LOTE%", "artistas": [
  {"id": "a1", "identidad": "seguro", "pais": "ES", "ciudad": "Madrid",
   "pais_url": "https://...", "pais_cita": "frase literal",
   "estilos": ["punk rock"], "estilos_url": "https://...", "estilos_cita": "frase literal",
   "enlaces": ["https://web-oficial-o-bandcamp..."]}
]}
```
"""

INSTR_CONCIERTOS = """Eres un documentalista de conciertos. Para cada concierto de la lista de abajo (en Madrid), busca en internet (usa
la búsqueda web) la página de la sala o de la venta de entradas que lo anuncie, y de ella la hora de comienzo y el
precio. Si el concierto se ha cancelado o aplazado, dilo.

Reglas (muy importantes, todo se comprueba automáticamente abriendo la página que cites):
1. "url": la página de ESE concierto (mismo artista, misma fecha) en la web oficial de la sala o en una web de venta de
   entradas (Dice, Entradas.com, Ticketmaster, Mutick, Wegow, Enterticket, Fever, Taquilla.com, la propia sala…).
   Tiene que abrirse sin iniciar sesión. NO sirven Instagram, Facebook, X/Twitter ni TikTok.
2. "hora" (HH:MM, 24 h) y "precio" (por ejemplo "15 €", "desde 12,50 €", "entrada libre") tienen que aparecer en esa
   página. Si la página no los dice, déjalos en null. No pongas la hora de apertura de puertas como hora de comienzo
   salvo que sea la única que aparece.
3. "estado": "cancelado" o "aplazado" solo si la página lo dice; si no, null.
4. Si no encuentras una página de ese concierto, pon "url": null. No uses la página de otra fecha ni de otra ciudad.

Responde SOLO con un bloque de código JSON con esta forma (un objeto por concierto, con su "id"):
```json
{"lote": "%LOTE%", "conciertos": [
  {"id": "c1", "url": "https://...", "hora": "21:00", "precio": "15 €", "estado": null}
]}
```
"""


def _dia(fecha: str) -> str:
    d = date.fromisoformat(fecha)
    return f"{DIAS_SEMANA[d.weekday()]} {d.day}/{d.month}/{d.year}"


def lote_artistas(cands: list[dict], n: int, lote: str) -> tuple[str, dict]:
    items, pedido = [], {}
    for i, x in enumerate(cands[:n], 1):
        aid = f"a{i}"
        cs = sorted(x["conciertos"], key=lambda r: r["fecha"])
        item = {"id": aid, "artista": unescape(x["nombre"]),
                "toca_en": [f"{_dia(r['fecha'])} · {r.get('sala') or '?'} ({r.get('municipio') or 'Madrid'})"
                            for r in cs[:3]],
                "buscar": sorted(x["falta"])}
        if x["etiquetas"]:
            item["etiquetas_de_las_agendas"] = sorted(x["etiquetas"])[:4]
        if x["sabemos"].get("spotify"):
            item["spotify"] = x["sabemos"]["spotify"]
        webs = list(dict.fromkeys(x["webs"]))[:2]
        if webs:
            item["anunciado_en"] = webs
        items.append(item)
        pedido[aid] = {"nombre": x["nombre"], "clave": ap.clave_artista(x["nombre"]), "falta": sorted(x["falta"]),
                       "salas": sorted({canon_sala(r.get("sala") or "") for r in cs if r.get("sala")})}
    texto = INSTR_ARTISTAS.replace("%LOTE%", lote) + "\nArtistas:\n```json\n" + \
        "[\n" + ",\n".join(json.dumps(x, ensure_ascii=False) for x in items) + "\n]\n```\n"
    return texto, pedido


def lote_conciertos(cands: list[dict], n: int, lote: str) -> tuple[str, dict]:
    webs = _webs_sala()
    items, pedido = [], {}
    for i, x in enumerate(cands[:n], 1):
        cid, r = f"c{i}", x["r"]
        sala = canon_sala(r.get("sala") or "")
        item = {"id": cid, "artista": r["artista"], "fecha": _dia(r["fecha"]), "sala": r.get("sala"),
                "municipio": r.get("municipio") or "Madrid",
                "buscar": [k for k, v in x["falta"].items() if v and k != "confirmacion"] or ["página del concierto"]}
        if r.get("hora"):
            item["hora_que_tenemos"] = r["hora"]
        if webs.get(sala):
            item["web_de_la_sala"] = webs[sala]
        anun = [f["url"] for f in r.get("fuentes") or [] if f.get("url", "").startswith("http")][:2]
        if anun:
            item["anunciado_en"] = anun
        items.append(item)
        pedido[cid] = {"id": x["id"], "fecha": r["fecha"], "artista": r["artista"], "sala": r.get("sala"),
                       "web_sala": webs.get(sala)}
    texto = INSTR_CONCIERTOS.replace("%LOTE%", lote) + "\nConciertos:\n```json\n" + \
        "[\n" + ",\n".join(json.dumps(x, ensure_ascii=False) for x in items) + "\n]\n```\n"
    return texto, pedido


def pendiente() -> str | None:
    """El lote enviado que aún no tiene respuesta (como mucho hay uno)."""
    apo = cargar(APORTES, ap.vacio())
    pend = sorted((k for k, l in apo.get("lotes", {}).items() if not l.get("importado") and not l.get("saltado")),
                  key=lambda k: apo["lotes"][k].get("creado", ""))
    return pend[-1] if pend else None


def saltar(hoy: str | None = None) -> str | None:
    """Da por perdido el lote pendiente (no se contestará): sus preguntas vuelven a estar disponibles."""
    apo = cargar(APORTES, ap.vacio())
    k = pendiente()
    if k:
        apo["lotes"][k]["saltado"] = hoy or date.today().isoformat()
        apo["lotes"][k].pop("items", None)
        guardar(APORTES, apo)
    return k


def generar(tipo: str = "auto", n: int | None = None, hoy: str | None = None) -> tuple[str | None, str]:
    """Crea el siguiente lote. Devuelve (id del lote o None si no queda nada, texto)."""
    hoy = hoy or date.today().isoformat()
    apo = cargar(APORTES, ap.vacio())
    recs = conciertos(hoy)
    if tipo == "auto":
        ultimo = max(apo.get("lotes", {}).values(), key=lambda l: l.get("creado", ""), default={}).get("tipo")
        tipo = "conciertos" if ultimo == "artistas" else "artistas"
    orden = [tipo, "conciertos" if tipo == "artistas" else "artistas"]
    for t in orden:
        cands = candidatos_artistas(recs, apo, hoy) if t == "artistas" else candidatos_conciertos(recs, apo, hoy)
        if not cands:
            continue
        num = sum(1 for k in apo.get("lotes", {}) if k.startswith(f"{t[0].upper()}-{hoy}")) + 1
        lote = f"{t[0].upper()}-{hoy}-{num:02d}"
        if t == "artistas":
            texto, pedido = lote_artistas(cands, n or N_ARTISTAS, lote)
        else:
            texto, pedido = lote_conciertos(cands, n or N_CONCIERTOS, lote)
        apo.setdefault("lotes", {})[lote] = {"tipo": t, "creado": hoy, "items": pedido, "pendientes": len(cands)}
        guardar(APORTES, apo)
        return lote, texto
    return None, "No queda nada que preguntar: todo lo que falta ya se ha preguntado en los últimos 30 días."


# ------------------------------------------------------------------ importar la respuesta
def extraer_json(texto: str) -> dict:
    bloques = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.S)
    for b in bloques + [texto[texto.find("{"):texto.rfind("}") + 1]]:
        try:
            d = json.loads(b)
        except ValueError:
            continue
        if isinstance(d, dict) and d.get("lote"):
            return d
    raise ValueError("no encuentro el bloque JSON con el campo \"lote\" en la respuesta")


def importar(texto: str, fetcher=None, hoy: str | None = None) -> str:
    """Comprueba la respuesta del chat y guarda lo aceptado. Devuelve el informe en Markdown."""
    hoy = hoy or date.today().isoformat()
    d = extraer_json(texto)
    apo = cargar(APORTES, ap.vacio())
    lote = apo.get("lotes", {}).get(d["lote"])
    if not lote:
        raise ValueError(f"el lote {d['lote']} no existe (¿es de otro día o ya se importó y se borró?)")
    if fetcher is None:
        from scraper.fetch import Fetcher
        fetcher = Fetcher()
    lector = ap.Lector(fetcher)
    lineas = [f"**Lote {d['lote']}** ({lote['tipo']})", ""]
    acept = rech = 0
    if lote["tipo"] == "artistas":
        for item in d.get("artistas") or []:
            ped = lote["items"].get(str(item.get("id")))
            if not ped:
                continue
            res = ap.verificar_artista(item, ped, lector)
            k = ped["clave"]
            if res["aceptado"]:
                a = apo.setdefault("artistas", {}).setdefault(k, {"nombre": ped["nombre"]})
                a.update(res["aceptado"])
                a["lote"], a["fecha"] = d["lote"], hoy
            apo.setdefault("consultados", {})["a:" + k] = {"fecha": hoy, "lote": d["lote"],
                                                           "aceptado": sorted(res["aceptado"]),
                                                           "rechazado": res["rechazado"][:4]}
            partes = []
            if str(item.get("identidad") or "").lower().startswith("no es"):
                # solo en las salas donde salió ("TAYLOR SWIFT" en Sala But es una fiesta; un concierto suyo no se oculta)
                apo.setdefault("ocultos", {})[k] = {"nombre": ped["nombre"], "motivo": str(item.get("nota") or "")[:160],
                                                    "salas": ped.get("salas") or [], "lote": d["lote"], "fecha": hoy}
                partes.append(f"🙈 no es un concierto: {str(item.get('nota') or '')[:120]} (se oculta de la agenda; "
                              f"lista revisable en aportes.json → ocultos)")
            if "pais" in res["aceptado"]:
                partes.append(f"✅ país {res['aceptado']['pais']['valor']}")
            if "estilos" in res["aceptado"]:
                partes.append("✅ estilos " + ", ".join(res["aceptado"]["estilos"]["valores"]))
            partes += [f"❌ {m}" for m in res["rechazado"]]
            if not partes:
                partes.append("— sin datos (el chat no encontró nada)")
            acept += sum(1 for x in ("pais", "estilos") if x in res["aceptado"])
            rech += len(res["rechazado"])
            lineas.append(f"- **{ped['nombre']}**: " + " · ".join(partes))
    else:
        recs = {ap.id_concierto(r): r for r in conciertos(hoy)}
        for item in d.get("conciertos") or []:
            ped = lote["items"].get(str(item.get("id")))
            if not ped:
                continue
            r = recs.get(ped["id"])
            etiqueta = f"{ped['fecha']} {ped['artista']} ({ped.get('sala')})"
            apo.setdefault("consultados", {})["c:" + ped["id"]] = {"fecha": hoy, "lote": d["lote"]}
            if not r:
                lineas.append(f"- **{etiqueta}**: — ya no está en la agenda")
                continue
            if not item.get("url"):
                lineas.append(f"- **{etiqueta}**: — sin página (el chat no la encontró)")
                continue
            res = ap.verificar_concierto(item, r, lector, ped.get("web_sala"))
            utiles = {k: v for k, v in res["aceptado"].items() if k != "pagina"}
            if utiles:
                apo.setdefault("conciertos", [])
                apo["conciertos"] = [c for c in apo["conciertos"] if c.get("id") != ped["id"]]
                apo["conciertos"].append({"id": ped["id"], "fecha": r["fecha"], "artistas": [r["artista"]],
                                          "salas": [r["sala"]] if r.get("sala") else [], **utiles,
                                          "lote": d["lote"], "comprobado": hoy})
            apo["consultados"]["c:" + ped["id"]].update({"aceptado": sorted(utiles), "rechazado": res["rechazado"][:4]})
            partes = [f"✅ {k}" + (f" {v['valor']}" if isinstance(v, dict) and v.get("valor") else "")
                      for k, v in utiles.items()] + [f"❌ {m}" for m in res["rechazado"]]
            acept += len(utiles)
            rech += len(res["rechazado"])
            lineas.append(f"- **{etiqueta}**: " + " · ".join(partes))
    lote["importado"] = hoy
    lote.pop("items", None)  # lo preguntado ya está en "consultados"
    guardar(APORTES, apo)
    lineas[1:1] = [f"{acept} datos aceptados y {rech} rechazados (cada dato se ha comprobado en la página citada).", ""]
    return "\n".join(lineas)


def ocultar(lista: list[dict], hoy: str | None = None) -> str:
    """Añade a la lista de ocultos [{nombre, motivo}] (lo que no es un concierto: fiestas, DJ, humor, cine…)."""
    apo = cargar(APORTES, ap.vacio())
    for x in lista:
        apo.setdefault("ocultos", {})[ap.clave_artista(x["nombre"])] = {
            "nombre": x["nombre"], "motivo": str(x.get("motivo") or "")[:160], "salas": x.get("salas") or [],
            "fecha": hoy or date.today().isoformat()}
    guardar(APORTES, apo)
    return f"Ocultos: {len(apo['ocultos'])} (añadidos {len(lista)})."


def mostrar(nombre: str) -> str:
    """Quita un nombre de la lista de ocultos: vuelve a salir en la agenda en la siguiente lectura."""
    apo = cargar(APORTES, ap.vacio())
    k = ap.clave_artista(nombre)
    quitado = (apo.get("ocultos") or {}).pop(k, None)
    guardar(APORTES, apo)
    return f"{'Vuelve a mostrarse' if quitado else 'No estaba oculto'}: {nombre}"


def estado(hoy: str | None = None) -> str:
    hoy = hoy or date.today().isoformat()
    apo = cargar(APORTES, ap.vacio())
    recs = conciertos(hoy)
    na, nc = len(candidatos_artistas(recs, apo, hoy)), len(candidatos_conciertos(recs, apo, hoy))
    arts = apo.get("artistas") or {}
    pend = [k for k, l in apo.get("lotes", {}).items() if not l.get("importado")]
    return (f"Por preguntar: {na} artistas (≈{-(-na // N_ARTISTAS)} lotes) y {nc} conciertos (≈{-(-nc // N_CONCIERTOS)} "
            f"lotes).\nAportado y comprobado: país de {sum(1 for a in arts.values() if a.get('pais'))} artistas, "
            f"estilos de {sum(1 for a in arts.values() if a.get('estilos'))}, datos de "
            f"{len(apo.get('conciertos') or [])} conciertos.\nLotes sin respuesta: {', '.join(pend) or 'ninguno'}.")


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="orden", required=True)
    g = sub.add_parser("generar")
    g.add_argument("--tipo", default="auto", choices=["auto", "artistas", "conciertos"])
    g.add_argument("--n", type=int)
    g.add_argument("--salida")
    i = sub.add_parser("importar")
    i.add_argument("respuesta")
    i.add_argument("--informe")
    sub.add_parser("estado")
    o = sub.add_parser("ocultar")
    o.add_argument("lista", help='JSON: [{"nombre": ..., "motivo": ...}]')
    m = sub.add_parser("mostrar")
    m.add_argument("nombre")
    sub.add_parser("pendiente")
    sub.add_parser("saltar")
    a = p.parse_args()
    if a.orden == "generar":
        lote, texto = generar(a.tipo, a.n)
        if a.salida:
            Path(a.salida).write_text(texto, encoding="utf-8")
        print(lote or "", file=sys.stderr)
        print(texto)
    elif a.orden == "importar":
        try:
            inf = importar(Path(a.respuesta).read_text(encoding="utf-8"))
        except ValueError as e:
            inf = (f"No he podido importar la respuesta: {e}. Comprueba que has pegado la respuesta completa del chat "
                   f"(con su bloque JSON) del lote pendiente ({pendiente() or 'ninguno'}).")
        if a.informe:
            Path(a.informe).write_text(inf, encoding="utf-8")
        print(inf)
    elif a.orden == "ocultar":
        print(ocultar(json.loads(a.lista)))
    elif a.orden == "mostrar":
        print(mostrar(a.nombre))
    elif a.orden == "pendiente":
        print(pendiente() or "")
    elif a.orden == "saltar":
        print(saltar() or "")
    else:
        print(estado())


if __name__ == "__main__":
    main()
