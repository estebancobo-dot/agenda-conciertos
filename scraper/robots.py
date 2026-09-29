"""Intérprete de robots.txt según RFC 9309, con comodines '*' y '$' (el módulo estándar de Python no los entiende).

- Se aplica el grupo cuyo User-agent coincide con el nuestro; si no hay, el grupo '*'.
- Gana la regla más larga que coincide; a igual longitud, Allow.
"""
from __future__ import annotations

import re
from urllib.parse import unquote, urlsplit


class Robots:
    def __init__(self, texto: str = "", allow_all: bool = False, disallow_all: bool = False):
        self.allow_all = allow_all
        self.disallow_all = disallow_all
        self.grupos: list[tuple[list[str], list[tuple[bool, str]], float | None]] = []
        if texto:
            self._parse(texto)

    def _parse(self, texto: str) -> None:
        agentes, reglas, delay = [], [], None
        en_reglas = False
        for linea in texto.splitlines():
            linea = linea.split("#", 1)[0].strip()
            if ":" not in linea:
                continue
            k, v = [x.strip() for x in linea.split(":", 1)]
            k = k.lower()
            if k == "user-agent":
                if en_reglas:  # empieza un grupo nuevo
                    self.grupos.append((agentes, reglas, delay))
                    agentes, reglas, delay, en_reglas = [], [], None, False
                agentes.append(v.lower())
            elif k in ("allow", "disallow"):
                en_reglas = True
                if v or k == "allow":
                    reglas.append((k == "allow", v))
            elif k == "crawl-delay":
                en_reglas = True
                try:
                    delay = float(v)
                except ValueError:
                    pass
        if agentes:
            self.grupos.append((agentes, reglas, delay))

    def _grupo(self, ua: str):
        ua = ua.lower()
        token = re.split(r"[/ ]", ua)[0]
        especificos = [g for g in self.grupos if any(a != "*" and a in token for a in g[0])]
        if especificos:
            return especificos
        return [g for g in self.grupos if "*" in g[0]]

    @staticmethod
    def _coincide(patron: str, ruta: str) -> bool:
        rx = "^" + re.escape(patron).replace(r"\*", ".*")
        if rx.endswith(r"\$"):
            rx = rx[:-2] + "$"
        return re.match(rx, ruta) is not None

    def can_fetch(self, ua: str, url: str) -> bool:
        if self.disallow_all:
            return False
        if self.allow_all:
            return True
        parts = urlsplit(url)
        ruta = unquote(parts.path or "/") + (("?" + parts.query) if parts.query else "")
        mejor = None  # (longitud, allow)
        for _, reglas, _ in self._grupo(ua):
            for allow, patron in reglas:
                if self._coincide(unquote(patron), ruta):
                    cand = (len(patron), allow)
                    if mejor is None or cand[0] > mejor[0] or (cand[0] == mejor[0] and allow):
                        mejor = cand
        return True if mejor is None else mejor[1]

    def crawl_delay(self, ua: str) -> float | None:
        for _, _, d in self._grupo(ua):
            if d:
                return d
        return None
