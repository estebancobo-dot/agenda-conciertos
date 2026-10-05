"""Fase D: lo que aporta el chat solo se acepta si la página citada lo dice."""
import json
from datetime import date, timedelta

import pytest

from scraper import aportes as ap
from scraper.fetch import RobotsBlocked

BIO = """<html><head><title>Los Chivatos | Bandcamp</title></head><body>
<h1>Los Chivatos</h1><p>Los Chivatos son una banda madrileña de punk rock formada en 2015 en Vallecas.</p>
</body></html>"""
OTRA = "<html><body><p>Agenda de conciertos de octubre: muchas bandas de punk rock madrileñas.</p></body></html>"
SALA = """<html><body><h2>Los Chivatos</h2><p>Viernes 13 de noviembre de 2026 · Apertura de puertas 20:30 ·
Concierto 21:00 h · Entradas: 12 € anticipada / 15 € taquilla</p></body></html>"""
TICKET = """<html><body><h1>Los Chivatos en Madrid</h1><p>13/11/2026 - Sala Changó. Desde 12,00 €</p></body></html>"""
CANCELADO = """<html><body><h1>Los Chivatos</h1><p>13 nov 2026. Concierto CANCELADO por enfermedad.</p></body></html>"""


class F:
    def __init__(self, pags):
        self.pags = pags
        self.urls = []

    def get(self, url, **kw):
        self.urls.append(url)
        if url == "https://bloqueada.example/x":
            raise RobotsBlocked(url)
        if url not in self.pags:
            raise RuntimeError("404")
        return self.pags[url]


PAGS = {"https://loschivatos.bandcamp.com/": BIO, "https://blog.example/agenda": OTRA,
        "https://salachango.com/agenda/los-chivatos": SALA, "https://dice.fm/event/los-chivatos-madrid": TICKET,
        "https://salachango.com/agenda/cancelado": CANCELADO}
PEDIDO = {"nombre": "Los Chivatos", "clave": "los chivatos"}
CITA = "Los Chivatos son una banda madrileña de punk rock formada en 2015"


def lector():
    return ap.Lector(F(PAGS))


def test_artista_aceptado_con_pais_y_estilos():
    item = {"id": "a1", "identidad": "seguro", "pais": "ES", "ciudad": "Madrid",
            "pais_url": "https://loschivatos.bandcamp.com/", "pais_cita": CITA,
            "estilos": ["punk rock"], "estilos_url": "https://loschivatos.bandcamp.com/", "estilos_cita": CITA,
            "enlaces": ["https://loschivatos.bandcamp.com/", "https://www.instagram.com/loschivatos"]}
    r = ap.verificar_artista(item, PEDIDO, lector())
    assert r["aceptado"]["pais"]["valor"] == "ES"
    assert r["aceptado"]["estilos"]["valores"] == ["punk rock"] and r["aceptado"]["estilos"]["web_musica"]
    assert r["aceptado"]["enlaces"] == ["https://loschivatos.bandcamp.com/"]
    assert not r["rechazado"]


@pytest.mark.parametrize("cambio,motivo", [
    ({"pais": "GB", "pais_cita": "Los Chivatos son una banda británica de punk rock"}, "la frase citada no está"),
    ({"pais_url": "https://blog.example/agenda", "pais_cita": "muchas bandas de punk rock madrileñas"}, "no nombra"),
    ({"pais_url": "https://www.instagram.com/loschivatos"}, "sin sesión"),
    ({"pais_url": "https://bloqueada.example/x"}, "robots.txt"),
    ({"pais": "AR"}, "lo dicen junto al nombre"),
])
def test_pais_rechazado(cambio, motivo):
    item = {"identidad": "seguro", "pais": "ES", "pais_url": "https://loschivatos.bandcamp.com/", "pais_cita": CITA}
    item.update(cambio)
    r = ap.verificar_artista(item, PEDIDO, lector())
    assert "pais" not in r["aceptado"]
    assert any(motivo in m for m in r["rechazado"]), r["rechazado"]


def test_estilo_que_la_frase_no_dice_se_rechaza():
    item = {"identidad": "seguro", "estilos": ["heavy metal"], "estilos_url": "https://loschivatos.bandcamp.com/",
            "estilos_cita": CITA}
    r = ap.verificar_artista(item, PEDIDO, lector())
    assert "estilos" not in r["aceptado"] and "junto al nombre" in r["rechazado"][0]


