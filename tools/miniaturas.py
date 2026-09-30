"""Miniaturas propias de TODAS las imágenes de los conciertos, servidas desde la propia web.

Antes solo se hacían para conciertos.club y Discogs; el resto (Madrid en Vivo, Songkick…) se reducía al vuelo con
wsrv.nl. Pero wsrv.nl solo es rápido con las imágenes que alguien ha pedido antes: la primera vez tiene que
descargar el original (los de Madrid en Vivo son de 2.560 px) y tarda 1-3 s por foto. Por eso las listas y las
fichas iban unas veces rápido y otras lento, según el día o el concierto. Aquí, al publicar la web, se descarga
cada imagen una sola vez con el mismo lector que las agendas (robots.txt, identificación y ritmo por servidor), se
reduce a 160×160 WebP (~5 KB) para las listas y a 720 px (~40 KB) para la ficha, y se sirve desde la propia web:
rápida y guardada por el service worker.

Se guardan en la rama `miniaturas` del repositorio (un único commit, sin historial). Cada ejecución la trae, hace
solo las que faltan, quita las de conciertos que ya no están en la agenda y sube el resultado; git solo envía los
archivos nuevos. Con límite de tiempo: lo que no dé tiempo se hace en la siguiente ejecución y, mientras, la web
usa la imagen original.

Uso: python tools/miniaturas.py [--minutos N] [--guardar]
"""
from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
DIR = RAIZ / "miniaturas"
RAMA = "miniaturas"


def git(*args: str, entrada: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=RAIZ, input=entrada, text=True, capture_output=True, check=check)


def traer() -> str | None:
    """Trae la rama `miniaturas` a DIR (sin tocar el repositorio de trabajo). Devuelve su commit."""
    DIR.mkdir(exist_ok=True)
    if git("fetch", "-q", "--depth=1", "origin", f"refs/heads/{RAMA}", check=False).returncode != 0:
        return None
    sha = git("rev-parse", "FETCH_HEAD").stdout.strip()
    tar = subprocess.run(["git", "archive", "--format=tar", sha], cwd=RAIZ, capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(DIR)], input=tar, check=True)
    return sha


def guardar(sha_base: str | None, validos: set[str]) -> None:
    """Sube DIR como único commit de la rama (quitando las de conciertos que ya no están). Reintenta si otra
    ejecución ha subido mientras tanto (se unen: cada archivo depende solo de su foto)."""
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    for intento in range(4):
        for p in DIR.glob("*.webp"):
            if p.name not in validos:
                p.unlink()
        rutas = sorted(DIR.glob("*.webp"))
        blobs = git("hash-object", "-w", "--stdin-paths", entrada="\n".join(map(str, rutas))).stdout.split()
        arbol = git("mktree", entrada="".join(f"100644 blob {b}\t{p.name}\n" for b, p in zip(blobs, rutas))).stdout.strip()
        if sha_base and git("rev-parse", f"{sha_base}^{{tree}}").stdout.strip() == arbol:
            print("Rama de miniaturas: sin cambios")
            return
        commit = git("commit-tree", arbol, "-m", f"Miniaturas ({len(rutas)} archivos)").stdout.strip()
        r = git("push", f"--force-with-lease=refs/heads/{RAMA}:{sha_base or ''}", "origin",
                f"{commit}:refs/heads/{RAMA}", check=False)
        if r.returncode == 0:
            print(f"Rama de miniaturas guardada: {len(rutas)} archivos")
            return
        print(f"La rama de miniaturas cambió mientras tanto (intento {intento + 1}): se unen y se reintenta")
        sha_base = traer()
    print("No se pudo guardar la rama de miniaturas", file=sys.stderr)
LADO = 160


def nombre(url: str, grande: bool = False) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:16] + ("-g" if grande else "") + ".webp"


GRANDE = 720  # foto de la ficha del concierto


def reducir_grande(datos: bytes) -> bytes:
    """Foto de la ficha: el cartel entero (sin recortar) a 720 px como mucho, ~40 KB."""
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(datos))).convert("RGB")
    im.thumbnail((GRANDE, GRANDE), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "WEBP", quality=75, method=6)
    return out.getvalue()


def reducir(datos: bytes) -> bytes:
    from PIL import Image, ImageOps
    im = Image.open(io.BytesIO(datos))
    im = ImageOps.exif_transpose(im).convert("RGB")
    im = ImageOps.fit(im, (LADO, LADO), Image.LANCZOS, centering=(0.5, 0.35))  # carteles: mejor la parte de arriba
    out = io.BytesIO()
    im.save(out, "WEBP", quality=70, method=6)
    return out.getvalue()


def pendientes(concerts: dict) -> list[str]:
    """Todas las imágenes, las de los conciertos más próximos primero (si no da tiempo, faltan las lejanas)."""
    urls: list[str] = []
    for r in sorted(concerts.get("conciertos", []), key=lambda r: r.get("fecha") or "9"):
        u = (r.get("imagen") or {}).get("url") or ""
        if u.startswith("https://") and u not in urls:
            urls.append(u)
    return urls


def origen(u: str) -> str:
    """Wikimedia da miniaturas de 250 px: para la ficha se pide la de 800 px del mismo archivo."""
    import re
    if "wikimedia.org" in u and "/thumb/" in u:
        return re.sub(r"/\d+px-([^/]+)$", r"/800px-\1", u)
    return u


def main() -> int:
    minutos = float(sys.argv[sys.argv.index("--minutos") + 1]) if "--minutos" in sys.argv else 8
    from scraper.fetch import Fetcher
    base = traer()
    concerts = json.loads((RAIZ / "data" / "concerts.json").read_text(encoding="utf-8"))
    urls = pendientes(concerts)
    hechas = {p.name for p in DIR.glob("*.webp")}
    faltan = [u for u in urls if nombre(u) not in hechas or nombre(u, True) not in hechas]
    f = Fetcher()
    t0 = time.monotonic()
    cuenta = {"nuevas": 0, "fallos": 0}

    def servidor(lista):
        # un hilo por servidor: cada uno a su ritmo (el Fetcher espera entre peticiones al mismo servidor)
        for u in lista:
            if time.monotonic() - t0 > minutos * 60:
                return
            try:
                try:
                    datos = f.get_bytes(origen(u))
                except Exception:  # noqa: BLE001 - el archivo original es más pequeño que 800 px
                    datos = f.get_bytes(u)
                (DIR / nombre(u)).write_bytes(reducir(datos))
                (DIR / nombre(u, True)).write_bytes(reducir_grande(datos))
                cuenta["nuevas"] += 1
            except Exception as e:  # noqa: BLE001 - una imagen rota no para las demás
                cuenta["fallos"] += 1
                print(f"  {u}: {type(e).__name__}: {str(e)[:100]}")

    por_servidor: dict[str, list[str]] = {}
    for u in faltan:
        por_servidor.setdefault(u.split("/")[2], []).append(u)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max(1, len(por_servidor))) as ex:
        list(ex.map(servidor, por_servidor.values()))
    nuevas, fallos = cuenta["nuevas"], cuenta["fallos"]
    total = len({nombre(u) for u in urls} & {p.name for p in DIR.glob("*.webp")})
    print(f"Miniaturas: {len(urls)} imágenes; {nuevas} nuevas, {fallos} fallos, "
          f"{total} listas, {len(faltan) - nuevas - fallos} para otro día ({round(time.monotonic() - t0)} s)")
    if "--guardar" in sys.argv:
        guardar(base, {n for u in urls for n in (nombre(u), nombre(u, True))})
    return 0


if __name__ == "__main__":
    sys.exit(main())
