"""Funciones de la web (site/index.html) probadas una a una en un navegador sin pantalla, sin datos ni red: origen,
hora de la tarjeta, búsqueda sin tildes, precio, iniciales, fechas (cambio de hora y de año), fotos, preajuste de
géneros, filtro por géneros y estilos, etiquetas y que nada de lo que viene de las webs se cuele como HTML."""
import os
from pathlib import Path

import pytest

sync_api = pytest.importorskip("playwright.sync_api")
WEB = (Path(__file__).resolve().parent.parent / "site" / "index.html").as_uri()


@pytest.fixture(scope="module")
def js():
    with sync_api.sync_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
        try:
            b = p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001
            pytest.skip(f"sin Chromium: {e}")
        pg = b.new_page()
        # solo el propio fichero: los datos no se cargan (la web lo dice) y nada sale a internet
        pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file:") else r.abort())
        errores = []
        pg.on("pageerror", lambda e: errores.append(str(e)))
        pg.goto(WEB)
        pg.wait_for_function("typeof origenDe==='function'")
        yield lambda expr, *a: pg.evaluate(expr, *a)
        assert not errores, errores
        b.close()


def test_origen(js):
    casos = {"ES": {"es"}, "MX": {"lat"}, "GB": {"ext"}}
    for pais, sale in casos.items():
        for o in ("es", "lat", "ext", "nc"):
            assert js(f"origenDe({{nacionalidad:'{pais}'}},'{o}')") == (o in sale), (pais, o)
    assert js("origenDe({nacionalidad_estimada:'ES'},'es')") and not js("origenDe({nacionalidad_estimada:'ES'},'nc')")
    assert js("origenDe({nacionalidad_estimada:'LATAM'},'lat')")
    assert not js("origenDe({nacionalidad_estimada:'ES'},'ext')")  # lo deducido nunca es internacional
    assert js("origenDe({},'nc')") and not js("origenDe({origen_no_aplica:true},'nc')")
    assert js("origenDe({},'todos')")


def test_hora_de_la_tarjeta(js):
    assert js("horaCard({hora:'21:00'})") == "21:00"
    # webs que no coinciden: la de más webs, con interrogación
    assert js("horaCard({conflictos:[{campo:'hora',versiones:[{valor:'20:00',fuentes:['a']},"
              "{valor:'21:30',fuentes:['b','c']}]}]})") == "21:30 ?"
    assert js("horaCard({hora_estimada:{hora:'21:30'}})") == "≈ 21:30"  # la habitual de la sala
    assert js("horaCard({})") == ""


def test_busqueda_sin_tildes_y_en_cualquier_orden(js):
    r = "{artista:'Hällas',sala:'Sala Nazca',municipio:'Madrid',estilos_discogs:['Progressive Rock']}"
    for q in ("hallas", "HÄLLAS", "nazca hallas", "progressive", "madrid"):
        assert js(f"pasaTexto({r},'{q}')"), q
    assert not js(f"pasaTexto({r},'hallas sol')")
    assert js(f"pasaTexto({r},'  ')")  # vacía: todo


def test_textos(js):
    assert js("precioTxt('15,00 EUR')") == "15 €" and js("precioTxt('desde 49,24 €')") == "desde 49,24 €"
    assert js("plural(1,'concierto')") == "1 concierto" and js("plural(3,'concierto')") == "3 conciertos"
    assert js("plural(2,'concierto nuevo','conciertos nuevos')") == "2 conciertos nuevos"
    assert js("iniciales('The Beatles')") == "B" and js("iniciales('Mujeres al borde')") == "MA"
    assert js("iniciales('Los Planetas')") == "P" and js("iniciales('')") == "?"


def test_fechas_con_cambio_de_hora_y_de_año(js):
    assert js("addDays('2026-10-24',1)") == "2026-10-25"  # cambio de hora de octubre
    assert js("addDays('2026-10-25',1)") == "2026-10-26"
    assert js("addDays('2027-03-27',2)") == "2027-03-29"  # cambio de hora de marzo
    assert js("addDays('2026-12-31',1)") == "2027-01-01"
    assert js("mondayOf('2026-10-25')") == "2026-10-19"  # domingo: su lunes es el anterior
    assert js("mondayOf('2027-01-01')") == "2026-12-28"
    assert js("viernesDe('2026-10-19')") == "2026-10-23"
    assert js("addDays('2028-02-28',1)") == "2028-02-29"  # bisiesto


def test_fotos(js):
    wiki = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Muse.jpg/800px-Muse.jpg"
    assert js(f"fotoUrl('{wiki}',100)").endswith("/120px-Muse.jpg")
    assert js(f"fotoUrl('{wiki}',720)").endswith("/500px-Muse.jpg")
    assert js("fotoUrl('https://img.discogs.com/a.jpg',160)") == "https://img.discogs.com/a.jpg"  # tal cual
    otra = js("fotoUrl('https://sala.es/cartel.jpg',160,true)")
    assert otra.startswith("https://wsrv.nl/?url=https%3A%2F%2Fsala.es%2Fcartel.jpg&w=160&h=160")
    assert js("fotoUrl('',160)") == ""


