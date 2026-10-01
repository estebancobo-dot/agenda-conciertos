from datetime import date

from scraper.clasificar import categoria_de, discogs
from scraper.normalize import (extrae_pais, load_json, municipio, norm, parse_fecha_texto, parse_hora,
                               split_artistas)


def test_179_municipios():
    d = load_json("municipios.json")
    assert len(d["municipios"]) == 179 == len(set(d["municipios"]))
    assert "Madrid" in d["municipios"] and "Rivas-Vaciamadrid" in d["municipios"]


def test_municipio():
    assert municipio("Leganés (Madrid)") == "Leganés"
    assert municipio("Madrid, Madrid") == "Madrid"
    assert municipio("Rivas") == "Rivas-Vaciamadrid"
    assert municipio("Vicálvaro") == "Madrid"
    assert municipio("Granada") is None and municipio("Barcelona") is None


def test_norm():
    assert norm("  Mägo de Oz! ") == "mago de oz"
    assert norm("Amann & the Wayward Sons") == "amann and the wayward sons"


def test_fechas_y_horas():
    hoy = date(2026, 9, 29)
    assert parse_fecha_texto("17 de octubre de 2026", hoy) == date(2026, 10, 17)
    assert parse_fecha_texto("sábado 17 octubre", hoy) == date(2026, 10, 17)
    assert parse_fecha_texto("5 enero", hoy) == date(2027, 1, 5)
    assert parse_fecha_texto("17/10/26", hoy) == date(2026, 10, 17)
    assert parse_hora("Puertas: 19:00 hrs") == "19:00" and parse_hora("21h") == "21:00"


def test_artistas_y_pais():
    assert split_artistas("Deep Purple + Jayler") == ("Deep Purple", ["Jayler"])
    assert extrae_pais("Samm (BE)") == ("Samm", "BE")
    assert extrae_pais("THE NOMADS (Suecia)") == ("THE NOMADS", "SE")
    assert extrae_pais("Grupo (en directo)") == ("Grupo (en directo)", None)


def test_categorias():
    assert categoria_de("Metal/Rock duro") == "rock y metal"
    assert categoria_de("Americana/Folk Rock/Country") == "americana/country/folk"
    assert categoria_de("Urbana/Reggaeton/Trap") == "urbana y hip hop"
    assert categoria_de("Versiones/Tributos") == "tributos y versiones"
    assert categoria_de(None) is None


def test_discogs_literal():
    assert discogs(["Indie Rock, Post Punk"]) == (["Indie Rock", "Post-Punk"], ["Rock"])
    assert discogs(["Músicas negras"]) == ([], [])


def test_relleno_no_es_invitado():
    from scraper.normalize import es_relleno
    from scraper.sources.base import make
    assert all(es_relleno(x) for x in ["INVITADOS ESPECIALES", "y más", "Banda invitada", "por confirmar", "DJ",
                                       "OFERTA ESPECIAL EN SKALLOWEEN MAD FEST"])
    assert not any(es_relleno(x) for x in ["Los Invitados", "Más Birras", "Dj Hueka", "Komodor"])
    e = make(date(2026, 10, 17), "SABBAT + Invitados especiales + Omission", "u")
    assert (e.artista, e.invitados) == ("SABBAT", ["Omission"])


def test_detecta_captcha_antibots():
    from pathlib import Path
    from scraper.fetch import es_antibot
    fix = Path(__file__).parent / "fixtures"
    assert es_antibot((fix / "galileo_captcha.html").read_text())  # SiteGround sgcaptcha (29-09-2026)
    assert not es_antibot((fix / "galileo.html").read_text())


def test_retry_after():
    from scraper.fetch import retry_after
    assert retry_after("30", 10) == 30 and retry_after(None, 10) == 10
    assert retry_after("Wed, 21 Oct 2026 07:28:00 GMT", 10) == 10 and retry_after("9999", 10) == 120
