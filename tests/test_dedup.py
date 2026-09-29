"""Deduplicación, fusión de fuentes, conflictos y prioridad entre fuentes."""
from datetime import date

from scraper.merge import Item
from scraper.model import RawEvent, Source
from scraper.normalize import canon_sala, misma_sala
from scraper.pipeline import preparar, unificar

HOY = date(2026, 9, 29)
F = date(2026, 10, 17)


def src(id_, prioridad=3, grupo=None, fiab="media"):
    return Source(id_, id_, "https://x/" + id_, "agregador", prioridad, fiab, grupo or id_)


def ev(artista, sala, hora=None, invitados=None, ciudad="Madrid", fecha=F, estilo=None):
    return RawEvent(fecha=fecha, artista=artista, url="https://x/" + artista, sala=sala, ciudad=ciudad, hora=hora,
                    invitados=invitados or [], estilo=estilo)


def run(*pares):
    items = [Item(e, s) for e, s in pares]
    items, _ = preparar(items, HOY, date(2027, 1, 27))
    return unificar(items)


def test_alias_de_salas():
    assert canon_sala("Lab Wagon") == canon_sala("sala lab") == canon_sala("Sala Wagon") == "Sala Wagon"
    assert canon_sala("Mon") == canon_sala("Sala Mon") == canon_sala("MON LIVE") == "Sala Mon Live"
    assert canon_sala("La Paqui") == "Sala But"
    assert canon_sala("Tempo Club") == "Tempo Audiophile Club"
    assert not misma_sala(canon_sala("Revi Live"), canon_sala("Revi Space"))
    assert not misma_sala(canon_sala("La Sala del Movistar Arena"), canon_sala("Movistar Arena"))


def test_mismo_concierto_se_fusiona_y_contrasta():
    recs = run((ev("Hällas", "Sala Nazca", "21:00"), src("cc")),
               (ev("HÄLLAS", "Nazca", "21:00", ["Komodor"]), src("hellpress")))
    assert len(recs) == 1
    r = recs[0]
    assert r["artista"] == "Hällas" and r["invitados"] == ["Komodor"] and r["sala"] == "Sala Nazca"
    assert r["estado"] == "contrastado" and len(r["fuentes"]) == 2


def test_artista_contra_invitados():
    recs = run((ev("Deep Purple", "Movistar Arena", invitados=["Jayler"]), src("a")),
               (ev("Jayler", "Movistar Arena", invitados=["Deep Purple"]), src("b")))
    assert len(recs) == 1


def test_misma_web_no_cuenta_como_contrastado():
    recs = run((ev("Sabbat", "Silikona"), src("cc_buscador", grupo="cc")),
               (ev("Sabbat", "Silikona"), src("cc_portada", grupo="cc")))
    assert len(recs) == 1 and recs[0]["estado"] == "1_fuente"


def test_conflicto_de_hora_mismo_nivel():
    recs = run((ev("Hällas", "Sala Nazca", "20:00"), src("laganzua")),
               (ev("Hällas", "Sala Nazca", "21:00"), src("cc")))
    r = recs[0]
    assert r["estado"] == "conflicto" and r["hora"] is None
    assert {v["valor"] for v in r["conflictos"][0]["versiones"]} == {"20:00", "21:00"}
    assert "Conflicto de hora" in r["notas"][0]


def test_hora_resuelta_por_prioridad():
    recs = run((ev("Sabbat", "Silikona", "20:00"), src("silikona_web", prioridad=1)),
               (ev("Sabbat", "Silikona", "21:00"), src("cc")))
    r = recs[0]
    assert r["hora"] == "20:00" and r["estado"] == "contrastado"
    assert "Resuelto por prioridad" in " ".join(r["notas"])


def test_conflicto_de_sala():
    recs = run((ev("Gloryhammer", "Sala But"), src("hellpress")),
               (ev("Gloryhammer", "Sala Mon"), src("songkick")))
    assert len(recs) == 1
    r = recs[0]
    assert r["estado"] == "conflicto" and r["sala"] == "Sala But / Sala Mon Live"
    assert r["conflictos"][0]["campo"] == "sala"


