"""Fetcher de pruebas: sirve HTML guardado en lugar de acceder a internet."""
from pathlib import Path


class HTTP404(Exception):
    pass


class FakeFetcher:
    def __init__(self, mapping: dict[str, Path | str]):
        self.mapping = mapping
        self.requests_count = 0
        self.urls = []

        class _S:
            headers = {}
        self.session = _S()

    def get(self, url, **kw):
        self.requests_count += 1
        self.urls.append(url)
        key = url
        if kw.get("method") == "POST":
            key = url + "#" + str(kw.get("data"))
        for k, v in self.mapping.items():
            if k == key or (k.endswith("*") and key.startswith(k[:-1])):
                if callable(v):
                    return v(url, kw)
                return Path(v).read_text(encoding="utf-8")
        raise HTTP404(f"404 Client Error: Not Found for url: {url}")

    def olvidar(self, url):
        """Como Fetcher.olvidar (antes de reintentar una web): aquí no hay nada guardado que olvidar."""

    def robots_status(self, url):
        return "ok"

    def robots_allows(self, url):
        return True