def test_sin_frase_literal_vale_lo_que_dice_la_pagina_junto_al_nombre():
    # la frase del chat no es literal, pero la página dice "madrileña" y "punk rock" junto al nombre
    item = {"identidad": "seguro", "pais": "ES", "pais_url": "https://loschivatos.bandcamp.com/",
            "pais_cita": "grupo de Madrid de punk", "estilos": ["punk rock"],
            "estilos_url": "https://loschivatos.bandcamp.com/", "estilos_cita": "hacen punk rock"}
    r = ap.verificar_artista(item, PEDIDO, lector())
    assert r["aceptado"]["pais"]["valor"] == "ES" and "madrilena" in r["aceptado"]["pais"]["cita"]
    assert r["aceptado"]["estilos"]["valores"] == ["punk rock"]


def test_nombre_real_dentro_del_titulo():
    pag = "<html><body><p>Fabio Lione is an Italian singer of power metal.</p></body></html>"
    lec = ap.Lector(F({"https://w.example/fl": pag}))
    item = {"identidad": "seguro", "nombre_real": "Fabio Lione", "pais": "IT", "pais_url": "https://w.example/fl",
            "pais_cita": "Fabio Lione is an Italian singer"}
    r = ap.verificar_artista(item, {"nombre": "FABIO LIONE’S DAWN OF VICTORY"}, lec)
    assert r["aceptado"]["pais"]["valor"] == "IT"
    otro = dict(item, nombre_real="Otro Cantante")  # un nombre que no está en el título no vale
    assert not ap.verificar_artista(otro, {"nombre": "FABIO LIONE’S DAWN OF VICTORY"}, lec)["aceptado"]


def test_identidad_dudosa_no_acepta_nada():
    item = {"identidad": "dudoso", "pais": "ES", "pais_url": "https://loschivatos.bandcamp.com/", "pais_cita": CITA}
    r = ap.verificar_artista(item, PEDIDO, lector())
    assert not r["aceptado"] and r["rechazado"]


REC = {"fecha": "2026-11-13", "artista": "Los Chivatos", "sala": "Sala Changó", "hora": None, "precio": None}


def test_concierto_en_la_web_de_la_sala():
    item = {"url": "https://salachango.com/agenda/los-chivatos", "hora": "21:00", "precio": "12 €"}
    r = ap.verificar_concierto(item, REC, lector(), web_sala="https://www.salachango.com/")
    assert r["aceptado"]["hora"]["valor"] == "21:00" and r["aceptado"]["precio"]["valor"] == "12 €"
    assert "sala_oficial" in r["aceptado"] and "entradas" not in r["aceptado"]


def test_concierto_en_ticketera_y_dato_que_no_esta():
    item = {"url": "https://dice.fm/event/los-chivatos-madrid", "hora": "22:00", "precio": "desde 12,00 €"}
    r = ap.verificar_concierto(item, REC, lector())
    assert r["aceptado"]["entradas"]["url"] == item["url"] and r["aceptado"]["precio"]["valor"] == "desde 12,00 €"
    assert "hora" not in r["aceptado"] and any("22:00" in m for m in r["rechazado"])


def test_concierto_otra_fecha_se_rechaza():
    rec = dict(REC, fecha="2026-11-14")
    r = ap.verificar_concierto({"url": "https://salachango.com/agenda/los-chivatos", "hora": "21:00"}, rec, lector())
    assert not r["aceptado"] and "2026-11-14" in r["rechazado"][0]


def test_pagina_con_varios_conciertos_mira_junto_al_artista():
    pag = ("<html><body><h1>Los Chivatos</h1><p>Viernes 13 de noviembre de 2026. Concierto 21:00 h. 12 €</p>"
           + "<p>" + "texto de relleno " * 80 + "</p><h3>Otros conciertos</h3><p>Sábado 14 de noviembre de 2026: "
           "Otra Banda, 22:30 h, 40 €</p></body></html>")
    lec = ap.Lector(F({"https://sala.example/x": pag}))
    r = ap.verificar_concierto({"url": "https://sala.example/x", "hora": "22:30", "precio": "40 €"},
                               dict(REC, fecha="2026-11-14"), lec)
    assert not r["aceptado"]  # el 14 es de otra banda
    r = ap.verificar_concierto({"url": "https://sala.example/x", "hora": "22:30", "precio": "40 €"}, REC, lec)
    assert "hora" not in r["aceptado"] and "precio" not in r["aceptado"]  # la hora y el precio de la otra banda


