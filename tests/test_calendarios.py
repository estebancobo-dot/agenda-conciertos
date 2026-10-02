"""Calendarios suscribibles y fichas de sala (tools/calendarios.py, fase 7)."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from calendarios import _plegar, generar, ics, slug  # noqa: E402

AHORA = datetime(2026, 10, 2, 20, 0, tzinfo=timezone.utc)


def rec(**kw):
    r = {"id": "abc", "fecha": "2026-10-10", "hora": "21:30", "artista": "Grupo; Q, y más", "sala": "Sala El Sol",
         "municipio": "Madrid", "grupos": ["rock y metal"], "fuentes": [{"nombre": "Sala El Sol (web oficial)", "prioridad": 1}],
         "primera_vez_visto": "2026-09-29"}
    r.update(kw)
    return r


def test_evento_con_hora_y_escapado():
    t = ics("Prueba", [rec()], "20261002T200000Z")
    assert "DTSTART;TZID=Europe/Madrid:20261010T213000" in t and "BEGIN:VTIMEZONE" in t
    assert "SUMMARY:Grupo\; Q\\, y más" in t and "STATUS:CONFIRMED" in t
    assert all(len(l.encode()) <= 75 for l in t.split("\r\n"))


def test_sin_hora_todo_el_dia_y_cancelado():
    t = ics("Prueba", [rec(hora=None, estado_evento={"tipo": "cancelado"}, cambios=[{"dia": "2026-10-01", "campo": "evento"}])],
            "20261002T200000Z")
    assert "DTSTART;VALUE=DATE:20261010" in t and "DTEND;VALUE=DATE:20261011" in t
    assert "STATUS:CANCELLED" in t and "SUMMARY:Cancelado: " in t and "SEQUENCE:1" in t
    assert "LAST-MODIFIED:20261001T000000Z" in t


def test_plegado_sin_partir_caracteres():
    l = "DESCRIPTION:" + "ñ" * 100
    partes = _plegar(l)
    assert "".join(p.lstrip(" ") if i else p for i, p in enumerate(partes)) == l
    assert all(len(p.encode()) <= 75 for p in partes)


def test_generar_salas_y_generos(tmp_path):
    datos = {"hoy": "2026-10-02", "conciertos": [
        rec(), rec(id="b", sala="Sala El Sol / Sala B", grupos=["punk y garage"], grupos_cartel={"blues": ["X"]}),
        rec(id="c", fecha="2026-09-01"),  # pasado: fuera
        rec(id="d", grupos=["fuera de foco"])]}
    out = generar(datos, tmp_path, {"rock y metal": "Rock y metal"}, [{"nombre": "Sala El Sol", "web": "https://elsol"}], AHORA)
    assert out == {"calendarios_sala": 2, "calendarios_genero": 3}
    salas = json.loads((tmp_path / "data" / "salas.json").read_text())
    sol = next(s for s in salas["salas"] if s["nombre"] == "Sala El Sol")
    assert sol["conciertos"] == 3 and sol["web"] == "https://elsol" and sol["oficial"] == "Sala El Sol (web oficial)"
    assert set(salas["generos"]) == {"rock y metal", "punk y garage", "blues"}
    assert (tmp_path / sol["ics"]).read_text().count("BEGIN:VEVENT") == 3
    assert "X-WR-CALNAME:Conciertos · Rock y metal" in (tmp_path / salas["generos"]["rock y metal"]).read_text()
    assert slug("Soul, funk y R&B") == "soul-funk-y-r-and-b"
