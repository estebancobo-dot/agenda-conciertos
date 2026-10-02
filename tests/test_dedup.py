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


def test_candlelight_es_clasica_no_tributo():
    # cuarteto de cuerda con versiones: lo decide el título aunque la agenda diga "tributo"
    r = run((ev("Tributo a Queen. Candlelight", "Círculo de Bellas Artes", estilo="Versiones/Tributos"), src("a")))[0]
    assert r["categoria"] == "clásica y lírica"


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


def test_cancelacion_solo_con_lectura_completa():
    from scraper.pipeline import conciliar
    s = src("mev")
    prev = run((ev("Grupo Q", "Sala El Sol"), s))
    prev[0]["id"] = "p1"
    # la fuente funcionó pero se cortó (tope de tiempo): no se marca como cancelado
    out = conciliar([], prev, HOY, {"mev": {"funciono": True, "brutos": 5, "completa": False}}, {"mev": s})
    assert out[0]["estado"] != "posiblemente cancelado"
    out = conciliar([], prev, HOY, {"mev": {"funciono": True, "brutos": 5, "completa": True}}, {"mev": s})
    assert out[0]["estado"] == "posiblemente cancelado"


def test_variantes_de_nombre_de_sala():
    from scraper.normalize import canon_sala
    assert misma_sala(canon_sala("Shoko"), canon_sala("Shoko Live"))
    assert misma_sala(canon_sala("Fotomatón Bar"), canon_sala("Fotomatón"))
    assert not misma_sala(canon_sala("Revi Live"), canon_sala("Revi Space"))
    assert not misma_sala(canon_sala("Sala B"), canon_sala("Sala But"))
    recs = run((ev("Toldos Verdes", "Shoko", invitados=["Garbí"]), src("cc")),
               (ev("RADAR JOVEN 2026 - MADRID EN VIVO 25 AÑOS: TOLDOS VERDES", "Shoko Live"), src("mev")))
    assert len(recs) == 1


def test_concierto_anunciado_dos_veces_en_la_misma_web_es_uno():
    # conciertos.club tenía a Devin Townsend a las 20:30 y a las 21:00 (dos fichas): es el mismo concierto
    recs = run((ev("Devin Townsend", "Revi Live"), src("revi", 1)),
               (ev("Devin Townsend", "Revi Live", "20:30"), src("cc")),
               (RawEvent(fecha=F, artista="Devin Townsend", url="https://x/otra", sala="Revi Live", ciudad="Madrid",
                         hora="21:00"), src("cc")))
    assert len(recs) == 1 and recs[0]["estado"] == "conflicto"


def test_sesiones_de_un_espectaculo_siguen_separadas():
    recs = run((ev("Tributo a Coldplay. Candlelight", "Ateneo de Madrid", "17:00"), src("cc")),
               (RawEvent(fecha=F, artista="Tributo a Coldplay. Candlelight", url="https://x/2", sala="Ateneo de Madrid",
                         ciudad="Madrid", hora="21:00"), src("cc")))
    assert len(recs) == 2


def test_variantes_de_nombre_en_la_misma_sala():
    recs = run((ev("Mikky Dee", "Revi Live"), src("revi", 1)), (ev("MIkkey Dee & Friends", "Revi Live", "20:00"), src("cc")))
    assert len(recs) == 1
    recs = run((ev("P.H.A.T", "Tempo Club", "21:00"), src("cc")),
               (ev("JAZZ CON SABOR A CLUB 26: P.H.A.T. (ITALIA) (Festival JazzMadrid)", "Tempo Club"), src("mev")))
    assert len(recs) == 1
    # nombres distintos con una palabra en común no se juntan
    assert len(run((ev("Tom & Jerry", "Sala El Sol", "21:00"), src("a")), (ev("Tom Waits", "Sala El Sol"), src("b")))) == 2


# ---------------------------------------------------------------- fase 3: cartel, festivales y ciclos
def test_festival_mismo_en_varias_agendas_con_su_cartel():
    # casos reales (2 oct. 2026): el mismo festival con otro nombre en otra agenda, y su cartel en el título
    recs = run((ev("Pirata Festival 2026 Madrid", "", "19:30"), src("laganzua")),
               (ev("Pirata Madrid Festival (Boikot, Evaristo, benito Kamelas, Reincidentes y más)", ""),
                src("rockforeveryone", prioridad=4)))
    assert len(recs) == 1
    r = recs[0]
    assert r["festival"] and r["artista"] == "Pirata Festival 2026 Madrid"
    assert r["invitados"] == ["Boikot", "Evaristo", "benito Kamelas", "Reincidentes"] and r["cartel_incompleto"]


