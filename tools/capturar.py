"""Captura el HTML real de las fuentes para escribir y verificar parsers (se ejecuta en GitHub Actions).

Uso: python tools/capturar.py tools/capturar_urls.txt capturas/
Cada línea del fichero: <nombre> <url>
"""
import json
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scraper.fetch import Fetcher, RobotsBlocked  # noqa: E402


def main(lista: str, salida: str) -> None:
    out = Path(salida)
    out.mkdir(parents=True, exist_ok=True)
    f = Fetcher(timeout=60)
    items = []
    for line in Path(lista).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            parts = line.split(None, 2)
            items.append((parts[0], parts[1], parts[2] if len(parts) > 2 else None))
    by_host = defaultdict(list)
    for name, url, post in items:
        by_host[urlsplit(url).netloc].append((name, url, post))
    index = {}

    def run(group):
        for name, url, post in group:
            rec = {"url": url}
            try:
                if post:
                    txt = f.get(url, method="POST", data=post, headers={"Content-Type": "application/json"})
                else:
                    # la API de MusicBrainz (/ws/2) es para uso programático: misma excepción documentada que
                    # en scraper/musicbrainz.py (su robots.txt se refiere al rastreo de las páginas web)
                    txt = f.get(url, check_robots=not url.endswith('robots.txt') and "musicbrainz.org/ws/" not in url,
                                headers={"Accept": "application/json"} if "musicbrainz.org/ws/" in url else None)
                (out / f"{name}.html").write_text(txt, encoding="utf-8")
                rec.update(ok=True, bytes=len(txt))
            except RobotsBlocked:
                rec.update(ok=False, robots_blocked=True)
            except Exception as e:  # noqa: BLE001
                rec.update(ok=False, error=f"{type(e).__name__}: {e}"[:300])
                resp = getattr(e, "response", None)
                if resp is not None:  # guarda el cuerpo del error (p. ej. 'falta la clave de API')
                    (out / f"{name}.html").write_text(resp.text[:20000], encoding="utf-8")
            rec["robots"] = f._host(url).robots_status
            rec["cabeceras"] = f.last_headers.get(url, {})
            index[name] = rec
            print(name, rec, flush=True)

    with ThreadPoolExecutor(max_workers=16) as ex:
        list(ex.map(run, by_host.values()))
    (out / "_index.json").write_text(json.dumps(index, indent=1, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
