"""Validación automática de la web publicada: en vivo, con un navegador real, sin que nadie pruebe nada a mano.

Recorre https://estebancobo-dot.github.io/agenda-conciertos/ como lo haría una persona con un móvil de gama
media-baja (Chromium, pantalla de iPhone, 4G lenta, CPU 6 veces más lenta) y comprueba, con umbrales fijos:

  Publicación   la web servida es exactamente el código de `main`; datos recientes, completos y coherentes
                (agenda ligera, detalle por días, miniaturas propias, todo por https)
  Funcional     semana, búsqueda, filtros, ficha, enlaces directos, vista mes e informe enseñan lo que dicen
                los datos (lo que se ve se compara con los propios datos de la página)
  UX            volver deja la lista donde estaba, una sola foto en la ficha, búsqueda y filtros claros, el día
                elegido en el mes se ve, sin scroll lateral en móvil pequeño ni en ordenador, modo oscuro,
                saltos de diseño (CLS), accesibilidad (axe-core) y tamaño de los botones
  Rendimiento   primera y segunda visita, LCP, miniaturas al bajar despacio y deprisa, cambiar de semana,
                abrir fichas (con la foto ya descargada y sin ella), filtros, bloqueos de JavaScript, bytes
  Fallos        sin conexión (copia del service worker), detalle que no llega, fotos que no cargan, agenda
                que no llega o tarda, taxonomía rota: la página avisa y sigue funcionando; 0 errores de JS
  Otros         imágenes de las agendas a través del proxy, enlaces a las fuentes

Cada comprobación queda como ok / aviso / fallo con su valor y su umbral. Salida: SALIDA/resultados.json,
SALIDA/informe.md y capturas. Termina con código 1 si hay algún fallo.

Uso: python tools/validar_web.py [URL] [SALIDA]
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import statistics
import sys
import time
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
URL = sys.argv[1] if len(sys.argv) > 1 else "https://estebancobo-dot.github.io/agenda-conciertos/"
URL = URL if URL.endswith("/") else URL + "/"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "pruebas")
OUT.mkdir(parents=True, exist_ok=True)
R: dict = {"url": URL, "fecha": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "comprobaciones": [],
           "medidas": {}, "errores_js": [], "consola": []}
CATEGORIAS = ["Publicación", "Funcional", "UX", "Rendimiento", "Fallos", "Otros"]

# 4G lenta (la de Lighthouse para móvil) y CPU 6 veces más lenta: un móvil de gama media-baja
RED = {"offline": False, "latency": 150, "downloadThroughput": 1.6 * 1024 * 1024 / 8,
       "uploadThroughput": 750 * 1024 / 8}
INICIO = """
window.__lt=[]; window.__cls=0; window.__lcp=0;
try{new PerformanceObserver(l=>l.getEntries().forEach(e=>window.__lt.push([Math.round(e.startTime),Math.round(e.duration)]))).observe({type:'longtask',buffered:true});}catch(e){}
window.__clsSrc=[];
try{new PerformanceObserver(l=>l.getEntries().forEach(e=>{if(e.hadRecentInput) return; window.__cls+=e.value;
  window.__clsSrc.push(e.value.toFixed(3)+' a los '+Math.round(e.startTime)+' ms: '+(e.sources||[]).map(s=>{const n=s.node;
    return !n?'?':n.nodeType!==1?'texto':(n.id?'#'+n.id:n.tagName.toLowerCase()+(n.className&&typeof n.className==='string'?'.'+n.className.split(' ')[0]:''));}).join(', '));
})).observe({type:'layout-shift',buffered:true});}catch(e){}
try{new PerformanceObserver(l=>{const e=l.getEntries(); if(e.length) window.__lcp=Math.round(e[e.length-1].startTime);}).observe({type:'largest-contentful-paint',buffered:true});}catch(e){}
"""
FOTO_LISTA = "(()=>{const i=document.querySelector('.hero img');return !i||(i.complete&&i.naturalWidth>0)})()"


# ---------------------------------------------------------------------------------------------- comprobaciones
def check(cat: str, nombre: str, valor=None, *, ok: bool | None = None, aviso=None, fallo=None, grave=True,
          detalle: str = "", unidad: str = "ms"):
    """Anota una comprobación. Con `ok` es sí/no (si no se cumple: fallo, o aviso si grave=False). Con umbrales
    numéricos: por encima de `fallo` es fallo, por encima de `aviso` es aviso."""
    if ok is not None:
        estado = "ok" if ok else ("fallo" if grave else "aviso")
        umbral = ""
    elif valor is None or isinstance(valor, str):
        estado, umbral = ("fallo" if grave else "aviso"), ""
    else:
        estado = "fallo" if fallo is not None and valor > fallo else "aviso" if aviso is not None and valor > aviso else "ok"
        umbral = " / ".join(x for x in (f"aviso > {aviso} {unidad}" if aviso is not None else "",
                                         f"fallo > {fallo} {unidad}" if fallo is not None else "") if x)
    R["comprobaciones"].append({"categoria": cat, "nombre": nombre, "estado": estado, "valor": valor,
                                "umbral": umbral, "detalle": detalle})
    print(f"[{estado:5}] {cat} · {nombre}: {json.dumps(valor, ensure_ascii=False)[:160]} {detalle[:160]}", flush=True)
    return estado == "ok"


def medida(nombre: str, **datos):
    R["medidas"][nombre] = datos


def escenario(cat: str, nombre: str):
    """Decorador: si un escenario se interrumpe, queda como fallo con el motivo y los demás siguen."""
    def dec(f):
        def run(*a, **k):
            try:
                return f(*a, **k)
            except Exception as e:  # noqa: BLE001
                check(cat, f"{nombre}: el escenario terminó", ok=False,
                      detalle=f"{type(e).__name__}: {str(e)[:300]}")
                traceback.print_exc()
        return run
    return dec


def ms(t0: float) -> int:
    return round((time.monotonic() - t0) * 1000)


def mediana(v):
    v = [x for x in v if isinstance(x, (int, float))]
    return round(statistics.median(v)) if v else None


# ---------------------------------------------------------------------------------------------- navegador
def contexto(b, *, movil=True, ancho=390, alto=844, sw="allow", oscuro=False):
    ctx = b.new_context(viewport={"width": ancho, "height": alto}, device_scale_factor=3 if movil else 1,
                        is_mobile=movil, has_touch=movil, locale="es-ES", timezone_id="Europe/Madrid",
                        color_scheme="dark" if oscuro else "light", service_workers=sw,
                        user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
                                    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1 AgendaValidacion")
                        if movil else None)
    ctx.add_init_script(INICIO)
    return ctx


def pagina(ctx, lenta=True):
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: R["errores_js"].append(f"{pg.url[-60:]}: {str(e)[:300]}"))
    pg.on("console", lambda m: m.type == "error" and R["consola"].append(m.text[:200]))
    if lenta:
        cdp = ctx.new_cdp_session(pg)
        cdp.send("Network.enable")
        cdp.send("Network.emulateNetworkConditions", RED)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 6})
    return pg


def esperar_datos(pg, timeout=90000):
    pg.wait_for_function("document.getElementById('upd') && /conciertos/.test(document.getElementById('upd').textContent)",
                         timeout=timeout)


def miniaturas(pg) -> dict:
    return pg.evaluate("""()=>{const v=[...document.querySelectorAll('img.thumb')].filter(i=>{const b=i.getBoundingClientRect();return b.bottom>0&&b.top<innerHeight});
      return {visibles:v.length,cargadas:v.filter(i=>i.complete&&i.naturalWidth>1).length}}""")


def esperar_miniaturas(pg, limite_ms=10000):
    t0 = time.monotonic()
    while ms(t0) < limite_ms:
        m = miniaturas(pg)
        if m["visibles"] == m["cargadas"]:
            return ms(t0)
        pg.wait_for_timeout(100)
    return None


def ficha_con_foto(pg, t0, limite=20000):
    try:
        pg.wait_for_function(FOTO_LISTA, timeout=limite)
        return ms(t0)
    except Exception:  # noqa: BLE001
        return None


def bajar_hasta_el_final(pg):
    """Baja la lista entera, de pantalla en pantalla, para que se pinten todos los días."""
    for _ in range(200):
        antes = pg.evaluate("scrollY")
        pg.mouse.wheel(0, 1500)
        pg.wait_for_timeout(120)
        if pg.evaluate("scrollY") == antes and not pg.evaluate("document.querySelectorAll('[data-dif]').length"):
            break
    pg.wait_for_timeout(300)


def lunes_de(d: date) -> date:
    return d - timedelta(days=d.weekday())


# ---------------------------------------------------------------------------------------------- 1. publicación
@escenario("Publicación", "Publicación y datos")
def publicacion(b):
    ctx = b.new_context()
    rq = ctx.request
    for nombre in ("index.html", "sw.js"):
        x = rq.get(URL + (nombre if nombre != "index.html" else "") + f"?v={random.randint(0, 1 << 30)}")
        local = (RAIZ / "site" / nombre).read_bytes()
        igual = x.ok and hashlib.sha256(x.body()).hexdigest() == hashlib.sha256(local).hexdigest()
        check("Publicación", f"{nombre} publicado = el de main", ok=igual,
              detalle="" if igual else f"HTTP {x.status}: la web publicada no es la última versión del código")
    version = re.search(r'__version__ = "([^"]+)"', (RAIZ / "scraper" / "__init__.py").read_text()).group(1)
    R["version_main"] = version

    ag = rq.get(URL + "data/agenda.json").json()
    datos = ag.get("conciertos") or []
    gen = datetime.fromisoformat(ag["generado"].replace("Z", "+00:00"))
    horas = round((datetime.now(timezone.utc) - gen).total_seconds() / 3600, 1)
    check("Publicación", "Datos de la agenda recientes", horas, aviso=26, fallo=50, unidad="h")
    hoy = date.today().isoformat()
    futuros = [r for r in datos if r.get("fecha", "") >= hoy]
    check("Publicación", "Conciertos próximos publicados", len(futuros), ok=len(futuros) >= 500,
          detalle="mínimo 500")
    ids = [r.get("id") for r in datos]
    check("Publicación", "Ids únicos", len(ids) - len(set(ids)), ok=len(ids) == len(set(ids)))
    malos = [r.get("id") for r in datos if not (r.get("id") and r.get("artista")
                                                 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", r.get("fecha") or ""))]
    check("Publicación", "Cada concierto con id, fecha y artista", len(malos), ok=not malos,
          detalle=", ".join(map(str, malos[:5])))
    # sin sala puede ser correcto (la agenda no la dice y no se inventa), pero al menos debe saberse el municipio
    sin_lugar = [f"{r.get('artista', '')[:30]} ({r.get('fecha')})" for r in futuros if not r.get("sala") and not r.get("municipio")]
    sin_sala = [r for r in futuros if not r.get("sala")]
    check("Publicación", "Conciertos sin sala ni municipio", len(sin_lugar), ok=not sin_lugar, detalle=", ".join(sin_lugar[:4]))
    check("Publicación", "Conciertos sin sala (la agenda no la dice)", len(sin_sala), ok=len(sin_sala) <= 20, grave=False,
          detalle=", ".join(f"{r.get('artista', '')[:30]} ({r.get('municipio')})" for r in sin_sala[:4]))
    no_https = [u for r in datos for u in (r.get("img"),) if u and not u.startswith("https://")]
    check("Publicación", "Imágenes solo por https", len(no_https), ok=not no_https, detalle=", ".join(no_https[:3]))

    # detalle por días: existe y trae todos los conciertos de ese día, con el mismo artista
    por_dia: dict = {}
    for r in futuros:
        por_dia.setdefault(r["fecha"], []).append(r)
    dias = sorted(por_dia)[:3] + random.sample(sorted(por_dia)[3:], min(4, max(0, len(por_dia) - 3)))
    faltan, distintos, sin_fichero = [], [], []
    fuentes = []
    for f in dias:
        x = rq.get(URL + "data/" + ag.get("detalles", "detalles/{fecha}.json").replace("{fecha}", f))
        if not x.ok:
            sin_fichero.append(f"{f} (HTTP {x.status})")
            continue
        det = x.json()
        for r in por_dia[f]:
            d = det.get(r["id"])
            if not d:
                faltan.append(r["id"])
            elif d.get("artista") != r.get("artista"):
                distintos.append(r["id"])
            else:
                fuentes += [e.get("url") for e in d.get("fuentes") or [] if e.get("url")]
    check("Publicación", "Fichero de detalle de cada día", len(sin_fichero), ok=not sin_fichero,
          detalle=", ".join(sin_fichero))
    check("Publicación", "El detalle trae todos los conciertos del día", len(faltan), ok=not faltan,
          detalle=", ".join(faltan[:5]))
    check("Publicación", "Detalle y agenda coinciden", len(distintos), ok=not distintos, detalle=", ".join(distintos[:5]))

    # miniaturas y fotos propias
    propias = [u for r in futuros for u in (r.get("mini"), r.get("foto")) if u]
    malas = []
    for u in random.sample(propias, min(12, len(propias))):
        x = rq.get(URL + u)
        if not (x.ok and (x.headers.get("content-type") or "").startswith("image/")):
            malas.append(f"{u} (HTTP {x.status})")
    check("Publicación", "Miniaturas y fotos propias servidas", len(malas), ok=not malas, detalle=", ".join(malas[:3]))
    n = max(1, len(futuros))
    sin_origen = sum(1 for r in futuros if not r.get("nacionalidad") and not r.get("nacionalidad_estimada")
                     and not r.get("origen_no_aplica"))
    estimados = sum(1 for r in futuros if not r.get("nacionalidad") and r.get("nacionalidad_estimada"))
    check("Publicación", "Conciertos próximos sin origen del artista (ni confirmado ni estimado)",
          round(100 * sin_origen / n, 1), aviso=30, fallo=50, unidad="%",
          detalle=f"{sin_origen} de {len(futuros)}; además {estimados} estimados por el nombre")
    # catálogo: que casi todo tenga un género propio y un estilo
    otros = sum(1 for r in futuros if "fuera de foco" in (r.get("grupos") or []))
    check("Publicación", "Conciertos en 'Otros' (sin género propio)", round(100 * otros / n, 1), aviso=3, fallo=10,
          unidad="%", detalle=f"{otros} de {len(futuros)}")
    sin_clas = sum(1 for r in futuros if "sin clasificar" in (r.get("grupos") or []))
    check("Publicación", "Conciertos sin clasificar", round(100 * sin_clas / n, 1), aviso=5, fallo=15, unidad="%",
          detalle=f"{sin_clas} de {len(futuros)}")
    genericos = sum(1 for r in futuros if r.get("grupos_generico"))
    check("Publicación", "Conciertos con etiqueta genérica (\"Pop / Rock\", \"Músicas negras\")",
          round(100 * genericos / n, 1), aviso=8, fallo=25, unidad="%", detalle=f"{genericos} de {len(futuros)}")
    sin_estilo = sum(1 for r in futuros if not r.get("estilos_discogs") and not r.get("origen_no_aplica"))
    check("Publicación", "Conciertos sin ningún estilo", round(100 * sin_estilo / n, 1), aviso=30, fallo=60, unidad="%",
          detalle=f"{sin_estilo} de {len(futuros)}")
    # las fotos que no son propias pasan por wsrv.nl, que tarda 1-3 s con las que nadie ha pedido antes
    con_img = [r for r in futuros if r.get("img")]
    for campo, nombre_c in (("mini", "miniatura"), ("foto", "foto de ficha")):
        pct = round(100 * sum(1 for r in con_img if r.get(campo)) / max(1, len(con_img)), 1)
        check("Rendimiento", f"Conciertos con {nombre_c} propia (servida desde la web)", pct, ok=pct >= 97,
              detalle=f"de {len(con_img)} con imagen; mínimo 97 %", unidad="%")

    try:
        inf = rq.get(URL + "data/informe.json").json()
        uc = inf.get("ultima_completa") or {}
        uc = uc.get("generado") if isinstance(uc, dict) else uc
        if uc:
            h = round((datetime.now(timezone.utc) - datetime.fromisoformat(uc.replace("Z", "+00:00"))).total_seconds() / 3600, 1)
            check("Publicación", "Última lectura completa de las agendas", h, aviso=27, fallo=50, unidad="h")
        check("Publicación", "Fuentes sin alertas", len(inf.get("alertas") or []), ok=not inf.get("alertas"),
              grave=False, detalle="; ".join((inf.get("alertas") or [])[:3]))
    except Exception as e:  # noqa: BLE001
        check("Publicación", "informe.json legible", ok=False, detalle=str(e)[:200])

    # enlaces a las fuentes (muchas webs bloquean robots: solo aviso)
    rotos = []
    for u in random.sample(sorted(set(fuentes)), min(12, len(set(fuentes)))):
        try:
            x = rq.get(u, timeout=20000, max_redirects=5)
            if x.status in (404, 410) or x.status >= 500:
                rotos.append(f"{u[:90]} ({x.status})")
        except Exception as e:  # noqa: BLE001
            rotos.append(f"{u[:90]} ({type(e).__name__})")
    check("Otros", "Enlaces a las fuentes responden", len(rotos), ok=len(rotos) <= 1, grave=False,
          detalle="; ".join(rotos[:4]))
    ctx.close()
    return datos


# ---------------------------------------------------------------------------------------------- 2. recorrido
@escenario("Funcional", "Recorrido en móvil")
def recorrido(b):
    ctx = contexto(b)
    pg = pagina(ctx)
    imgs, fallidas = [], []
    pg.on("requestfinished", lambda q: q.resource_type == "image" and not q.url.startswith("data:") and imgs.append(
        {"url": q.url[:140], "ms": round(q.timing["responseEnd"]) if q.timing else None}))
    pg.on("response", lambda x: x.request.resource_type == "image" and x.status >= 400 and fallidas.append(
        f"{x.status} {x.url[:120]}"))
    pg.on("requestfailed", lambda q: q.resource_type == "image" and fallidas.append(f"{q.failure} {q.url[:120]}"))
    no_https = []
    pg.on("request", lambda q: q.url.startswith("http://") and not q.url.startswith("http://localhost")
          and no_https.append(q.url[:120]))

    # primera visita
    t0 = time.monotonic()
    pg.goto(URL, wait_until="commit")
    esperar_datos(pg)
    primera = ms(t0)
    pg.wait_for_load_state("networkidle", timeout=90000)
    check("Rendimiento", "Primera visita: datos y lista pintados", primera, aviso=5000, fallo=8000)
    check("Rendimiento", "Primera visita: LCP", pg.evaluate("window.__lcp") or None, aviso=4000, fallo=6000)
    kb = round(pg.evaluate("performance.getEntriesByType('resource').reduce((a,e)=>a+(e.transferSize||0),0)") / 1024)
    check("Rendimiento", "Primera visita: KB descargados", kb, aviso=1500, fallo=3000, unidad="KB")
    pg.screenshot(path=str(OUT / "1_inicio.png"))
    check("Funcional", "La cabecera dice cuántos conciertos hay y cuándo se actualizó",
          pg.inner_text("#upd"), ok=bool(re.search(r"\d+ conciertos · actualizado", pg.inner_text("#upd"))))

    # semana: lo que se ve es lo que dicen los datos
    lunes = lunes_de(date.today())
    t0 = time.monotonic()
    pg.evaluate(f"location.hash='#semana/{lunes.isoformat()}'")
    pg.wait_for_selector(".card", timeout=30000)
    medida("semana_pintar", ms=ms(t0))
    bajar_hasta_el_final(pg)  # que se pinten todos los días
    sem = pg.evaluate("""(l)=>{const fin=new Date(new Date(l).getTime()+6*864e5).toISOString().slice(0,10);
       const ids=[...document.querySelectorAll('#main .card')].map(c=>c.dataset.id);
       const esperados=DATA.filter(r=>r.fecha>=l&&r.fecha<=fin&&visible(r)).map(r=>r.id);
       const fechas=ids.map(i=>(BYID[i]||{}).fecha);
       return {vistos:ids.length, esperados:esperados.length,
               fuera:fechas.filter(f=>!f||f<l||f>fin).length,
               desordenados:fechas.filter((f,i)=>i&&f<fechas[i-1]).length,
               faltan:esperados.filter(i=>!ids.includes(i)).slice(0,5), sobran:ids.filter(i=>!esperados.includes(i)).slice(0,5),
               pendientes:document.querySelectorAll('[data-dif]').length}}""", lunes.isoformat())
    check("Funcional", "Semana: salen justo los conciertos de los datos (con los filtros puestos)",
          f"{sem['vistos']} de {sem['esperados']}", ok=sem["vistos"] == sem["esperados"] and not sem["faltan"],
          detalle=f"faltan {sem['faltan']} sobran {sem['sobran']} días sin pintar {sem['pendientes']}")
    check("Funcional", "Semana: todos de esa semana y en orden de fecha", sem["fuera"] + sem["desordenados"],
          ok=sem["fuera"] == 0 and sem["desordenados"] == 0)

    # bajar despacio (con pausas) y deprisa (sin pausas)
    pg.evaluate("scrollTo(0,0)")
    pg.wait_for_timeout(800)
    faltan = []
    for _ in range(0, pg.evaluate("document.body.scrollHeight"), 700):
        pg.mouse.wheel(0, 700)
        pg.wait_for_timeout(400)
        m = miniaturas(pg)
        faltan.append(m["visibles"] - m["cargadas"])
    medida("scroll_despacio", sin_cargar_por_pantalla=faltan)
    check("Rendimiento", "Bajar despacio: miniaturas sin cargar a los 0,4 s (peor pantalla)", max(faltan or [0]),
          aviso=1, fallo=3, unidad="miniaturas")
    pg.evaluate("scrollTo(0,0)")
    pg.wait_for_timeout(300)
    for _ in range(25):
        pg.mouse.wheel(0, 900)
        pg.wait_for_timeout(120)
    check("Rendimiento", "Bajar deprisa: al parar, miniaturas visibles cargadas en", esperar_miniaturas(pg),
          aviso=1500, fallo=3000)

    # semana siguiente
    t = []
    for _ in range(3):
        pg.evaluate("scrollTo(0,0)")
        t0 = time.monotonic()
        pg.click("[data-nav='7']")
        pg.wait_for_function("document.querySelectorAll('.card').length>0", timeout=30000)
        t.append(ms(t0))
        pg.wait_for_timeout(800)
    check("Rendimiento", "Cambiar de semana (mediana de 3)", mediana(t), aviso=700, fallo=1500)

    # ficha y volver: se queda donde estabas (con el atrás del móvil y con "‹ Volver")
    for modo in ("atrás del navegador", "botón ‹ Volver"):
        pg.evaluate(f"location.hash='#semana/{lunes.isoformat()}'")
        pg.wait_for_selector(".card")
        pg.wait_for_timeout(600)
        cards = pg.locator("#main .card")
        n = min(12 if modo.startswith("atrás") else 20, cards.count() - 1)
        cards.nth(n).scroll_into_view_if_needed()
        pg.wait_for_timeout(1200)
        cid = cards.nth(n).get_attribute("data-id")
        t0 = time.monotonic()
        cards.nth(n).click()
        pg.wait_for_selector(".dt h2", timeout=30000)
        datos_ms = ms(t0)
        if modo.startswith("atrás"):
            check("Rendimiento", "Abrir ficha desde la lista (datos)", datos_ms, aviso=500, fallo=1500)
            fin = pg.wait_for_function("!document.getElementById('cargando')", timeout=15000) and ms(t0)
            check("Rendimiento", "Ficha completa (fuentes y precio)", fin, aviso=1500, fallo=4000)
            ficha_funcional(pg, cid)
            pg.evaluate("history.back()")
        else:
            pg.click("a.back")
        pg.wait_for_selector("#main .card")
        pg.wait_for_timeout(700)
        se_ve = pg.evaluate("""(a)=>{const c=document.querySelector(`.card[data-id="${a}"]`);
           if(!c) return false; const b=c.getBoundingClientRect(); return b.top>-10&&b.top<innerHeight-40}""", cid)
        check("UX", f"Volver ({modo}) deja la lista en el concierto que abriste", ok=se_ve)

    # uso normal: bajas, te paras a leer 2 s y abres uno con foto que estás viendo; la foto ya debe estar
    pg.evaluate(f"location.hash='#semana/{lunes.isoformat()}'")
    pg.wait_for_selector(".card")
    pg.evaluate("scrollTo(0,0)")
    fotos, ya = [], []
    for _ in range(5):
        pg.mouse.wheel(0, 1200)
        pg.wait_for_timeout(2000)
        cid = pg.evaluate("""()=>{for(const c of document.querySelectorAll('#main .card')){const b=c.getBoundingClientRect();
            const r=BYID[c.dataset.id]; if(b.top>60&&b.bottom<innerHeight&&r&&r.img) return c.dataset.id;} return null}""")
        if not cid:
            continue
        t0 = time.monotonic()
        pg.locator(f'.card[data-id="{cid}"]').first.click()
        pg.wait_for_selector(".dt h2", timeout=30000)
        ya.append(pg.evaluate("(()=>{const i=document.querySelector('.hero img');return !!i&&i.complete&&i.naturalWidth>0})()"))
        fotos.append(ficha_con_foto(pg, t0))
        n_img = pg.evaluate("document.querySelectorAll('.hero img').length")
        if len(fotos) == 1:
            pg.screenshot(path=str(OUT / "3_ficha.png"))
            check("UX", "Ficha con una sola foto (sin miniatura provisional encima)", n_img, ok=n_img <= 1)
        pg.go_back()
        pg.wait_for_selector("#main .card")
        pg.wait_for_timeout(400)
    medida("ficha_tras_ver_la_lista", fotos_ms=fotos, ya_descargada=ya)
    check("Rendimiento", "Foto de la ficha tras ver la lista 2 s (mediana)", mediana(fotos), aviso=600, fallo=1500)
    check("Rendimiento", "Fichas cuya foto ya estaba descargada al abrir", sum(ya), ok=sum(ya) >= len(ya) * 0.6,
          grave=False, detalle=f"{sum(ya)} de {len(ya)}")

    # fichas lejanas (sin nada descargado antes), una de cada origen de foto
    casos = pg.evaluate("""()=>{const hoy=HOY; const out={};
      const tipo=u=>!u?'sin foto':/discogs/.test(u)?'discogs':/conciertos\\.club/.test(u)?'conciertos.club':/wikimedia/.test(u)?'wikimedia':/madridenvivo/.test(u)?'madridenvivo':'otros';
      for(const r of DATA.filter(r=>r.fecha>hoy).reverse()){const t=tipo(r.img); if(!out[t]) out[t]=r.id;} return out}""")
    lejanas = {}
    for t, cid in casos.items():
        t0 = time.monotonic()
        pg.evaluate(f"location.hash='#concierto/{cid}'")
        pg.wait_for_selector(".dt h2", timeout=30000)
        d = ms(t0)
        f = ficha_con_foto(pg, t0) if t != "sin foto" else None
        lejanas[t] = {"datos_ms": d, "foto_ms": f}
        check("Rendimiento", f"Ficha lejana ({t}): datos", d, aviso=800, fallo=2000)
        if t != "sin foto":
            check("Rendimiento", f"Ficha lejana ({t}): foto", f, aviso=3000, fallo=8000, grave=False)
    medida("fichas_lejanas", **lejanas)

    filtros(pg, lunes)
    estilos(pg, lunes)
    busqueda(pg, lunes)
    # filtros de origen: España confirmados, Latinoamérica, resto del mundo, estimados, sin confirmar y "no aplica"
    # reparten todos los conciertos sin dejar ninguno fuera ni contar ninguno dos veces
    o = pg.evaluate("""()=>{const f=DATA.filter(r=>r.fecha>=HOY); const c=k=>f.filter(r=>origenDe(r,k)).length;
        const est=f.filter(r=>!r.nacionalidad&&r.nacionalidad_estimada==='ES').length;
        const na=f.filter(r=>!r.nacionalidad&&!r.nacionalidad_estimada&&r.origen_no_aplica).length;
        return {total:f.length, esc:c('esc'), es:c('es'), lat:c('lat'), ext:c('ext'), nc:c('nc'), est, na}}""")
    suma = o["esc"] + o["lat"] + o["ext"] + o["est"] + o["nc"] + o["na"]
    check("Funcional", "Filtros de origen: España, Latinoamérica, resto del mundo y sin confirmar cuadran",
          f"{suma} de {o['total']}", ok=suma == o["total"] and o["es"] == o["esc"] + o["est"], detalle=str(o))
    mes(pg)
    entradas_ficha(pg)
    cabeceras_fijas(pg, lunes)
    accesos_al_bajar(pg, lunes)
    cambiar_fecha_bajado(pg, lunes)
    cartel_web(pg)
    pagina_fuentes(pg)

    # informe
    pg.evaluate("location.hash='#informe'")
    pg.wait_for_timeout(1500)
    txt = pg.inner_text("#main")
    check("Funcional", "Informe se abre", ok="Rendimiento en este móvil" in txt and "Conciertos por grupo" in txt)

    # segunda visita (caché del navegador y del service worker). Antes se iba a la misma dirección en la que ya estaba
    # y el navegador no recargaba nada: los saltos de diseño (CLS) eran los de todo el recorrido, con sus scrolls
    # forzados, y crecían con cada comprobación nueva. Pasando por una página en blanco es una visita de verdad.
    pg.goto("about:blank")
    t0 = time.monotonic()
    pg.goto(URL + "#semana/" + lunes.isoformat(), wait_until="commit")
    pg.wait_for_selector(".card", timeout=60000)
    check("Rendimiento", "Segunda visita: lista pintada", ms(t0), aviso=1500, fallo=3000)
    check("Rendimiento", "Segunda visita: miniaturas visibles cargadas", esperar_miniaturas(pg), aviso=800, fallo=2500)

    lt = pg.evaluate("window.__lt||[]")
    peor = max((d for _, d in lt), default=0)
    medida("bloqueos_js", n=len(lt), total_ms=sum(d for _, d in lt), peores=sorted(lt, key=lambda x: -x[1])[:8])
    check("Rendimiento", "Bloqueo de JavaScript más largo (CPU 6x)", peor, aviso=300, fallo=1000)
    check("UX", "Saltos de diseño (CLS)", round(pg.evaluate("window.__cls"), 3), aviso=0.1, fallo=0.25, unidad="",
          detalle=" | ".join(pg.evaluate("window.__clsSrc||[]")[:6]))
    dur = [i["ms"] for i in imgs if isinstance(i.get("ms"), (int, float)) and i["ms"] > 0]
    medida("imagenes", pedidas=len(imgs), mediana_ms=mediana(dur), hosts=sorted({i["url"].split("/")[2] for i in imgs}),
           fallidas=fallidas[:20])
    tasa = round(100 * len(fallidas) / max(1, len(imgs) + len(fallidas)), 1)
    check("Rendimiento", "Imágenes que no cargan", tasa, aviso=1, fallo=5, unidad="%", detalle="; ".join(fallidas[:3]))
    check("Otros", "Todo por https (sin contenido mixto)", len(no_https), ok=not no_https, detalle="; ".join(no_https[:3]))
    try:
        medida("rum_en_el_dispositivo", **pg.evaluate("resumenRum()"))
    except Exception:  # noqa: BLE001
        pass
    ctx.close()


def ficha_funcional(pg, cid):
    """Lo que enseña la ficha es lo que dicen los datos del concierto."""
    f = pg.evaluate("""(id)=>{const r=BYID[id]; const t=document.querySelector('#main').innerText;
       const links=[...document.querySelectorAll('#main a[href^="http"]')].map(a=>a.href);
       return {artista:document.querySelector('.dt h2').innerText.trim(), esperado:r.artista, sala:r.sala,
               tiene_sala:t.includes(r.sala), fuentes:(r.fuentes||[]).length, enlaces:links.length,
               enlaces_fuente:(r.fuentes||[]).filter(f=>f.url&&links.includes(new URL(f.url,location.href).href)).length,
               cargando:t.includes('Cargando')}}""", cid)
    check("Funcional", "Ficha: artista y sala de los datos", f["artista"],
          ok=f["artista"].lower() == (f["esperado"] or "").lower() and f["tiene_sala"],
          detalle=f"esperado {f['esperado']!r} en {f['sala']!r}")
    check("Funcional", "Ficha: enlaza a sus fuentes", f"{f['enlaces_fuente']} de {f['fuentes']}",
          ok=f["fuentes"] > 0 and f["enlaces_fuente"] == f["fuentes"])
    check("UX", "Ficha: no se queda en 'Cargando…'", ok=not f["cargando"])


def entradas_ficha(pg):
    """Página de entradas (scraper/entradas.py): un concierto con enlace de compra lo enseña como botón principal;
    agotado/cancelado se avisan. Y cuántos conciertos tienen ya enlace, hora y cartel."""
    r = pg.evaluate("""async()=>{const dias=[...new Set(DATA.filter(r=>r.fecha>=HOY).map(r=>r.fecha))].sort().slice(0,10);
        let tot=0, ent=0, gira=0, hora=0, uno=null;
        for(const d of dias){ const x=DATA.find(r=>r.fecha===d); if(!x) continue; await asegurarDetalle(x.id);
          for(const r of DATA.filter(r=>r.fecha===d&&r._full)){ tot++; if(r.hora) hora++; if(r.gira) gira++;
            if(r.entradas){ ent++; if(!uno) uno=r.id; } } }
        return {tot, ent, gira, hora, uno}}""")
    medida("entradas_10_dias", **r)
    check("Otros", "Próximos 10 días: conciertos con enlace de compra directo", f"{r['ent']} de {r['tot']}",
          ok=r["tot"] > 0, grave=False, detalle=f"con cartel de gira {r['gira']}, con hora {r['hora']}")
    if not r["uno"]:
        return
    pg.evaluate(f"location.hash='#concierto/{r['uno']}'")
    pg.wait_for_selector(".dt h2", timeout=15000)
    pg.wait_for_timeout(800)
    b = pg.evaluate("""(id)=>{const r=BYID[id], a=document.getElementById('comprar');
        return {ok:!!a&&a.href===new URL(r.entradas.url,location.href).href&&a.innerText.includes(r.entradas.nombre),
                texto:a&&a.innerText, agotado:!!r.agotado, aviso:!!r.agotado===!!document.querySelector('.dt .box-warn,.dt .box-bad')}}""",
                    r["uno"])
    check("Funcional", "Ficha: el enlace de compra de la página de entradas es el botón principal", b["texto"],
          ok=b["ok"], detalle=str(b))


def filtros(pg, lunes):
    pg.evaluate(f"location.hash='#semana/{lunes.isoformat()}'")
    pg.wait_for_selector("#fgen")
    pg.evaluate("scrollTo(0,0)")
    t0 = time.monotonic()
    pg.click("#fgen")
    pg.wait_for_selector(".sheet")
    abrir = ms(t0)
    pg.screenshot(path=str(OUT / "4_filtros.png"))
    # solo un grupo: todo lo que sale es de ese grupo, y cuadra con los datos
    grupo = pg.evaluate("""(l)=>{const fin=new Date(new Date(l).getTime()+6*864e5).toISOString().slice(0,10);
       const c={}; DATA.filter(r=>r.fecha>=l&&r.fecha<=fin&&r.fecha>=HOY).forEach(r=>(r.grupos||[]).forEach(g=>c[g]=(c[g]||0)+1));
       return Object.entries(c).filter(([g])=>document.querySelector(`[data-g="${g}"]`)).sort((a,b)=>b[1]-a[1]).map(x=>x[0])[1]||null}""",
                        lunes.isoformat())
    t0 = time.monotonic()
    pg.click("[data-rap='ninguno']")
    pg.wait_for_timeout(30)
    marcar = ms(t0)
    if grupo:
        pg.click(f"[data-g='{grupo}']")
    pre = pg.evaluate("[...document.querySelectorAll('.segp [aria-pressed=true]')].map(b=>b.dataset.rap)")
    res = pg.evaluate("(document.getElementById('resgen')||{}).textContent||''")
    check("UX", "Filtros: al elegir géneros a mano no queda marcado ningún preajuste y el título dice 'a tu medida'",
          f"{pre} · {res!r}", ok=pre == [] and "a tu medida" in res)
    boton = pg.inner_text("#sclose")
    t0 = time.monotonic()
    pg.click("#sclose")
    pg.wait_for_function("!document.querySelector('.sheet')")
    aplicar = ms(t0)
    bajar_hasta_el_final(pg)
    if grupo:
        r = pg.evaluate("""(g)=>{const ids=[...document.querySelectorAll('#main .card')].map(c=>c.dataset.id);
           return {n:ids.length, otros:ids.filter(i=>{const r=BYID[i]||{}; return !(r.grupos||[]).includes(g)&&!(g in (r.grupos_cartel||{}));}).length}}""", grupo)
        n_boton = int(re.search(r"\d+", boton).group()) if re.search(r"\d+", boton) else None
        check("Funcional", f"Filtro de un solo grupo ({grupo}): solo salen de ese grupo", f"{r['n']} tarjetas",
              ok=r["n"] > 0 and r["otros"] == 0, detalle=f"{r['otros']} de otros grupos")
        medida("filtro_grupo", grupo=grupo, boton=boton, tarjetas=r["n"], n_boton=n_boton)
    t0 = time.monotonic()
    if pg.locator("#freset").count():
        pg.click("#freset")
    pg.wait_for_timeout(30)
    quitar = ms(t0)
    sin = pg.evaluate("document.querySelectorAll('.active').length")
    check("Funcional", "'Borrar filtros' deja la agenda sin filtros", ok=sin == 0)
    # restablecer desde la hoja y chip rápido
    pg.click("#fgen")
    pg.wait_for_selector(".sheet")
    t0 = time.monotonic()
    pg.click("[data-rap='def']")
    pg.wait_for_timeout(30)
    rest = ms(t0)
    pre = pg.evaluate("[...document.querySelectorAll('.segp [aria-pressed=true]')].map(b=>b.dataset.rap)")
    check("UX", "Filtros: 'Habituales' queda marcado al elegirlo", pre, ok=pre == ["def"])
    alto = pg.evaluate("document.querySelector('.sheet .sc').scrollHeight")
    check("UX", "Filtros: la hoja es corta (géneros en chips; estilos en su propio panel)", alto, aviso=2000,
          fallo=3000, unidad="px")
    pg.click("#sclose")
    pg.wait_for_function("!document.querySelector('.sheet')")
    marcados = "[...document.querySelectorAll('#main .chips .chip[aria-pressed=true]')].map(c=>c.dataset.chip||'pre')"
    sin_filtro = pg.evaluate(marcados)
    chip = pg.locator("[data-chip]").first
    cid = chip.get_attribute("data-chip")
    t0 = time.monotonic()
    chip.click()
    pg.wait_for_timeout(30)
    t_chip = ms(t0)
    con_filtro = pg.evaluate(marcados)
    otros = pg.evaluate("(g)=>[...document.querySelectorAll('#main .card')].filter(c=>!((BYID[c.dataset.id]||{}).grupos||[]).includes(g)).length", cid)
    chip = pg.locator("[data-chip]").first
    chip.click()
    pg.wait_for_timeout(30)
    vuelta = pg.evaluate(marcados)
    pg.locator("[data-chip]").first.click()
    pg.wait_for_timeout(30)
    hay = pg.locator("#fquitar").count()
    if hay:
        pg.click("#fquitar")
        pg.wait_for_timeout(30)
    check("UX", "Con filtros, la fila de chips tiene '✕ Quitar filtros' y deja la agenda sin filtros",
          ok=bool(hay) and pg.evaluate("nFiltros()===0") and not pg.locator("#fquitar").count())
    check("UX", "Chips de género: sin filtro solo 'Habituales' está marcado; al tocar uno se filtra por él y solo él "
          "sale relleno; al quitarlo se vuelve a 'Habituales'", f"{sin_filtro} → {con_filtro} → {vuelta}",
          ok=sin_filtro == ["pre"] and con_filtro == [cid] and otros == 0 and vuelta == ["pre"])
    for nombre, v in (("abrir la hoja", abrir), ("'Ninguno'", marcar), ("aplicar", aplicar), ("borrar filtros", quitar),
                      ("'Los de siempre'", rest), ("chip de grupo", t_chip)):
        check("Rendimiento", f"Filtros: {nombre}", v, aviso=300, fallo=800)


def estilos(pg, lunes):
    """Elegir dos subgéneros de géneros distintos con el buscador del panel de estilos, partiendo de "Habituales":
    salen justo los conciertos con alguno de esos estilos (el resto de géneros no se cuela)."""
    pg.evaluate(f"location.hash='#semana/{lunes.isoformat()}'")
    pg.wait_for_selector("#fgen")
    pg.evaluate("scrollTo(0,0)")
    dos = pg.evaluate("""()=>{const c={}; DATA.filter(r=>r.fecha>=HOY).forEach(r=>(r.estilos_discogs||[]).forEach(s=>{
        const g=grupoDeEstilo(s); if(DEF_GRUPOS.includes(g)) (c[g]=c[g]||{})[s]=((c[g]||{})[s]||0)+1;}));
      return Object.entries(c).map(([g,o])=>Object.entries(o).sort((a,b)=>a[1]-b[1]).find(x=>x[1]>=2)).filter(Boolean).slice(0,2).map(x=>x[0])}""")
    if len(dos) < 2:
        return
    pg.click("#fgen")
    pg.wait_for_selector(".sheet")
    pg.click("[data-rap='def']")
    pg.click("#vestilos")
    for e in dos:
        pg.fill("#bes", e[:6])
        pg.wait_for_timeout(100)
        pg.click(f"[data-es$='|{e}']")
    pg.click("#sclose")
    pg.wait_for_function("!document.querySelector('.sheet')")
    r = pg.evaluate("""(es)=>{const f=DATA.filter(r=>r.fecha>=HOY&&visible(r));
        return {n:f.length, malos:f.filter(r=>!(r.estilos_discogs||[]).some(s=>es.includes(s))).length,
          esperados:DATA.filter(r=>r.fecha>=HOY&&pasaTexto(r)&&pasaOrigen(r)&&(r.estilos_discogs||[]).some(s=>es.includes(s))).length}}""", dos)
    check("Funcional", "Subgéneros: buscando y marcando dos estilos de géneros distintos salen justo sus conciertos",
          f"{dos}: {r['n']} de {r['esperados']}", ok=r["n"] == r["esperados"] and r["malos"] == 0 and r["n"] > 0,
          detalle=str(r))
    pg.evaluate("()=>{setGrupos([...DEF_GRUPOS]); state.estilos={}; store.set('estilos',{}); renderBody(false);}")


def busqueda(pg, lunes):
    pg.evaluate(f"location.hash='#semana/{lunes.isoformat()}'")
    pg.wait_for_selector("#q")
    obj = pg.evaluate("""()=>{const r=DATA.filter(r=>r.fecha>=HOY&&visible(r)&&r.artista.length>4)[7]; return r&&{id:r.id,a:r.artista}}""")
    if obj:
        pg.fill("#q", obj["a"])
        pg.wait_for_timeout(600)
        encontrado = pg.locator(f'#main .card[data-id="{obj["id"]}"]').count() > 0
        check("Funcional", "Buscar un artista lo encuentra", obj["a"], ok=encontrado)
    pg.fill("#q", "zzqxw sin resultados")
    pg.wait_for_timeout(600)
    check("UX", "Búsqueda sin resultados lo dice", ok=pg.locator("#main .card").count() == 0
          and "Nada encontrado" in pg.inner_text("#main"))
    # búsqueda + filtros: la búsqueda se ve en la hoja, "Todos" no la quita, "Borrar filtros" sí
    pg.fill("#q", "Leiva")
    pg.wait_for_timeout(400)
    resumen = pg.locator(".active").inner_text() if pg.locator(".active").count() else ""
    check("UX", "La barra dice que se está buscando", resumen, ok="búsqueda" in resumen)
    pg.click("#fgen")
    pg.wait_for_selector(".sheet")
    check("UX", "La búsqueda se ve dentro de la hoja de filtros", ok=pg.locator(".qact").count() > 0)
    pg.click("[data-rap='todos']")
    check("UX", "'Todos' (grupos) no borra la búsqueda a escondidas", ok=pg.locator(".qact").count() > 0)
    pg.click("#sdef")
    check("UX", "'Borrar filtros' en la hoja quita también la búsqueda", ok=pg.locator(".qact").count() == 0)
    pg.click("#sclose")
    pg.wait_for_function("!document.querySelector('.sheet')")
    check("UX", "El cuadro de búsqueda queda vacío al borrar", ok=pg.input_value("#q") == "")


@escenario("Rendimiento", "Listas y fichas en frío")
def en_frio(b, datos):
    """Como la primera vez que alguien mira un día, un mes o una ficha cualquiera: navegador sin caché y fechas
    y conciertos elegidos al azar en cada validación (nada calentado por validaciones anteriores)."""
    hoy = date.today().isoformat()
    por_dia: dict = {}
    for r in datos:
        if r.get("fecha", "") >= hoy and r.get("img"):
            por_dia.setdefault(r["fecha"], []).append(r)
    dias = [f for f, lista in por_dia.items() if len(lista) >= 6]
    tiempos, ajenas = {"día": [], "mes": []}, []
    for vista, f in [("día", x) for x in random.sample(dias, min(3, len(dias)))] + \
                    [("mes", x) for x in random.sample(dias, min(3, len(dias)))]:
        ctx = contexto(b)
        pg = pagina(ctx)
        pedidas = []
        pg.on("request", lambda q: q.resource_type == "image" and not q.url.startswith("data:") and pedidas.append(q.url))
        pg.goto(URL + (f"#dia/{f}" if vista == "día" else f"#mes/{f}"), wait_until="commit")
        esperar_datos(pg)
        if vista == "mes":
            pg.wait_for_selector(f"[data-mdia='{f}']")
            pg.click(f"[data-mdia='{f}']")
            pg.wait_for_timeout(700)  # baja hasta la lista del día
        else:
            # el día elegido al azar puede no tener ninguno de los géneros habituales: entonces se ven los ocultos
            pg.wait_for_selector("#main .card, #main .empty")
            if not pg.query_selector("#main .card") and pg.query_selector("#main [data-quitar]"):
                pg.click("#main [data-quitar]")
                pg.wait_for_selector("#main .card")
        t = esperar_miniaturas(pg)
        tiempos[vista].append(t)
        ajenas += [u for u in pedidas if not u.startswith(URL)]
        if t is None or t > 2500:
            pg.screenshot(path=str(OUT / f"8_frio_{vista}_{f}.png"))
        ctx.close()
    medida("listas_en_frio", **{k: v for k, v in tiempos.items()})
    for vista, v in tiempos.items():
        peor = None if any(x is None for x in v) else max(v, default=0)
        check("Rendimiento", f"Vista {vista} sin caché: miniaturas visibles cargadas (peor de {len(v)} fechas al azar)",
              peor, aviso=1000, fallo=2500, detalle=str(v))
    # fichas al azar, cada una en un navegador nuevo (como al abrir un enlace compartido)
    fotos, hosts = [], []
    for r in random.sample([r for lista in por_dia.values() for r in lista], min(4, sum(map(len, por_dia.values())))):
        ctx = contexto(b)
        pg = pagina(ctx)
        pg.goto(URL + f"#concierto/{r['id']}", wait_until="commit")
        pg.wait_for_selector(".dt h2", timeout=60000)
        t0 = time.monotonic()
        fotos.append(ficha_con_foto(pg, t0))
        hosts.append(pg.evaluate("(()=>{const i=document.querySelector('.hero img');return i?new URL(i.currentSrc||i.src).hostname:''})()"))
        ctx.close()
    medida("fichas_en_frio", fotos_ms=fotos, servidores=hosts)
    check("Rendimiento", f"Ficha sin caché: foto desde que se ve la ficha (peor de {len(fotos)} al azar)",
          None if any(x is None for x in fotos) else max(fotos, default=0), aviso=1200, fallo=2500,
          detalle=f"{fotos} {hosts}")
    check("Rendimiento", "Imágenes de las listas pedidas fuera de la web (wsrv.nl, agendas)", len(ajenas),
          ok=len(ajenas) <= 3, detalle="; ".join(sorted({u.split('/')[2] for u in ajenas})), unidad="")


@escenario("Rendimiento", "Peor caso: la semana, el día y el mes con más conciertos, con todos cargados")
def peor_caso(b, datos):
    """La semana, el día y el mes con más conciertos, con el filtro 'Todos' (todos los grupos, también fuera de
    foco): el listado más largo que puede ver alguien. Navegador sin caché, móvil lento, bajando entero."""
    hoy = date.today()
    fut = [r for r in datos if r.get("fecha", "") >= hoy.isoformat()]
    sem, dia, mes_ = {}, {}, {}
    for r in fut:
        f = date.fromisoformat(r["fecha"])
        sem[lunes_de(f)] = sem.get(lunes_de(f), 0) + 1
        dia[f] = dia.get(f, 0) + 1
        mes_[(f.year, f.month)] = mes_.get((f.year, f.month), 0) + 1
    lunes = max(sem, key=sem.get)
    dmax = max(dia, key=dia.get)
    ym = max(mes_, key=mes_.get)

    def abrir_con_todos(pg, hash_):
        pg.goto(URL + hash_, wait_until="commit")
        esperar_datos(pg)
        pg.wait_for_selector("#fgen")
        pg.click("#fgen")
        pg.wait_for_selector(".sheet")
        pg.click("[data-rap='todos']")
        t0 = time.monotonic()
        pg.click("#sclose")
        pg.wait_for_function("!document.querySelector('.sheet')")
        pg.wait_for_selector("#main .card", timeout=30000)
        return ms(t0)

    # semana
    ctx = contexto(b)
    pg = pagina(ctx)
    ajenas = []
    pg.on("request", lambda q: q.resource_type == "image" and not q.url.startswith(("data:", URL)) and ajenas.append(q.url))
    aplicar = abrir_con_todos(pg, f"#semana/{lunes.isoformat()}")
    nombre = f"semana del {lunes.strftime('%d/%m')} ({sem[lunes]} conciertos)"
    check("Rendimiento", f"Peor caso {nombre}: pintar con 'Todos'", aplicar, aviso=700, fallo=1500)
    check("Rendimiento", f"Peor caso {nombre}: miniaturas de la primera pantalla", esperar_miniaturas(pg),
          aviso=1000, fallo=2500)
    pg.evaluate("window.__lt=[]")
    faltan, t_total = [], time.monotonic()
    for _ in range(400):
        antes = pg.evaluate("scrollY")
        pg.mouse.wheel(0, 700)
        pg.wait_for_timeout(400)
        m = miniaturas(pg)
        faltan.append(m["visibles"] - m["cargadas"])
        if pg.evaluate("scrollY") == antes and not pg.evaluate("document.querySelectorAll('[data-dif]').length"):
            break
    r = pg.evaluate("""(l)=>{const fin=new Date(new Date(l).getTime()+6*864e5).toISOString().slice(0,10);
        return {vistos:document.querySelectorAll('#main .card').length,
                esperados:DATA.filter(r=>r.fecha>=l&&r.fecha<=fin&&visible(r)).length,
                pendientes:document.querySelectorAll('[data-dif]').length}}""", lunes.isoformat())
    lt = pg.evaluate("window.__lt||[]")
    medida("peor_caso_semana", semana=lunes.isoformat(), conciertos=sem[lunes], sin_cargar_por_pantalla=faltan,
           recorrer_ms=ms(t_total), bloqueos=sorted(lt, key=lambda x: -x[1])[:8])
    check("Funcional", f"Peor caso {nombre}: con 'Todos' salen todos", f"{r['vistos']} de {r['esperados']}",
          ok=r["vistos"] == r["esperados"] and r["pendientes"] == 0)
    peores = sorted(faltan)[-3:]
    check("Rendimiento", f"Peor caso {nombre}: bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla)",
          max(faltan or [0]), aviso=1, fallo=3, unidad="miniaturas",
          detalle=f"{len(faltan)} pantallas; peores {peores}; pantallas con alguna sin cargar: {sum(1 for x in faltan if x)}")
    check("Rendimiento", f"Peor caso {nombre}: bloqueo de JavaScript más largo al bajar", max((d for _, d in lt), default=0),
          aviso=300, fallo=1000)
    # bajando seguido a ritmo de lectura rápida con el dedo (~1.500 px/s): huecos sin foto a la vista mientras baja
    pg.evaluate("scrollTo(0,0)")
    pg.wait_for_timeout(1500)
    vistas = cargadas = 0
    for _ in range(60):
        pg.mouse.wheel(0, 300)
        pg.wait_for_timeout(200)
        m = miniaturas(pg)
        vistas += m["visibles"]
        cargadas += m["cargadas"]
    check("Rendimiento", f"Peor caso {nombre}: bajando seguido, miniaturas a la vista sin cargar",
          round(100 * (vistas - cargadas) / max(1, vistas), 1), aviso=5, fallo=15, unidad="%",
          detalle=f"{vistas - cargadas} de {vistas} vistas en 12 s")
    pg.evaluate("scrollTo(0,0)")
    pg.wait_for_timeout(500)
    for _ in range(40):
        pg.mouse.wheel(0, 1200)
        pg.wait_for_timeout(100)
    check("Rendimiento", f"Peor caso {nombre}: bajando deprisa, al parar miniaturas visibles cargadas en",
          esperar_miniaturas(pg), aviso=1000, fallo=2500)
    # abrir una ficha del final de la lista y volver
    cards = pg.locator("#main .card")
    c = cards.nth(cards.count() - 3)
    c.scroll_into_view_if_needed()
    pg.wait_for_timeout(2000)
    cid = c.get_attribute("data-id")
    t0 = time.monotonic()
    c.click()
    pg.wait_for_selector(".dt h2", timeout=30000)
    check("Rendimiento", f"Peor caso {nombre}: foto de una ficha del final de la lista", ficha_con_foto(pg, t0),
          aviso=800, fallo=2000)
    pg.go_back()
    pg.wait_for_selector("#main .card")
    pg.wait_for_timeout(800)
    se_ve = pg.evaluate("""(a)=>{const c=document.querySelector(`.card[data-id="${a}"]`);
       if(!c) return false; const b=c.getBoundingClientRect(); return b.top>-10&&b.top<innerHeight-40}""", cid)
    check("UX", f"Peor caso {nombre}: volver deja la lista en el concierto", ok=se_ve)
    check("Rendimiento", f"Peor caso {nombre}: imágenes pedidas fuera de la web", len(ajenas), ok=len(ajenas) <= 3,
          detalle="; ".join(sorted({u.split('/')[2] for u in ajenas})), unidad="")
    ctx.close()

    # día con más conciertos
    ctx = contexto(b)
    pg = pagina(ctx)
    aplicar = abrir_con_todos(pg, f"#dia/{dmax.isoformat()}")
    nombre = f"día {dmax.strftime('%d/%m')} ({dia[dmax]} conciertos)"
    check("Rendimiento", f"Peor caso {nombre}: miniaturas de la primera pantalla", esperar_miniaturas(pg),
          aviso=1000, fallo=2500)
    faltan = []
    for _ in range(200):
        antes = pg.evaluate("scrollY")
        pg.mouse.wheel(0, 700)
        pg.wait_for_timeout(400)
        m = miniaturas(pg)
        faltan.append(m["visibles"] - m["cargadas"])
        if pg.evaluate("scrollY") == antes:
            break
    check("Rendimiento", f"Peor caso {nombre}: bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla)",
          max(faltan or [0]), aviso=1, fallo=3, unidad="miniaturas", detalle=f"{len(faltan)} pantallas")
    ctx.close()

    # mes con más conciertos: tocar el día con más conciertos de ese mes
    ctx = contexto(b)
    pg = pagina(ctx)
    d_mes = max((d for d in dia if (d.year, d.month) == ym), key=dia.get)
    abrir_con_todos(pg, f"#mes/{d_mes.isoformat()}")
    otro = next((d for d in sorted(dia, key=dia.get, reverse=True) if (d.year, d.month) == ym and d != d_mes), d_mes)
    t0 = time.monotonic()
    pg.click(f"[data-mdia='{otro.isoformat()}']")
    pg.wait_for_timeout(700)
    t = esperar_miniaturas(pg)
    nombre = f"mes {ym[1]:02d}/{ym[0]} ({mes_[ym]} conciertos), día {otro.strftime('%d/%m')}"
    check("Rendimiento", f"Peor caso {nombre}: al tocar el día, miniaturas visibles cargadas", t, aviso=1000,
          fallo=2500, detalle=f"desde el toque: {ms(t0)} ms")
    ctx.close()


def mes(pg):
    t0 = time.monotonic()
    pg.evaluate(f"location.hash='#mes/{(date.today() + timedelta(days=10)).isoformat()}'")
    pg.wait_for_selector(".cal")
    check("Rendimiento", "Vista mes", ms(t0), aviso=700, fallo=1500)
    dia = pg.locator("[data-mdia]:not(.zero):not(.sel)").last
    f = dia.get_attribute("data-mdia")
    t0 = time.monotonic()
    dia.click()
    pg.wait_for_timeout(1000)
    r = pg.evaluate("""(f)=>{const h=document.querySelector('#mlista .mhead'); const b=h&&h.getBoundingClientRect();
       const ids=[...document.querySelectorAll('#mlista .card')].map(c=>c.dataset.id);
       return {a_la_vista:!!b&&b.top>=0&&b.top<innerHeight, n:ids.length,
               esperados:DATA.filter(r=>r.fecha===f&&visible(r)).length, otros:ids.filter(i=>(BYID[i]||{}).fecha!==f).length}}""", f)
    check("UX", "Mes: al tocar un día, su lista queda a la vista", ok=r["a_la_vista"])
    check("Funcional", "Mes: la lista del día son los conciertos de ese día", f"{r['n']} de {r['esperados']}",
          ok=r["n"] == r["esperados"] and r["otros"] == 0)
    pg.screenshot(path=str(OUT / "5_mes.png"))


def accesos_al_bajar(pg, lunes):
    """A media lista: el menú ☰ se abre a la vista, y Buscar y Filtros están en la cabecera (Filtros abre la hoja sin
    mover la lista; Buscar lleva a la caja de búsqueda lista para escribir). Arriba del todo no se duplican."""
    pg.evaluate(f"location.hash='#semana/{lunes.isoformat()}'")
    pg.wait_for_selector(".card", timeout=30000)
    pg.evaluate("scrollTo(0,0)")
    pg.wait_for_timeout(500)
    arriba = pg.is_visible("#hq") or pg.is_visible("#hf")
    pg.evaluate("scrollTo(0,document.documentElement.scrollHeight/2)")
    pg.wait_for_timeout(600)
    check("UX", "Al bajar por la lista, Buscar y Filtros siguen a mano en la cabecera (y arriba no se duplican)",
          ok=pg.is_visible("#hq") and pg.is_visible("#hf") and not arriba)
    pg.evaluate("scrollTo(0,document.documentElement.scrollHeight/2)")
    pg.wait_for_timeout(400)
    pg.click("#menubtn")
    pg.wait_for_timeout(300)
    m = pg.evaluate("(()=>{const m=document.querySelector('#menu .menu'); if(!m) return null;"
                    "const b=m.getBoundingClientRect(); return b.top>=0&&b.bottom<=innerHeight})()")
    check("Funcional", "A media lista, el menú ☰ se abre a la vista", ok=bool(m))
    pg.evaluate("document.getElementById('menu').innerHTML=''")
    if pg.is_visible("#hf"):
        y = pg.evaluate("scrollY")
        pg.click("#hf")
        pg.wait_for_timeout(500)
        check("Funcional", "A media lista, Filtros abre la hoja sin mover la lista",
              ok=pg.is_visible(".sheet") and pg.evaluate("scrollY") == y)
        pg.evaluate("document.getElementById('sheet').innerHTML=''")
    # ‹ periodo › y Hoy en la cabecera: avanzar desde media lista deja la semana siguiente lista para leer
    if pg.is_visible("#hnav [data-hn]"):
        antes = pg.evaluate("state.date")
        pg.click("#hnav [data-hn]:last-child")
        pg.wait_for_timeout(700)
        r = pg.evaluate("""()=>{const ss=document.querySelector('#main .stickystrip'), h=document.querySelector('#main .dayhead');
            return {fecha:state.date, fija:document.getElementById('hdr').classList.contains('navfija'),
              titulo:(document.querySelector('#hnav .t')||{}).innerText||'',
              cabecera:!!h&&!!ss&&h.getBoundingClientRect().top>=ss.getBoundingClientRect().bottom-2&&h.getBoundingClientRect().top<innerHeight/2}}""")
        esperado = (date.fromisoformat(antes) + timedelta(days=7)).isoformat()
        check("UX", "A media lista, ‹ semana › en la cabecera: pasa a la siguiente y deja su primer día a la vista",
              f"{r['fecha']} · {r['titulo']!r}", ok=r["fecha"] == esperado and r["fija"] and r["cabecera"],
              detalle=str(r))
    else:
        check("UX", "A media lista, ‹ semana › y Hoy están en la cabecera", ok=False)
    pg.evaluate("scrollTo(0,document.documentElement.scrollHeight/2)")
    pg.wait_for_timeout(400)
    y = pg.evaluate("scrollY")
    pg.click("#hq")
    pg.wait_for_timeout(400)
    check("Funcional", "A media lista, la lupa abre la búsqueda en la cabecera lista para escribir, sin mover la lista",
          ok=pg.evaluate("document.activeElement&&document.activeElement.id==='hqi'") and pg.evaluate("scrollY") == y)
    ancla = pg.evaluate("anclaBus")
    pg.keyboard.type("rock")
    pg.wait_for_timeout(800)
    n = pg.evaluate("document.querySelectorAll('#main .card').length")
    pg.click("#hqc")
    pg.wait_for_timeout(600)
    vuelve = pg.evaluate("(a)=>{const c=a&&document.querySelector(`#main .card[data-id=\"${a.id}\"]`);"
                         "return !!c&&Math.abs(c.getBoundingClientRect().top-a.top)<3&&!state.q}", ancla)
    check("Funcional", "Buscar desde media lista y cancelar: vuelve a la misma tarjeta", f"{n} resultados",
          ok=n > 0 and vuelve)



DESLIZAR = """(sel)=>{const s=document.querySelector(sel); const t=x=>new Touch({identifier:1,target:s,clientX:x,clientY:400});
  s.dispatchEvent(new TouchEvent('touchstart',{touches:[t(300)],changedTouches:[t(300)]}));
  s.dispatchEvent(new TouchEvent('touchend',{touches:[],changedTouches:[t(90)]}));}"""
POSICION = """()=>{const hh=document.getElementById('hdr').offsetHeight, ss=document.querySelector('#main .stickystrip');
  const sb=ss?ss.getBoundingClientRect().bottom:hh, nav=document.querySelector('#main .nav'), cal=document.querySelector('#main .cal');
  const sec=document.querySelector(`#main .dia[data-f="${state.date}"]`)||document.querySelector('#main .dia,#main [data-dif]');
  const hoy=[...document.querySelectorAll('#hoy,#hnav [data-hn=hoy]')];
  return {fecha:state.date, y:Math.round(scrollY), arriba:Math.round(nav.getBoundingClientRect().bottom+scrollY-hh+1),
    sec:sec?Math.round(sec.getBoundingClientRect().top-sb):null, secF:sec&&(sec.dataset.f||sec.dataset.dif),
    cal:cal?Math.round(cal.getBoundingClientRect().top-hh):null, hoyVisible:hoy.some(b=>!b.classList.contains('off'))}}"""


def cambiar_fecha_bajado(pg, lunes):
    """Desde media lista, cambiar de día, semana o mes (tira de días, flechas de la cabecera, deslizar, Hoy) deja la
    vista nueva desde su principio, justo bajo la cabecera, nunca a media lista. Hoy sale siempre que no estés ya
    en hoy (también en el mes actual con otro día elegido y en la semana actual cuando vas por otro día) y lleva a
    hoy (en la semana, a la lista de hoy)."""
    hoy = date.fromisoformat(pg.evaluate("HOY"))
    malos: list[str] = []
    n = 0

    def pulsar(boton):
        # el de la cabecera fija si se ve (a media lista); si no (lista corta), el de la fila de navegación
        alt = {"sig": ("#hnav [data-hn]:last-child", "#main .nav [data-nav]:last-child"),
               "ant": ("#hnav [data-hn]:first-child", "#main .nav [data-nav]:first-child"),
               "hoy": ("#hnav [data-hn=hoy]", "#hoy")}[boton]
        return lambda: pg.click(alt[0] if pg.is_visible(alt[0]) else alt[1])

    def caso(nombre, inicio, accion, esperado, donde, bajar=True):
        nonlocal n
        n += 1
        pg.evaluate(f"location.hash='#{inicio}'")
        pg.wait_for_function(f"location.hash==='#{inicio}'&&!!document.querySelector('#main .nav')", timeout=15000)
        pg.wait_for_timeout(400)
        if bajar:
            pg.evaluate("scrollTo(0,(document.documentElement.scrollHeight-innerHeight)/2)")
            pg.wait_for_timeout(400)
        accion()
        pg.wait_for_timeout(700)
        r = pg.evaluate(POSICION)
        mal = []
        if r["fecha"] != esperado:
            mal.append(f"fecha {r['fecha']}")
        if donde == "lista" and not (r["sec"] is not None and -3 <= r["sec"] <= 24 and r["y"] <= r["arriba"] + 2):
            mal.append(f"lista a {r['sec']} px de la tira (scroll {r['y']}, principio {r['arriba']})")
        if donde == "hoy" and not (r["sec"] is not None and -3 <= r["sec"] <= 24 and r["secF"] >= hoy.isoformat()):
            mal.append(f"día {r['secF']} a {r['sec']} px")
        if donde == "mes" and not (r["cal"] is not None and -3 <= r["cal"] <= 24):
            mal.append(f"cuadrícula a {r['cal']} px")
        if r["fecha"] == hoy.isoformat() and r["hoyVisible"]:
            mal.append("Hoy sigue a la vista estando en hoy")
        if mal:
            malos.append(f"{nombre}: {'; '.join(mal)}")

    dia = lunes + timedelta(days=3)
    d = dia.isoformat()
    caso("Día: otro día de la tira", f"dia/{d}", lambda: pg.click(f"#main .strip [data-sel='{(dia + timedelta(days=1)).isoformat()}']"),
         (dia + timedelta(days=1)).isoformat(), "lista")
    caso("Día: deslizar", f"dia/{d}", lambda: pg.evaluate(DESLIZAR, "#swipe"), (dia + timedelta(days=1)).isoformat(), "lista")
    caso("Día: › de la cabecera", f"dia/{d}", pulsar("sig"),
         (dia + timedelta(days=1)).isoformat(), "lista")
    caso("Día: ‹ de la cabecera", f"dia/{d}", pulsar("ant"),
         (dia - timedelta(days=1)).isoformat(), "lista")
    if dia != hoy:
        caso("Día: Hoy", f"dia/{d}", pulsar("hoy"), hoy.isoformat(), "lista")
    caso("Semana: › de la cabecera", f"semana/{lunes.isoformat()}", pulsar("sig"),
         (lunes + timedelta(days=7)).isoformat(), "lista")
    caso("Semana: deslizar", f"semana/{lunes.isoformat()}", lambda: pg.evaluate(DESLIZAR, "#swipe"),
         (lunes + timedelta(days=7)).isoformat(), "lista")
    l_hoy = lunes_de(hoy)
    if lunes != l_hoy:
        caso("Semana: Hoy desde otra semana", f"semana/{lunes.isoformat()}", pulsar("hoy"),
             hoy.isoformat(), "hoy")
    if hoy.weekday() > 0:
        caso("Semana actual: Hoy desde su lunes", f"semana/{l_hoy.isoformat()}",
             pulsar("hoy"), hoy.isoformat(), "hoy", bajar=False)
    caso("Mes: › de la cabecera", f"mes/{d}", pulsar("sig"),
         (dia.replace(day=1) + timedelta(days=32)).replace(day=1).isoformat()
         if (dia.replace(day=1) + timedelta(days=32)).strftime("%Y-%m") != hoy.strftime("%Y-%m") else hoy.isoformat(), "mes")
    otro = hoy + timedelta(days=1 if hoy.day < 28 else -1)
    caso("Mes actual con otro día: Hoy", f"mes/{otro.isoformat()}",
         pulsar("hoy"), hoy.isoformat(), "mes")
    check("UX", "Cambiar de día, semana o mes desde media lista deja la vista nueva desde su principio; Hoy siempre a mano",
          f"{n - len(malos)} de {n} casos bien", ok=not malos, detalle=" | ".join(malos[:6]))



def cartel_web(pg):
    """Fase 3: un festival sale con su insignia y todo su cartel en la ficha, y un concierto cuyo telonero es de
    otro género sale al filtrar solo por ese género (y su tarjeta dice por qué)."""
    f = pg.evaluate("(DATA.filter(r=>r.festival&&r.fecha>=HOY&&(r.invitados||[]).length>=2)[0]||{}).id")
    if not f:
        check("Funcional", "Festivales: insignia y cartel en la ficha", grave=False, detalle="hoy no hay ninguno")
    else:
        pg.evaluate(f"location.hash='#concierto/{f}'")
        pg.wait_for_selector(".dt h2", timeout=30000)
        pg.wait_for_timeout(800)
        r = pg.evaluate("""(id)=>({fest:!!document.querySelector('.dt h2 .fest'), n:document.querySelectorAll('.cartel li').length,
            esperados:(BYID[id].invitados||[]).length, titulo:(document.querySelector('.dt h2')||{}).innerText})""", f)
        check("Funcional", "Festivales: insignia y cartel en la ficha", f"{r['titulo']!r}: {r['n']} de {r['esperados']}",
              ok=r["fest"] and r["n"] == r["esperados"])
    c = pg.evaluate("""(()=>{const r=DATA.find(r=>r.fecha>=HOY&&r.grupos_cartel&&Object.keys(r.grupos_cartel).some(g=>!grupos(r).includes(g)));
        if(!r) return null; const g=Object.keys(r.grupos_cartel).find(g=>!grupos(r).includes(g)); return {id:r.id,fecha:r.fecha,g}})()""")
    if not c:
        check("Funcional", "Teloneros: el concierto sale al filtrar por el género del telonero", grave=False,
              detalle="hoy no hay ninguno con fichas del cartel")
        return
    pg.evaluate(f"(()=>{{setGrupos(['{c['g']}']); state.estilos={{}}; location.hash='#dia/{c['fecha']}';}})()")
    pg.wait_for_timeout(1200)
    pg.evaluate("document.querySelectorAll('[data-dif]').forEach(e=>e._pintar&&e._pintar())")
    r = pg.evaluate("(id)=>{const el=document.querySelector(`#main .card[data-id=\"${id}\"]`); return {sale:!!el, tag:!!(el&&el.querySelector('.tcart'))}}", c["id"])
    check("Funcional", "Teloneros: el concierto sale al filtrar por el género del telonero (y la tarjeta lo dice)",
          f"{c['g']} el {c['fecha']}", ok=r["sale"] and r["tag"], detalle=str(r))
    pg.evaluate("(()=>{setGrupos(DEF_GRUPOS); renderBody(false);})()")



def pagina_fuentes(pg):
    """Fase 5: la página de Fuentes enseña una tarjeta por web (con su estado, su tira de 14 días y sus datos), los
    filtros por tipo y la búsqueda funcionan, y no hay scroll lateral."""
    pg.evaluate("location.hash='#fuentes'")
    pg.wait_for_selector("#fulist .fu", timeout=30000)
    pg.wait_for_timeout(400)
    r = pg.evaluate("""()=>({n:document.querySelectorAll('#fulist .fu').length, total:INFORME.fuentes.length,
        tiras:document.querySelectorAll('#fulist .fsal').length, metricas:document.querySelectorAll('#fulist .fmets').length,
        lateral:document.documentElement.scrollWidth-innerWidth, salas:document.querySelectorAll('.fsin li').length})""")
    pg.click("[data-fu=salas]")
    pg.wait_for_timeout(300)
    salas = pg.evaluate("""()=>({n:document.querySelectorAll('#fulist .fu').length,
        bien:[...document.querySelectorAll('#fulist .fu')].every(a=>a.dataset.cat==='salas'),
        esperadas:INFORME.fuentes.filter(f=>f.tipo==='sala').length})""")
    nombre = pg.evaluate("INFORME.fuentes[0].nombre")
    pg.click("[data-fu=todas]")
    pg.fill("#fuq", nombre[:12])
    pg.wait_for_timeout(300)
    busca = pg.evaluate("(n)=>[...document.querySelectorAll('#fulist .fun')].some(a=>a.textContent===n)", nombre)
    pg.fill("#fuq", "")
    check("UX", "Fuentes: una tarjeta por web con estado, 14 días y datos; filtros y búsqueda; sin scroll lateral",
          f"{r['n']} de {r['total']} webs · {salas['n']} salas · {r['salas']} salas sin web leída",
          ok=r["n"] == r["total"] == r["tiras"] == r["metricas"] and r["lateral"] <= 0 and salas["bien"]
          and salas["n"] == salas["esperadas"] and busca, detalle=str({**r, **salas, "busca": busca}))


def cabeceras_fijas(pg, lunes):
    """Al bajar por una lista, la fecha completa del día se queda pegada arriba (debajo de la tira de días en semana
    y día) y, en la semana, la tira marca el día por el que vas. Tocar un día de la tira lleva justo a su cabecera."""
    estado = """()=>{const ss=document.querySelector('#main .stickystrip'), lim=ss?ss.getBoundingClientRect().bottom
         :document.getElementById('hdr').getBoundingClientRect().bottom;
       const pegada=[...document.querySelectorAll('#main .dayhead')].find(h=>Math.abs(h.getBoundingClientRect().top-lim)<3);
       const sec=pegada&&pegada.closest('.dia');
       const en=document.querySelector('#main .strip .en,#main .strip .sel');
       return {pegada:!!pegada, fecha:sec&&sec.dataset.f, texto:pegada&&pegada.textContent, marcado:en&&(en.dataset.jump||en.dataset.sel),
               alto:Math.round(lim)}}"""
    # semana: a media lista
    pg.evaluate(f"location.hash='#semana/{lunes.isoformat()}'")
    pg.wait_for_selector(".card", timeout=30000)
    pg.wait_for_timeout(800)
    pg.evaluate("scrollTo(0,document.documentElement.scrollHeight/2)")
    pg.wait_for_timeout(600)
    r = pg.evaluate(estado)
    check("UX", "Semana: al bajar, la fecha completa del día se queda fija arriba", r["texto"], ok=r["pegada"],
          detalle=str(r))
    check("UX", "Semana: la tira de días marca el día por el que vas", f"{r['marcado']} / {r['fecha']}",
          ok=r["pegada"] and r["marcado"] == r["fecha"])
    check("UX", "Semana: lo fijo arriba (cabecera, tira y fecha) no ocupa más de un tercio de la pantalla",
          r["alto"] + 40, aviso=844 // 3, fallo=844 // 2, unidad="px")
    pg.screenshot(path=str(OUT / "5b_semana_fija.png"))
    # semana: tocar el último día con conciertos lleva a su cabecera
    dias = pg.evaluate("[...document.querySelectorAll('#main .stickystrip [data-jump]')]"
                       ".filter(b=>document.getElementById('d-'+b.dataset.jump)).map(b=>b.dataset.jump)")
    if dias:
        pg.evaluate("scrollTo(0,0)")
        pg.wait_for_timeout(300)
        pg.click(f"[data-jump='{dias[-1]}']")
        pg.wait_for_timeout(1500)
        r = pg.evaluate(estado)
        check("UX", "Semana: tocar un día de la tira lleva justo a ese día", f"{r['fecha']} (pedido {dias[-1]})",
              ok=r["fecha"] == dias[-1] and r["marcado"] == dias[-1], detalle=str(r))
    # día
    dia = pg.evaluate("""(l)=>{const b=byDate(); let m=l; for(let i=0;i<7;i++){const f=addDays(l,i);
        if((b[f]||[]).length>(b[m]||[]).length) m=f;} return m}""", lunes.isoformat())
    pg.evaluate(f"location.hash='#dia/{dia}'")
    pg.wait_for_timeout(1200)
    if pg.evaluate("document.querySelectorAll('#main .card').length") > 8:
        pg.evaluate("scrollTo(0,document.documentElement.scrollHeight/2)")
        pg.wait_for_timeout(600)
        r = pg.evaluate(estado)
        check("UX", "Día: al bajar, la fecha completa se queda fija arriba con la tira de días", r["texto"],
              ok=r["pegada"] and r["fecha"] == dia and r["marcado"] == dia, detalle=str(r))
    # mes: la lista del día elegido
    pg.evaluate(f"location.hash='#mes/{dia}'")
    pg.wait_for_selector(".cal")
    pg.wait_for_timeout(800)
    if pg.evaluate("document.querySelectorAll('#mlista .card').length") > 8:
        pg.evaluate("scrollTo(0,document.documentElement.scrollHeight-innerHeight*1.5)")
        pg.wait_for_timeout(600)
        r = pg.evaluate(estado)
        check("UX", "Mes: al bajar por la lista del día, su fecha completa se queda fija arriba", r["texto"],
              ok=r["pegada"] and r["fecha"] == dia, detalle=str(r))


# ---------------------------------------------------------------------------------------------- 3. enlaces directos
MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
            "noviembre", "diciembre"]


def ultimo_domingo(y: int, m: int) -> date:
    d = (date(y, m + 1, 1) if m < 12 else date(y + 1, 1, 1)) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() + 1) % 7)


@escenario("Funcional", "Paso de días, semanas, meses y años")
def navegacion_fechas(b):
    """Con las flechas ‹ › de las tres vistas: de un día a otro, de una semana a otra, de un mes al siguiente, de un
    año al siguiente (y vuelta atrás), por el cambio de hora de octubre y de marzo y por febrero. En cada paso,
    la fecha de la dirección, el título, la tira de 7 días, la cuadrícula del mes y los conciertos de la lista
    tienen que ser justo los que tocan según el calendario y los datos."""
    ctx = contexto(b)
    pg = pagina(ctx, lenta=False)
    pg.goto(URL, wait_until="commit")
    esperar_datos(pg)
    hoy = date.fromisoformat(pg.evaluate("HOY"))
    fin_anyo = date(hoy.year, 12, 28)
    fallos: list[str] = []
    pasos = malos = 0
    leer = """()=>{document.querySelectorAll('[data-dif]').forEach(e=>e._pintar&&e._pintar());
       const ids=[...document.querySelectorAll('#main .card')].map(c=>c.dataset.id);
       return {hash:location.hash, fecha:state.date, titulo:(document.querySelector('#main .nav .title')||{}).innerText||'',
         tira:[...document.querySelectorAll('#main .strip button')].map(b=>b.dataset.jump||b.dataset.sel),
         marcado:[...document.querySelectorAll('#main .strip .sel')].map(b=>b.dataset.sel),
         celdas:[...document.querySelectorAll('#main [data-mdia]:not(.out)')].map(b=>b.dataset.mdia),
         primera:[...document.querySelectorAll('#main [data-mdia]')].findIndex(b=>!b.classList.contains('out')),
         elegida:[...document.querySelectorAll('#main [data-mdia].sel')].map(b=>b.dataset.mdia),
         cabeceras:[...document.querySelectorAll('#main .dia')].map(s=>s.dataset.f),
         fechas:ids.map(i=>(BYID[i]||{}).fecha), ids}}"""
    esperados = """([a,z])=>DATA.filter(r=>r.fecha>=a&&r.fecha<=z&&visible(r)).map(r=>r.id).sort()"""

    def comprobar(vista: str, d: date, que: str):
        nonlocal pasos, malos
        pasos += 1
        v = pg.evaluate(leer)
        mal = []
        if v["fecha"] != d.isoformat():
            mal.append(f"fecha {v['fecha']}")
        if not v["hash"].endswith("/" + d.isoformat()):
            mal.append(f"dirección {v['hash']}")
        if vista in ("semana", "dia"):
            lunes = lunes_de(d)
            tira = [(lunes + timedelta(days=i)).isoformat() for i in range(7)]
            if v["tira"] != tira:
                mal.append(f"tira {v['tira']}")
        if vista == "dia":
            a = z = d
            if v["marcado"] != [d.isoformat()]:
                mal.append(f"marcado {v['marcado']}")
            if f"{MESES_ES[d.month - 1]} de {d.year}" not in v["titulo"].lower():
                mal.append(f"título {v['titulo']!r}")
            if v["cabeceras"] != [d.isoformat()]:
                mal.append(f"cabecera {v['cabeceras']}")
        elif vista == "semana":
            a, z = lunes_de(d), lunes_de(d) + timedelta(days=6)
            if str(a.day) not in v["titulo"] or str(z.day) not in v["titulo"]:
                mal.append(f"título {v['titulo']!r}")
        else:
            a = z = d
            uno = d.replace(day=1)
            sig = (uno + timedelta(days=32)).replace(day=1)
            dias = [(uno + timedelta(days=i)).isoformat() for i in range((sig - uno).days)]
            if v["celdas"] != dias:
                mal.append(f"cuadrícula {len(v['celdas'])} días ({v['celdas'][:1]}…{v['celdas'][-1:]})")
            if v["primera"] != uno.weekday():
                mal.append(f"el día 1 cae en la columna {v['primera']} y no en la {uno.weekday()}")
            if v["elegida"] != [d.isoformat()]:
                mal.append(f"día elegido {v['elegida']}")
            if f"{MESES_ES[d.month - 1]} de {d.year}" not in v["titulo"].lower():
                mal.append(f"título {v['titulo']!r}")
        esp = pg.evaluate(esperados, [a.isoformat(), z.isoformat()])
        if sorted(v["ids"]) != esp:
            mal.append(f"conciertos {len(v['ids'])} de {len(esp)}")
        if any(f is None or f < a.isoformat() or f > z.isoformat() for f in v["fechas"]):
            mal.append("conciertos de otras fechas")
        if v["fechas"] != sorted(v["fechas"]):
            mal.append("desordenados")
        if mal:
            malos += 1
            fallos.append(f"{vista} {que} → {d}: {'; '.join(mal)}")

    def recorrer(vista: str, inicio: date, n: int, paso: int, flecha: int, que: str):
        pg.evaluate(f"location.hash='#{vista}/{inicio.isoformat()}'")
        pg.wait_for_function(f"state.date==='{inicio.isoformat()}'", timeout=15000)
        pg.wait_for_timeout(200)
        comprobar(vista, inicio, que)
        d = inicio
        for sentido in (1, -1):
            for _ in range(n):
                pg.click(f"#main [data-nav='{flecha * sentido}']")
                if vista == "mes":
                    m = d.month - 1 + sentido
                    d = date(d.year + m // 12, m % 12 + 1, 1)
                    if d.strftime("%Y-%m") == hoy.strftime("%Y-%m"):
                        d = hoy
                else:
                    d = d + timedelta(days=paso * sentido)
                pg.wait_for_function(f"state.date==='{d.isoformat()}'", timeout=15000)
                pg.wait_for_timeout(150)
                comprobar(vista, d, que)

    cambio_oct = ultimo_domingo(hoy.year if hoy.month <= 10 else hoy.year + 1, 10)
    cambio_mar = ultimo_domingo(hoy.year + 1 if hoy.month > 3 else hoy.year, 3)
    try:
        recorrer("dia", fin_anyo, 7, 1, 1, "de un año a otro")
        recorrer("dia", cambio_oct - timedelta(days=2), 4, 1, 1, "por el cambio de hora de octubre")
        recorrer("dia", cambio_mar - timedelta(days=2), 4, 1, 1, "por el cambio de hora de marzo")
        recorrer("dia", date(hoy.year + 1, 2, 26), 4, 1, 1, "de febrero a marzo")
        recorrer("semana", lunes_de(hoy) + timedelta(days=2), 6, 7, 7, "semana a semana y de un mes a otro")
        recorrer("semana", lunes_de(fin_anyo) - timedelta(days=14), 5, 7, 7, "de un año a otro")
        recorrer("mes", hoy, 16, 0, 1, "mes a mes y de un año a otro")
        # cambiar de vista conserva la fecha; "Hoy" vuelve a hoy
        d = date(hoy.year + 1, 1, 2)
        for vista in ("dia", "semana", "mes"):
            pg.click(f"[data-tab='{ {'dia': 'Día', 'semana': 'Semana', 'mes': 'Mes'}[vista] }']")
            if vista == "dia":
                pg.evaluate(f"location.hash='#dia/{d.isoformat()}'")
            pg.wait_for_function(f"state.date==='{d.isoformat()}'", timeout=15000)
            pg.wait_for_timeout(200)
            comprobar(vista, d, "al cambiar de vista")
        pg.click("#hoy")
        pg.wait_for_function(f"state.date==='{hoy.isoformat()}'", timeout=15000)
        comprobar("mes", hoy, "botón Hoy")
    except Exception as e:  # noqa: BLE001
        fallos.append(f"se atascó: {str(e)[:200]}")
    check("Funcional", "Paso de días, semanas, meses y años (con cambios de hora y febrero) con las flechas",
          f"{pasos - malos} de {pasos} pasos bien", ok=not fallos, detalle=" | ".join(fallos[:6]))
    ctx.close()


@escenario("Funcional", "Enlaces directos")
def enlaces_directos(b, datos):
    ctx = contexto(b)
    pg = pagina(ctx)
    r = next((x for x in datos if x.get("fecha", "") > (date.today() + timedelta(days=20)).isoformat()), None)
    if r:
        t0 = time.monotonic()
        pg.goto(URL + f"#concierto/{r['id']}", wait_until="commit")
        pg.wait_for_selector(".dt h2", timeout=60000)
        check("Funcional", "Enlace directo a una ficha la abre", pg.inner_text(".dt h2"),
              ok=pg.inner_text(".dt h2").strip().lower() == r["artista"].strip().lower())
        check("Rendimiento", "Enlace directo a una ficha (visita nueva)", ms(t0), aviso=5000, fallo=9000)
    pg.goto(URL + "#concierto/no-existe-123", wait_until="commit")
    esperar_datos(pg)
    pg.wait_for_timeout(500)
    check("Fallos", "Enlace a un concierto que ya no existe: lo dice y deja volver",
          ok="No se encontró el concierto" in pg.inner_text("#main") and pg.locator("a.back").count() > 0)
    pg.goto(URL + "#semana/2031-01-06", wait_until="commit")
    esperar_datos(pg)
    pg.wait_for_timeout(500)
    check("UX", "Semana sin conciertos: lo dice", ok="No hay conciertos" in pg.inner_text("#main"))
    ctx.close()


# ---------------------------------------------------------------------------------------------- 4. fallos
@escenario("Fallos", "Sin conexión")
def sin_conexion(b):
    ctx = contexto(b)
    pg = pagina(ctx, lenta=False)
    pg.goto(URL, wait_until="load")
    esperar_datos(pg)
    pg.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.ready.then(()=>true)", timeout=30000)
    pg.reload(wait_until="load")                      # ya controlada por el service worker
    esperar_datos(pg)
    hoy = date.today().isoformat()
    pg.evaluate(f"location.hash='#dia/{hoy}'")
    pg.wait_for_timeout(8000)                         # tiempo para que se guarden los detalles de los primeros días
    ctx.set_offline(True)
    t0 = time.monotonic()
    pg.reload(wait_until="commit")
    try:
        esperar_datos(pg, timeout=15000)
        ok = True
    except Exception:  # noqa: BLE001
        ok = False
    check("Fallos", "Sin conexión: la agenda se abre con la copia guardada", ms(t0) if ok else None, aviso=4500,
          fallo=8000, detalle="" if ok else pg.inner_text("#main")[:200])
    if ok:
        pg.evaluate(f"location.hash='#semana/{lunes_de(date.today()).isoformat()}'")
        pg.wait_for_timeout(800)
        check("Fallos", "Sin conexión: se ven los conciertos", ok=pg.locator("#main .card").count() > 0)
        lejos = pg.evaluate("(()=>{const r=DATA.filter(r=>r.fecha>HOY).slice(-1)[0]; return r&&r.id})()")
        pg.evaluate(f"location.hash='#concierto/{lejos}'")
        pg.wait_for_selector(".dt h2", timeout=10000)
        pg.wait_for_timeout(2500)
        txt = pg.inner_text("#main")
        check("Fallos", "Sin conexión: una ficha no guardada avisa en vez de quedarse cargando",
              ok="No se pudieron cargar" in txt and "Cargando" not in txt, detalle=txt[:160].replace("\n", " "))
    ctx.set_offline(False)
    ctx.close()


@escenario("Fallos", "Averías simuladas")
def averias(b, datos):
    # detalle que no llega
    ctx = contexto(b, sw="block")
    ctx.route("**/data/detalles/**", lambda r: r.abort())
    pg = pagina(ctx, lenta=False)
    r = next((x for x in datos if x.get("fecha", "") >= date.today().isoformat()), None)
    pg.goto(URL + f"#concierto/{r['id']}", wait_until="commit")
    pg.wait_for_selector(".dt h2", timeout=30000)
    pg.wait_for_timeout(2500)
    txt = pg.inner_text("#main")
    check("Fallos", "Detalle que no llega: se ve la ficha básica y avisa", ok=r["artista"].lower() in txt.lower()
          and "No se pudieron cargar" in txt and "Cargando" not in txt, detalle=txt[:160].replace("\n", " "))
    ctx.close()

    # fotos que no cargan: ni iconos rotos ni huecos, se ven las iniciales
    ctx = contexto(b, sw="block")
    ctx.route(re.compile(r".*\.(jpe?g|png|webp)(\?.*)?$|.*wsrv\.nl.*|.*thumb\.wikimedia.*|.*discogs.*"),
              lambda r: r.abort() if r.request.resource_type == "image" else r.continue_())
    pg = pagina(ctx, lenta=False)
    pg.goto(URL + f"#semana/{lunes_de(date.today()).isoformat()}", wait_until="commit")
    pg.wait_for_selector(".card", timeout=30000)
    pg.wait_for_timeout(3000)
    rotas = pg.evaluate("""[...document.querySelectorAll('#main img')].filter(i=>{const b=i.getBoundingClientRect();
        return b.bottom>0&&b.top<innerHeight&&!i.src.startsWith('data:')&&i.complete&&i.naturalWidth===0}).length""")
    check("Fallos", "Fotos que no cargan: sin iconos de imagen rota", rotas, ok=rotas == 0)
    pg.screenshot(path=str(OUT / "6_sin_fotos.png"))
    ctx.close()

    # agenda que no llega
    ctx = contexto(b, sw="block")
    ctx.route(re.compile(r".*/data/(agenda|concerts)\.json.*"), lambda r: r.fulfill(status=503, body="caída"))
    pg = pagina(ctx, lenta=False)
    pg.goto(URL, wait_until="commit")
    pg.wait_for_timeout(4000)
    txt = pg.inner_text("#main")
    check("Fallos", "Agenda que no llega: mensaje claro para recargar", ok="No se pudieron cargar los datos" in txt,
          detalle=txt[:160])
    ctx.close()

    # agenda que tarda 6 s: se ve que está cargando y luego se pinta
    ctx = contexto(b, sw="block")
    ctx.add_init_script("""const f0=window.fetch; window.fetch=(u,o)=>String(u).includes('agenda.json')?
        new Promise(r=>setTimeout(r,6000)).then(()=>f0(u,o)):f0(u,o);""")
    pg = pagina(ctx, lenta=False)
    pg.goto(URL, wait_until="commit")
    pg.wait_for_timeout(2500)
    cargando = "Cargando" in (pg.inner_text("#upd") if pg.locator("#upd").count() else "")
    try:
        esperar_datos(pg, timeout=30000)
        pintada = True
    except Exception:  # noqa: BLE001
        pintada = False
    check("Fallos", "Agenda lenta: indica 'Cargando…' y luego se pinta", ok=cargando and pintada)
    ctx.close()

    # taxonomía rota: la agenda sigue funcionando
    ctx = contexto(b, sw="block")
    ctx.route("**/data/taxonomia.json*", lambda r: r.fulfill(status=404, body=""))
    pg = pagina(ctx, lenta=False)
    pg.goto(URL + f"#semana/{lunes_de(date.today()).isoformat()}", wait_until="commit")
    try:
        pg.wait_for_selector(".card", timeout=30000)
        ok = True
    except Exception:  # noqa: BLE001
        ok = False
    check("Fallos", "Sin taxonomía de estilos: la agenda sigue funcionando", ok=ok)
    ctx.close()


# ---------------------------------------------------------------------------------------------- 5. pantallas
@escenario("UX", "Pantallas y accesibilidad")
def pantallas(b):
    for nombre, kw in (("móvil pequeño 320 px", dict(ancho=320, alto=640)),
                       ("ordenador 1366 px", dict(movil=False, ancho=1366, alto=900)),
                       ("móvil en modo oscuro", dict(oscuro=True))):
        ctx = contexto(b, **kw)
        pg = pagina(ctx, lenta=False)
        pg.goto(URL + f"#semana/{lunes_de(date.today()).isoformat()}", wait_until="commit")
        pg.wait_for_selector(".card", timeout=30000)
        pg.wait_for_timeout(1500)
        lateral = pg.evaluate("document.documentElement.scrollWidth - innerWidth")
        check("UX", f"Sin scroll lateral ({nombre})", lateral, ok=lateral <= 1, detalle=f"{lateral} px de más")
        pg.screenshot(path=str(OUT / f"7_{re.sub(r'[^a-z0-9]+', '_', nombre)}.png"))
        if "oscuro" in nombre:
            lum = pg.evaluate("""(()=>{const m=getComputedStyle(document.body).backgroundColor.match(/\\d+/g).map(Number);
                return Math.round(0.2126*m[0]+0.7152*m[1]+0.0722*m[2])})()""")
            check("UX", "Modo oscuro: fondo oscuro", lum, ok=lum < 80, grave=False)
        if nombre.startswith("móvil pequeño"):
            peq = pg.evaluate("""[...document.querySelectorAll('button,a,input,[role=button]')].filter(e=>{const b=e.getBoundingClientRect();
                return b.width>0&&b.height>0&&b.top<innerHeight&&(b.height<32||b.width<32)&&!e.closest('.card')}).map(e=>(e.id||e.className||e.tagName)+':'+Math.round(e.getBoundingClientRect().width)+'x'+Math.round(e.getBoundingClientRect().height)).slice(0,8)""")
            check("UX", "Botones con tamaño de dedo (≥ 32 px)", len(peq), ok=not peq, grave=False, detalle=", ".join(peq))
        if nombre.startswith("móvil pequeño") or "oscuro" in nombre:
            accesibilidad(pg, "modo oscuro" if "oscuro" in nombre else "modo claro")
        ctx.close()


def accesibilidad(pg, modo):
    """axe-core en semana, mes, ficha e informe: problemas graves y contraste (el contraste ya está corregido:
    si vuelve a fallar es fallo, no aviso)."""
    graves, contraste = set(), []
    for h in (f"#semana/{lunes_de(date.today()).isoformat()}", f"#dia/{date.today().isoformat()}",
              f"#mes/{date.today().isoformat()}", "ficha", "#informe"):
        if h == "ficha":
            pg.evaluate("location.hash='#concierto/'+DATA.find(r=>r.fecha>=HOY&&r.img).id")
        else:
            pg.evaluate(f"location.hash='{h}'")
        pg.wait_for_timeout(1500)
        if not pg.evaluate("typeof axe!=='undefined'"):
            pg.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js")
        v = pg.evaluate("""axe.run(document,{resultTypes:['violations']}).then(r=>r.violations
            .filter(v=>['critical','serious'].includes(v.impact)).map(v=>({id:v.id,n:v.nodes.map(n=>n.target.join(' '))})))""")
        for x in v:
            if x["id"] == "color-contrast":
                contraste += [f"{h.split('/')[0]} {t}" for t in x["n"]]
            else:
                graves.add(f"{x['id']} ({len(x['n'])})")
    check("UX", f"Contraste de color suficiente ({modo})", len(contraste), ok=not contraste,
          detalle=", ".join(contraste[:6]))
    check("UX", f"Accesibilidad (axe-core): otros problemas graves ({modo})", len(graves), ok=not graves,
          grave=False, detalle=", ".join(sorted(graves)))


@escenario("Otros", "Imágenes a través del proxy")
def proxy_imagenes(b, datos):
    ctx = contexto(b)
    pg = pagina(ctx, lenta=False)
    pg.goto(URL, wait_until="commit")
    esperar_datos(pg)
    urls = pg.evaluate("""()=>{const out={}; for(const r of DATA.filter(r=>r.fecha>=HOY&&r.img&&!r.mini)){
        const h=new URL(r.img).hostname; (out[h]=out[h]||[]).length<3&&out[h].push(fotoUrl(r.img,160,true));} return out}""")
    malos, n = [], 0
    for host, us in urls.items():
        for u in us:
            n += 1
            try:
                x = pg.request.get(u, timeout=20000)
                if not (x.ok and (x.headers.get("content-type") or "").startswith("image/")):
                    malos.append(f"{host} ({x.status})")
            except Exception as e:  # noqa: BLE001
                malos.append(f"{host} ({type(e).__name__})")
    check("Otros", "Miniaturas de las agendas a través del proxy", f"{n - len(malos)} de {n}",
          ok=len(malos) <= max(1, n // 10), grave=False, detalle=", ".join(malos[:6]))
    ctx.close()


# ---------------------------------------------------------------------------------------------- informe
def informe() -> int:
    cs = R["comprobaciones"]
    R["errores_js"] = sorted(set(R["errores_js"]))
    check("Fallos", "Errores de JavaScript en todo el recorrido", len(R["errores_js"]), ok=not R["errores_js"],
          detalle=" | ".join(R["errores_js"][:3]))
    consola = [c for c in set(R["consola"]) if "Failed to load resource" not in c]
    check("Otros", "Errores en la consola", len(consola), ok=not consola, grave=False, detalle=" | ".join(consola[:3]))
    tot = {e: sum(1 for c in cs if c["estado"] == e) for e in ("ok", "aviso", "fallo")}
    R["resumen"] = tot
    icono = {"ok": "✅", "aviso": "⚠️", "fallo": "❌"}
    lin = [f"# Validación de la web publicada — {R['fecha']}", "",
           f"{URL} · código de main {R.get('version_main', '?')} · móvil con 4G lenta y CPU 6x", "",
           f"**{tot['ok']} bien · {tot['aviso']} avisos · {tot['fallo']} fallos**", ""]
    for cat in CATEGORIAS:
        de = [c for c in cs if c["categoria"] == cat]
        if not de:
            continue
        lin += [f"## {cat}", "", "| | Comprobación | Valor | Umbral | Detalle |", "|---|---|---|---|---|"]
        for c in sorted(de, key=lambda c: ("fallo", "aviso", "ok").index(c["estado"])):
            v = c["valor"] if c["valor"] is not None else "—"
            lin.append(f"| {icono[c['estado']]} | {c['nombre']} | {str(v)[:60]} | {c['umbral']} | "
                       f"{c['detalle'][:200].replace('|', '/')} |")
        lin.append("")
    md = "\n".join(lin)
    (OUT / "informe.md").write_text(md, encoding="utf-8")
    (OUT / "resultados.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(md + "\n")
    print(f"\n{tot}")
    return 1 if tot["fallo"] else 0


def main() -> int:
    random.seed()  # fechas y conciertos distintos en cada validación: sin cachés calentadas por la anterior
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None)
        datos = publicacion(b) or []
        recorrido(b)
        navegacion_fechas(b)
        if datos:
            enlaces_directos(b, datos)
            averias(b, datos)
            proxy_imagenes(b, datos)
            en_frio(b, datos)
            peor_caso(b, datos)
        sin_conexion(b)
        pantallas(b)
        b.close()
    return informe()


if __name__ == "__main__":
    sys.exit(main())
