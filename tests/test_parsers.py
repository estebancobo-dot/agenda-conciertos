"""Cada parser contra HTML real guardado en tests/fixtures (capturado el 29-09-2026)."""
from datetime import date
from pathlib import Path

import pytest

from scraper.normalize import municipio
from scraper.sources import agregadores as ag
from scraper.sources import blogs, conciertos_club as cc, otras, rock_metal as rm, salas
from scraper.sources.municipios import municipal_parse

HOY = date(2026, 9, 29)
FIX = Path(__file__).parent / "fixtures"


def html(name: str) -> str:
    return (FIX / f"{name}.html").read_text(encoding="utf-8")


def buscar(evs, fecha, artista):
    f = date.fromisoformat(fecha)
    return [e for e in evs if e.fecha == f and artista.lower() in e.artista.lower()]


def uno(evs, fecha, artista):
    r = buscar(evs, fecha, artista)
    assert r, f"no se encontró {artista} el {fecha}"
    return r[0]


# ---------------------------------------------------------------- A. agregadores
def test_conciertos_club_buscador():
    evs = cc.parse_list(html("cc_search"), "u")
    assert len(evs) == 140
    e = uno(evs, "2026-10-17", "Hällas")
    assert (e.hora, e.sala, e.precio) == ("21:00", "Sala Nazca", "28€")
    e = uno(evs, "2026-10-17", "Larsen")
    assert e.invitados == ["Klobber"] and e.sala == "Gruta 77" and e.estilo == "Rock/Rock Alternativo"
    e = uno(evs, "2026-10-17", "Amann")
    assert e.hora == "22:00" and e.sala == "Tempo Audiophile Club"
    # hora 00:00 = sin hora
    assert uno(evs, "2026-10-17", "Concierto de versiones").hora is None


def test_conciertos_club_estilo():
    evs = cc.parse_list(html("cc_estilo_metal"), "u")
    assert len(evs) == 59
    assert all(e.estilo == "Metal/Rock duro" for e in evs)
    e = uno(evs, "2026-10-01", "Saturna")
    assert e.invitados == ["Troy Torino"] and e.sala == "Dime que me Quieres"


def test_laganzua():
    evs = ag.laganzua_parse(html("laganzua_oct"), "u", HOY)
    assert len(evs) == 20
    e = uno(evs, "2026-10-01", "Blood Red Shoes")
    assert e.hora == "21:00" and e.sala == "Sala Moby Dick" and e.estilo == "Indie Rock, Post Punk"


def test_conciertospormadrid():
    evs = ag.cpm_parse(html("cpm_oct"), "u", HOY)
    e = uno(evs, "2026-10-20", "LAURA COX")
    assert e.sala == "Sala Villanos"
    e = uno(evs, "2026-10-10", "EUROPE")
    assert e.sala == "La Nueva Cubierta" and e.ciudad == "Leganés"
    e = uno(evs, "2026-10-02", "EVANESCENCE")
    assert e.invitados == ["NOVA TWINS", "POPPY"]


def test_madridenvivo_ajax():
    import json
    data = json.loads(html("mev_ajax_p1"))
    evs = ag.mev_parse(data["html"], "u", HOY, "Pop / Rock")
    assert len(evs) >= 5
    assert all(e.estilo == "Pop / Rock" and e.sala for e in evs)


def test_songkick():
    evs = ag.songkick_parse(html("songkick_madrid"), "u", HOY)
    assert len(evs) == 50
    e = uno(evs, "2026-09-29", "Isabel van Gelder")
    assert e.invitados == ["Orange Oak"] and e.hora == "20:00"
    e = uno(evs, "2026-09-30", "Lera Lynn")
    assert e.estilo == "folk_blues"


def test_rockandblog():
    evs = ag.rockandblog_parse(html("rockandblog"), "u", HOY)
    assert len(evs) == 106
    assert uno(evs, "2026-10-01", "Blood Red Shoes").sala == "Moby Dick Club"


