"""Los datos generados (conciertos, informe, cachés) viven en la rama `datos`, no en `main`.

Así `main` solo tiene código y configuración, y el repositorio deja de crecer ~10 MB al día: la rama `datos` es
un único commit que se reemplaza en cada ejecución (sin historial).

Uso: python tools/datos.py      → trae a data/ los datos de la rama `datos` (antes de rastrear)

Si la rama aún no existe (primera ejecución tras el cambio), se parte de los datos que haya en `main`. Si no se
pueden traer y tampoco hay datos en `main`, falla: rastrear desde cero perdería el historial de conciertos y las
fichas, y el guardado posterior los borraría.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
RAMA = "datos"
GENERADOS = ("concerts.json", "concerts.csv", "informe.json", "estado.json", "fuentes_cache.json",
             "artistas.json", "musicbrainz_cache.json", "paginas.json")
TRAIDOS = DATA / ".traidos.json"  # huella de lo traído: el guardado sabe qué ha regenerado esta ejecución


def git(*args: str, check: bool = True, entrada: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=RAIZ, check=check, capture_output=True, input=entrada)


def huella(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def sha_remoto() -> str | None:
    """Commit de la rama de datos en origin, None si no existe. Reintenta los fallos de red."""
    for intento in range(4):
        r = git("ls-remote", "--exit-code", "origin", f"refs/heads/{RAMA}", check=False)
        if r.returncode == 0:
            return r.stdout.decode().split()[0]
        if r.returncode == 2:  # la rama no existe
            return None
        time.sleep(2 ** (intento + 1))
    raise RuntimeError(f"no se pudo consultar la rama {RAMA}: {r.stderr.decode()[-300:]}")


def restaurar(sha: str | None) -> str:
    """Pone en data/ los datos de la rama (o, si aún no existe, los de main). Devuelve el origen usado."""
    if sha:
        for intento in range(4):
            if git("fetch", "--depth=1", "origin", sha, check=False).returncode == 0:
                break
            time.sleep(2 ** (intento + 1))
        else:
            raise RuntimeError(f"no se pudo traer la rama {RAMA}")
        for n in GENERADOS:
            r = git("show", f"{sha}:data/{n}", check=False)
            if r.returncode == 0:
                (DATA / n).write_bytes(r.stdout)
        return f"rama {RAMA} ({sha[:7]})"
    for n in GENERADOS:
        r = git("show", f"HEAD:data/{n}", check=False)
        if r.returncode == 0:
            (DATA / n).write_bytes(r.stdout)
    return "main (la rama de datos aún no existe)"


def traer() -> int:
    sha = sha_remoto()
    origen = restaurar(sha)
    if not (DATA / "concerts.json").exists():
        print(f"No hay datos de partida ({origen}): no se rastrea desde cero", file=sys.stderr)
        return 1
    TRAIDOS.write_text(json.dumps({"sha": sha, "huellas": {n: huella(DATA / n) for n in GENERADOS}}))
    print(f"Datos de partida: {origen}")
    return 0


if __name__ == "__main__":
    sys.exit(traer())