def test_cancelacion_solo_si_la_pagina_la_dice():
    r = ap.verificar_concierto({"url": "https://salachango.com/agenda/cancelado", "estado": "cancelado"}, REC, lector())
    assert r["aceptado"]["estado"]["valor"] == "cancelado"
    r = ap.verificar_concierto({"url": "https://salachango.com/agenda/los-chivatos", "estado": "cancelado"}, REC,
                               lector())
    assert "estado" not in r["aceptado"]


def test_aplicar_solo_donde_falta():
    apo = {"artistas": {"los chivatos": {"pais": {"valor": "ES", "url": "https://loschivatos.bandcamp.com/",
                                                   "cita": CITA},
                                         "estilos": {"valores": ["punk rock"], "url": "https://x.bandcamp.com/",
                                                     "cita": CITA, "web_musica": True}}},
           "conciertos": [{"id": "x", "fecha": "2026-11-13", "artistas": ["Los Chivatos"], "salas": ["Sala Changó"],
                           "hora": {"valor": "21:00", "url": "https://salachango.com/a"},
                           "entradas": {"url": "https://dice.fm/e", "nombre": "Dice"},
                           "sala_oficial": {"url": "https://salachango.com/a"}}]}
    r = dict(REC, grupos=[], fuentes=[])
    ap.aplicar_artista(r, apo)
    assert r["nacionalidad"] == "ES" and "comprobada" in r["nacionalidad_fuente"]
    assert r["grupos"] == ["punk y garage"] and r["grupos_origen"] == "página citada"
    conocido = dict(REC, nacionalidad="AR", nacionalidad_fuente="Discogs", grupos=["rock y metal"],
                    grupos_origen="Discogs")
    ap.aplicar_artista(conocido, apo)
    assert conocido["nacionalidad"] == "AR" and conocido["grupos"] == ["rock y metal"]  # no pisa a una web de música
    recs = [dict(REC), dict(REC, hora="20:00", fecha="2026-11-13")]
    assert ap.aplicar_conciertos(recs, apo) == 2
    assert recs[0]["hora"] == "21:00" and recs[0]["entradas"]["nombre"] == "Dice" and recs[0]["confirmado_sala"]
    assert recs[1]["hora"] == "20:00"  # la hora que ya había no se toca


def test_generar_e_importar(tmp_path, monkeypatch):
    import tools.lotes as lotes
    hoy = date.today().isoformat()
    f1, f2 = (date.today() + timedelta(days=10)).isoformat(), (date.today() + timedelta(days=11)).isoformat()
    datos = {"conciertos": [
        {"fecha": f1, "artista": "Los Chivatos", "sala": "Sala Changó", "municipio": "Madrid",
         "fuentes": [{"id": "cc", "url": "https://cc/x"}], "estilo_fuente": [],
         "normalizacion": {"origen": {"estado": "desconocido"}, "estilo": {"estado": "desconocido"},
                           "hora": {"estado": "desconocido"}, "precio": {"estado": "conocido"}}},
        {"fecha": f2, "artista": "Gumbo Jam", "sala": "Big Mama",
         "normalizacion": {"origen": {"estado": "desconocido"}, "estilo": {"estado": "desconocido"}}}]}
    (tmp_path / "concerts.json").write_text(json.dumps(datos))
    monkeypatch.setattr(lotes, "DATA", tmp_path)
    monkeypatch.setattr(lotes, "APORTES", tmp_path / "aportes.json")
    lote, texto = lotes.generar("artistas", hoy=hoy)
    assert lote == f"A-{hoy}-01" and "Los Chivatos" in texto and "Gumbo Jam" not in texto  # una jam no se pregunta
    resp = "Aquí tienes:\n```json\n" + json.dumps({"lote": lote, "artistas": [
        {"id": "a1", "identidad": "seguro", "pais": "ES", "pais_url": "https://loschivatos.bandcamp.com/",
         "pais_cita": CITA, "estilos": ["punk rock"], "estilos_url": "https://loschivatos.bandcamp.com/",
         "estilos_cita": CITA}]}) + "\n```"
    inf = lotes.importar(resp, fetcher=F(PAGS), hoy=hoy)
    assert "2 datos aceptados" in inf
    apo = json.loads((tmp_path / "aportes.json").read_text())
    assert apo["artistas"]["los chivatos"]["pais"]["valor"] == "ES"
    # ya preguntado: no vuelve a salir; el siguiente lote es de conciertos
    lote2, texto2 = lotes.generar("auto", hoy=hoy)
    assert lote2.startswith("C-") and "Los Chivatos" in texto2 and "Gumbo" not in texto2
    with pytest.raises(ValueError):
        lotes.importar('{"lote": "A-1999-01-01-01", "artistas": []}', fetcher=F(PAGS), hoy=hoy)


