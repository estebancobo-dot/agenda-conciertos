"""Guarda data/ en el repositorio aunque otra ejecución haya guardado datos mientras tanto.

Dos ejecuciones pueden solaparse (la de fichas cada 2 horas y la diaria). Antes, la segunda en terminar
chocaba con la primera al subir sus datos y perdía todo su trabajo. Ahora:
  1. se apartan los datos generados por esta ejecución;
  2. se parte del último main (con lo que haya subido la otra ejecución);
  3. las cachés (fichas de artista, MusicBrainz) se unen, y de cada artista se queda la consulta más reciente;
  4. los conciertos, el informe y el estado son los de esta ejecución si ha leído las agendas; si solo ha
     completado fichas, se conservan los de main y se les aplican las fichas;
  5. se sube; si otra ejecución se adelanta otra vez, se repite (hasta 4 intentos).

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

CACHES = ("artistas.json", "musicbrainz_cache.json")
PROPIOS = ("concerts.json", "concerts.csv", "informe.json", "estado.json", "fuentes_cache.json")


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
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


def main() -> int:
    solo_fichas = "--fichas" in sys.argv
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    # los que esta ejecución ha escrito (modificados o nuevos, como la caché de fuentes la primera vez)
    regenerados = {n for n in PROPIOS if git("status", "--porcelain", "--", f"data/{n}").stdout.strip()}
    apartado = Path(tempfile.mkdtemp())
    for p in DATA.glob("*"):
        if p.is_file() and not p.name.endswith(".tmp"):
            shutil.copy(p, apartado / p.name)
    cambios = False
    for intento in range(1, 5):
        git("fetch", "origin", "main")
        git("reset", "--hard", "origin/main")
        combinar(apartado, solo_fichas, regenerados)
        git("add", "data/")
        if git("diff", "--cached", "--quiet", check=False).returncode == 0:
            print("Sin cambios en los datos")
            break
        from datetime import datetime, timezone
        git("commit", "-m", f"Datos actualizados {datetime.now(timezone.utc):%Y-%m-%dT%H:%MZ}")
        r = git("push", "origin", "HEAD:main", check=False)
        if r.returncode == 0:
            cambios = True
            print(f"Datos guardados (intento {intento})")
            break
        print(f"Otra ejecución subió datos a la vez (intento {intento}): se vuelve a combinar.\n{r.stderr[-300:]}")
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
