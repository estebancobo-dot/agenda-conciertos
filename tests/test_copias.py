"""Copias de seguridad de los datos (tools/copias.py) con repositorios git de verdad en una carpeta temporal: cuáles
se conservan, una al día (la segunda del mismo día no se repite), la rama sin historial, y restaurar una copia en
data/ y en la rama `datos`."""
import json
import subprocess
import sys
from datetime import date, timedelta

from tests.test_guardar_datos import escribir, git, leer_rama, repo  # noqa: F401  (fixture)

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent / "tools"))
import copias  # noqa: E402
import datos  # noqa: E402
import guardar_datos as gd  # noqa: E402

HOY = date(2026, 10, 10)  # sábado


def test_cuales_se_conservan():
    fechas = [HOY - timedelta(days=d) for d in range(0, 60)]
    q = copias.quedarse(fechas, HOY)
    assert all(HOY - timedelta(days=d) in q for d in range(7))  # las de los 7 últimos días
    viejas = [f for f in q if (HOY - f).days >= 7]
    assert len({f.isocalendar()[:2] for f in viejas}) == len(viejas)  # de las anteriores, una por semana
    assert min(q) >= HOY - timedelta(days=35) and len(q) <= 7 + 5  # y nada de hace más de un mes
    assert copias.quedarse([HOY + timedelta(days=1)], HOY) == []  # ni fechas futuras


def test_una_copia_al_dia_y_rama_sin_historial(repo):  # noqa: F811
    origen, trabajo, data = repo
    assert "guardada" in copias.guardar(HOY)
    assert "ya estaba" in copias.guardar(HOY)  # la segunda del mismo día no se repite
    escribir(data, "concerts.json", {"conciertos": [{"id": "otro"}]})
    copias.guardar(HOY + timedelta(days=1))
    assert git(origen, "ls-tree", "--name-only", f"{copias.RAMA}:copias").split() == \
        ["2026-10-10.tar.gz", "2026-10-11.tar.gz"]
    assert git(origen, "rev-list", "--count", copias.RAMA) == "1"


def test_restaurar_una_copia(repo, monkeypatch):  # noqa: F811
    origen, trabajo, data = repo
    copias.guardar(HOY)  # copia buena: Muse
    escribir(data, "concerts.json", {"conciertos": []})  # una lectura la estropea
    assert copias.restaurar(HOY) and json.loads((data / "concerts.json").read_text())["conciertos"][0]["artista"] == "Muse"
    # y subida a la rama de datos (lo que hace la tarea «Restaurar una copia»)
    datos.traer()
    escribir(data, "concerts.json", {"conciertos": []})
    gd.main()  # la rama datos queda estropeada (y de paso hace la copia de hoy, que ya estaba)
    assert leer_rama(origen, "concerts.json")["conciertos"] == []
    monkeypatch.setattr(sys, "argv", ["copias.py", "restaurar", HOY.isoformat(), "--subir"])
    assert copias.main() == 0
    assert leer_rama(origen, "concerts.json")["conciertos"][0]["artista"] == "Muse"


def test_sin_esa_copia_lo_dice(repo):  # noqa: F811
    copias.guardar(HOY)
    try:
        copias.restaurar(HOY - timedelta(days=3))
    except SystemExit as e:
        assert "No hay copia del 2026-10-07" in str(e) and "2026-10-10" in str(e)
    else:
        raise AssertionError("debía decir que no hay copia")


def test_las_pruebas_no_usan_git_por_red(tmp_path):
    r = subprocess.run(["git", "ls-remote", "https://github.com/estebancobo-dot/agenda-conciertos"], cwd=tmp_path,
                       capture_output=True, text=True)
    assert r.returncode != 0 and "not allowed" in r.stderr