def test_tm_blog_ignora_tachadas_y_separa_ciudad():
    evs = ag.tm_blog_parse(html("tm_blog_rock"), "u", HOY)
    assert not buscar(evs, "2026-01-17", "Robby Valentine")  # tachada (<del>)
    e = uno(evs, "2026-11-28", "Baron Rojo")
    assert (e.sala, e.ciudad) == ("La Riviera", "Madrid")


# ---------------------------------------------------------------- B. rock y metal
def test_metallegion():
    evs = rm.metallegion_parse(html("metallegion"), "u", HOY)
    e = uno(evs, "2026-11-14", "AMON AMARTH")
    assert e.invitados == ["ORBIT CULTURE", "SOILWORK"] and e.sala == "Palacio Vistalegre" and e.ciudad == "Madrid"


def test_hellpress():
    evs = rm.hellpress_parse(html("hellpress_agenda"), "u", HOY)
    e = uno(evs, "2026-10-18", "GLORYHAMMER")
    assert e.sala == "Sala But" and e.invitados == ["MAJESTICA", "ARION"]
    e = uno(evs, "2026-10-29", "TANKARD")
    assert e.sala == "Sala Independence" and e.invitados == ["HIDDEN", "EXODIA"]
    e = uno(evs, "2026-10-17", "HÄLLAS")
    assert e.sala == "Sala Nazca"


def test_parse_linea_formatos():
    assert rm.parse_linea("28 Noviembre - Leganés (Madrid) - La Cubierta", HOY)[1:3] == ("Leganés", "La Cubierta")
    assert rm.parse_linea("Sábado 10 de octubre de 2026 - Madrid (Leganés, La Nueva Cubierta)", HOY)[1:3] == (
        "Leganés", "La Nueva Cubierta")
    assert rm.parse_linea("7 noviembre – Palacio Vistalegre – Madrid", HOY)[1:3] == ("Madrid", "Palacio Vistalegre")
    assert rm.parse_linea("Martes 13 de octubre de 2026 | Nazca (Madrid) | Anticipada: 25€", HOY)[1:3] == (
        "Madrid", "Nazca")
    f, ciudad, sala, extra = rm.parse_linea(
        "29 de octubre de 2026 – Madrid (sala Independence | Nueva sala) + HIDDEN + EXODIA", HOY)
    assert (str(f), ciudad, sala, extra) == ("2026-10-29", "Madrid", "Sala Independence", ["HIDDEN", "EXODIA"])


def test_mariskal_fiabilidad_baja():
    evs = rm.mariskal_parse(html("mariskal"), "u", HOY)
    e = uno(evs, "2027-01-08", "ADRIAN VANDENBERG")
    assert e.invitados == ["TABÜ"] and e.sala == "Revi Live" and "fiabilidad baja" in e.nota


def test_madness():
    evs = rm.madness_parse(html("madness"), "u", HOY)
    e = uno(evs, "2026-10-21", "Myrath")
    assert e.invitados == ["Roses of Thieves"] and e.sala == "Revi Live"


def test_getrock():
    evs = rm.getrock_parse(html("getrock"), "u", HOY)
    e = uno(evs, "2026-10-18", "GLORYHAMMER")
    assert (e.sala, e.hora) == ("Sala But", "18:00") and e.invitados == ["Majestica", "Arion"]


def test_metalcry_ignora_hora():
    evs = otras.metalcry_parse(html("metalcry"), "u", HOY)
    e = uno(evs, "2026-11-03", "THE BROWNING")
    assert e.hora is None and e.sala == "Sala Nazca" and e.invitados == ["WITHIN DESTRUCTION", "ABBIE FALLS"]


def test_todoheavymetal():
    evs = otras.thm_parse(html("thm_agenda"), "u", HOY)
    e = uno(evs, "2027-02-05", "ATLANTEAN KODEX")
    assert (e.sala, e.ciudad) == ("Sala Silikona", "Madrid") and e.invitados == ["TRIUMPHER", "CRIMSON COVEN"]


