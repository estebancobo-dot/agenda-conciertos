"""Prueba real de la comprobación de los lotes (fase D) con páginas de verdad, sin guardar nada: datos correctos que
se tienen que aceptar y datos falsos que se tienen que rechazar. Solo escribe en la salida."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper import aportes as ap  # noqa: E402
from scraper.fetch import Fetcher  # noqa: E402

BUZZ = "https://www.jacksonlive.es/concierto/concierto-de-the-buzz-lovers-en-madrid"
SILVIO = "https://www.jacksonlive.es/concierto/concierto-de-silvio-rodriguez-en-madrid"
lector = ap.Lector(Fetcher())
casos = [
    ("artista bien: estilos", True, "estilos", ap.verificar_artista(
        {"identidad": "seguro", "estilos": ["grunge", "punk rock"], "estilos_url": BUZZ,
         "estilos_cita": "dos tributos dedicados a referentes fundamentales del grunge y el punk rock"},
        {"nombre": "The Buzz Lovers"}, lector)),
    ("artista bien: país por gentilicio", True, "pais", ap.verificar_artista(
        {"identidad": "seguro", "pais": "CU", "pais_url": SILVIO,
         "pais_cita": "El maestro de la Nueva Trova Cubana ofrecerá nueve conciertos"},
        {"nombre": "Silvio Rodríguez"}, lector)),
    ("artista mal: país inventado", False, "pais", ap.verificar_artista(
        {"identidad": "seguro", "pais": "AR", "pais_url": SILVIO,
         "pais_cita": "El maestro de la Nueva Trova Cubana ofrecerá nueve conciertos"},
        {"nombre": "Silvio Rodríguez"}, lector)),
    ("artista mal: frase que no está", False, "estilos", ap.verificar_artista(
        {"identidad": "seguro", "estilos": ["heavy metal"], "estilos_url": BUZZ,
         "estilos_cita": "la mejor banda de heavy metal de Vallecas"}, {"nombre": "The Buzz Lovers"}, lector)),
    ("artista mal: página de otro artista", False, "pais", ap.verificar_artista(
        {"identidad": "seguro", "pais": "CU", "pais_url": BUZZ,
         "pais_cita": "dos tributos dedicados a referentes fundamentales del grunge"}, {"nombre": "Silvio Rodríguez"},
        lector)),
]
rec = {"fecha": "2026-10-09", "artista": "The Buzz Lovers", "sala": "Sala Changó"}
c_bien = ap.verificar_concierto({"url": BUZZ, "hora": "19:00", "precio": "15 €"}, rec, lector)
c_mal = ap.verificar_concierto({"url": BUZZ, "hora": "22:30", "precio": "40 €"}, rec, lector)
c_fecha = ap.verificar_concierto({"url": BUZZ, "hora": "19:00"}, dict(rec, fecha="2026-10-10"), lector)
casos += [("concierto bien: hora", True, "hora", c_bien), ("concierto bien: precio", True, "precio", c_bien),
          ("concierto mal: hora", False, "hora", c_mal), ("concierto mal: precio", False, "precio", c_mal),
          ("concierto mal: otra fecha", False, "hora", c_fecha)]
fallos = 0
for nombre, debe, campo, res in casos:
    ok = (campo in res["aceptado"]) == debe
    fallos += not ok
    print(f"{'OK ' if ok else 'MAL'} {nombre}: aceptado={sorted(res['aceptado'])} rechazado={res['rechazado']}")
print(f"\n{len(casos) - fallos} de {len(casos)} como se esperaba")

# un lote de verdad con los datos de hoy, sin guardar nada
import tools.lotes as lotes  # noqa: E402
lotes.APORTES = Path(tempfile.mkdtemp()) / "aportes.json"
print("\n" + lotes.estado())
for t in ("artistas", "conciertos"):
    lote, texto = lotes.generar(t)
    print(f"\n--- {lote}: {len(texto)} letras ---\n{texto[-1800:]}")
sys.exit(1 if fallos else 0)