def test_telonero_aparte_no_impide_unir_salas():
    from scraper.merge import _misma_fuente_dos_eventos
    a = {"artista": "Papa Roach", "invitados": [], "fuentes": [
        {"id": "totalstage", "url": "https://totalstage.vercel.app/concierto/Landmvrks/2026-12-04"},
        {"id": "hellpress", "url": "https://www.hellpress.com/noticias/papa-roach-show-madrid"}]}
    b = {"artista": "Papa Roach", "invitados": [], "fuentes": [
        {"id": "totalstage", "url": "https://totalstage.vercel.app/concierto/Papa%20Roach/2026-12-04"},
        {"id": "songkick", "url": "https://www.songkick.com/concerts/1-papa-roach-at-palacio-vistalegre"}]}
    assert not _misma_fuente_dos_eventos(a, b)
    c1 = {"artista": "Tributo a Queen. Candlelight", "invitados": [], "fuentes": [
        {"id": "cc_buscador", "url": "https://conciertos.club/madrid/conciertos/1-tributo-a-queen-candlelight"}]}
    c2 = {"artista": "Tributo a Queen. Candlelight", "invitados": [], "fuentes": [
        {"id": "cc_buscador", "url": "https://conciertos.club/madrid/conciertos/2-tributo-a-queen-candlelight"}]}
    assert _misma_fuente_dos_eventos(c1, c2)


def test_ocultos_no_salen_en_la_web(tmp_path):
    from tools.web_datos import preparar
    apo = {"ocultos": {"la cuota comedy": {"nombre": "La Cuota Comedy", "motivo": "monólogos de comedia"}}}
    a = {"id": "x1", "fecha": "2026-10-10", "artista": "La Cuota Comedy", "sala": "Galileo Galilei", "fuentes": []}
    b = {"id": "x2", "fecha": "2026-10-10", "artista": "Los Chivatos", "sala": "Sala Changó", "fuentes": []}
    for r in (a, b):
        ap.aplicar_artista(r, apo)
    assert a["oculto"]["motivo"] == "monólogos de comedia" and "oculto" not in b
    res = preparar({"conciertos": [a, b]}, tmp_path)
    assert res["conciertos"] == 1 and res["ocultos"] == 1
    assert json.loads((tmp_path / "ocultos.json").read_text())[0]["artista"] == "La Cuota Comedy"


def test_oculto_solo_en_su_sala():
    apo = {"ocultos": {"taylor swift": {"nombre": "TAYLOR SWIFT", "motivo": "fiesta temática", "salas": ["Sala But"]}}}
    fiesta = {"fecha": "2026-11-23", "artista": "TAYLOR SWIFT", "sala": "Sala But", "fuentes": []}
    concierto = {"fecha": "2027-06-01", "artista": "Taylor Swift", "sala": "Estadio Santiago Bernabéu", "fuentes": []}
    ap.aplicar_artista(fiesta, apo)
    ap.aplicar_artista(concierto, apo)
    assert fiesta.get("oculto") and not concierto.get("oculto")


def test_reglas_no_concierto():
    for t in ("Real Madrid vs", "Movistar Estudiantes vs", "FURI DJ", "DJ TAZZMANIA", "Fast Expo Laura Blanco",
              "KARAOKE CANALLA", "La Cuota Comedy", "Presentación festival", "Warren Sonbert. Sesión de cortometrajes I"):
        assert ap.no_es_concierto(t), t
    for t in ("Baloncesto", "Queen vs. ABBA. Candlelight", "Concierto y Exposición de Guitarras", "Niños Bravos",
              "Dj Nano en directo", "Antonio Reyes presenta “Maestros”", "Un pingüino en mi ascensor", "Jam Session Jazz"):
        assert not ap.no_es_concierto(t), t


def test_regla_se_puede_deshacer():
    r = {"fecha": "2026-10-08", "artista": "FURI DJ", "sala": "Thundercat", "fuentes": []}
    ap.aplicar_artista(r, {})
    assert r["oculto"]["regla"]
    ap.aplicar_artista(r, {"mostrar": {"furi dj": {"nombre": "FURI DJ"}}})
    assert not r.get("oculto")


