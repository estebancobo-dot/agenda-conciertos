"""ReccoBeats (api.reccobeats.com): gratuita y sin clave, con el catálogo de Spotify (artistas, discos, fechas y
sellos). Da a la ficha del artista su página de Spotify y su último disco.

Tiene artistas repetidos con el mismo nombre (dos «Vetusta Morla»), así que nunca se elige por el nombre:
  - si Wikidata ya da su Spotify, se usa ese artista (identidad exacta);
  - si no, solo se acepta un candidato que comparta al menos dos discos con la discografía que ya se conoce del
    artista (MusicBrainz o Discogs), y que sea el único que lo hace. Si no, no se pone nada.

Es un servicio gratuito sin garantías: si falla, la ficha sigue igual y se reintenta en otra pasada."""
from __future__ import annotations

import json
import re
import unicodedata
from urllib.parse import quote

from .fetch import Fetcher
from .normalize import norm

API = "https://api.reccobeats.com/v1"
MB_DISCOS = "https://musicbrainz.org/ws/2/release-group?artist={mbid}&limit=100&fmt=json"
DC_DISCOS = "https://api.discogs.com/artists/{id}/releases?per_page=100"
MAX_CANDIDATOS = 4
VERSION = 1


def fetcher_reccobeats() -> Fetcher:
    return Fetcher(min_interval=1.0)  # no publica límite: una petición por segundo (avisa con 429 si es mucho)


def _sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def titulo_disco(t: str) -> str:
    """Título comparable: sin '(feat. …)', '[Directo]', '- Remastered', '- EP'…"""
    t = re.sub(r"\s*[(\[][^)\]]*[)\]]", "", t or "")
    t = re.sub(r"(?i)\s+-\s+(remaster(ed)?|ep|single|live|en directo|deluxe)\b.*$", "", t)
    return norm(t)


def _spotify_id(href: str | None) -> str | None:
    m = re.search(r"open\.spotify\.com/(?:intl-\w+/)?(?:artist|album)/([A-Za-z0-9]+)", href or "")
    return m.group(1) if m else None


def discos_referencia(f_mb: Fetcher, f_dc: Fetcher, ent: dict) -> tuple[set[str], str]:
    """Títulos de sus discos según MusicBrainz o, si no, Discogs (los artistas que esas webs ya identifican)."""
    mb = ent.get("musicbrainz") or {}
    mbid = (mb.get("mbid") if mb.get("encontrado") else None) or ((ent.get("wikidata") or {}).get("ids") or {}).get("musicbrainz")
    if mbid:
        # la API /ws/2 de MusicBrainz, como en scraper/musicbrainz.py (su robots.txt es para las páginas web)
        d = json.loads(f_mb.get(MB_DISCOS.format(mbid=mbid), check_robots=False,
                                headers={"Accept": "application/json"}))
        t = {titulo_disco(r.get("title") or "") for r in d.get("release-groups") or []} - {""}
        if t:
            return t, "MusicBrainz"
    dc = ent.get("discogs") or {}
    if dc.get("encontrado") and dc.get("id"):
        d = json.loads(f_dc.get(DC_DISCOS.format(id=dc["id"])))
        t = {titulo_disco(r.get("title") or "") for r in d.get("releases") or []} - {""}
        if t:
            return t, "Discogs"
    return set(), ""


def _discos(f: Fetcher, rid: str) -> list[dict]:
    out = []
    for pagina in range(3):
        d = json.loads(f.get(f"{API}/artist/{rid}/album?size=50&page={pagina}"))
        out += d.get("content") or []
        if pagina + 1 >= int(d.get("totalPages") or 1):
            break
    return out


def ultimo_disco(discos: list[dict]) -> dict | None:
    """El disco (álbum) más reciente; si no tiene ninguno, el último single. Con la fecha tal como la da Spotify
    (día, mes o solo año)."""
    for tipo in ("album", "single"):
        lista = [d for d in discos if d.get("albumType") == tipo and re.match(r"\d{4}", str(d.get("releaseDate") or ""))]
        if lista:
            d = max(lista, key=lambda x: str(x["releaseDate"]))
            fmt = d.get("releaseDateFormat") or "day"
            fecha = str(d["releaseDate"])[: {"year": 4, "month": 7}.get(fmt, 10)]
            return {"titulo": d.get("name") or "", "fecha": fecha, "tipo": tipo, "sello": d.get("label") or None,
                    "url": d.get("href") or None}
    return None


def buscar(f: Fetcher, f_mb: Fetcher, f_dc: Fetcher, nombre: str, ent: dict) -> dict:
    sp_wd = ((ent.get("wikidata") or {}).get("ids") or {}).get("spotify")
    # su buscador compara el texto tal cual: «Pablo Alborán» solo sale con tilde y «Angel Stanich» solo sin ella
    d, exactos = {}, []
    for q in dict.fromkeys([nombre, _sin_tildes(nombre)]):
        d = json.loads(f.get(f"{API}/artist/search?searchText={quote(q)}&size=25"))
        exactos = [c for c in d.get("content") or [] if norm(_sin_tildes(c.get("name") or "")) == norm(_sin_tildes(nombre))]
        if exactos:
            break
    if sp_wd:
        c = next((c for c in exactos + (d.get("content") or []) if _spotify_id(c.get("href")) == sp_wd), None)
        if not c:
            return {"encontrado": False, "v": VERSION, "motivo": "su Spotify (de Wikidata) no está en ReccoBeats"}
        return {"encontrado": True, "v": VERSION, "spotify": sp_wd, "nombre": c.get("name"),
                "identificado_por": "su Spotify en Wikidata", "ultimo": ultimo_disco(_discos(f, c["id"]))}
    if not exactos:
        return {"encontrado": False, "v": VERSION, "motivo": "ningún artista con ese nombre exacto"}
    ref, fuente = discos_referencia(f_mb, f_dc, ent)
    if not ref:
        return {"encontrado": False, "v": VERSION, "motivo": "sin discografía de referencia para comprobar quién es"}
    validos = []
    for c in exactos[:MAX_CANDIDATOS]:
        discos = _discos(f, c["id"])
        comunes = {titulo_disco(x.get("name") or "") for x in discos} & ref
        if len(comunes) >= 2:
            validos.append((c, discos, comunes))
    if len(validos) != 1:
        motivo = ("varios artistas con ese nombre comparten discos con " + fuente) if validos else \
            f"ningún artista con ese nombre comparte al menos dos discos con {fuente}"
        return {"encontrado": False, "v": VERSION, "motivo": motivo, "candidatos": len(exactos)}
    c, discos, comunes = validos[0]
    return {"encontrado": True, "v": VERSION, "spotify": _spotify_id(c.get("href")), "nombre": c.get("name"),
            "identificado_por": f"{len(comunes)} discos en común con {fuente}", "ultimo": ultimo_disco(discos)}
