"""robots.txt según RFC 9309, con comodines (probado con los robots.txt reales del 29-09-2026)."""
from pathlib import Path

from scraper.fetch import USER_AGENT as UA
from scraper.robots import Robots

R = Path(__file__).parent / "fixtures" / "robots"


def rob(n):
    return Robots((R / f"{n}.txt").read_text(encoding="utf-8"))


def test_comodines_prohiben():
    assert not rob("rb_deezer").can_fetch(UA, "https://api.deezer.com/search/artist?q=x")  # Disallow: /*
    assert not rob("rb_itunes").can_fetch(UA, "https://itunes.apple.com/search?term=x")     # Disallow: /search*
    assert not rob("rb_wdqs").can_fetch(UA, "https://query.wikidata.org/sparql?query=x")
    assert not rob("bc_robots").can_fetch(UA, "https://bandcamp.com/search?q=x")


def test_allow_mas_largo_gana():
    r = rob("rb_wikidata")
    assert r.can_fetch(UA, "https://www.wikidata.org/wiki/Special:EntityData/Q101505.json")
    assert not r.can_fetch(UA, "https://www.wikidata.org/w/api.php?action=wbgetentities")


def test_nuestras_urls_siguen_permitidas():
    assert rob("robots_cc").can_fetch(UA, "https://conciertos.club/madrid/conciertos/estilos/blues-rnb")
    assert not rob("robots_cc").can_fetch(UA, "https://conciertos.club/flamenco")
    assert rob("robots_songkick").can_fetch(UA, "https://www.songkick.com/metro-areas/28755-spain-madrid?page=2")
    assert rob("dc_robots").can_fetch(UA, "https://api.discogs.com/database/search?q=x&type=artist")
    assert rob("eswiki_robots").can_fetch(UA, "https://es.wikipedia.org/wiki/Los_Vinagres")
    assert not rob("eswiki_robots").can_fetch(UA, "https://es.wikipedia.org/w/api.php?action=parse")


def test_crawl_delay():
    assert rob("mb_robots").crawl_delay(UA) == 2
