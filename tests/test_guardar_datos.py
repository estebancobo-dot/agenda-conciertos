"""Guardado de los datos en la rama `datos` (tools/datos.py y tools/guardar_datos.py) con repositorios git de
verdad en una carpeta temporal (sin red): primera vez sin rama, la rama sin historial, dos ejecuciones que se
solapan (cachés unidas, conciertos de quien ha leído las agendas), otra ejecución que se adelanta al subir, sin
cambios y sin datos de partida."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import copias  # noqa: E402
import datos  # noqa: E402
import guardar_datos as gd  # noqa: E402

ID = ["-c", "user.name=prueba", "-c", "user.email=prueba@localhost"]


def git(cwd, *a):
    return subprocess.run(["git", *ID, *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def escribir(d: Path, nombre: str, contenido) -> None:
    (d / nombre).write_text(json.dumps(contenido, ensure_ascii=False), encoding="utf-8")


def leer_rama(origen: Path, nombre: str):
    return json.loads(git(origen, "show", f"{datos.RAMA}:data/{nombre}"))


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """origin (vacío, como GitHub) y un clon de trabajo con data/ en main, como la primera ejecución."""
    origen, trabajo = tmp_path / "origen.git", tmp_path / "trabajo"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origen))
    git(tmp_path, "clone", "-q", str(origen), str(trabajo))
    data = trabajo / "data"
    data.mkdir()
    escribir(data, "concerts.json", {"conciertos": [{"id": "a", "artista": "Muse"}]})
    escribir(data, "artistas.json", {"muse": {"fecha": "2026-10-01", "pais": "GB"}})
    escribir(data, "informe.json", {"artistas": {"completados": 1}})
    git(trabajo, "add", "data")
    git(trabajo, "commit", "-qm", "inicio")
    git(trabajo, "push", "-q", "origin", "HEAD:main")
    for m in (datos, gd, copias):
        monkeypatch.setattr(m, "RAIZ", trabajo)
        monkeypatch.setattr(m, "DATA", data)
    monkeypatch.setattr(datos, "TRAIDOS", data / ".traidos.json")
    monkeypatch.setattr(datos, "traer_aportes", lambda: "sin aportes")
    monkeypatch.setattr(datos.time, "sleep", lambda s: None)
    import scraper.pipeline
    monkeypatch.setattr(scraper.pipeline, "reaplicar_fichas", lambda: None)  # tiene sus propias pruebas
    monkeypatch.setattr(sys, "argv", ["guardar_datos.py"])
    return origen, trabajo, data


def test_primera_vez_crea_la_rama_sin_historial(repo):
    origen, trabajo, data = repo
    assert datos.traer() == 0  # sin rama: parte de los datos de main
    escribir(data, "concerts.json", {"conciertos": [{"id": "a", "artista": "Muse"}, {"id": "b", "artista": "Kmmn"}]})
    assert gd.main() == 0
    assert [r["id"] for r in leer_rama(origen, "concerts.json")["conciertos"]] == ["a", "b"]
    assert git(origen, "rev-list", "--count", datos.RAMA) == "1"  # un único commit, sin padre
    assert git(origen, "ls-tree", "-r", "--name-only", datos.RAMA).split() == \
        sorted(f"data/{n}" for n in ("concerts.json", "artistas.json", "informe.json"))  # solo los generados


def test_sin_cambios_no_sube_nada(repo, tmp_path):
    origen, trabajo, data = repo
    datos.traer()
    gd.main()
    antes = git(origen, "rev-parse", datos.RAMA)
    datos.traer()
    salida = tmp_path / "salida"
    import os
    os.environ["GITHUB_OUTPUT"] = str(salida)
    try:
        assert gd.main() == 0
    finally:
        del os.environ["GITHUB_OUTPUT"]
    assert git(origen, "rev-parse", datos.RAMA) == antes and "cambios=false" in salida.read_text()


def test_sin_datos_de_partida_no_guarda(repo):
    origen, trabajo, data = repo
    assert gd.main() == 1  # no se ejecutó tools/datos.py: guardar machacaría la rama con datos incompletos
    with pytest.raises(subprocess.CalledProcessError):
        git(origen, "rev-parse", "--verify", datos.RAMA)


def _otra_ejecucion(origen: Path, tmp: Path, artistas: dict, concerts: dict) -> None:
    """Otra ejecución que sube a la rama de datos mientras esta trabaja."""
    otro = tmp / "otro"
    git(tmp, "clone", "-q", "-b", datos.RAMA, str(origen), str(otro))
    escribir(otro / "data", "artistas.json", artistas)
    escribir(otro / "data", "concerts.json", concerts)
    git(otro, "commit", "-qam", "otra")
    git(otro, "push", "-q", "-f", "origin", f"HEAD:{datos.RAMA}")


def test_dos_ejecuciones_unen_las_caches_y_quedan_los_conciertos_leidos(repo, tmp_path):
    origen, trabajo, data = repo
    datos.traer()
    gd.main()
    datos.traer()  # esta ejecución lee las agendas y completa una ficha
    escribir(data, "concerts.json", {"conciertos": [{"id": "nuevo", "artista": "Leído ahora"}]})
    escribir(data, "artistas.json", {"muse": {"fecha": "2026-10-01", "pais": "GB"},
                                     "kmmn": {"fecha": "2026-10-03", "pais": "ES"}})
    # mientras tanto, la de fichas sube otra ficha y una consulta más reciente de Muse
    _otra_ejecucion(origen, tmp_path, {"muse": {"fecha": "2026-10-05", "pais": "GB", "oyentes": 7},
                                       "leiva": {"fecha": "2026-10-04", "pais": "ES"}},
                    {"conciertos": [{"id": "viejo", "artista": "De la otra"}]})
    assert gd.main() == 0
    art = leer_rama(origen, "artistas.json")
    assert set(art) == {"muse", "kmmn", "leiva"} and art["muse"]["oyentes"] == 7  # gana la consulta más reciente
    assert [r["id"] for r in leer_rama(origen, "concerts.json")["conciertos"]] == ["nuevo"]  # quien leyó las agendas


def test_solo_fichas_conserva_los_conciertos_guardados(repo, tmp_path, monkeypatch):
    origen, trabajo, data = repo
    datos.traer()
    gd.main()
    datos.traer()  # pasada de solo fichas: no toca los conciertos
    escribir(data, "artistas.json", {"muse": {"fecha": "2026-10-01"}, "kmmn": {"fecha": "2026-10-06"}})
    escribir(data, "informe.json", {"artistas": {"completados": 2}})
    _otra_ejecucion(origen, tmp_path, {"muse": {"fecha": "2026-10-01"}},
                    {"conciertos": [{"id": "leido-por-la-otra", "artista": "X"}]})
    monkeypatch.setattr(sys, "argv", ["guardar_datos.py", "--fichas"])
    assert gd.main() == 0
    assert [r["id"] for r in leer_rama(origen, "concerts.json")["conciertos"]] == ["leido-por-la-otra"]
    assert "kmmn" in leer_rama(origen, "artistas.json")
    assert leer_rama(origen, "informe.json")["artistas"] == {"completados": 2}


def test_si_otra_ejecucion_se_adelanta_al_subir_se_vuelve_a_combinar(repo, tmp_path, monkeypatch):
    origen, trabajo, data = repo
    datos.traer()
    gd.main()
    datos.traer()
    escribir(data, "artistas.json", {"muse": {"fecha": "2026-10-01"}, "kmmn": {"fecha": "2026-10-06"}})
    combinar, veces = gd.combinar, []

    def combinar_y_adelantarse(*a, **k):
        combinar(*a, **k)
        if not veces:  # justo antes de subir, otra ejecución sube lo suyo
            _otra_ejecucion(origen, tmp_path, {"muse": {"fecha": "2026-10-01"}, "leiva": {"fecha": "2026-10-07"}},
                            {"conciertos": []})
        veces.append(1)
    monkeypatch.setattr(gd, "combinar", combinar_y_adelantarse)
    assert gd.main() == 0
    assert len(veces) == 2  # el primer intento se rechaza (--force-with-lease) y se repite con lo nuevo
    assert set(leer_rama(origen, "artistas.json")) == {"muse", "kmmn", "leiva"}  # no se pierde nada de nadie
