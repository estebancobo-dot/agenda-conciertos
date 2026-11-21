"""ReccoBeats: Spotify y último disco solo si se sabe que es el mismo artista (nunca por el nombre solo)."""
import json

from scraper import reccobeats as rb

BUENO = {"id": "rb-1", "name": "Vetusta Morla", "href": "https://open.spotify.com/artist/6J6yx1t3nwIDyPXk5xa7O8"}
OTRO = {"id": "rb-2", "name": "Vetusta Morla", "href": "https://open.spotify.com/artist/2HfVTWz1WoiwBnJhbqFzII"}
DISCOS = [{"albumType": "single", "name": "¡Ay, Madrid!", "releaseDate": "2024-05-09", "releaseDateFormat": "day",
           "label": "Pequeño Salto Mortal", "href": "https://open.spotify.com/album/3NyH"},
          {"albumType": "album", "name": "FIGURANTES", "releaseDate": "2024-05-31", "releaseDateFormat": "day",
           "label": "Pequeño Salto Mortal", "href": "https://open.spotify.com/album/5vop"},
          {"albumType": "album", "name": "Mismo sitio, distinto lugar", "releaseDate": "2017-11-10",
           "releaseDateFormat": "day", "label": "Pequeño Salto Mortal", "href": "u"}]
MB = {"release-groups": [{"title": "FIGURANTES"}, {"title": "Mismo sitio, distinto lugar"}, {"title": "La deriva"}]}
ENT = {"nombre": "Vetusta Morla", "musicbrainz": {"encontrado": True, "mbid": "b185"}}


class F:
    def __init__(self, resp):
        self.resp, self.urls = resp, []

    def get(self, url, **kw):
        self.urls.append(url)
        for clave, v in self.resp.items():
            if clave in url:
                return json.dumps(v)
        raise AssertionError(url)


def api(candidatos, discos_de):
    r = {"artist/search": {"content": candidatos}}
    for rid, d in discos_de.items():
        r[f"artist/{rid}/album"] = {"content": d, "totalPages": 1}
    return F(r)


def test_entre_homonimos_elige_el_que_comparte_discos():
    f = api([BUENO, OTRO], {"rb-1": DISCOS, "rb-2": []})
    r = rb.buscar(f, F({"release-group": MB}), F({}), "Vetusta Morla", ENT)
    assert r["encontrado"] and r["spotify"] == "6J6yx1t3nwIDyPXk5xa7O8"
    assert r["identificado_por"] == "2 discos en común con MusicBrainz"
    # el último álbum (no el single, aunque sea anterior al álbum) con su fecha y sello
    assert r["ultimo"] == {"titulo": "FIGURANTES", "fecha": "2024-05-31", "tipo": "album",
                           "sello": "Pequeño Salto Mortal", "url": "https://open.spotify.com/album/5vop"}


def test_sin_dos_discos_en_comun_no_se_pone_nada():
    f = api([BUENO], {"rb-1": DISCOS[:2]})   # solo FIGURANTES en común
    r = rb.buscar(f, F({"release-group": MB}), F({}), "Vetusta Morla", ENT)
    assert not r["encontrado"] and "dos discos" in r["motivo"]


def test_dos_candidatos_validos_no_se_elige():
    f = api([BUENO, OTRO], {"rb-1": DISCOS, "rb-2": DISCOS})
    r = rb.buscar(f, F({"release-group": MB}), F({}), "Vetusta Morla", ENT)
    assert not r["encontrado"] and "varios" in r["motivo"]


def test_spotify_de_wikidata_es_identidad_exacta():
    ent = {"nombre": "Vetusta Morla", "wikidata": {"ids": {"spotify": "2HfVTWz1WoiwBnJhbqFzII"}}}
    f = api([BUENO, OTRO], {"rb-2": DISCOS})
    r = rb.buscar(f, F({}), F({}), "Vetusta Morla", ent)
    assert r["encontrado"] and r["spotify"] == "2HfVTWz1WoiwBnJhbqFzII" and r["identificado_por"] == "su Spotify en Wikidata"


def test_busca_sin_tildes_y_compara_el_nombre_exacto():
    # primero tal cual ("Pablo Alborán" solo sale con tilde) y, si no, sin tildes ("Angel Stanich" solo sale sin ella)
    class Busca(F):
        def get(self, url, **kw):
            if "searchText=%C3%81ngel" in url:
                self.urls.append(url)
                return json.dumps({"content": []})
            return super().get(url, **kw)
    f = Busca({"artist/search": {"content": [{"id": "x", "name": "Angel Stanich", "href": "https://open.spotify.com/artist/1S3q"}]},
               "artist/x/album": {"content": DISCOS, "totalPages": 1}})
    r = rb.buscar(f, F({"release-group": MB}), F({}), "Ángel Stanich", {"musicbrainz": {"encontrado": True, "mbid": "m"}})
    assert "searchText=%C3%81ngel%20Stanich" in f.urls[0] and "searchText=Angel%20Stanich" in f.urls[1]
    assert r["encontrado"]


def test_sin_discografia_de_referencia_no_se_adivina():
    f = api([BUENO], {"rb-1": DISCOS})
    r = rb.buscar(f, F({}), F({}), "Vetusta Morla", {"nombre": "Vetusta Morla", "wikipedia": {"encontrado": True}})
    assert not r["encontrado"] and "referencia" in r["motivo"]


def test_ficha_con_spotify_y_ultimo_disco():
    from scraper.artistas import ficha
    ent = {"nombre": "Vetusta Morla", "discogs": {"encontrado": True, "url": "https://www.discogs.com/artist/1"},
           "reccobeats": {"encontrado": True, "v": rb.VERSION, "spotify": "6J6y", "identificado_por": "33 discos en común",
                          "ultimo": {"titulo": "FIGURANTES", "fecha": "2024-05-31", "tipo": "album", "sello": "PSM",
                                     "url": "u"}}}
    f = ficha(ent)
    assert {"nombre": "Spotify", "url": "https://open.spotify.com/artist/6J6y"} in f["enlaces"]
    assert f["ultimo_disco"]["titulo"] == "FIGURANTES" and f["ultimo_disco"]["identificado_por"] == "33 discos en común"
    # no encontrado: ni enlace ni disco
    ent["reccobeats"] = {"encontrado": False, "v": rb.VERSION, "motivo": "x"}
    f = ficha(ent)
    assert not any(e["nombre"] == "Spotify" for e in f["enlaces"]) and f["ultimo_disco"] is None


def test_titulos_comparables():
    assert rb.titulo_disco("Finisterre [directo Estadio Metropolitano]") == rb.titulo_disco("Finisterre")
    assert rb.titulo_disco("La Deriva - Remastered 2020") == rb.titulo_disco("La deriva")
