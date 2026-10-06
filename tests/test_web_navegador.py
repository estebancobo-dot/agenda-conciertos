"""La web en un navegador real con datos fijos (los del recorrido completo, sin red): filtros de origen, tarjeta,
ficha con nivel y botón de compra. No depende de los conciertos del día como la validación de la web publicada.
Necesita Playwright y Chromium (se salta si no están; corre en validar_web.yml)."""
import functools
import http.server
import json
import os
import shutil
import sys
import threading
from pathlib import Path

import pytest

from scraper import pipeline
from tests.test_recorrido import entorno  # noqa: F401  (fixture: agendas y fichas fijas)

sync_api = pytest.importorskip("playwright.sync_api")
RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def web(entorno, tmp_path):  # noqa: F811
    sys.path.insert(0, str(RAIZ / "tools"))
    import web_datos
    pipeline.ejecutar(hoy=pipeline.date.today(), musicbrainz=False, pausa_reintento=0)
    sitio = tmp_path / "sitio"
    (sitio / "data").mkdir(parents=True)
    shutil.copy(RAIZ / "site" / "index.html", sitio)
    for n in ("taxonomia.json", "estilos_map.json", "salas_alias.json"):
        shutil.copy(RAIZ / "data" / n, sitio / "data")
    (sitio / "data" / "informe.json").write_text("{}")
    web_datos.preparar(json.loads((entorno / "concerts.json").read_text()), sitio / "data")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(sitio)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/"
    srv.shutdown()


def test_filtros_tarjeta_y_ficha(web):
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None)
        except Exception as e:  # noqa: BLE001
            pytest.skip(f"sin Chromium: {e}")
        pg = b.new_page(viewport={"width": 390, "height": 844})
        errores = []
        pg.on("pageerror", lambda e: errores.append(str(e)))
        pg.goto(web + "#todos")
        pg.wait_for_function("DATA.length>0", timeout=15000)
        orig = lambda o: pg.evaluate(f"DATA.filter(r=>origenDe(r,'{o}')).map(r=>r.artista.toLowerCase()).sort()")  # noqa: E731
        assert orig("ext") == ["muse"]                      # Reino Unido según Wikidata
        assert orig("es") == ["orfeón de moratalaz"]        # deducido: agrupación local
        assert orig("nc") == ["kmmn"]                       # nada lo dice: sin confirmar
        mid = pg.evaluate("DATA.find(r=>r.artista.toLowerCase()==='muse').id")
        assert "gran formato" in pg.evaluate(f"card(BYID['{mid}'])")
        pg.evaluate(f"location.hash='#concierto/{mid}'")
        pg.wait_for_selector("#nivel", timeout=15000)
        assert "Gran formato" in pg.inner_text("#nivel") and "oyentes" in pg.inner_text("#nivel")
        pg.wait_for_selector("#comprar", timeout=15000)
        assert "Ticketmaster" in pg.inner_text("#comprar")
        assert pg.get_attribute("#comprar", "href") == "https://www.ticketmaster.es/event/muse-123"
        gid = pg.evaluate("DATA.find(r=>r.artista.toLowerCase()==='kmmn').id")
        pg.evaluate(f"location.hash='#concierto/{gid}'")
        pg.wait_for_function("document.querySelector('.rows') && document.body.innerText.includes('Origen sin confirmar')",
                             timeout=15000)
        assert not errores, errores
        b.close()
