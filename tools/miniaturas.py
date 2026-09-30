"""Miniaturas propias para las imágenes de las agendas que ningún servicio puede reducir.

conciertos.club (más de 1.000 conciertos) publica carteles a tamaño completo en un servidor lento (4-9 s por
imagen con 4G) y el redimensionador wsrv.nl lo tiene bloqueado. Aquí, al publicar la web, se descarga cada
imagen una sola vez con el mismo lector que las agendas (robots.txt, identificación y ritmo por servidor), se
reduce a 160×160 WebP (~5 KB) y se sirve desde la propia web: rápida y guardada por el service worker.

Las miniaturas ya hechas se guardan entre ejecuciones (caché de GitHub Actions, carpeta DIR): cada día solo se
descargan las nuevas. Con límite de tiempo: lo que no dé tiempo se hace al día siguiente y, mientras, la web usa
la imagen original.

Uso: python tools/miniaturas.py [--minutos N]
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
DIR = RAIZ / "miniaturas"
HOSTS = ("conciertos.club", "doc.conciertos.club")
LADO = 160


def nombre(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:16] + ".webp"


def reducir(datos: bytes) -> bytes:
    from PIL import Image, ImageOps
    im = Image.open(io.BytesIO(datos))
    im = ImageOps.exif_transpose(im).convert("RGB")
    im = ImageOps.fit(im, (LADO, LADO), Image.LANCZOS, centering=(0.5, 0.35))  # carteles: mejor la parte de arriba
    out = io.BytesIO()
    im.save(out, "WEBP", quality=70, method=6)
    return out.getvalue()


def pendientes(concerts: dict) -> list[str]:
    urls = []
    for r in concerts.get("conciertos", []):
        u = (r.get("imagen") or {}).get("url") or ""
        if u.split("/")[2:3] and u.split("/")[2] in HOSTS and u not in urls:
            urls.append(u)
    return urls


def main() -> int:
    minutos = float(sys.argv[sys.argv.index("--minutos") + 1]) if "--minutos" in sys.argv else 8
    from scraper.fetch import Fetcher
    DIR.mkdir(exist_ok=True)
    concerts = json.loads((RAIZ / "data" / "concerts.json").read_text(encoding="utf-8"))
    urls = pendientes(concerts)
    hechas = {p.name for p in DIR.glob("*.webp")}
    faltan = [u for u in urls if nombre(u) not in hechas]
    f = Fetcher()
    t0, nuevas, fallos = time.monotonic(), 0, 0
    for u in faltan:
        if time.monotonic() - t0 > minutos * 60:
            break
        try:
            (DIR / nombre(u)).write_bytes(reducir(f.get_bytes(u)))
            nuevas += 1
        except Exception as e:  # noqa: BLE001 - una imagen rota no para las demás
            fallos += 1
            print(f"  {u}: {type(e).__name__}: {str(e)[:100]}")
    total = len({nombre(u) for u in urls} & {p.name for p in DIR.glob("*.webp")})
    print(f"Miniaturas: {len(urls)} imágenes de {', '.join(HOSTS)}; {nuevas} nuevas, {fallos} fallos, "
          f"{total} listas, {len(faltan) - nuevas - fallos} para otro día ({round(time.monotonic() - t0)} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
