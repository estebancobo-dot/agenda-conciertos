"""Descargador educado: respeta robots.txt, 1 petición cada 2 s por web y User-Agent identificable."""
from __future__ import annotations

import threading
import time
import urllib.robotparser
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import requests

USER_AGENT = (
    "AgendaConciertosMadridBot/2.0 (+https://github.com/estebancobo-dot/agenda-conciertos; "
    "agenda personal sin animo de lucro)"
)
MIN_INTERVAL = 2.0  # segundos entre peticiones a la misma web


class RobotsBlocked(Exception):
    """robots.txt prohíbe rastrear esta URL."""


@dataclass
class HostState:
    lock: threading.Lock = field(default_factory=threading.Lock)
    last: float = 0.0
    robots: urllib.robotparser.RobotFileParser | None = None
    robots_checked: bool = False


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

    def _host(self, url: str) -> HostState:
        host = urlsplit(url).netloc.lower()
        with self._hosts_lock:
            return self._hosts.setdefault(host, HostState())

    def _wait(self, st: HostState) -> None:
        delta = time.monotonic() - st.last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        st.last = time.monotonic()

    def robots_allows(self, url: str) -> bool:
        st = self._host(url)
        with st.lock:
            if not st.robots_checked:
                parts = urlsplit(url)
                robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
                rp = urllib.robotparser.RobotFileParser()
                try:
                    self._wait(st)
                    r = self.session.get(robots_url, timeout=self.timeout)
                    if r.status_code in (401, 403):
                        rp.disallow_all = True
                    elif r.status_code >= 400:
                        rp.allow_all = True
                    else:
                        rp.parse(r.text.splitlines())
                except requests.RequestException:
                    # Sin robots.txt accesible: se asume permitido (norma habitual de los rastreadores)
                    rp.allow_all = True
                st.robots = rp
                st.robots_checked = True
            return st.robots.can_fetch(self.user_agent, url)

    def get(self, url: str, *, check_robots: bool = True, use_cache: bool = True, **kw) -> str:
        if use_cache and url in self._cache:
            return self._cache[url]
        if check_robots and not self.robots_allows(url):
            raise RobotsBlocked(url)
        st = self._host(url)
        with st.lock:
            self._wait(st)
            r = self.session.get(url, timeout=self.timeout, **kw)
        r.raise_for_status()
        if not r.encoding or r.encoding.lower() == "iso-8859-1":
            r.encoding = r.apparent_encoding or "utf-8"
        text = r.text
        if use_cache:
            self._cache[url] = text
        return text

    def get_json(self, url: str, **kw):
        import json
        return json.loads(self.get(url, **kw))
