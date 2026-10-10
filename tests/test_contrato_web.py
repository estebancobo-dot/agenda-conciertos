"""Los datos que escribe la lectura y la web que los lee hablan el mismo idioma (tools/web_datos.py ↔ site/index.html):

- la agenda ligera y los ficheros de detalle de cada día juntos traen cada concierto entero (y nada de lo oculto);
- todo lo que la tarjeta lee de un concierto antes de que llegue su detalle está en la agenda ligera (si no, la
  tarjeta saldría distinta hasta abrir el concierto);
- los campos de la agenda ligera existen en la lectura (un cambio de nombre en un lado rompería el otro sin aviso)."""
import json
import re
import sys
from pathlib import Path

from scraper import pipeline
from tests.fakefetch import FakeFetcher
from tests.test_recorrido import HOY
from tests.test_recorrido import entorno  # noqa: F401  (fixture: agendas y fichas fijas)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
import web_datos  # noqa: E402

WEB = (RAIZ / "site" / "index.html").read_text(encoding="utf-8")
# lo que pinta la tarjeta y deciden los filtros, con la agenda ligera (sin el detalle)
DE_LA_LISTA = ("card", "cardCompacta", "cardCuadricula", "horaCard", "estiloTags", "estadoMini", "cambioMini",
               "banderaDe", "confMini", "salaMini", "origenDe", "textoDe", "pasaGrupo", "gruposF", "grupos", "nivelDe",
               "cartelTags", "marcas", "color", "img", "etiquetaAgenda", "cartelCorto", "estilosDe")
# los que añade web_datos.ligero (resumen de un dato del detalle) y los que la web calcula y guarda en el concierto
DEL_RESUMEN = {"conflictos", "estilo_fuente", "agotado", "gf", "conf", "cambio", "evento", "img", "mini", "foto", "pmin"}
CALCULADOS = {"_card", "_cardC", "_cardG", "_conImg", "_e", "_g", "_gf", "_t", "_full"}
# del detalle, pero la tarjeta usa su resumen mientras no llega: confianza → conf, estado_evento → evento, imagen → img
CON_RESUMEN = {"confianza", "estado_evento", "imagen"}


def cuerpo(nombre: str) -> str:
    m = re.search(rf"(?:function {nombre}\(|const {nombre}=)", WEB)
    assert m, f"la web ya no tiene {nombre}: actualiza DE_LA_LISTA"
    fin = WEB.find("\n}", m.start()) if m.group(0).startswith("function") else WEB.find("\n", m.start())
    return WEB[m.start():fin]


def test_agenda_y_detalle_traen_cada_concierto_entero(entorno, tmp_path):  # noqa: F811
    pipeline.ejecutar(hoy=HOY, musicbrainz=False, pausa_reintento=0, fetcher=FakeFetcher({}))
    concerts = json.loads((entorno / "concerts.json").read_text())
    concerts["conciertos"][0]["oculto"] = {"motivo": "no es un concierto"}
    oculto = concerts["conciertos"][0]["id"]
    web_datos.preparar(concerts, tmp_path)
    agenda = json.loads((tmp_path / "agenda.json").read_text())
    ligeros = {r["id"]: r for r in agenda["conciertos"]}
    assert oculto not in ligeros  # lo oculto no llega a la web
    assert json.loads((tmp_path / "ocultos.json").read_text())[0]["motivo"] == "no es un concierto"
    for r in concerts["conciertos"][1:]:
        detalle = json.loads((tmp_path / agenda["detalles"].format(fecha=r["fecha"])).read_text())[r["id"]]
        assert detalle == r  # el detalle es el concierto entero
        for k, v in ligeros[r["id"]].items():  # y la agenda ligera, sus mismos datos (o su resumen)
            assert k in DEL_RESUMEN or v == r[k], k


def test_la_tarjeta_solo_lee_lo_que_trae_la_agenda_ligera():
    leidos = set()
    for f in DE_LA_LISTA:
        leidos |= set(re.findall(r"\br\.(\w+)", cuerpo(f)))
    faltan = leidos - set(web_datos.LIGEROS) - DEL_RESUMEN - CALCULADOS - CON_RESUMEN
    assert not faltan, f"la tarjeta lee campos que solo llegan con el detalle: {sorted(faltan)}"


def test_los_campos_de_la_agenda_ligera_existen_en_la_lectura():
    codigo = "\n".join(p.read_text(encoding="utf-8") for p in (RAIZ / "scraper").rglob("*.py"))
    for k in web_datos.LIGEROS:
        assert re.search(rf"[\"']{k}[\"']|\b{k}\s*[:=]", codigo), f"ningún sitio de la lectura escribe «{k}»"
