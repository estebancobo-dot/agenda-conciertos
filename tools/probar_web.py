"""Prueba de uso de la web publicada, en vivo, con un navegador real (Chromium) que imita un móvil con 4G lenta.

No es una prueba de la página estática: recorre la web como una persona y mide lo que tarda cada cosa:
  1. primera visita (sin nada guardado) y segunda visita (con la copia del service worker);
  2. vista semana: pintar, miniaturas visibles cargadas a los 0,5/1/2/4 s, pasar semanas, bajar hasta el final;
  3. abrir un concierto (datos y foto) y volver: ¿se queda donde estabas?;
  4. filtros: abrir, marcar un género, elegir un estilo, aplicar, restablecer y quitar filtros;
  5. vista mes; tareas largas de JavaScript (bloqueos de más de 50 ms) durante todo el recorrido.

Uso: python tools/probar_web.py URL SALIDA   → SALIDA/resultados.json y capturas PNG.
"""
from __future__ import annotations

import json
import os  # noqa: F401
import sys
import time
from datetime import date, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://estebancobo-dot.github.io/agenda-conciertos/"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "pruebas")
OUT.mkdir(parents=True, exist_ok=True)
R: dict = {"url": URL, "fecha": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), "pasos": {}, "errores": []}

# 4G lenta (la de Lighthouse para móvil) y CPU 4 veces más lenta que la del servidor
RED = {"offline": False, "latency": 150, "downloadThroughput": 1.6 * 1024 * 1024 / 8,
       "uploadThroughput": 750 * 1024 / 8}
INICIO = """
window.__lt=[]; try{new PerformanceObserver(l=>l.getEntries().forEach(e=>window.__lt.push([Math.round(e.startTime),Math.round(e.duration)]))).observe({type:'longtask',buffered:true});}catch(e){}
"""


def ms(t0: float) -> int:
    return round((time.monotonic() - t0) * 1000)


def paso(nombre: str, **datos):
    R["pasos"][nombre] = datos
    print(nombre, json.dumps(datos, ensure_ascii=False)[:400], flush=True)


def miniaturas(pg) -> dict:
    """Miniaturas en pantalla: cuántas hay y cuántas ya se ven."""
    return pg.evaluate("""()=>{const v=[...document.querySelectorAll('img.thumb')].filter(i=>{const b=i.getBoundingClientRect();return b.bottom>0&&b.top<innerHeight});
      return {visibles:v.length,cargadas:v.filter(i=>i.complete&&i.naturalWidth>0).length,
              todas:document.querySelectorAll('img.thumb').length,
              todas_cargadas:[...document.querySelectorAll('img.thumb')].filter(i=>i.complete&&i.naturalWidth>0).length}}""")


def esperar_miniaturas(pg) -> list:
    out, t0 = [], time.monotonic()
    for t in (0.5, 1, 2, 4, 8):
        pg.wait_for_timeout(max(0, int((t - (time.monotonic() - t0)) * 1000)))
        m = miniaturas(pg)
        out.append({"s": t, **m})
    return out


def nuevo_contexto(b, persist=None):
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True,
                        has_touch=True, locale="es-ES", timezone_id="Europe/Madrid",
                        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
                                   "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1 AgendaPrueba",
                        service_workers="allow")
    ctx.add_init_script(INICIO)
    return ctx


def lento(pg):
    cdp = pg.context.new_cdp_session(pg)
    cdp.send("Network.enable")
    cdp.send("Network.emulateNetworkConditions", RED)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    return cdp


