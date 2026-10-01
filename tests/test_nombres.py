"""Nombre del artista para buscar su ficha (scraper/nombres.py)."""
import pytest

from scraper.nombres import claves_ficha, pais_del_titulo


@pytest.mark.parametrize("titulo,esperado", [
    ("Leiva", ["Leiva"]),
    ("Fiestas de Boadilla del Monte 2026. Siloé", ["Fiestas de Boadilla del Monte 2026. Siloé", "Siloé"]),
    ("Inverfest. Sho-Hai", ["Inverfest. Sho-Hai", "Sho-Hai"]),
    ("Kiko Veneno - Gira 2026", ["Kiko Veneno - Gira 2026", "Kiko Veneno"]),
    ("ACCEPT 50º ANIVERSARIO", ["ACCEPT 50º ANIVERSARIO", "ACCEPT"]),
    ("The SILENCERS (UK) en Madrid - CAMBIA A NAZCA", ["The SILENCERS (UK) en Madrid - CAMBIA A NAZCA", "The SILENCERS"]),
    ("LA BANDA EN OBRAS & MC CLAN", ["LA BANDA EN OBRAS & MC CLAN", "LA BANDA EN OBRAS"]),
    # tributos y espectáculos: nunca la ficha del homenajeado
    ("LA VAN GOGH (TRIB. LA OREJA DE VAN GOGH)", ["LA VAN GOGH (TRIB. LA OREJA DE VAN GOGH)"]),
    ("Queen vs. ABBA. Candlelight", ["Queen vs. ABBA. Candlelight"]),
    ("BLISS (Muse Tribute)", ["BLISS (Muse Tribute)"]),
])
def test_claves_ficha(titulo, esperado):
    assert claves_ficha({"artista": titulo}) == esperado


def test_tributo_por_la_agenda():
    assert claves_ficha({"artista": "Aurora & The Six", "categorias": ["tributos y versiones"]}) == ["Aurora & The Six"]


@pytest.mark.parametrize("titulo,pais", [
    ("THE SILENCERS (UK) en Madrid", "GB"), ("THE SCREAMIN' CHEETAH WHEELIES (USA)", "US"),
    ("JAZZ CON SABOR A CLUB 26: P.H.A.T. (ITALIA) (Festival JazzMadrid)", "IT"), ("AKONI ASTROBEAT (FR)", "FR"),
    ("BLISS (Muse Tribute)", None), ("Leiva", None), ("A (UK) y B (USA)", None),
])
def test_pais_del_titulo(titulo, pais):
    assert pais_del_titulo(titulo) == pais


def test_espectaculo_origen_no_aplica_y_pais_del_titulo():
    from scraper.pipeline import aplicar_ficha
    r = {"artista": "Los Miserables", "estilo_fuente": [{"estilo": "Musicales/Teatro musical", "fuente": "cc"}],
         "categorias": ["fuera de foco"], "fuentes": []}
    aplicar_ficha(r, None)
    assert r["origen_no_aplica"] and not r.get("nacionalidad")
    r = {"artista": "THE SILENCERS (UK) en Madrid", "estilo_fuente": [], "categorias": [], "fuentes": []}
    aplicar_ficha(r, None)
    assert (r["nacionalidad"], r["nacionalidad_fuente"]) == ("GB", "la agenda (en el título)")


def test_titulo_sin_letras_no_rompe():
    # un título solo con símbolos u otro alfabeto no da nombres que buscar (y no debe romper la ejecución)
    from scraper.musicbrainz import completar
    r = {"id": "x", "fecha": "2030-01-01", "artista": "★★★", "en_foco": True, "categorias": [], "fuentes": []}
    assert claves_ficha(r) == []
    completar([r], {}, __import__("datetime").date(2030, 1, 1), None, max_consultas=0)
