"""Fase C: hora habitual de la sala (estimada) y origen deducido solo cuando no puede fallar."""
from scraper.normalizacion import estado_hora, estimar_horas
from scraper.pipeline import tributo_y_estimacion


def rec(hora=None, sala="Sala El Sol", **kw):
    r = {"fecha": "2026-10-10", "artista": "X", "hora": hora, "sala": sala, "fuentes": [], "conflictos": []}
    r.update(kw)
    return r


def test_hora_habitual_de_la_sala():
    recs = [rec("21:00") for _ in range(8)] + [rec("20:00"), rec("22:30")] + [rec(None)]
    otra = [rec("20:00", sala="Otra"), rec("21:00", sala="Otra"), rec(None, sala="Otra")]
    conflicto = rec(None, conflictos=[{"campo": "hora", "versiones": [{"valor": "20:00"}, {"valor": "21:00"}]}])
    todos = recs + otra + [conflicto]
    assert estimar_horas(todos) == 1
    sin = recs[-1]
    assert sin["hora_estimada"]["hora"] == "21:00" and "8 de sus 10" in sin["hora_estimada"]["motivo"]
    assert "hora_estimada" not in otra[-1]       # Otra no tiene hora habitual clara
    assert "hora_estimada" not in conflicto       # con horas distintas en las webs no se estima
    e = estado_hora(sin)
    assert e["estado"] == "estimado" and e["valor"] == "21:00"


def test_origen_deducido_sin_falsos_positivos():
    """Nombre en español, solo agendas de salas madrileñas, programa municipal o tributo en sala no dicen de dónde es
    un grupo (medido: aciertan del 36 al 76 %). Solo coros, bandas municipales y escuelas de música."""
    loc = [{"id": "madridenvivo"}, {"id": "cc_buscador"}]
    casos = [rec(artista="Los Rayos", fuentes=loc, grupos=["pop e indie"]),
             rec(artista="LUCÍA FERNÁNDEZ", fuentes=loc),
             rec(artista="Concierto barroco", fuentes=[{"id": "datos_madrid"}]),
             rec(artista="Dire Straits Tribute", fuentes=loc, grupos=["tributos y versiones"]),
             rec(artista="ENCUENTRO CORAL INTERNACIONAL IBEROAMERICANO", fuentes=loc),
             rec(artista="Música coral para la memoria", fuentes=loc)]
    for r in casos:
        tributo_y_estimacion(r, {})
        assert "nacionalidad_estimada" not in r, r["artista"]
    for nombre in ("Orfeón de Moratalaz", "Banda de música de Policía municipal de Madrid", "Coro amabile"):
        r = rec(artista=nombre, fuentes=loc)
        tributo_y_estimacion(r, {})
        assert r["nacionalidad_estimada"] == "ES" and "agrupación local" in r["nacionalidad_estimada_motivo"]
