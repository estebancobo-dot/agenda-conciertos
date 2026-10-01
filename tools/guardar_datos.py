"""Guarda data/ en el repositorio aunque otra ejecución haya guardado datos mientras tanto.

Dos ejecuciones pueden solaparse (la de fichas cada 2 horas y la diaria). Antes, la segunda en terminar
chocaba con la primera al subir sus datos y perdía todo su trabajo. Ahora:
  1. se apartan los datos generados por esta ejecución;
  2. se parte de lo último guardado en la rama `datos` (con lo que haya subido la otra ejecución);
  3. las cachés (fichas de artista, MusicBrainz) se unen, y de cada artista se queda la consulta más reciente;
  4. los conciertos, el informe y el estado son los de esta ejecución si ha leído las agendas; si solo ha
     completado fichas, se conservan los guardados y se les aplican las fichas;
  5. se sube como único commit de la rama `datos` (sin historial: el repositorio no crece); si otra ejecución
     se adelanta, se repite (hasta 4 intentos).

Uso: python tools/guardar_datos.py [--fichas]
Escribe "cambios=true|false" en $GITHUB_OUTPUT si existe.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))

CACHES = ("artistas.json", "musicbrainz_cache.json", "paginas.json")
PROPIOS = ("concerts.json", "concerts.csv", "informe.json", "estado.json", "fuentes_cache.json")


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:  # noqa: D103
    return subprocess.run(["git", *args], cwd=RAIZ, check=check, text=True, capture_output=True)


def unir_caches(nuestra: dict, suya: dict) -> dict:
    """Unión de dos cachés {clave: entrada}; si ambas tienen la clave, gana la consulta más reciente."""
    out = dict(suya)
    for k, v in nuestra.items():
        w = out.get(k)
        if w is None or not isinstance(w, dict) or not isinstance(v, dict) or v.get("fecha", "") >= w.get("fecha", ""):
            out[k] = v
    return out


def _leer(p: Path, defecto):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defecto


def combinar(apartado: Path, solo_fichas: bool, regenerados: set[str]) -> None:
    """Coloca en data/ (que ya es el último main) los datos de esta ejecución."""
    from scraper.pipeline import reaplicar_fichas
    for nombre in CACHES:
        nuestra = _leer(apartado / nombre, None)
        if nuestra is None:
            continue
        unida = unir_caches(nuestra, _leer(DATA / nombre, {}))
        (DATA / nombre).write_text(json.dumps(unida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if solo_fichas:
        inf_nuestro = _leer(apartado / "informe.json", {})
        inf = _leer(DATA / "informe.json", {})
        if inf_nuestro.get("artistas"):
            inf["artistas"] = inf_nuestro["artistas"]
            (DATA / "informe.json").write_text(json.dumps(inf, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    else:
        for nombre in PROPIOS:
            # solo los que esta ejecución ha vuelto a generar: si el rastreo falló antes de escribirlos,
            # los de main (quizá más nuevos) se quedan como están
            if nombre in regenerados and (apartado / nombre).exists():
                shutil.copy(apartado / nombre, DATA / nombre)
    # las fichas unidas pueden traer artistas que esta ejecución no tenía (o al revés): se vuelven a aplicar
    reaplicar_fichas()


def publicar(sha_base: str | None, mensaje: str) -> tuple[bool, bool]:
    """Sube data/ (solo los generados) como único commit de la rama de datos. Devuelve (subido, hubo_cambios)."""
    from datos import GENERADOS, RAMA
    filas = []
    for n in GENERADOS:
        if (DATA / n).exists():
            blob = git("hash-object", "-w", f"data/{n}").stdout.strip()
            filas.append(f"100644 blob {blob}\t{n}\n")
    sub = subprocess.run(["git", "mktree"], cwd=RAIZ, input="".join(filas), text=True, capture_output=True,
                         check=True).stdout.strip()
    raiz = subprocess.run(["git", "mktree"], cwd=RAIZ, input=f"040000 tree {sub}\tdata\n", text=True,
                          capture_output=True, check=True).stdout.strip()
    if sha_base and git("rev-parse", f"{sha_base}^{{tree}}").stdout.strip() == raiz:
        return True, False
    commit = git("commit-tree", raiz, "-m", mensaje).stdout.strip()  # sin padre: la rama no acumula historial
    r = git("push", f"--force-with-lease=refs/heads/{RAMA}:{sha_base or ''}", "origin",
            f"{commit}:refs/heads/{RAMA}", check=False)
    if r.returncode != 0:
        print(f"La rama de datos cambió mientras tanto: se vuelve a combinar.\n{r.stderr[-300:]}")
        return False, True
    return True, True


def main() -> int:
    from datos import GENERADOS, TRAIDOS, restaurar, sha_remoto, huella
    solo_fichas = "--fichas" in sys.argv
    if not TRAIDOS.exists():
        # no se trajeron los datos de partida: guardar ahora machacaría la rama con datos incompletos
        print("No se trajeron los datos de partida (tools/datos.py): no se guarda nada", file=sys.stderr)
        return 1
    traidos = json.loads(TRAIDOS.read_text())["huellas"]
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    # los que esta ejecución ha escrito (distintos de los traídos)
    regenerados = {n for n in PROPIOS if huella(DATA / n) != traidos.get(n)}
    apartado = Path(tempfile.mkdtemp())
    for n in GENERADOS:
        if (DATA / n).exists():
            shutil.copy(DATA / n, apartado / n)
    cambios = False
    from datetime import datetime, timezone
    for intento in range(1, 5):
        sha = sha_remoto()
        restaurar(sha)  # data/ = lo último guardado (quizá por otra ejecución)
        combinar(apartado, solo_fichas, regenerados)
        subido, cambios = publicar(sha, f"Datos actualizados {datetime.now(timezone.utc):%Y-%m-%dT%H:%MZ}")
        if subido:
            print(f"Datos guardados (intento {intento})" if cambios else "Sin cambios en los datos")
            break
    else:
        print("No se pudieron guardar los datos tras 4 intentos", file=sys.stderr)
        return 1
    salida = os.environ.get("GITHUB_OUTPUT")
    if salida:
        with open(salida, "a") as f:
            f.write(f"cambios={'true' if cambios else 'false'}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
