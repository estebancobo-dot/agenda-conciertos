"""Uso: python -m scraper [--solo id1,id2] [--sin-musicbrainz] [--hoy AAAA-MM-DD] | --fichas [--minutos N]"""
import argparse
import logging
from datetime import date

from .pipeline import ejecutar


def main() -> None:
    ap = argparse.ArgumentParser(description="Agenda de conciertos de la Comunidad de Madrid")
    ap.add_argument("--solo", help="ids de fuentes separados por comas (por defecto, todas)")
    ap.add_argument("--sin-musicbrainz", action="store_true")
    ap.add_argument("--max-musicbrainz", type=int, default=600)
    ap.add_argument("--hoy", help="fecha de referencia AAAA-MM-DD (pruebas)")
    ap.add_argument("--fichas", action="store_true",
                    help="solo completar fichas de artista pendientes (no lee las agendas)")
    ap.add_argument("--minutos", type=int, default=50, help="tope de tiempo para --fichas")
    ap.add_argument("--reintentar", action="store_true",
                    help="volver a leer solo las fuentes que fallaron en la última ejecución")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    if a.fichas:
        from .pipeline import ejecutar_fichas
        st = ejecutar_fichas(hoy=date.fromisoformat(a.hoy) if a.hoy else None, presupuesto_seg=a.minutos * 60)
        print({k: v for k, v in st.items() if k != "errores"})
        for e in st["errores"]:
            print("  error:", e)
        return
    inf = ejecutar(hoy=date.fromisoformat(a.hoy) if a.hoy else None,
                   solo=a.solo.split(",") if a.solo else None,
                   musicbrainz=not a.sin_musicbrainz, max_mb=a.max_musicbrainz, reintentar=a.reintentar)
    if inf is None:
        print("Reintento: nada que cambiar (ninguna fuente pendiente o ninguna ha respondido)")
        return
    t = inf["totales"]
    print(f"Conciertos: {t['conciertos']} (en foco {t['en_foco']}, contrastados {t['contrastados']}, "
          f"1 fuente {t['una_fuente']}, conflictos {t['conflictos']}, posiblemente cancelados "
          f"{t['posiblemente_cancelados']}) · fuentes OK {t['fuentes_ok']}/{t['fuentes_total']}")
    for f in inf["fuentes"]:
        print(f"  {f['id']:24} {f['estado']:18} {f['conciertos']:4} conc. {f['nuevos']:4} nuevos "
              f"{f['solo_en_esta']:4} solo aquí {f['paginas']:3} págs {'; '.join(f['errores'])[:120]}")


if __name__ == "__main__":
    main()