def test_tributos_solo_en_su_grupo():
    from scraper.nombres import agrupar_tributo, es_tributo
    r = {"artista": "BOYS STILL CRY: TRIBUTO A THE CURE", "grupos": ["rock y metal"], "categoria": "rock y metal",
         "grupos_generico": True, "estilos_discogs": ["Post-Punk"]}
    agrupar_tributo(r)
    assert r["grupos"] == ["tributos y versiones"] and r["estilo_tributo"] == ["rock y metal"]
    assert r["estilos_discogs"] == ["Post-Punk"] and not r["grupos_generico"] and not r["en_foco"]
    # la agenda lo etiqueta como tributo aunque el título no lo diga
    assert es_tributo({"artista": "gREAT sTRAITS", "categorias": ["tributos y versiones"]})
    assert es_tributo({"artista": "Tributo a Queen. Candlelight"})
    assert not es_tributo({"artista": "Banda de música de Policía municipal de Madrid"})
    assert not es_tributo({"artista": "Leiva", "categorias": ["pop e indie"]})


def test_ciclo_inverfest_fuera_del_artista():
    from scraper.merge import separar_ciclo
    for titulo, artista in [("Inverfest. Marwan", "Marwan"), ("INVERFEST 2026: NACHO SARRIA", "NACHO SARRIA"),
                            ("Inverfest Fito & Fitipaldis", "Fito & Fitipaldis")]:
        r = {"artista": titulo, "ciclo": None}
        separar_ciclo(r)
        assert r["artista"] == artista and r["ciclo"].lower().startswith("inverfest")
    r = {"artista": "INVERFEST 2026", "ciclo": None}
    separar_ciclo(r)
    assert r["artista"] == "INVERFEST 2026"


def test_claves_antiguas_con_ciclo():
    assert ap.clave_artista("Inverfest. Marwan") == ap.clave_artista("Marwan")
    apo = ap.normalizar_claves({"artistas": {"inverfest marwan": {"pais": 1}, "marwan": {"pais": 2}},
                                "consultados": {"a:inverfest sienna": {}, "c:x": {}}})
    assert apo["artistas"] == {"marwan": {"pais": 2}}
    assert set(apo["consultados"]) == {"a:sienna", "c:x"}


def test_estilo_y_origen_por_el_titulo_y_el_tipo_de_grupo():
    from scraper.clasificar import estilo_de_titulo
    from scraper.pipeline import pais_por_tipo_local
    assert estilo_de_titulo("Coro de castañuelas de Madrid") == ("clásica y lírica", "Choral")
    assert estilo_de_titulo("Concierto: Boleros con alma") == ("latina", "Bolero")
    assert estilo_de_titulo("Concierto sinfónico de bandas sonoras") == ("clásica y lírica", "Score")
    assert estilo_de_titulo("Orquesta Mondragón") is None  # un grupo de pop, no una orquesta
    assert estilo_de_titulo("Los Planetas") is None
    muni = [{"id": "datos_madrid"}]
    assert pais_por_tipo_local({"artista": "Orfeón de Moratalaz", "fuentes": [{"id": "songkick"}]})[0] == "ES"
    assert pais_por_tipo_local({"artista": "Concierto barroco", "fuentes": muni})[0] == "ES"
    assert pais_por_tipo_local({"artista": "Over the rainbow", "fuentes": muni})[0] is None  # en inglés
    trib = {"artista": "Dire Straits Tribute", "grupos": ["tributos y versiones"], "categorias": []}
    assert pais_por_tipo_local({**trib, "fuentes": [{"id": "madridenvivo"}]})[0] == "ES"
    assert pais_por_tipo_local({**trib, "fuentes": [{"id": "songkick"}]})[0] is None  # gira, gran recinto


def test_halloween_y_jam_y_latina():
    assert ap.no_es_concierto("AFROJAM HALLOWEEN PARTY") == "fiesta de Halloween"
    assert ap.no_es_concierto("Gran fiesta de Halloween con The Exploding Boys") is None
    assert ap.no_es_concierto("Concierto especial Halloween") is None
    from scraper.pipeline import aplicar_ficha, tributo_y_estimacion
    r = {"artista": "On Fire Jam!", "fuentes": [{"id": "cc_buscador"}], "estilo_fuente": [], "categorias": []}
    aplicar_ficha(r, None)
    assert r["grupos"] == ["rock y metal", "pop e indie"] and r["grupos_origen"] == "título (jam)"
    r = {"artista": "Los Hermanos Rodríguez", "grupos": ["latina"], "fuentes": [{"id": "cc_buscador"}]}
    tributo_y_estimacion(r, {})
    assert r.get("nacionalidad_estimada") in ("LATAM", None)