def recorrido(b):
    imgs: list = []
    ctx = nuevo_contexto(b)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: R["errores"].append(str(e)[:300]))
    fallos: list = []
    pg.on("response", lambda x: x.request.resource_type == "image" and x.status >= 400 and fallos.append(
        {"status": x.status, "url": x.url[:160]}))
    pg.on("requestfailed", lambda q: q.resource_type == "image" and fallos.append(
        {"error": (q.failure or "")[:80], "url": q.url[:160]}))
    pg.on("requestfinished", lambda q: q.resource_type == "image" and imgs.append(
        {"url": q.url[:120], "ms": round(q.timing["responseEnd"]) if q.timing else None}))
    lento(pg)

    # 1. primera visita
    t0 = time.monotonic()
    pg.goto(URL, wait_until="commit")
    pg.wait_for_function("document.getElementById('upd') && /conciertos/.test(document.getElementById('upd').textContent)",
                         timeout=90000)
    listo = ms(t0)
    pg.wait_for_load_state("networkidle", timeout=90000)
    paso("1_primera_visita", datos_y_pintado_ms=listo, red_quieta_ms=ms(t0),
         bytes_transferidos=pg.evaluate("performance.getEntriesByType('resource').reduce((a,e)=>a+(e.transferSize||0),0)"))
    pg.screenshot(path=str(OUT / "1_inicio.png"))

    # 2. semana
    lunes = date.today() - timedelta(days=date.today().weekday())
    t0 = time.monotonic()
    pg.evaluate(f"location.hash='#semana/{lunes.isoformat()}'")
    pg.wait_for_selector(".card", timeout=30000)
    paso("2_semana_pintar", ms=ms(t0), tarjetas=pg.locator(".card").count(), miniaturas=esperar_miniaturas(pg))
    pg.screenshot(path=str(OUT / "2_semana.png"))
    # bajar hasta el final a ritmo de persona
    faltan = []
    alto = pg.evaluate("document.body.scrollHeight")
    for y in range(0, alto, 700):
        pg.mouse.wheel(0, 700)
        pg.wait_for_timeout(350)
        m = miniaturas(pg)
        faltan.append(m["visibles"] - m["cargadas"])
    paso("2_semana_scroll", pantallas=len(faltan), miniaturas_sin_cargar_por_pantalla=faltan)
    # semana siguiente (x3)
    tiempos = []
    for _ in range(3):
        pg.evaluate("scrollTo(0,0)")
        t0 = time.monotonic()
        pg.click("[data-nav='7']")
        pg.wait_for_timeout(50)
        pg.wait_for_function("document.querySelectorAll('.card').length>0", timeout=30000)
        tiempos.append({"pintar_ms": ms(t0), "miniaturas_1s": (pg.wait_for_timeout(1000) or miniaturas(pg))})
    paso("2_semana_siguiente", pasos=tiempos)

    # 3. detalle y volver
    pg.evaluate(f"location.hash='#semana/{lunes.isoformat()}'")
    pg.wait_for_selector(".card")
    cards = pg.locator(".card")
    n = min(12, cards.count() - 1)
    cards.nth(n).scroll_into_view_if_needed()
    pg.wait_for_timeout(500)
    y_antes = pg.evaluate("scrollY")
    art = cards.nth(n).locator(".art").inner_text()
    cid = cards.nth(n).get_attribute("data-id")
    t0 = time.monotonic()
    cards.nth(n).click()
    pg.wait_for_selector(".dt h2", timeout=30000)
    datos_ms = ms(t0)
    foto = pg.evaluate("!!document.querySelector('.hero img')")
    foto_ms = None
    if foto:
        try:
            pg.wait_for_function("(()=>{const i=document.querySelector('.hero img');return !i||(i.complete&&i.naturalWidth>0)})()",
                                 timeout=20000)
            foto_ms = ms(t0)
        except Exception:
            foto_ms = "más de 20 s"
    pg.screenshot(path=str(OUT / "3_detalle.png"))
    t0 = time.monotonic()
    pg.evaluate("history.back()")
    pg.wait_for_function("location.hash.startsWith('#semana') && document.querySelectorAll('.card').length>0")
    volver_ms = ms(t0)
    pg.wait_for_timeout(600)
    y_despues = pg.evaluate("scrollY")
    visible = pg.evaluate("""(a)=>{const c=document.querySelector(`.card[data-id="${a}"]`);
       if(!c) return false; const b=c.getBoundingClientRect(); return b.top>-10&&b.top<innerHeight-40}""", cid)
    pg.screenshot(path=str(OUT / "3_volver.png"))
    # otra vez, ahora con el botón "‹ Volver" de la ficha
    cards = pg.locator(".card")
    m = min(20, cards.count() - 1)
    cards.nth(m).scroll_into_view_if_needed()
    pg.wait_for_timeout(400)
    art2 = cards.nth(m).get_attribute("data-id")
    cards.nth(m).click()
    pg.wait_for_selector(".dt h2", timeout=30000)
    pg.click("a.back")
    pg.wait_for_selector(".card")
    pg.wait_for_timeout(600)
    visible2 = pg.evaluate("""(a)=>{const c=document.querySelector(`.card[data-id="${a}"]`);
       if(!c) return false; const b=c.getBoundingClientRect(); return b.top>-10&&b.top<innerHeight-40}""", art2)
    paso("3_detalle", artista=art, datos_ms=datos_ms, foto=foto, foto_ms=foto_ms, volver_ms=volver_ms,
         scroll_antes=y_antes, scroll_despues=y_despues, sigue_viendo_el_concierto=visible,
         boton_volver_sigue_viendo=visible2)

    # 3b. fichas de conciertos lejanos (sin precarga), de cada origen de foto
    casos = pg.evaluate("""()=>{const hoy=new Date().toISOString().slice(0,10); const out={};
      const tipo=u=>!u?'sin foto':/discogs/.test(u)?'discogs':/conciertos\.club/.test(u)?'conciertos.club':/wikimedia/.test(u)?'wikimedia':/madridenvivo/.test(u)?'madridenvivo':'otros';
      for(const r of DATA.filter(r=>r.fecha>hoy).reverse()){const t=tipo(r.img); if(!out[t]) out[t]=r.id;} return out}""")
    fichas = {}
    for t, cid in casos.items():
        t0 = time.monotonic()
        pg.evaluate(f"location.hash='#concierto/{cid}'")
        pg.wait_for_selector(".dt h2", timeout=30000)
        d = ms(t0)
        f = None
        if pg.evaluate("!!document.querySelector('.hero img')"):
            try:
                pg.wait_for_function("(()=>{const i=document.querySelector('.hero img');return !i||(i.complete&&i.naturalWidth>0)})()",
                                     timeout=20000)
                f = ms(t0)
            except Exception:
                f = "más de 20 s"
        fichas[t] = {"datos_ms": d, "foto_ms": f}
    paso("3b_fichas_por_origen_de_foto", **fichas)

    # 4. filtros
    pg.evaluate("scrollTo(0,0)")
    t0 = time.monotonic()
    pg.click("#fgen")
    pg.wait_for_selector(".sheet")
    abrir = ms(t0)
    pg.screenshot(path=str(OUT / "4_filtros.png"))
    t0 = time.monotonic()
    pg.locator("[data-g='fuera de foco']").click()
    pg.wait_for_timeout(30)
    marcar = ms(t0)
    pg.locator("[data-ver='rock y metal']").click()
    t0 = time.monotonic()
    est = pg.locator("[data-inc='rock y metal'] button.est").first
    est_nombre = est.inner_text()
    est.click()
    pg.wait_for_timeout(30)
    estilo = ms(t0)
    pg.screenshot(path=str(OUT / "4_filtros_estilo.png"))
    t0 = time.monotonic()
    pg.click("#sclose")
    pg.wait_for_function("!document.querySelector('.sheet')")
    aplicar = ms(t0)
    t0 = time.monotonic()
    pg.click("#freset") if pg.locator("#freset").count() else None
    pg.wait_for_timeout(30)
    quitar = ms(t0)
    t0 = time.monotonic()
    pg.click("#fgen")
    pg.wait_for_selector(".sheet")
    pg.click("#sdef")
    pg.wait_for_timeout(30)
    restablecer = ms(t0)
    pg.click("#sclose")
    t0 = time.monotonic()
    pg.locator("[data-chip='blues']").click()
    pg.wait_for_timeout(30)
    chip = ms(t0)
    pg.locator("[data-chip='blues']").click()
    paso("4_filtros", abrir_ms=abrir, marcar_genero_ms=marcar, elegir_estilo_ms=estilo, estilo=est_nombre,
         aplicar_ms=aplicar, quitar_filtros_ms=quitar, restablecer_ms=restablecer, chip_ms=chip)

    # 5. mes
    t0 = time.monotonic()
    pg.evaluate(f"location.hash='#mes/{(date.today() + timedelta(days=10)).isoformat()}'")
    pg.wait_for_selector(".cal")
    mes_ms = ms(t0)
    dia = pg.locator("[data-mdia]:not(.zero):not(.sel)").last
    t0 = time.monotonic()
    dia.click()
    pg.wait_for_function("document.querySelector('#mlista')!==null")
    pg.wait_for_timeout(30)
    paso("5_mes", ms=mes_ms, elegir_dia_ms=ms(t0), lista_debajo=pg.locator("#mlista .card").count())
    pg.screenshot(path=str(OUT / "5_mes.png"), full_page=True)

    tiempos = pg.evaluate("window.__tiempos||[]")
    por: dict = {}
    for q, t in tiempos:
        por.setdefault(q, []).append(t)
    paso("6_pintado_interno_ms", **{q: {"n": len(v), "mediana": sorted(v)[len(v) // 2], "max": max(v)} for q, v in por.items()})
    lt = pg.evaluate("window.__lt||[]")
    paso("6_bloqueos_js", tareas_largas=len(lt), total_ms=sum(d for _, d in lt), peores=sorted(lt, key=lambda x: -x[1])[:8])
    dur = [i["ms"] for i in imgs if isinstance(i.get("ms"), (int, float)) and i["ms"] > 0]
    paso("7_imagenes", pedidas=len(imgs), mediana_ms=sorted(dur)[len(dur) // 2] if dur else None,
         lentas=[i for i in imgs if (i.get("ms") or 0) > 3000][:10],
         hosts=sorted({i["url"].split("/")[2] for i in imgs}))

    paso("7_imagenes_fallidas", total=len(fallos), ejemplos=fallos[:15])
    # cómo responde wsrv.nl con cada servidor de imágenes de las agendas
    from urllib.parse import quote
    diag = {}
    for u in ("https://doc.conciertos.club/doc/c/2026/luciaferna_20260930.jpg",
              "https://conciertos.club/doc/c/2025/c_losmiserables.jpg",
              "https://madridenvivo.com/wp-content/uploads/2026/09/06-DE-ESTRAPERLO-1-scaled.jpg",
              "https://i.discogs.com/ykcwyCltCUe0YKUKr7M6Wq6KKBBrypCgTi40Qr10HmU/rs:fit/g:sm/q:90/h:684/w:463/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWltYWdlcy9BLTEyODgwOTItMTYyNTI3NDkzNy01Mjg4LmpwZWc.jpeg",
              "https://images.sk-static.com/images/media/profile_images/artists/10317821/huge_avatar"):
        t0 = time.monotonic()
        try:
            x = pg.request.get(f"https://wsrv.nl/?url={quote(u, safe='')}&w=160&h=160&fit=cover&output=webp&q=70",
                               timeout=30000)
            diag[u.split("/")[2]] = {"status": x.status, "ms": ms(t0), "bytes": len(x.body()),
                                     "tipo": x.headers.get("content-type"), "texto": x.text()[:120] if x.status >= 400 else ""}
        except Exception as e:  # noqa: BLE001
            diag[u.split("/")[2]] = {"error": str(e)[:120]}
    paso("9_wsrv", **diag)
    # segunda visita (misma sesión: caché del navegador y del service worker)
    t0 = time.monotonic()
    pg.goto(URL + "#semana/" + lunes.isoformat(), wait_until="commit")
    pg.wait_for_selector(".card", timeout=60000)
    paso("8_segunda_visita", pintar_ms=ms(t0), miniaturas=esperar_miniaturas(pg))
    ctx.close()


with sync_playwright() as p:
    import os
    b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None)
    try:
        recorrido(b)
    except Exception as e:  # noqa: BLE001
        R["errores"].append(f"recorrido interrumpido: {type(e).__name__}: {str(e)[:400]}")
    b.close()
(OUT / "resultados.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
print("errores:", R["errores"])
