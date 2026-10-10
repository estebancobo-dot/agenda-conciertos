"""Lectura con navegador real (scraper/render.py) contra una web servida en esta máquina: monta la agenda que pinta
JavaScript, respeta robots.txt de la página y de cada petición que hace la página (las prohibidas se cortan, no se
hacen), se identifica con el User-Agent de siempre y no descarga imágenes. Necesita Playwright y Chromium (se salta
si no están)."""
import http.server
import os
import threading

import pytest
from bs4 import BeautifulSoup

from scraper.fetch import Fetcher, RobotsBlocked
from scraper.render import Navegador, RenderNoDisponible

pytest.importorskip("playwright.sync_api")

PAGINA = """<!doctype html><html><body><div id="agenda">cargando</div><img src="/foto.jpg">
<script>
Promise.all([fetch('/api/conciertos.json').then(r=>r.json()),
             fetch('/privado/secreto.json').then(r=>r.json()).catch(()=>({nombre:'cortado'}))])
  .then(([c,s])=>{document.getElementById('agenda').innerHTML=c.map(x=>`<p class="ev">${x}</p>`).join('')
    +`<p id="s">${s.nombre}</p>`;});
</script></body></html>"""
RUTAS = {"/robots.txt": ("text/plain", "User-agent: *\nDisallow: /privado/\nDisallow: /prohibida\n"),
         "/agenda": ("text/html", PAGINA), "/prohibida": ("text/html", PAGINA),
         "/api/conciertos.json": ("application/json", '["Muse 12/10", "Kmmn 13/10"]'),
         "/privado/secreto.json": ("application/json", '{"nombre": "no debía leerse"}'),
         "/foto.jpg": ("image/jpeg", "x")}


@pytest.fixture
def sitio():
    pedidas = []

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            pedidas.append((self.path, self.headers.get("User-Agent")))
            tipo, cuerpo = RUTAS.get(self.path, ("text/html", "no existe"))
            self.send_response(200 if self.path in RUTAS else 404)
            self.send_header("Content-Type", tipo + "; charset=utf-8")
            self.end_headers()
            self.wfile.write(cuerpo.encode())

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", pedidas
    srv.shutdown()


@pytest.fixture
def nav(monkeypatch):
    if os.environ.get("CHROMIUM") and not os.environ.get("NAVEGADOR"):
        monkeypatch.setenv("NAVEGADOR", os.environ["CHROMIUM"])
    n = Navegador(Fetcher(min_interval=0))
    try:
        n._arrancar()
    except RenderNoDisponible as e:
        pytest.skip(str(e))
    yield n
    n.cerrar()


def test_monta_la_agenda_y_corta_lo_que_robots_no_permite(sitio, nav):
    base, pedidas = sitio
    html = nav.html(base + "/agenda", esperar="#s")
    sp = BeautifulSoup(html, "lxml")
    assert [p.text for p in sp.select("#agenda p.ev")] == ["Muse 12/10", "Kmmn 13/10"]  # lo que pinta JavaScript
    # la petición a /privado/ que hace la página no se hace: robots.txt no la permite
    assert sp.select_one("#s").text == "cortado" and "no debía leerse" not in html
    assert any(u.endswith("/privado/secreto.json") for u in nav.cortadas)
    rutas = [p for p, _ in pedidas]
    assert "/privado/secreto.json" not in rutas and "/foto.jpg" not in rutas  # ni lo prohibido ni imágenes
    # se identifica como el lector de siempre en todas las peticiones
    assert {ua for _, ua in pedidas} == {nav.fetcher.user_agent}


def test_pagina_prohibida_por_robots_no_se_abre(sitio, nav):
    base, pedidas = sitio
    with pytest.raises(RobotsBlocked):
        nav.html(base + "/prohibida")
    assert "/prohibida" not in [p for p, _ in pedidas]


def test_pagina_que_no_existe_da_error(sitio, nav):
    base, _ = sitio
    with pytest.raises(RuntimeError, match="404"):
        nav.html(base + "/no-existe")


def test_sin_navegador_avisa(monkeypatch):
    monkeypatch.setenv("NAVEGADOR", "/no/existe/chromium")
    n = Navegador(Fetcher(min_interval=0))
    with pytest.raises(RenderNoDisponible):
        n._arrancar()
    assert n._browser is None
