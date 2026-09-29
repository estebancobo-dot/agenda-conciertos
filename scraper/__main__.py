"""Uso: python -m scraper [--solo id1,id2] [--sin-musicbrainz] [--hoy AAAA-MM-DD]"""
import argparse
import logging
from datetime import date

from .pipeline import ejecutar


def main() -> None:
    ap = argparse.ArgumentParser(description="Agenda de conciertos de la Comunidad de Madrid")
    ap.add_argument("--solo", help="ids de fuentes separados por comas (por defecto, todas)")
    ap.add_argument("--sin-musicbrainz", action="store_true")
    ap.add_argument("--max-musicbrainz", type=int, default=700)
    ap.add_argument("--hoy", help="fecha de referencia AAAA-MM-DD (pruebas)")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    inf = ejecutar(hoy=date.fromisoformat(a.hoy) if a.hoy else None,
                   solo=a.solo.split(",") if a.solo else None,
                   musicbrainz=not a.sin_musicbrainz, max_mb=a.max_musicbrainz)
    t = inf["totales"]
    print(f"Conciertos: {t['conciertos']} (en foco {t['en_foco']}, contrastados {t['contrastados']}, "
          f"1 fuente {t['una_fuente']}, conflictos {t['conflictos']}, posiblemente cancelados "
          f"{t['posiblemente_cancelados']}) · fuentes OK {t['fuentes_ok']}/{t['fuentes_total']}")
    for f in inf["fuentes"]:
        print(f"  {f['id']:24} {f['estado']:18} {f['conciertos']:4} conc. {f['nuevos']:4} nuevos "
              f"{f['solo_en_esta']:4} solo aquí {f['paginas']:3} págs {'; '.join(f['errores'])[:120]}")


if __name__ == "__main__":
    main()
