"""Captura con navegador la búsqueda de Madrid en Vivo y registra las peticiones de 'cargar más' (desarrollo)."""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scraper.fetch import USER_AGENT  # noqa: E402

URL = "https://madridenvivo.com/buscador-avanzado/?salas=&estilos=&fecha-desde=2026-10-12&fecha-hasta=2026-10-18&buscar="
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
reqs = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(user_agent=USER_AGENT)

    def on_req(r):
        if r.resource_type in ("xhr", "fetch"):
            reqs.append({"url": r.url, "method": r.method, "post": r.post_data})

    pg.on("request", on_req)
    pg.goto(URL, wait_until="networkidle", timeout=90000)
    for _ in range(8):
        pg.mouse.wheel(0, 20000)
        pg.wait_for_timeout(2500)
    (out / "mev_rendered.html").write_text(pg.content(), encoding="utf-8")
    b.close()
(out / "mev_requests.json").write_text(json.dumps(reqs, indent=1, ensure_ascii=False))
