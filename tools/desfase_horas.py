"""Diagnóstico: ¿cuánto se desvía la hora de cada agenda de la que da la web oficial de la sala, en los mismos
conciertos? Con la última lectura de cada fuente (data/fuentes_cache.json, sin red). Por agenda: conciertos
comparables, cuántos coinciden, cuántos dan la hora antes o después (y cuánto), y la diferencia más repetida. Sirve
para ver si una agenda da sistemáticamente la apertura de puertas en vez del inicio. Solo escribe en la salida.

Uso: python tools/desfase_horas.py [mínimo de conciertos comparables, 10 por defecto]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper.horas import diferencias  # noqa: E402
from scraper.registry import FUENTES  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent


def comparar(cache: dict, fuentes) -> dict:
    """{agenda: Counter(diferencia en minutos, agenda − sala)} (scraper/horas.py, lo mismo que mide cada lectura)."""
    return diferencias({sid: c.get("eventos") or [] for sid, c in cache.items()}, {s.id: s.tipo for s in fuentes})


def main() -> int:
    minimo = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    cache = json.loads((RAIZ / "data" / "fuentes_cache.json").read_text())
    nombres = {s.id: s.nombre for s in FUENTES}
    filas = []
    for sid, c in comparar(cache, FUENTES).items():
        n = sum(c.values())
        if n < minimo:
            continue
        igual = c[0]
        antes = sum(v for d, v in c.items() if d < 0)
        despues = sum(v for d, v in c.items() if d > 0)
        moda = c.most_common(1)[0]
        filas.append((sid, n, igual, antes, despues, moda, c))
    print(f"Agenda | comparables | coinciden | antes que la sala | después | diferencia más repetida | reparto")
    for sid, n, igual, antes, despues, moda, c in sorted(filas, key=lambda x: x[2] / x[1]):
        reparto = ", ".join(f"{d:+d}′:{v}" for d, v in sorted(c.items()) if v >= 2)
        print(f"{nombres.get(sid, sid)} | {n} | {igual} ({igual / n:.0%}) | {antes} | {despues} | "
              f"{moda[0]:+d} min ({moda[1]}) | {reparto}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
