"""Descargador educado: respeta robots.txt y el ritmo que admite cada web, con User-Agent identificable.

Ritmo por web (las peticiones a una misma web van siempre de una en una):
- entre el final de una respuesta y la siguiente petición, `min_interval` (1 s para webs, el límite publicado
  para las API) o el Crawl-delay de su robots.txt si es mayor; un servidor lento recibe así menos peticiones;
- ante 429 o 503 se espera lo que diga Retry-After (o 10 s, 20 s…), se reintenta y se duplica la pausa de esa web.
"""
from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from .robots import Robots

import requests

USER_AGENT = (
    "AgendaConciertosMadridBot/2.0 (+https://github.com/estebancobo-dot/agenda-conciertos; "
    "agenda personal sin animo de lucro)"
)
MIN_INTERVAL = 1.0  # segundos mínimos entre peticiones a la misma web (webs sin límite publicado)
REINTENTOS = 3      # ante 429/503


class RobotsBlocked(Exception):
    """robots.txt prohíbe rastrear esta URL."""


class AntiBotBlocked(Exception):
    """La web responde con una página de captcha o verificación anti-bots en lugar del contenido."""


_ANTIBOT = re.compile(r"sgcaptcha|imunify-bot-check|cf-chl-|challenge-platform|Just a moment\.\.\.|"
                      r"captcha-delivery|Attention Required! \| Cloudflare", re.I)


def es_antibot(text: str) -> bool:
    return len(text) < 20000 and bool(_ANTIBOT.search(text))


def retry_after(valor: str | None, defecto: float) -> float:
    """Segundos de la cabecera Retry-After (solo el formato numérico), entre 1 y 120."""
    try:
        return min(max(float(valor), 1.0), 120.0)
    except (TypeError, ValueError):
        return defecto


class RobotsUnreachable(Exception):
    """No se pudo leer robots.txt (error de red o 5xx): por norma no se rastrea la web."""


@dataclass
class HostState:
    lock: threading.Lock = field(default_factory=threading.Lock)
    last: float = 0.0
    robots: Robots | None = None
    robots_checked: bool = False
    robots_status: str = ""
    delay: float = 0.0       # Crawl-delay de robots.txt
    latencia: float = 0.0    # lo que tardó la última respuesta
    freno: float = 0.0       # pausa extra tras un 429/503


class Fetcher:
    def __init__(self, user_agent: str = USER_AGENT, min_interval: float = MIN_INTERVAL, timeout: int = 30):
        self.user_agent = user_agent
        self.min_interval = min_interval
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.5",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
        })
        self._hosts: dict[str, HostState] = {}
        self._hosts_lock = threading.Lock()
        self._cache: dict[str, str] = {}
        self.requests_count = 0
        self.last_headers: dict[str, dict] = {}  # cabeceras de la última respuesta por URL (diagnóstico)

    def _host(self, url: str) -> HostState:
        host = urlsplit(url).netloc.lower()
        with self._hosts_lock:
            return self._hosts.setdefault(host, HostState())

    def _wait(self, st: HostState) -> None:
        interval = max(self.min_interval, st.delay, st.freno)
        delta = time.monotonic() - st.last
        if delta < interval:
            time.sleep(interval - delta)
        st.last = time.monotonic()

    def robots_status(self, url: str) -> str:
        """Estado del robots.txt de la web: 'ok', 'sin_robots' (4xx) o 'inaccesible' (5xx / error de red)."""
        self.robots_allows(url)
        return self._host(url).robots_status

    def robots_allows(self, url: str) -> bool:
        """Aplica robots.txt según RFC 9309: 4xx = sin restricciones; 5xx o error de red = no rastrear."""
        st = self._host(url)
        with st.lock:
            if not st.robots_checked:
                parts = urlsplit(url)
                robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
                rp = Robots()
                try:
                    self._wait(st)
                    r = self.session.get(robots_url, timeout=self.timeout)
                    if 400 <= r.status_code < 500:
                        rp.allow_all = True
                        st.robots_status = f"sin_robots ({r.status_code})"
                    elif r.status_code >= 500:
                        rp.disallow_all = True
                        st.robots_status = f"inaccesible ({r.status_code})"
                    else:
                        rp = Robots(r.text)
                        st.robots_status = "ok"
                        delay = rp.crawl_delay(self.user_agent)
                        if delay:
                            st.delay = max(self.min_interval, float(delay))
                except requests.RequestException as e:
                    rp.disallow_all = True
                    st.robots_status = f"inaccesible ({type(e).__name__})"
                st.robots = rp
                st.robots_checked = True
            return st.robots.can_fetch(self.user_agent, url)

    def get(self, url: str, *, check_robots: bool = True, use_cache: bool = True, method: str = "GET", **kw) -> str:
        key = url + repr(sorted(kw.items())) if kw else url
        if use_cache and key in self._cache:
            return self._cache[key]
        if check_robots and not self.robots_allows(url):
            if self._host(url).robots_status.startswith("inaccesible"):
                raise RobotsUnreachable(f"web inaccesible al leer robots.txt: {self._host(url).robots_status}")
            raise RobotsBlocked(url)
        st = self._host(url)
        with st.lock:
            for intento in range(REINTENTOS + 1):
                self._wait(st)
                self.requests_count += 1
                t0 = time.monotonic()
                r = self.session.request(method, url, timeout=self.timeout, **kw)
                st.latencia = time.monotonic() - t0
                st.last = time.monotonic()  # la pausa cuenta desde que termina la respuesta
                if r.status_code not in (429, 503) or intento == REINTENTOS:
                    break
                espera = retry_after(r.headers.get("Retry-After"), 10.0 * (intento + 1))
                st.freno = min(max(st.freno * 2, self.min_interval * 2), 30.0)
                time.sleep(espera)
            self.after_response(r)
        self.last_headers[url] = {"status": r.status_code, **{k: v for k, v in r.headers.items()
                                                             if k.lower().startswith(("x-", "retry", "ratelimit"))}}
        r.raise_for_status()
        if not r.encoding or r.encoding.lower() == "iso-8859-1":
            r.encoding = r.apparent_encoding or "utf-8"
        text = r.text
        if es_antibot(text):
            raise AntiBotBlocked(f"{url}: la web responde con un captcha/verificación anti-bots")
        if use_cache:
            self._cache[key] = text
        return text

    def after_response(self, r) -> None:
        """Gancho para ajustar el ritmo según las cabeceras de la API (p. ej. Discogs)."""

    def get_json(self, url: str, **kw):
        import json
        return json.loads(self.get(url, **kw))