def test_festival_sin_variantes_del_nombre_como_artistas():
    recs = run((ev("SAUROM JUGLAR FEST MADRID", "Recinto Ferial", None, ["Alestorm", "DARTAGNAN"]), src("laganzua")),
               (ev("Saurom Juglar Festival 2026", "Recinto Ferial"), src("cpm")),
               (ev("SAUROM JUGLAR FEST: SAUROM", "Recinto Ferial"), src("mariskal", prioridad=4)))
    assert len(recs) == 1
    r = recs[0]
    assert r["festival"] and r["artista"] == "SAUROM JUGLAR FEST MADRID"
    assert r["invitados"] == ["Alestorm", "DARTAGNAN", "SAUROM"]


def test_festival_de_songkick_por_su_nombre():
    e = ev("Cadena 100 Por Ellas 2026", "Movistar Arena", None, ["Rosana", "Fangoria", "Pablo López"])
    e.tipo = "festival"
    recs = run((e, src("songkick")), (ev("Cadena 100 Por Ellas Festival 2026", "Movistar Arena"), src("laganzua")))
    assert len(recs) == 1 and recs[0]["festival"] and recs[0]["invitados"] == ["Rosana", "Fangoria", "Pablo López"]


def test_artista_dentro_de_un_festival_es_su_ciclo_no_un_festival():
    r = run((ev("JAZZ CON SABOR A CLUB 26: SAN PATRICIO BIG BAND (Festival JazzMadrid)", "Sala Clamores"),
             src("madridenvivo")))[0]
    assert not r["festival"] and r["artista"] == "SAN PATRICIO BIG BAND"
    assert r["ciclo"] == "Festival JazzMadrid · JAZZ CON SABOR A CLUB 26"
    r = run((ev("Hällas", "Sala Nazca", "21:00", ["Komodor"]), src("cc")))[0]
    assert not r["festival"] and r["invitados"] == ["Komodor"] and not r["ciclo"]


def test_cartel_con_fichas_y_grupos_de_teloneros(monkeypatch):
    import scraper.artistas as art
    from scraper.pipeline import aplicar_cartel
    fichas = {"fleshcrawl": {"evidencias": [{"nombre": "Death Metal", "tipo": "estilo", "peso": 1.0, "fuente": "Discogs"}],
                             "pais": "DE"},
              "biznaga": {"evidencias": [{"nombre": "Punk", "tipo": "estilo", "peso": 1.0, "fuente": "Discogs"}],
                          "pais": "ES"}}
    monkeypatch.setattr(art, "ficha", lambda ent: ent)
    r = {"artista": "Avulsed", "invitados": ["Fleshcrawl", "Biznaga", "Desconocidos"], "grupos": ["rock y metal"],
         "fuentes": [], "estilo_fuente": []}
    aplicar_cartel(r, fichas)
    assert [x["nombre"] for x in r["cartel"]] == ["Fleshcrawl", "Biznaga", "Desconocidos"]
    assert r["cartel"][0]["pais"] == "DE" and r["cartel"][0]["grupos"] == ["rock y metal"]
    assert r["grupos_cartel"] == {"punk y garage": ["Biznaga"]}  # sale también al filtrar por punk
    # festival sin estilo propio: toma el de su cartel
    f = {"artista": "Madcore Fest", "festival": True, "invitados": ["Fleshcrawl"], "grupos": ["sin clasificar"],
         "fuentes": [], "estilo_fuente": []}
    aplicar_cartel(f, fichas)
    assert f["grupos"] == ["rock y metal"] and f["grupos_origen"] == "cartel del festival" and "grupos_cartel" not in f


def test_tope_de_tiempo_por_fuente():
    import time

    from scraper.pipeline import leer_fuente

    class F:
        def get(self, url, **kw):
            time.sleep(0.05)
            return "x"

        def robots_status(self, url):
            return "ok"

    def lector(ctx):
        for i in range(100):  # una agenda que no acaba nunca
            ctx.get(f"https://x/{i}")
            yield RawEvent(fecha=date(2026, 10, 17), artista=f"A{i}", url="u")
    s = Source("lenta", "Lenta", "https://x", "agregador", 3, "media", "lenta", lector, tope_seg=0.3)
    evs, res = leer_fuente(s, F(), HOY, date(2027, 1, 27), {})
    assert res["estado"] == "tope_de_tiempo" and res["funciono"] and not res["completa"]
    assert 2 <= len(evs) <= 8 and res["segundos"] < 1.5  # se queda con lo leído; el resto, de su caché


def test_codificacion_equivocada():
    from scraper.normalize import clean
    assert clean("Ed├®n") == "Edén" and clean("CafÃ© BerlÃ­n") == "Café Berlín"
    assert clean("Motörhead") == "Motörhead" and clean("Brujer├Ła") == "Brujería" and clean("┬ĀSarkrista") == "Sarkrista"
    # irreparable y con el mismo concierto bien escrito por otra web ese día en esa sala: se descarta
    recs = run((ev("Motörhits. Tributo a Motörhead", "Revi Live", "21:00"), src("mutick")),
               (ev("M├Č╢torHits", "Revi Live"), src("revi", prioridad=1)))
    assert [r["artista"] for r in recs] == ["Motörhits. Tributo a Motörhead"]
