"""Calendarios suscribibles y fichas de sala para la web (fase 7).

  - DESTINO/calendario/sala-<nombre>.ics: los conciertos de cada sala;
  - DESTINO/calendario/genero-<nombre>.ics: los de cada género (también los festivales y carteles donde toca un
    artista de ese género);
  - DESTINO/data/salas.json: cada sala con su municipio, su web, cuántos conciertos tiene, de qué webs salen y su
    calendario (lo usa la página de la sala).

Un calendario suscrito (Google Calendar, Apple Calendar, Outlook…) se vuelve a descargar solo cada pocas horas:
los conciertos nuevos aparecen, los cambios de hora o de fecha se actualizan (mismo UID) y los cancelados se marcan.
Nada se inventa: sin hora anunciada el concierto ocupa el día entero; la duración de 3 horas es solo para que se vea
en la agenda (se dice en la descripción que la hora de fin no está anunciada).
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from scraper.normalize import norm  # noqa: E402

SITIO = os.environ.get("SITIO_URL", "https://estebancobo-dot.github.io/agenda-conciertos/")
DIAS_ATRAS = 7  # lo de la semana pasada sigue en el calendario (no desaparece nada más pasar)
NO_CALENDARIO = {"fuera de foco"}
# zona horaria de Madrid (reglas de la UE desde 1996): obligatoria en el archivo cuando se usa TZID
VTIMEZONE = ["BEGIN:VTIMEZONE", "TZID:Europe/Madrid", "X-LIC-LOCATION:Europe/Madrid",
             "BEGIN:DAYLIGHT", "TZOFFSETFROM:+0100", "TZOFFSETTO:+0200", "TZNAME:CEST", "DTSTART:19700329T020000",
             "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU", "END:DAYLIGHT",
             "BEGIN:STANDARD", "TZOFFSETFROM:+0200", "TZOFFSETTO:+0100", "TZNAME:CET", "DTSTART:19701025T030000",
             "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU", "END:STANDARD", "END:VTIMEZONE"]


def slug(s: str) -> str:
    return re.sub(r"\s+", "-", norm(s))[:60].strip("-") or "sin-nombre"


def _txt(s) -> str:
    return re.sub(r"([\;,])", r"\\\1", str(s or "")).replace("\r", "").replace("\n", "\\n")


def _plegar(linea: str) -> list[str]:
    """Líneas de 75 octetos como máximo (RFC 5545), sin partir un carácter UTF-8."""
    out, actual = [], ""
    for ch in linea:
        lim = 75 if not out else 74
        if len((actual + ch).encode("utf-8")) > lim:
            out.append(actual)
            actual = ch
        else:
            actual += ch
    out.append(actual)
    return [out[0]] + [" " + x for x in out[1:]]


def salas_de(r: dict) -> list[str]:
    return [x.strip() for x in (r.get("sala") or "").split(" / ") if x.strip()]


def grupos_de(r: dict) -> list[str]:
    return list(dict.fromkeys([*(r.get("grupos") or []), *(r.get("grupos_cartel") or {})]))


def vevent(r: dict, sello: str) -> list[str]:
    d = r["fecha"].replace("-", "")
    hora = (r.get("hora") or "").replace(":", "")
    ev = (r.get("estado_evento") or {}).get("tipo")
    pref = "Cancelado: " if ev == "cancelado" else "Aplazado: " if ev == "aplazado" else \
        "¿Cancelado? " if r.get("estado") == "posiblemente cancelado" else ""
    sala = " / ".join(salas_de(r))
    desc = []
    if r.get("ciclo"):
        desc.append(r["ciclo"])
    if r.get("invitados"):
        desc.append(("Cartel: " if r.get("festival") else "Con ") + ", ".join(r["invitados"][:12]))
    estilos = r.get("estilos_discogs") or [e["estilo"] for e in r.get("estilo_fuente") or []][:3]
    if estilos:
        desc.append("Estilo: " + ", ".join(dict.fromkeys(estilos)))
    if r.get("precio"):
        desc.append("Precio: " + str(r["precio"]))
    if not hora:
        desc.append("Hora sin anunciar.")
    else:
        desc.append("Hora de fin no anunciada.")
    if r.get("agotado"):
        desc.append("Entradas agotadas.")
    url = f"{SITIO}#concierto/{r['id']}"
    desc.append(url)
    cambios = r.get("cambios") or []
    modif = max([c["dia"] for c in cambios] + [r.get("primera_vez_visto") or r["fecha"]])
    lineas = ["BEGIN:VEVENT", f"UID:{r['id']}@agenda-conciertos", f"DTSTAMP:{sello}",
              f"LAST-MODIFIED:{modif.replace('-', '')}T000000Z", f"SEQUENCE:{len(cambios)}"]
    if hora:
        lineas += [f"DTSTART;TZID=Europe/Madrid:{d}T{hora}00", "DURATION:PT3H"]
    else:
        fin = (date.fromisoformat(r["fecha"]) + timedelta(days=1)).isoformat().replace("-", "")
        lineas += [f"DTSTART;VALUE=DATE:{d}", f"DTEND;VALUE=DATE:{fin}", "TRANSP:TRANSPARENT"]
    lineas += [f"SUMMARY:{_txt(pref + r['artista'])}",
               f"LOCATION:{_txt(', '.join(x for x in (sala, r.get('municipio') or 'Madrid') if x))}",
               f"DESCRIPTION:{_txt(chr(10).join(desc))}", f"URL:{url}",
               "STATUS:" + ("CANCELLED" if ev == "cancelado" else "TENTATIVE" if pref else "CONFIRMED"),
               "END:VEVENT"]
    return lineas


def ics(nombre: str, recs: list[dict], sello: str) -> str:
    lineas = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//agenda-conciertos//Conciertos en Madrid//ES",
              "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{_txt(nombre)}",
              "X-WR-TIMEZONE:Europe/Madrid", f"X-WR-CALDESC:{_txt('Conciertos en la Comunidad de Madrid · ' + SITIO)}",
              "REFRESH-INTERVAL;VALUE=DURATION:PT6H", "X-PUBLISHED-TTL:PT6H", *VTIMEZONE]
    for r in sorted(recs, key=lambda r: (r["fecha"], r.get("hora") or "99")):
        lineas += vevent(r, sello)
    lineas.append("END:VCALENDAR")
    return "\r\n".join(x for l in lineas for x in _plegar(l)) + "\r\n"


def generar(concerts: dict, sitio: Path, nombres_grupo: dict[str, str], salas_alias: list[dict],
            ahora: datetime | None = None) -> dict:
    ahora = ahora or datetime.now(timezone.utc)
    sello = ahora.strftime("%Y%m%dT%H%M%SZ")
    hoy = concerts.get("hoy") or ahora.date().isoformat()
    desde = (date.fromisoformat(hoy) - timedelta(days=DIAS_ATRAS)).isoformat()
    recs = [r for r in concerts.get("conciertos", []) if r["fecha"] >= desde]
    por_sala, por_grupo = defaultdict(list), defaultdict(list)
    for r in recs:
        for s in salas_de(r):
            por_sala[s].append(r)
        for g in grupos_de(r):
            if g not in NO_CALENDARIO:
                por_grupo[g].append(r)
    carpeta = sitio / "calendario"
    carpeta.mkdir(parents=True, exist_ok=True)
    alias = {norm(x["nombre"]): x for x in salas_alias}
    salas, cal_grupos, usados = [], {}, set()
    for nombre, rs in sorted(por_sala.items()):
        futuros = [r for r in rs if r["fecha"] >= hoy]
        if not futuros:
            continue
        archivo = f"sala-{slug(nombre)}"
        while archivo in usados:
            archivo += "-2"
        usados.add(archivo)
        (carpeta / f"{archivo}.ics").write_text(ics(f"Conciertos · {nombre}", rs, sello), encoding="utf-8")
        fuentes = Counter(f["nombre"].split(" (")[0] for r in futuros for f in r.get("fuentes") or [])
        oficial = Counter(f["nombre"] for r in futuros for f in r.get("fuentes") or [] if f.get("prioridad") == 1)
        info = alias.get(norm(nombre), {})
        municipios = Counter(r.get("municipio") for r in futuros if r.get("municipio"))
        salas.append({"nombre": nombre, "municipio": info.get("municipio") or (municipios.most_common(1) or [[None]])[0][0],
                      "web": info.get("web"), "conciertos": len(futuros),
                      "oficial": oficial.most_common(1)[0][0] if oficial else None,
                      "fuentes": [{"nombre": n, "conciertos": c} for n, c in fuentes.most_common(8)],
                      "ics": f"calendario/{archivo}.ics"})
    for g, rs in sorted(por_grupo.items()):
        if not any(r["fecha"] >= hoy for r in rs):
            continue
        archivo = f"genero-{slug(g)}"
        (carpeta / f"{archivo}.ics").write_text(ics(f"Conciertos · {nombres_grupo.get(g, g)}", rs, sello),
                                                encoding="utf-8")
        cal_grupos[g] = f"calendario/{archivo}.ics"
    (sitio / "data").mkdir(parents=True, exist_ok=True)
    (sitio / "data" / "salas.json").write_text(
        json.dumps({"generado": ahora.isoformat(timespec="seconds"), "salas": salas, "generos": cal_grupos},
                   ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return {"calendarios_sala": len(salas), "calendarios_genero": len(cal_grupos)}


def nombres_grupo_web() -> dict[str, str]:
    """Los nombres de los géneros tal como los enseña la web (la lista GRUPOS de site/index.html)."""
    html = (RAIZ / "site" / "index.html").read_text(encoding="utf-8")
    return dict(re.findall(r'\{id:"([^"]+)",\s*nombre:"([^"]+)"', html))


def main() -> int:
    sitio = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "_site"
    concerts = json.loads((RAIZ / "data" / "concerts.json").read_text(encoding="utf-8"))
    alias = json.loads((RAIZ / "data" / "salas_alias.json").read_text(encoding="utf-8")).get("salas", [])
    print(generar(concerts, sitio, nombres_grupo_web(), alias))
    return 0


if __name__ == "__main__":
    sys.exit(main())
