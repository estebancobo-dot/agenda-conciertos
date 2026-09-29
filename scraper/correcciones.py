"""Correcciones manuales verificadas (data/correcciones.json). Se aplican siempre después del rastreo."""
from __future__ import annotations

from .merge import UMBRAL, nombres_rec
from .normalize import canon_sala, es_generico, misma_sala, norm, parecido


def coincide(c: dict, r: dict) -> bool:
    if r["fecha"] != c["fecha"]:
        return False
    if c.get("hora") and r.get("hora") and r["hora"] != c["hora"]:
        return False
    if c.get("hora") and not r.get("hora"):
        # sin hora en el registro: solo si además coincide artista o sala
        if not (c.get("artistas") or c.get("salas")):
            return False
    if c.get("municipio") and r.get("municipio") and norm(r["municipio"]) != norm(c["municipio"]):
        return False
    if c.get("salas"):
        salas_r = [s.strip() for s in (r.get("sala") or "").split(" / ") if s.strip()]
        if not any(misma_sala(canon_sala(cs), sr) for cs in c["salas"] for sr in salas_r):
            return False
    if c.get("artistas"):
        nombres = nombres_rec(r)
        if not any(parecido(a, n) >= UMBRAL for a in c["artistas"] for n in nombres if not es_generico(n)):
            return False
    return True


def aplicar(recs: list[dict], correcciones: list[dict], hoy: str) -> tuple[list[dict], dict]:
    """Devuelve (registros, resumen). Los descartes se quitan; los conflictos fusionan todos los registros
    que coinciden en uno solo, guardando todas las versiones."""
    resumen = {"aplicadas": [], "sin_coincidencia": [], "descartados": []}
    for c in correcciones:
        matches = [r for r in recs if coincide(c, r)]
        etiqueta = f"{c['tipo']} {c['fecha']} {', '.join(c.get('artistas', []) or c.get('salas', []))}"
        if not matches:
            resumen["sin_coincidencia"].append({"correccion": etiqueta, "nota": c.get("nota")})
            continue
        resumen["aplicadas"].append({"correccion": etiqueta, "registros": len(matches)})
        nota = f"Corrección manual verificada ({c.get('verificado', 's/f')}): {c.get('nota', '')}".strip()
        if c["tipo"] == "descarte":
            for r in matches:
                resumen["descartados"].append({"id": r["id"], "fecha": r["fecha"], "artista": r["artista"],
                                               "sala": r["sala"], "motivo": c.get("nota")})
            ids = {id(r) for r in matches}
            recs = [r for r in recs if id(r) not in ids]
        elif c["tipo"] == "conflicto":
            base = matches[0]
            for otro in matches[1:]:
                versiones = []
                for r in (base, otro):
                    cartel = r["artista"] + (" + " + " + ".join(r["invitados"]) if r["invitados"] else "")
                    versiones.append({"valor": f"{cartel} ({r['sala']}{', ' + r['hora'] if r['hora'] else ''})",
                                      "fuentes": sorted({f["nombre"] for f in r["fuentes"]})})
                base["conflictos"].append({"campo": "cartel/sala/hora (corrección manual)", "versiones": versiones})
                base["fuentes"] += [f for f in otro["fuentes"] if f not in base["fuentes"]]
                for n in otro["notas"]:
                    if n not in base["notas"]:
                        base["notas"].append(n)
                for e in otro["estilo_fuente"]:
                    if e not in base["estilo_fuente"]:
                        base["estilo_fuente"].append(e)
                base.setdefault("versiones_fusionadas", []).append(
                    {k: otro[k] for k in ("id", "artista", "invitados", "sala", "hora", "municipio")})
            ids = {id(r) for r in matches[1:]}
            recs = [r for r in recs if id(r) not in ids]
            base["estado"] = "conflicto"
            if not base["conflictos"]:
                base["conflictos"].append({"campo": "corrección manual", "versiones": []})
            if nota not in base["notas"]:
                base["notas"].insert(0, nota)
            base["correccion_manual"] = True
        elif c["tipo"] == "nota":
            for r in matches:
                if nota not in r["notas"]:
                    r["notas"].append(nota)
    return recs, resumen
