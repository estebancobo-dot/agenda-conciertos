"""Copias de seguridad de los datos (rama `datos-copias`).

La rama `datos` es un único commit sin historial: si una lectura defectuosa estropea los datos, en GitHub no hay
versión anterior a la que volver. Aquí se guarda, una vez al día (tras el primer guardado bueno del día, hora de
Madrid), una copia comprimida de los datos generados (los mismos ficheros que la rama `datos`). Se conservan las de
los 7 últimos días y, del último mes, una por semana (la primera de cada semana). La rama es también un único commit
sin historial que se rehace en cada copia (las copias que se quedan no se vuelven a subir: git reutiliza el mismo
contenido).

Uso:
  python tools/copias.py listar
  python tools/copias.py guardar                 → la de hoy, si aún no está (lo hace solo tools/guardar_datos.py)
  python tools/copias.py restaurar AAAA-MM-DD    → pone esa copia en data/
  python tools/copias.py restaurar AAAA-MM-DD --subir → y la sube a la rama `datos` (tarea «Restaurar una copia»)
"""
from __future__ import annotations

import io
import subprocess
import sys
import tarfile
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
RAMA = "datos-copias"
DIARIAS, SEMANAS = 7, 5


def git(*args: str, check: bool = True, entrada: str | bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=RAIZ, check=check, capture_output=True, input=entrada,
                          text=isinstance(entrada, str) or entrada is None)


def hoy_madrid() -> date:
    return datetime.now(ZoneInfo("Europe/Madrid")).date()


def quedarse(fechas: list[date], hoy: date) -> list[date]:
    """Las copias que se conservan: las de los últimos DIARIAS días y, de las SEMANAS últimas semanas, la primera
    copia de cada semana. Lo demás (y lo que tenga fecha futura) se descarta."""
    validas = sorted(f for f in fechas if f <= hoy)
    out = {f for f in validas if (hoy - f).days < DIARIAS}
    semanas: dict[tuple[int, int], date] = {}
    for f in validas:
        if (hoy - f).days < SEMANAS * 7:
            semanas.setdefault(f.isocalendar()[:2], f)
    return sorted(out | set(semanas.values()))


def _sha_rama() -> str | None:
    r = git("ls-remote", "--exit-code", "origin", f"refs/heads/{RAMA}", check=False)
    return r.stdout.split()[0] if r.returncode == 0 else None


def copias_remotas() -> tuple[str | None, dict[date, str]]:
    """(commit de la rama, {fecha: blob de su copia})."""
    sha = _sha_rama()
    if not sha:
        return None, {}
    git("fetch", "-q", "--depth=1", "origin", sha)
    out = {}
    for linea in git("ls-tree", sha, "copias/").stdout.splitlines():
        meta, ruta = linea.split("\t")
        nombre = Path(ruta).name
        if nombre.endswith(".tar.gz"):
            out[date.fromisoformat(nombre[:10])] = meta.split()[2]
    return sha, out


def empaquetar(nombres) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", compresslevel=9) as tar:
        for n in nombres:
            p = DATA / n
            if p.exists():
                info = tar.gettarinfo(str(p), arcname=f"data/{n}")
                info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, "", ""
                with p.open("rb") as f:
                    tar.addfile(info, f)
    return buf.getvalue()


def guardar(hoy: date | None = None) -> str:
    """Sube la copia de hoy si aún no está. Devuelve qué ha hecho."""
    from datos import GENERADOS
    hoy = hoy or hoy_madrid()
    for intento in range(3):
        sha, copias = copias_remotas()
        if hoy in copias:
            return f"la copia de hoy ({hoy}) ya estaba"
        tmp = DATA / ".copia.tar.gz"
        tmp.write_bytes(empaquetar(GENERADOS))
        try:
            copias[hoy] = git("hash-object", "-w", str(tmp)).stdout.strip()
        finally:
            tmp.unlink()
        filas = "".join(f"100644 blob {copias[f]}\t{f.isoformat()}.tar.gz\n" for f in quedarse(list(copias), hoy))
        sub = git("mktree", entrada=filas).stdout.strip()
        raiz = git("mktree", entrada=f"040000 tree {sub}\tcopias\n").stdout.strip()
        commit = git("commit-tree", raiz, "-m", f"Copia de los datos del {hoy}").stdout.strip()
        r = git("push", f"--force-with-lease=refs/heads/{RAMA}:{sha or ''}", "origin", f"{commit}:refs/heads/{RAMA}",
                check=False)
        if r.returncode == 0:
            return f"copia del {hoy} guardada ({len(quedarse(list(copias), hoy))} copias en {RAMA})"
    raise RuntimeError(f"no se pudo subir la copia: {r.stderr[-300:]}")


def restaurar(fecha: date) -> list[str]:
    """Pone en data/ la copia de esa fecha. Devuelve los ficheros restaurados."""
    sha, copias = copias_remotas()
    if fecha not in copias:
        raise SystemExit(f"No hay copia del {fecha}. Hay: {', '.join(str(f) for f in sorted(copias)) or 'ninguna'}")
    contenido = subprocess.run(["git", "cat-file", "blob", copias[fecha]], cwd=RAIZ, check=True,
                               capture_output=True).stdout
    hechos = []
    with tarfile.open(fileobj=io.BytesIO(contenido), mode="r:gz") as tar:
        for m in tar.getmembers():
            if not m.isfile() or not m.name.startswith("data/") or "/" in m.name[5:] or ".." in m.name:
                continue  # solo ficheros sueltos de data/
            (DATA / m.name[5:]).write_bytes(tar.extractfile(m).read())
            hechos.append(m.name[5:])
    return hechos


def main() -> int:
    sys.path.insert(0, str(RAIZ / "tools"))
    orden = sys.argv[1] if len(sys.argv) > 1 else "listar"
    if orden == "listar":
        _, copias = copias_remotas()
        for f in sorted(copias):
            print(f)
        print(f"{len(copias)} copias en la rama {RAMA}" if copias else f"Aún no hay copias en la rama {RAMA}")
    elif orden == "guardar":
        print(guardar())
    elif orden == "restaurar":
        fecha = date.fromisoformat(sys.argv[2])
        print("Restaurados en data/:", ", ".join(restaurar(fecha)))
        if "--subir" in sys.argv:
            from datos import sha_remoto
            from guardar_datos import git as git_gd, publicar
            git_gd("config", "user.name", "github-actions[bot]")
            git_gd("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
            subido, _ = publicar(sha_remoto(), f"Datos restaurados de la copia del {fecha}")
            if not subido:
                print("La rama de datos cambió mientras tanto: vuelve a lanzarlo", file=sys.stderr)
                return 1
            print(f"Rama datos = copia del {fecha}")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
