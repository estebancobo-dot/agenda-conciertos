"""Prueba de concepto (no forma parte del rastreador): ¿funcionan las alternativas para leer AllMusic?

Se prueba con pocas peticiones y con artistas conocidos. Resultado en capturas/poc_allmusic/informe.json.
Claves opcionales (secrets): PARSEBOT_KEY, APIFY_TOKEN, ALLAPI_KEY. Sin clave se comprueba solo qué responde
el servicio (normalmente 401).
"""
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

import requests

OUT = Path("capturas/poc_allmusic")
OUT.mkdir(parents=True, exist_ok=True)
NAVEGADOR = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
             "Chrome/140.0 Safari/537.36")
NUESTRO = "AgendaConciertosMadridBot/2.0 (+https://github.com/estebancobo-dot/agenda-conciertos)"
informe = {}


def guardar(nombre, texto):
    (OUT / f"{nombre}.txt").write_text(str(texto)[:200000], encoding="utf-8")


def prueba(nombre):
    def deco(fn):
        t0 = time.monotonic()
        try:
            res = fn()
            informe[nombre] = {"ok": True, **res}
        except Exception as e:  # noqa: BLE001
            informe[nombre] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:500]}
            guardar(nombre + "_traza", traceback.format_exc())
        informe[nombre]["segundos"] = round(time.monotonic() - t0, 1)
        print(nombre, json.dumps(informe[nombre], ensure_ascii=False)[:600], flush=True)
        time.sleep(3)
    return deco


# 0. Referencia: ¿responde allmusic.com a una petición directa desde GitHub?
@prueba("0_allmusic_directo")
def _():
    out = {}
    for ua, etiqueta in ((NUESTRO, "ua_propio"), (NAVEGADOR, "ua_navegador")):
        for url in ("https://www.allmusic.com/robots.txt",
                    "https://www.allmusic.com/artist/deep-purple-mn0000192382"):
            r = requests.get(url, headers={"User-Agent": ua}, timeout=30)
            out[f"{etiqueta} {url.split('.com')[1]}"] = r.status_code
            guardar(f"0_{etiqueta}_{url.rsplit('/', 1)[-1] or 'raiz'}", r.text)
            time.sleep(3)
    return out


# 1. allmusic-python (GitHub jack-arms): scraper en Python
@prueba("1_allmusic_python")
def _():
    subprocess.run(["git", "clone", "-q", "--depth", "1", "https://github.com/jack-arms/allmusic-python",
                    "/tmp/allmusic_python"], check=True)
    fuente = Path("/tmp/allmusic_python/allmusic.py").read_text(encoding="utf-8", errors="ignore")
    guardar("1_codigo", fuente)
    sys.path.insert(0, "/tmp/allmusic_python")
    import allmusic as am  # noqa: E402
    funciones = [x for x in dir(am) if not x.startswith("_")]
    out = {"funciones": funciones}
    for cand in ("search", "search_artist", "artist_search", "get_artist", "Artist"):
        if hasattr(am, cand):
            try:
                obj = getattr(am, cand)("Deep Purple")
                out[f"{cand}('Deep Purple')"] = str(obj)[:800]
            except Exception as e:  # noqa: BLE001
                out[f"{cand}('Deep Purple')"] = f"{type(e).__name__}: {e}"[:300]
    return out


# 2. allmusic (PyPI 0.0.1): reseñas de álbumes
@prueba("2_allmusic_pypi")
def _():
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "allmusic"], check=True)
    # el clon de allmusic-python usa el mismo nombre de módulo: se aparta para importar el de PyPI
    sys.path[:] = [p for p in sys.path if p != "/tmp/allmusic_python"]
    sys.modules.pop("allmusic", None)
    import allmusic as am2  # noqa: E402
    out0 = getattr(am2, "__file__", "")
    out = {"modulo": out0, "funciones": [x for x in dir(am2) if not x.startswith("_")]}
    rv = am2.getAlbumReviewForAllMusicUrl("https://www.allmusic.com/album/beauty-and-the-beat-mw0000736440")
    out["resena"] = {k: str(getattr(rv, k, None))[:200] for k in ("album", "artist", "rating", "genre", "styles")}
    return out


# 3. Parse.bot (API REST con clave X-API-Key)
@prueba("3_parsebot")
def _():
    key = os.environ.get("PARSEBOT_KEY", "")
    url = ("https://api.parse.bot/scraper/d7a9ab92-2f81-4e05-9fcf-ab472eae476c/search_music"
           "?query=Deep%20Purple&search_type=artist")
    r = requests.get(url, headers={"X-API-Key": key} if key else {}, timeout=60)
    guardar("3_respuesta", r.text)
    return {"con_clave": bool(key), "status": r.status_code, "inicio": r.text[:400]}


# 4. Apify (actor lexis-solutions/allmusic-scraper, con token)
@prueba("4_apify")
def _():
    token = os.environ.get("APIFY_TOKEN", "")
    url = "https://api.apify.com/v2/acts/lexis-solutions~allmusic-scraper/run-sync-get-dataset-items"
    r = requests.post(url, params={"token": token} if token else {}, json={"searchQuery": "Deep Purple",
                                                                          "maxItems": 1}, timeout=300)
    guardar("4_respuesta", r.text)
    info = requests.get("https://api.apify.com/v2/acts/lexis-solutions~allmusic-scraper", timeout=30)
    guardar("4_actor", info.text)
    return {"con_token": bool(token), "status": r.status_code, "inicio": r.text[:400],
            "actor_publico_status": info.status_code}


# 5. AllAPI.io (una clave para muchas plataformas)
@prueba("5_allapi")
def _():
    doc = requests.get("https://www.allapi.io/platforms/allmusic.html", headers={"User-Agent": NAVEGADOR},
                       timeout=30)
    guardar("5_documentacion", doc.text)
    out = {"doc_status": doc.status_code}
    key = os.environ.get("ALLAPI_KEY", "")
    out["con_clave"] = bool(key)
    return out


(OUT / "informe.json").write_text(json.dumps(informe, indent=1, ensure_ascii=False), encoding="utf-8")
