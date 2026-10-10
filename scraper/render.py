"""Lectura con un navegador real (Playwright/Chromium) de las webs que montan su agenda con JavaScript.

Mismas reglas que el lector normal (scraper/fetch.py): se identifica con el mismo User-Agent, respeta el robots.txt de
la página y el de cada petición que hace la página (las que robots.txt no permite se cortan, no se saltan), y el
mismo ritmo por servidor. No descarga imágenes, vídeo ni tipografías: solo hace falta el texto de la agenda."""
from __future__ import annotations

import os
import queue
import threading
import time
from concurrent.futures import Future
from urllib.parse import urlsplit

from .fetch import Fetcher, RobotsBlocked, RobotsUnreachable

_NO_HACE_FALTA = {"image", "media", "font"}


class RenderNoDisponible(Exception):
    """Playwright o su navegador no están instalados en esta máquina."""


class Navegador:
    """Un Chromium para toda la ejecución (arrancarlo cuesta ~1 s); se cierra con cerrar().

    Playwright (su API síncrona) solo se puede usar desde el hilo que lo arrancó, y las fuentes se leen en varios
    hilos: Festify abría el navegador en el suyo e Intruso y Moe, desde otro, fallaban con "Cannot switch to a
    different thread" (8-10/10/2026). Por eso todo lo del navegador va por un hilo propio, venga de donde venga la
    petición (una cola: una página cada vez, como antes con el cerrojo)."""

    def __init__(self, fetcher: Fetcher):
        self.fetcher = fetcher
        self._pw = self._browser = None
        self._cola: queue.Queue = queue.Queue()
        self._hilo: threading.Thread | None = None
        self._lock = threading.Lock()
        self.cortadas: list[str] = []  # peticiones que robots.txt no permite y no se hicieron (diagnóstico)

    def _en_hilo(self, f, *a, **k):
        """Ejecuta f en el hilo del navegador y devuelve su resultado (o lanza su excepción)."""
        if threading.current_thread() is self._hilo:
            return f(*a, **k)
        with self._lock:
            if self._hilo is None or not self._hilo.is_alive():
                self._hilo = threading.Thread(target=self._bucle, name="navegador", daemon=True)
                self._hilo.start()
        fut: Future = Future()
        self._cola.put((fut, f, a, k))
        return fut.result()

    def _bucle(self) -> None:
        while True:
            fut, f, a, k = self._cola.get()
            if not fut.set_running_or_notify_cancel():
                continue
            try:
                fut.set_result(f(*a, **k))
            except BaseException as e:  # noqa: BLE001 - se devuelve a quien lo pidió
                fut.set_exception(e)

    def _arrancar(self):
        return self._en_hilo(self._arrancar_aqui)

    def _arrancar_aqui(self):
        if self._browser is None:
            try:
                from playwright.sync_api import sync_playwright
            except ImportError as e:
                raise RenderNoDisponible("Playwright no está instalado") from e
            try:
                self._pw = sync_playwright().start()
                # NAVEGADOR: ruta a un Chromium ya instalado (en local); en GitHub, el que instala Playwright
                exe = os.environ.get("NAVEGADOR")
                self._browser = self._pw.chromium.launch(headless=True, args=["--disable-background-networking", "--disable-component-update"], **({"executable_path": exe} if exe else {}))
            except Exception as e:  # noqa: BLE001 - sin navegador descargado
                self._cerrar_aqui()
                raise RenderNoDisponible(f"no se pudo abrir el navegador: {e}") from e
        return self._browser

    def _ruta(self, route) -> None:
        req = route.request
        if req.resource_type in _NO_HACE_FALTA:
            route.abort()
            return
        url = req.url
        if not url.startswith("http"):
            route.continue_()
            return
        if not self.fetcher.robots_allows(url):
            self.cortadas.append(url)
            route.abort()
            return
        route.continue_()

    def html(self, url: str, *, esperar: str | None = None, timeout: float = 30) -> str:
        """HTML de la página ya montada. `esperar`: selector CSS que indica que la agenda ya está en la página."""
        f = self.fetcher
        if not f.robots_allows(url):
            if f._host(url).robots_status.startswith("inaccesible"):
                raise RobotsUnreachable(f"web inaccesible al leer robots.txt: {f._host(url).robots_status}")
            raise RobotsBlocked(url)
        return self._en_hilo(self._html, url, esperar, timeout)

    def _html(self, url: str, esperar: str | None, timeout: float) -> str:
        f = self.fetcher
        browser = self._arrancar_aqui()
        st, rt = f._host(url), f._ritmo(url)
        with rt.lock:  # solo el turno: durante la carga la página pide robots.txt de otros nombres del servidor
            f._wait(rt, st)
        f.requests_count += 1
        ctx = browser.new_context(user_agent=f.user_agent, locale="es-ES", timezone_id="Europe/Madrid",
                                  java_script_enabled=True)
        try:
            page = ctx.new_page()
            page.route("**/*", self._ruta)
            t0 = time.monotonic()
            resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            if resp is not None and resp.status >= 400:
                raise RuntimeError(f"{resp.status} al abrir {urlsplit(url).netloc}")
            if esperar:
                page.wait_for_selector(esperar, timeout=timeout * 1000)
            else:
                try:
                    page.wait_for_load_state("networkidle", timeout=min(timeout, 15) * 1000)
                except Exception:  # noqa: BLE001 - webs con conexiones abiertas siempre: vale lo que hay
                    pass
            st.latencia = time.monotonic() - t0
            return page.content()
        finally:
            ctx.close()
            rt.last = time.monotonic()

    def cerrar(self) -> None:
        if self._hilo is not None and self._hilo.is_alive():
            self._en_hilo(self._cerrar_aqui)
        else:
            self._cerrar_aqui()

    def _cerrar_aqui(self) -> None:
        for x, m in ((self._browser, "close"), (self._pw, "stop")):
            try:
                if x is not None:
                    getattr(x, m)()
            except Exception:  # noqa: BLE001
                pass
        self._browser = self._pw = None


def navegador_de(fetcher: Fetcher) -> Navegador:
    """Un navegador por lector (se abre la primera vez que hace falta y se cierra al terminar el programa)."""
    nav = getattr(fetcher, "_navegador", None)
    if nav is None:
        import atexit
        nav = fetcher._navegador = Navegador(fetcher)
        atexit.register(nav.cerrar)
    return nav
