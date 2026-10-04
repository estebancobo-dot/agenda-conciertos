"""Datos de la web: agenda ligera + detalle por días (tools/web_datos.py)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from web_datos import LIGEROS, preparar  # noqa: E402

REC = {"id": "a1", "fecha": "2026-10-09", "hora": None, "artista": "Devin Townsend", "invitados": [],
       "sala": "Revi Live", "municipio": "Madrid", "grupos": ["rock y metal"], "categoria": "rock y metal",
       "estilos_discogs": ["Progressive Metal"], "nacionalidad": "CA", "estado": "conflicto",
       "conflictos": [{"campo": "hora", "versiones": [{"valor": "20:00", "fuentes": ["x"]}]},
                      {"campo": "sala", "versiones": [{"valor": "Otra", "fuentes": ["y"]}]}],
       "estilo_fuente": [{"estilo": "Metal", "fuente": "a"}, {"estilo": "Metal", "fuente": "b"}],
       "imagen": {"url": "https://x/y.jpg", "credito": "Commons"}, "fuentes": [{"nombre": "Revi", "url": "u"}],
       "ficha": {"evidencias": [1, 2, 3]}, "precio": "30 €", "notas": ["n"]}


def test_agenda_ligera_y_detalle(tmp_path):
    r = preparar({"generado": "2026-09-30T05:00:00+00:00", "conciertos": [REC]}, tmp_path)
    assert r == {"conciertos": 1, "dias": 1, "ocultos": 0}
    ag = json.loads((tmp_path / "agenda.json").read_text())
    assert ag["generado"] and ag["detalles"] == "detalles/{fecha}.json"
    x = ag["conciertos"][0]
    assert set(x) <= set(LIGEROS) | {"conflictos", "estilo_fuente", "img"}
    assert "fuentes" not in x and "ficha" not in x and "precio" not in x and "hora" not in x  # vacíos fuera
    assert x["img"] == "https://x/y.jpg"
    assert [c["campo"] for c in x["conflictos"]] == ["hora", "sala"]
    assert x["estilo_fuente"] == [{"estilo": "Metal"}]
    det = json.loads((tmp_path / "detalles" / "2026-10-09.json").read_text())
    assert det["a1"] == REC  # el detalle es el registro completo


def test_imagen_generica_fuera(tmp_path):
    g = "https://madridenvivo.com/fondo-privado.jpg"
    recs = [dict(REC, id=str(i), artista=f"Artista {i}", imagen={"url": g}) for i in range(5)]
    preparar({"conciertos": recs}, tmp_path)
    ag = json.loads((tmp_path / "agenda.json").read_text())
    assert all("img" not in x for x in ag["conciertos"])  # la misma foto para 5 artistas distintos no es de ninguno


def test_miniaturas_propias(tmp_path):
    import io

    import pytest
    Image = pytest.importorskip("PIL.Image")
    import web_datos
    from miniaturas import nombre, pendientes, reducir
    buf = io.BytesIO()
    Image.new("RGB", (800, 1100), (200, 30, 30)).save(buf, "JPEG")
    from miniaturas import reducir_grande
    grande = Image.open(io.BytesIO(reducir_grande(buf.getvalue())))
    assert max(grande.size) == 720 and grande.size[1] > grande.size[0]  # el cartel entero, sin recortar
    mini = reducir(buf.getvalue())
    assert Image.open(io.BytesIO(mini)).size == (160, 160) and len(mini) < 20000
    u = "https://doc.conciertos.club/doc/c/2026/x.jpg"
    d = "https://i.discogs.com/abc/rs:fit/g:sm/q:90/h:600/w:600/x.jpeg"
    w = "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/80/ZENET.jpg/250px-ZENET.jpg"
    recs = [{"fecha": "2026-11-01", "imagen": {"url": u}}, {"fecha": "2026-10-01", "imagen": {"url": w}},
            {"fecha": "2026-12-01", "imagen": {"url": d}}, {"fecha": "2026-10-02", "imagen": {"url": u}}]
    assert pendientes({"conciertos": recs}) == [w, u, d]  # todas, las más próximas primero
    from miniaturas import origen
    assert origen(w).endswith("/800px-ZENET.jpg") and origen(u) == u
    (tmp_path / nombre(u)).write_bytes(mini)
    web_datos.MINIATURAS.clear()
    web_datos.cargar_miniaturas(recs, tmp_path)
    assert web_datos.ligero({"id": "1", "fecha": "2026-10-01", "imagen": {"url": u}})["mini"] == f"miniaturas/{nombre(u)}"
    web_datos.MINIATURAS.clear()