def test_preajuste_y_filtro_de_generos(js):
    assert js("modoGrupos([...DEF_GRUPOS])") == "def"
    assert js("modoGrupos(GRUPOS.map(g=>g.id))") == "todos"
    assert js("modoGrupos(['jazz y swing'])") == "custom"
    js("state.grupos=['jazz y swing']; state.estilos={}; state.genericos=true")
    assert js("pasaGrupo({grupos:['jazz y swing']})") and not js("pasaGrupo({grupos:['rock y metal']})")
    # un telonero de jazz hace que el concierto salga en jazz
    assert js("pasaGrupo({grupos:['rock y metal'],grupos_cartel:{'jazz y swing':['Telonero']}})")
    js("state.genericos=false")  # sin las etiquetas genéricas de la agenda
    assert not js("pasaGrupo({grupos:['jazz y swing'],grupos_generico:true})")
    js("state.grupos=[...DEF_GRUPOS]; state.genericos=true")


def test_etiquetas_de_estilo(js):
    assert js("estiloTags({estilos_discogs:['Indie Rock','Post-Punk','Shoegaze']},2)") == \
        '<span class="tag">Indie Rock</span><span class="tag">Post-Punk</span>'
    gen = js("estiloTags({estilo_fuente:[{estilo:'Pop / Rock'}],grupos_generico:true,grupos:['pop e indie']},2)")
    assert 'class="tag ag"' in gen and "genérico" in gen


def test_nada_de_las_webs_se_cuela_como_html(js):
    malo = "<img src=x onerror=alert(1)>"
    assert js(f"esc({malo!r})") == "&lt;img src=x onerror=alert(1)&gt;"
    html = js(f"card({{id:'x1',artista:{malo!r},sala:{malo!r},municipio:'Getafe',fecha:'2026-10-12',"
              f"invitados:[{malo!r}],estilos_discogs:[{malo!r}]}})")
    assert "<img src=x" not in html and html.count("&lt;img src=x") >= 3


def test_el_carrusel_de_fotos_se_alcanza_con_el_teclado(js):
    # con foto y cartel de la gira, la ficha se desliza de lado: tiene que poder enfocarse (axe: scrollable-region)
    html = js("(()=>{BYID['k1']={id:'k1',artista:'Muse',fecha:'2026-10-12',sala:'La Riviera',img:'https://x/a.jpg',"
              "gira:{imagen:'https://x/b.jpg',credito:'x'},_full:true,estado:'1_fuente',"
              "fuentes:[{id:'riviera',nombre:'La Riviera (web oficial)',url:'https://x/'}]};state.id='k1';return viewConcierto()})()")
    assert 'id="carr" role="region" tabindex="0"' in html


def test_la_hora_descartada_sigue_a_la_vista_en_la_ficha(js):
    html = js("(()=>{BYID['h1']={id:'h1',artista:'Lera Lynn',fecha:'2026-10-12',sala:'Café Berlín',hora:'20:00',_full:true,"
              "estado:'contrastado',fuentes:[{id:'cc',nombre:'conciertos.club',url:'https://x/'}],"
              "hora_descartada:[{valor:'21:00',fuentes:['Songkick Madrid'],motivo:'Songkick Madrid coincide con la web de "
              "la sala en el 40 % de los conciertos'}]};state.id='h1';return viewConcierto()})()")
    assert "Songkick Madrid dice 21:00: Songkick Madrid coincide con la web de la sala en el 40 % de los conciertos" in html


def test_enlaces_seguros(js):
    """Un enlace leído de una web ajena nunca puede ejecutar código al pulsarlo: solo pasan http(s), webcal,
    mailto y las rutas de la propia web."""
    for malo in ("javascript:alert(1)", " JavaScript:alert(1)", "java\tscript:alert(1)", "\u0001javascript:x",
                 "data:text/html,<script>alert(1)</script>", "vbscript:x", "file:///etc/passwd"):
        assert js("u=>urlSegura(u)", malo) == "#", malo
    for bueno in ("https://sala.es/e?a=1&b=2", "http://x.es", "webcal://x/y.ics", "mailto:a@b.es", "#concierto/7",
                  "data/salas.json", "/agenda"):
        assert js("u=>urlSegura(u)", bueno) == bueno, bueno
    assert js("hr('javascript:alert(\"x\")')") == "#"
    assert js("hr('https://x.es/?a=1&b=\"2\"')") == "https://x.es/?a=1&amp;b=&quot;2&quot;"


def test_politica_de_contenido():
    """La política de seguridad del contenido está y no deja cargar scripts ni conectarse fuera de la web."""
    html = Path(WEB.removeprefix("file://")).read_text(encoding="utf-8")
    import re
    m = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', html)
    assert m
    reglas = dict((p.split()[0], p.split()[1:]) for p in m.group(1).split(";") if p.strip())
    assert reglas["default-src"] == ["'self'"] and reglas["connect-src"] == ["'self'"]
    assert reglas["script-src"] == ["'self'", "'unsafe-inline'"]
    assert reglas["object-src"] == ["'none'"] and reglas["base-uri"] == ["'none'"]
