"""Capturas de la web con datos fijos y un día fijo (FECHA_PRUEBAS, también en el reloj del navegador), para
compararlas con las de la validación anterior (tools/comparar_capturas.py, en validar_web.yml): un cambio de aspecto
que nadie buscaba se ve aunque todo siga funcionando. Solo corre con CAPTURAS=carpeta de destino."""
import os
from datetime import datetime
from pathlib import Path

import pytest

from tests.test_web_navegador import D2, DIA, id_de, nav, web  # noqa: F401  (fixtures)
from tests.test_recorrido import entorno  # noqa: F401  (fixture)

DESTINO = os.environ.get("CAPTURAS")
pytestmark = pytest.mark.skipif(not DESTINO or not os.environ.get("FECHA_PRUEBAS"),
                                reason="solo con CAPTURAS y FECHA_PRUEBAS (validar_web.yml)")


def pagina(nav, url, *, ancho=390, alto=844, oscuro=False):  # noqa: F811
    _, b = nav
    ctx = b.new_context(viewport={"width": ancho, "height": alto}, color_scheme="dark" if oscuro else "light",
                        locale="es-ES", timezone_id="Europe/Madrid", device_scale_factor=1)
    ctx.clock.set_fixed_time(datetime.fromisoformat(os.environ["FECHA_PRUEBAS"] + "T12:00:00+02:00"))
    pg = ctx.new_page()
    pg.goto(url)
    pg.wait_for_function("DATA.length>0", timeout=15000)
    pg.wait_for_selector("#main .card, #main .rows", timeout=15000)
    pg.evaluate("document.fonts && document.fonts.ready")
    return pg


def foto(pg, nombre):
    Path(DESTINO).mkdir(parents=True, exist_ok=True)
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(Path(DESTINO) / f"{nombre}.png"), animations="disabled", caret="hide")


def test_capturas(web, nav):  # noqa: F811
    semana = web + f"#semana/{DIA.isoformat()}"
    pg = pagina(nav, semana)
    pg.click("#fvertodos")
    for m in ("lista", "compacta", "cuadricula"):
        pg.click(f"[data-modo='{m}']")
        pg.evaluate("scrollTo(0,0)")
        foto(pg, f"movil_semana_{m}")
    pg.click("[data-modo='lista']")
    pg.click("#fgen")
    pg.wait_for_selector(".sheet")
    foto(pg, "movil_filtros")
    pg.click("#sx")
    pg.evaluate(f"location.hash='#concierto/{id_de(pg, 'Muse')}'")
    pg.wait_for_function("!document.getElementById('cargando')")
    foto(pg, "movil_ficha")
    pg.evaluate(f"location.hash='#concierto/{id_de(pg, 'Los Conflictos')}'")
    pg.wait_for_function("!document.getElementById('cargando') && !!document.querySelector('.box-bad')")
    foto(pg, "movil_ficha_conflicto")
    pg.evaluate(f"location.hash='#mes/{DIA.isoformat()}'")
    pg.wait_for_selector("#main .cal")
    foto(pg, "movil_mes")
    pg = pagina(nav, semana, oscuro=True)
    foto(pg, "movil_semana_oscuro")
    pg = pagina(nav, semana, ancho=1440, alto=900)
    pg.click("#fvertodos")
    pg.click(f"#main .card[data-id='{id_de(pg, 'Muse')}']")
    pg.wait_for_selector("#panel .rows")
    pg.wait_for_function("!document.querySelector('#panel #cargando')")
    foto(pg, "ordenador_semana_ficha")
