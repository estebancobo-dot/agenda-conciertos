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
    ({"pais_cita": "Los Chivatos son una banda gallega de punk rock"}, "la frase citada no está"),
    ({"pais_url": "https://blog.example/agenda", "pais_cita": "muchas bandas de punk rock madrileñas"}, "no nombra"),
    ({"pais_url": "https://www.instagram.com/loschivatos"}, "sin sesión"),
    ({"pais_url": "https://bloqueada.example/x"}, "robots.txt"),
    ({"pais": "AR"}, "no dice ese país"),
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
    assert "estilos" not in r["aceptado"] and "no dice ninguno" in r["rechazado"][0]


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
    assert not r["aceptado"] and "fecha" in r["rechazado"][0]


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