def test_sala_resuelta_por_web_oficial():
    recs = run((ev("Gloryhammer", "Sala But"), src("salabut", prioridad=1)),
               (ev("Gloryhammer", "Sala Mon"), src("songkick")))
    assert len(recs) == 1 and recs[0]["sala"] == "Sala But" and recs[0]["estado"] != "conflicto"


def test_conflicto_de_cartel_con_web_oficial():
    recs = run((ev("La Pestilencia", "Gruta 77", "21:30"), src("gruta77", prioridad=1)),
               (ev("Larsen", "Gruta 77", "21:30", ["Klobber"]), src("cc")))
    assert len(recs) == 2 and all(r["estado"] == "conflicto" for r in recs)


def test_dos_sesiones_mismo_dia_no_se_fusionan():
    recs = run((ev("WICKED, El Musical", "Nuevo Teatro Alcalá", "16:00"), src("songkick")),
               (ev("WICKED, El Musical", "Nuevo Teatro Alcalá", "20:00"), src("songkick")))
    assert len(recs) == 2 and all(r["estado"] != "conflicto" for r in recs)


def test_prefijo_de_ciclo():
    recs = run((ev("LOS VINAGRES", "Sala Villanos", "21:00"), src("villanos", prioridad=1)),
               (ev("Las Noches de Río Babel. Los Vinagres", "Sala Villanos", "21:00"), src("cc")))
    assert len(recs) == 1 and recs[0]["estado"] == "contrastado"


def test_misma_fuente_en_dos_salas_son_dos_eventos():
    recs = run((ev("Queen vs. ABBA Candlelight", "La Vega del Henares", ciudad="Alcalá de Henares"), src("cc")),
               (ev("Queen vs. ABBA Candlelight", "Exe Victoria Palace"), src("cc")))
    assert len(recs) == 2


def test_fuera_de_la_comunidad_se_descarta():
    # 'Palacio de los Deportes' también existe en Granada: se comprueba la ciudad
    recs = run((ev("Loquillo", "Palacio de los Deportes", ciudad="Granada"), src("x")),
               (ev("Europe", "La Nueva Cubierta", ciudad="Madrid"), src("y")))
    assert [r["artista"] for r in recs] == ["Europe"]
    assert recs[0]["municipio"] == "Leganés"  # la sala está en Leganés aunque la fuente diga 'Madrid'


def test_sin_estilo_es_sin_clasificar_y_en_foco():
    r = run((ev("Grupo X", "Sala El Sol"), src("a")))[0]
    assert r["categoria"] == "sin clasificar" and r["en_foco"] and r["estilo_fuente"] == []


def test_estilo_solo_de_la_fuente():
    r = run((ev("Grupo Y", "Sala El Sol", estilo="Metal/Rock duro"), src("a")))[0]
    assert r["categoria"] == "rock y metal"
    assert r["estilo_fuente"] == [{"estilo": "Metal/Rock duro", "fuente": "a"}]


def test_candlelight_fuera_de_foco():
    r = run((ev("Tributo a Queen. Candlelight", "Círculo de Bellas Artes", estilo="Versiones/Tributos"), src("a")))[0]
    assert r["categoria"] == "fuera de foco"


def test_nacionalidad_solo_si_la_da_la_fuente():
    r = run((ev("Grupo Z", "Sala El Sol"), src("a")))[0]
    assert r["nacionalidad"] is None
    e = ev("Samm", "Lula Club")
    e.nacionalidad = "BE"
    r = run((e, src("songkick")))[0]
    assert (r["nacionalidad"], r["nacionalidad_fuente"]) == ("BE", "songkick")


def test_una_sola_fuente_de_fiabilidad_baja():
    r = run((ev("Laura DSK", "Sala Mon"), src("mariskal", prioridad=4, fiab="baja")))[0]
    assert r["estado"] == "1_fuente" and any("fiabilidad baja" in n for n in r["notas"])