def test_metalsymphony_articulo():
    evs = otras.articulo_agenda_parse(html("metalsymphony_art"), "u", HOY)
    assert uno(evs, "2026-10-17", "Hällas").sala == "Sala Nazca"
    e = uno(evs, "2026-11-08", "Joe Bonamassa")
    assert (e.sala, e.ciudad) == ("Palacio Vistalegre", "Madrid")


def test_neverland_tabla():
    evs = otras.articulo_agenda_parse(html("neverland"), "u", HOY)
    e = uno(evs, "2026-10-06", "Big Big Train")
    assert (e.sala, e.hora, e.ciudad) == ("La Sala del Movistar Arena", "19:45", "Madrid")


def test_rockforeveryone():
    evs = otras.rfe_parse(html("rfe_madrid_oct"), "u", HOY)
    e = uno(evs, "2026-10-17", "La Pestilencia")
    assert (e.sala, e.hora) == ("Sala Gruta 77", "21:30")
    assert uno(evs, "2026-10-07", "Mercury Rev").sala == "Sala Wagon"


def test_rockprog_calendario():
    evs = otras.rockprog_cal_parse(html("rockprog_agenda"), "u", HOY, 2026, 9)
    e = uno(evs, "2026-09-12", "Red Zone")
    assert e.ciudad == "Madrid"


# ---------------------------------------------------------------- C. blogs
def test_blog_dirtyrock_articulo():
    evs = blogs.parse_articulo(html("dirtyrock_art"), "u", HOY)
    assert [(str(e.fecha), e.artista, e.sala, e.ciudad) for e in evs] == [("2027-02-26", "Dirty Honey", "Mon", "Madrid")]


def test_blog_viriaor_articulo():
    evs = blogs.parse_articulo(html("viriaor_art"), "u", HOY)
    assert [(str(e.fecha), e.artista, e.sala) for e in evs] == [("2026-09-24", "THE VOLCANICS", "GRUTA 77")]


def test_blog_incremental_solo_lee_nuevas():
    from scraper.sources.base import Ctx
    from tests.fakefetch import FakeFetcher
    art = "https://www.dirtyrock.info/2026/09/dirty-honey-presentan-catch-my-butterfly-en-madrid-y-pamplona/"
    ff = FakeFetcher({"https://www.dirtyrock.info/category/giras/": FIX / "dirtyrock.html",
                      art: FIX / "dirtyrock_art.html",
                      "https://www.dirtyrock.info/2026/*": lambda u, kw: "<html><body><h1>x</h1></body></html>"})
    estado = {}
    evs = list(blogs.dirtyrock(Ctx(ff, HOY, date(2027, 1, 27), estado=estado)))
    assert any(e.artista == "Dirty Honey" for e in evs)
    n = ff.requests_count
    evs2 = list(blogs.dirtyrock(Ctx(ff, HOY, date(2027, 1, 27), estado=estado)))
    assert ff.requests_count == n + 1  # solo el listado: ninguna entrada nueva que leer
    assert any(e.artista == "Dirty Honey" for e in evs2)  # se conserva lo ya extraído


# ---------------------------------------------------------------- D. americana / blues
def test_mutick_momentazos():
    evs = otras.mutick_evento_parse(html("mutick_evento"), "u", HOY)
    assert len(evs) == 1
    e = evs[0]
    assert (e.artista, str(e.fecha), e.hora, e.nacionalidad) == ("STEVE WYNN & CHRIS CACAVAS", "2026-11-19", "21:30", "US")


def test_sociedad_blues():
    e = uno(otras.sbm_parse(html("sbm"), "u", HOY), "2026-10-03", "MIDNITE BRAWLERS")
    assert e.sala.startswith("Centro Cívico Zigia28") and "Blues" in e.estilo


def test_qconciertos():
    e = uno(otras.qconciertos_parse(html("qconciertos_madrid"), "u", HOY, None), "2026-09-30", "Noel McKay")
    assert e.sala == "Fun House"


