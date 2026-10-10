"""La web en un navegador real con datos fijos (los del recorrido completo y unos pocos más, sin red): filtros,
búsqueda, tarjeta, ficha, conflictos, Mis conciertos, Novedades, página de sala con su calendario, modos de vista y
la ficha al lado en el ordenador. No depende de los conciertos del día como la validación de la web publicada.

Corre antes de publicar (actualizar.yml, publicar_web.yml) y en la validación (validar_web.yml), también con
Safari (WebKit, como un iPhone) y Firefox: NAVEGADOR_PRUEBA=webkit|firefox (por defecto, Chromium). Se salta si
Playwright o el navegador no están instalados."""
import functools
import http.server
import json
import os
import shutil
import sys
import threading
from datetime import timedelta
from pathlib import Path

import pytest

from scraper import pipeline
from scraper.model import RawEvent
from tests.fakefetch import FakeFetcher
from tests.test_recorrido import DIA, HOY, _fuente
from tests.test_recorrido import entorno  # noqa: F401  (fixture: agendas y fichas fijas)

sync_api = pytest.importorskip("playwright.sync_api")
RAIZ = Path(__file__).resolve().parent.parent
TIPO = os.environ.get("NAVEGADOR_PRUEBA", "chromium")
D2 = DIA + timedelta(days=1)