def test_bigmama():
    evs = salas.secuencia(html("bigmama"), "u", HOY, orden="despues", sala="Big Mama Ballroom")
    assert [(str(e.fecha), e.hora, e.artista) for e in evs][0] == ("2026-10-03", "21:00", "Fine and Mellow Blues Night")


# ---------------------------------------------------------------- E. salas oficiales
@pytest.mark.parametrize("fn,fixture,fecha,artista,esperado", [
    (salas.gruta77_parse, "gruta77", "2026-10-02", "G.A.S. DRUMMERS", {"hora": "21:30", "estilo": "Punk Rock"}),
    (salas.gruta77_parse, "gruta77", "2026-10-09", "THE SLACKERS", {"sala": "Sala Copérnico", "nacionalidad": "US"}),
    (salas.villanos_parse, "villanos", "2026-10-03", "LOS VINAGRES", {"hora": "21:00", "estilo": "Rock"}),
    (salas.wurlitzer_parse, "wurlitzer", "2026-10-04", "YAWNING MAN", {"estilo": "PSYCH, DESERT ROCK, KRAUTROCK"}),
    (salas.rockville_parse, "rockville", "2026-10-04", "TOXIC RAVIOLIS", {"hora": "13:00",
                                                                          "estilo": "Versiones Rock-Metal"}),
    (salas.elsol_parse, "elsol", "2026-09-30", "LUCÍA FERNÁNDEZ", {"hora": "20:30"}),
    (salas.silikona_parse, "silikona", "2026-10-17", "SABBAT", {"hora": "20:00"}),
    (salas.revi_parse, "revi_eventos", "2026-10-17", "Leyenda", {"sala": "Revi Space"}),
    (salas.movistar_parse, "movistar", "2026-10-01", "Placebo", {"hora": "20:45", "sala": "Movistar Arena"}),
    (salas.riviera_parse, "riviera_conciertos", "2026-10-06", "GONDWANA", {"hora": "20:00"}),
    (salas.funhouse_parse, "funhouse", "2026-10-04", "MFC CHICKEN", {"hora": "19:00"}),
    (salas.mobydick_parse, "mobydick", "2026-10-01", "BLOOD RED SHOES", {"hora": "19:30"}),
    (salas.siroco_parse, "siroco", "2026-10-01", "Baloncesto", {"hora": "21:00"}),
    (salas.cubierta_parse, "nuevacubierta", "2026-10-10", "EUROPE", {"ciudad": "Leganés"}),
])
def test_salas(fn, fixture, fecha, artista, esperado):
    e = uno(fn(html(fixture), "u", HOY), fecha, artista)
    for k, v in esperado.items():
        assert getattr(e, k) == v, (k, getattr(e, k))


@pytest.mark.parametrize("fixture,fecha,artista", [
    ("nazca", "2026-10-17", "HÄLLAS"), ("wagon_home", "2026-10-08", "Primal Fear"),
    ("salabut", "2026-10-18", "GLORYHAMMER"), ("independance", "2026-10-29", "TANKARD"),
    ("clamores", "2026-10-02", "Clarence Bekker"), ("salab2", "2026-10-16", "GRETA"),
    ("chango2", "2026-10-07", "Mercury Rev"),
])
def test_salas_secuencia(fixture, fecha, artista):
    uno(salas.secuencia(html(fixture), "u", HOY, sala="X"), fecha, artista)


def test_galileo():
    e = uno(otras.galileo_parse(html("galileo"), "u", HOY), "2026-10-07", "Track Dogs")
    assert e.hora == "21:00"


def test_honky_mes_por_dia_semana():
    # la página no dice el mes: 'Martes 01' se interpreta como el martes 1 más cercano (1-sep-2026)
    evs = salas.honky_parse(html("honky"), "u", HOY)
    assert str(evs[0].fecha) == "2026-09-01"


# ---------------------------------------------------------------- F. municipios
def test_municipal_solo_musica():
    evs = municipal_parse(html("m_aranjuez"), "u", HOY, "Aranjuez")
    assert evs and all(municipio(e.ciudad) == "Aranjuez" for e in evs)