@pytest.fixture
def web(entorno, tmp_path, monkeypatch):  # noqa: F811
    sys.path.insert(0, str(RAIZ / "tools"))
    import calendarios
    import web_datos
    # además del recorrido: un concierto de jazz (fuera de los géneros por defecto) y una hora en la que dos agendas
    # de la misma prioridad no coinciden
    ganzua = [RawEvent(fecha=D2, artista="Los Conflictos", url="https://laganzua.es/c", sala="Sala El Sol",
                       ciudad="Madrid", hora="20:00"),
              RawEvent(fecha=D2, artista="Cuarteto Swing de Lavapiés", url="https://laganzua.es/s", sala="Café Central",
                       ciudad="Madrid", hora="21:00", estilo="Jazz")]
    rock = [RawEvent(fecha=D2, artista="Los Conflictos", url="https://rock.es/c", sala="Sala El Sol", ciudad="Madrid",
                     hora="21:00")]
    monkeypatch.setattr(pipeline, "FUENTES", [*pipeline.FUENTES, _fuente("laganzua", "La Ganzúa", "agregador", 2, ganzua),
                                              _fuente("rockb", "Rock Blog", "agregador", 2, rock)])
    pipeline.ejecutar(hoy=HOY, musicbrainz=False, pausa_reintento=0, fetcher=FakeFetcher({}))
    sitio = tmp_path / "sitio"
    (sitio / "data").mkdir(parents=True)
    shutil.copy(RAIZ / "site" / "index.html", sitio)
    for n in ("taxonomia.json", "estilos_map.json", "salas_alias.json"):
        shutil.copy(RAIZ / "data" / n, sitio / "data")
    (sitio / "data" / "informe.json").write_text("{}")
    concerts = json.loads((entorno / "concerts.json").read_text())
    if os.environ.get("FECHA_PRUEBAS"):  # día fijo (capturas): también la hora de «actualizado» de la cabecera
        concerts["generado"] = f"{HOY.isoformat()}T09:00:00+00:00"
    web_datos.preparar(concerts, sitio / "data")
    calendarios.generar(concerts, sitio, {}, json.loads((RAIZ / "data" / "salas_alias.json").read_text())["salas"])
    class Silencioso(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Silencioso, directory=str(sitio)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/"
    srv.shutdown()


@pytest.fixture
def nav():
    with sync_api.sync_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if TIPO == "chromium" and os.environ.get("CHROMIUM") else {}
        try:
            b = getattr(p, TIPO).launch(**kw)
        except Exception as e:  # noqa: BLE001
            pytest.skip(f"sin {TIPO}: {e}")
        yield p, b
        b.close()


def abrir(nav, url, *, ordenador=False):
    """Una página como un móvil (en WebKit, un iPhone 13) o como un ordenador; recoge los errores de JavaScript."""
    p, b = nav
    if ordenador:
        opciones = {"viewport": {"width": 1440, "height": 900}}
    elif TIPO == "webkit":
        opciones = {k: v for k, v in p.devices["iPhone 13"].items() if k != "default_browser_type"}
    else:
        opciones = {"viewport": {"width": 390, "height": 844}}
    pg = b.new_context(**opciones).new_page()
    pg.errores = []
    pg.on("pageerror", lambda e: pg.errores.append(str(e)))
    pg.goto(url)
    pg.wait_for_function("DATA.length>0", timeout=15000)
    pg.wait_for_selector("#main .card, #main .rows", timeout=15000)
    return pg


def id_de(pg, artista):
    return pg.evaluate(f"DATA.find(r=>r.artista.toLowerCase()==={json.dumps(artista.lower())}).id")


def ficha(pg, artista):
    pg.evaluate(f"location.hash='#concierto/{id_de(pg, artista)}'")
    pg.wait_for_selector("#main .rows", timeout=15000)
    pg.wait_for_function("!document.getElementById('cargando')", timeout=15000)  # con su detalle ya cargado


def test_origen_ficha_nivel_y_compra(web, nav):
    pg = abrir(nav, web + "#todos")
    orig = lambda o: pg.evaluate(f"DATA.filter(r=>origenDe(r,'{o}')).map(r=>r.artista.toLowerCase()).sort()")  # noqa: E731
    assert orig("ext") == ["muse"]                      # Reino Unido según Wikidata
    assert "orfeón de moratalaz" in orig("es")          # deducido: agrupación local
    assert "kmmn" in orig("nc")                         # nada lo dice: sin confirmar
    assert "gran formato" in pg.evaluate(f"card(BYID['{id_de(pg, 'muse')}'])")
    ficha(pg, "Muse")
    assert "Gran formato" in pg.inner_text("#nivel") and "oyentes" in pg.inner_text("#nivel")
    assert "Ticketmaster" in pg.inner_text("#comprar")
    assert pg.get_attribute("#comprar", "href") == "https://www.ticketmaster.es/event/muse-123"
    # lo necesario para ir antes que la confirmación: fecha, sala y comprar arriba
    orden = pg.evaluate("(()=>{const y=s=>{const e=document.querySelector(s);return e?e.getBoundingClientRect().top:1e9};"
                        "return [y('.rows'),y('#comprar'),y('.confb')]})()")
    assert orden == sorted(orden), orden
    # zonas táctiles de al menos 44 px en el móvil
    bajos = pg.evaluate("[...document.querySelectorAll('.back,.row a,.seg button')]"
                        ".filter(a=>a.getBoundingClientRect().height<44).map(a=>a.textContent)")
    assert not bajos, bajos
    ficha(pg, "Kmmn")
    assert "Origen sin confirmar" in pg.inner_text("#main")
    assert not pg.errores, pg.errores


def test_conflicto_de_hora_en_tarjeta_y_ficha(web, nav):
    pg = abrir(nav, web + "#todos")
    if pg.locator("#fvertodos").count():
        pg.click("#fvertodos")
    assert "sin confirmar" in pg.evaluate(f"card(BYID['{id_de(pg, 'Los Conflictos')}'])")
    ficha(pg, "Los Conflictos")
    caja = pg.inner_text(".box-bad")
    assert "Las webs no coinciden" in caja and "20:00" in caja and "21:00" in caja
    assert "La Ganzúa" in caja and "Rock Blog" in caja
    assert not pg.errores, pg.errores


def test_generos_ocultos_busqueda_y_hoja_de_filtros(web, nav):
    pg = abrir(nav, web + f"#semana/{DIA.isoformat()}")
    swing = id_de(pg, "Cuarteto Swing de Lavapiés")
    tarjetas = lambda: pg.evaluate("[...document.querySelectorAll('#main .card')].map(c=>c.dataset.id)")  # noqa: E731
    # por defecto ("Rock, pop y afines") el jazz no sale, pero se dice cuántos quedan fuera
    assert swing not in tarjetas() and "otros géneros" in pg.inner_text(".fuera")
    # la búsqueda mira en todos los géneros
    pg.fill("#q", "swing")
    pg.wait_for_function("document.querySelectorAll('#main .card').length>0")
    assert tarjetas() == [swing] and "géneros" in pg.inner_text("#main .hint")
    pg.fill("#q", "")
    pg.wait_for_selector(".fuera")
    # "Ver todos los géneros" lo enseña
    pg.click("#fvertodos")
    pg.wait_for_timeout(200)
    assert swing in tarjetas()
    # hoja de filtros: "Ninguno" + jazz deja solo el jazz; el botón dice cuántos se verán
    pg.click("#fgen")
    pg.wait_for_selector(".sheet")
    pg.click("[data-rap='ninguno']")
    pg.click("[data-g='jazz y swing']")
    assert pg.inner_text("#sclose") == "Ver 1 concierto"
    pg.click("#sclose")
    pg.wait_for_function("!document.querySelector('.sheet')")
    assert tarjetas() == [swing]
    # "Quitar filtros" vuelve a lo de por defecto
    pg.click("#fquitar")
    pg.wait_for_timeout(200)
    assert swing not in tarjetas() and pg.evaluate("nFiltros()") == 0
    assert not pg.errores, pg.errores


def test_mis_conciertos_y_novedades(web, nav):
    pg = abrir(nav, web + "#todos")
    ficha(pg, "Muse")
    pg.click("#fav")
    assert pg.inner_text("#fav").startswith("★")
    pg.evaluate("state.tab='Mis conciertos'; render()")
    pg.wait_for_selector("#main .card")
    assert pg.evaluate("[...document.querySelectorAll('#main .card')].map(c=>BYID[c.dataset.id].artista)") == ["Muse"]
    pg.reload()  # se guarda en el móvil
    pg.wait_for_function("DATA.length>0")
    assert pg.evaluate("Object.keys(FAV.get())") == [id_de(pg, "Muse")]
    pg.evaluate("state.tab='Novedades'; render()")
    pg.wait_for_selector("#main .todos-h, #main .empty", timeout=15000)
    assert not pg.errores, pg.errores


def test_pagina_de_sala_con_su_calendario(web, nav):
    pg = abrir(nav, web + "#sala/Movistar%20Arena")
    pg.wait_for_selector("#main .card", timeout=15000)
    assert pg.evaluate("[...document.querySelectorAll('#main .card')].map(c=>BYID[c.dataset.id].artista)") == ["Muse"]
    ics = pg.evaluate("fetch('calendario/sala-movistar-arena.ics').then(r=>r.text())")
    assert ics.count("BEGIN:VEVENT") == 1 and "SUMMARY:Muse" in ics
    assert not pg.errores, pg.errores


def test_menu_clave_y_modos_de_vista(web, nav):
    pg = abrir(nav, web + "#todos")
    pg.wait_for_selector(".claves")
    pg.click("#menubtn")
    assert pg.is_visible("#menu [data-go='Salas']") and not pg.is_visible("#menu [data-go='Fuentes']")
    pg.click(".mdatos summary")
    assert pg.is_visible("#menu [data-go='Fuentes']")
    assert not pg.locator("#menu [data-go='Estilos']").count()  # la página de estilos ya no está en el menú
    pg.evaluate("document.getElementById('menu').innerHTML=''")
    for m, cls in (("compacta", "fila"), ("cuadricula", "tile"), ("lista", "card")):
        pg.click(f"[data-modo='{m}']")
        pg.wait_for_timeout(200)
        assert pg.evaluate(f"[...document.querySelectorAll('#main .card')].every(c=>c.classList.contains('{cls}'))")
        assert pg.evaluate("state.modo") == m and pg.evaluate("localStorage.getItem('agenda:modo')") == f'"{m}"'
        assert pg.evaluate("document.documentElement.scrollWidth-innerWidth") <= 1
    assert not pg.errores, pg.errores


def test_ordenador_ficha_al_lado(web, nav):
    pg = abrir(nav, web + "#todos", ordenador=True)
    pg.click(f"#main .card[data-id='{id_de(pg, 'Muse')}']")
    pg.wait_for_selector("#panel .rows", timeout=15000)
    assert pg.evaluate("location.hash").startswith("#todos")  # la lista sigue ahí
    assert pg.evaluate("document.getElementById('panel').getBoundingClientRect().left>="
                       "document.getElementById('main').getBoundingClientRect().right-1")
    assert pg.locator(f"#main .card[data-id='{id_de(pg, 'Muse')}'][aria-current]").count() == 1
    pg.keyboard.press("Escape")
    assert not pg.is_visible("#panel")
    assert not pg.errores, pg.errores


def test_con_el_teclado(web, nav):
    pg = abrir(nav, web + "#todos")
    # modos de vista: botones de verdad (Tab + Enter o espacio)
    pg.focus("[data-modo='compacta']")
    pg.keyboard.press("Enter")
    assert pg.evaluate("state.modo") == "compacta"
    pg.focus("[data-modo='lista']")
    pg.keyboard.press(" ")
    assert pg.evaluate("state.modo") == "lista"
    # menú: se abre con Enter con el foco en la primera opción; Escape lo cierra y devuelve el foco al botón
    pg.focus("#menubtn")
    pg.keyboard.press("Enter")
    assert pg.evaluate("document.activeElement.getAttribute('role')") == "menuitem"
    pg.keyboard.press("Escape")
    assert not pg.inner_html("#menu") and pg.evaluate("document.activeElement.id") == "menubtn"
    # hoja de filtros: Escape la cierra sin aplicar
    pg.focus("#fgen")
    pg.keyboard.press("Enter")
    pg.wait_for_selector(".sheet")
    pg.keyboard.press("Escape")
    pg.wait_for_function("!document.querySelector('.sheet')")
    # una tarjeta se abre con Enter
    pg.focus("#main .card")
    pg.keyboard.press("Enter")
    pg.wait_for_selector("#main .rows", timeout=15000)
    # nada quita el contorno del foco
    sin_contorno = pg.evaluate("[...document.styleSheets].flatMap(s=>[...s.cssRules]).filter(r=>r.selectorText&&"
                               "/:focus/.test(r.selectorText)&&/none|^0/.test(r.style.outline||'')).map(r=>r.selectorText)")
    assert not sin_contorno, sin_contorno
    assert not pg.errores, pg.errores


def test_mas_generos_deja_solo_lo_que_no_es_rock(web, nav):
    pg = abrir(nav, web + f"#semana/{DIA.isoformat()}")
    artistas = lambda: sorted(pg.evaluate("[...document.querySelectorAll('#main .card')].map(c=>BYID[c.dataset.id].artista)"))  # noqa: E731
    pg.click("[data-pre='mas']")
    pg.wait_for_timeout(200)
    assert artistas() == ["Cuarteto Swing de Lavapiés", "Orfeón de Moratalaz"]  # jazz y clásica; ni rock ni sin clasificar
    assert pg.get_attribute("[data-pre='mas']", "aria-pressed") == "true"
    assert "más géneros" in pg.inner_text(".active")
    pg.click("[data-pre='mas']")  # vuelve a lo de por defecto
    pg.wait_for_timeout(200)
    assert "Muse" in artistas() and pg.evaluate("nFiltros()") == 0
    pg.click("#fgen")  # también en la hoja de filtros
    pg.wait_for_selector(".sheet")
    pg.click("[data-rap='mas']")
    assert pg.inner_text("#sclose") == "Ver 2 conciertos"
    assert not pg.errores, pg.errores


def test_periodo_siguiente_y_anterior_desde_la_lista(web, nav):
    pg = abrir(nav, web + f"#dia/{DIA.isoformat()}")
    pasos = lambda: pg.evaluate("[...document.querySelectorAll('#main [data-paso]')].map(b=>b.className.split(' ')[1])")  # noqa: E731
    assert pasos() == ["ant", "sig"]  # el día anterior aún no ha pasado; el siguiente tiene conciertos
    assert "1 concierto" in pg.inner_text(".paso.sig") or "conciertos" in pg.inner_text(".paso.sig")
    pg.click(".paso.sig")
    pg.wait_for_function(f"location.hash==='#dia/{D2.isoformat()}'")
    assert pasos() == ["ant"]  # más allá de lo anunciado no hay botón (no lleva a una lista vacía)
    pg.keyboard.press("ArrowLeft")  # en el ordenador, ← → como ‹ ›
    pg.wait_for_function(f"location.hash==='#dia/{DIA.isoformat()}'")
    pg.focus("#q")
    pg.keyboard.press("ArrowRight")  # escribiendo en el buscador, las flechas son del buscador
    assert pg.evaluate("location.hash") == f"#dia/{DIA.isoformat()}"
    assert not pg.errores, pg.errores


def test_los_filtros_van_en_la_direccion(web, nav):
    pg = abrir(nav, web + f"#semana/{DIA.isoformat()}")
    assert "?" not in pg.evaluate("location.hash")  # por defecto, la dirección limpia
    pg.click("[data-pre='mas']")
    pg.wait_for_function("location.hash.includes('?g=mas')")
    pg.click("#fgen")
    pg.wait_for_selector(".sheet")
    pg.click("[data-o='es']")
    pg.click("#sclose")
    pg.wait_for_function("location.hash.includes('o=es')")
    enlace = pg.evaluate("location.href")
    assert pg.locator("#fcompartir").count() == 1
    # el enlace, abierto en otro navegador (sin nada guardado), enseña lo mismo
    otra = abrir(nav, enlace)
    assert otra.evaluate("modoGrupos(state.grupos)") == "mas" and otra.evaluate("state.origen") == "es"
    vistos = sorted(otra.evaluate("[...document.querySelectorAll('#main .card')].map(c=>BYID[c.dataset.id].artista)"))
    assert vistos == ["Orfeón de Moratalaz"]  # clásica y de España (el jazz de la prueba no tiene origen)
    # y no se guardan: quien abre un enlace conserva sus filtros para la próxima vez
    assert otra.evaluate("localStorage.getItem('agenda:grupos5')") is None
    # una búsqueda también viaja en el enlace
    tercera = abrir(nav, web + f"#semana/{DIA.isoformat()}?g=todos&q=swing")
    assert tercera.evaluate("state.q") == "swing"
    assert tercera.evaluate("[...document.querySelectorAll('#main .card')].map(c=>BYID[c.dataset.id].artista)") == \
        ["Cuarteto Swing de Lavapiés"]
    assert not pg.errores and not otra.errores and not tercera.errores
