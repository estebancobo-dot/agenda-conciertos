"""Prueba real de una fuente registrada: ejecuta su lector completo (con robots.txt, identificación y ritmo, como
en la lectura de agendas), lo pasa por la misma preparación (ventana de fechas, ámbito de la Comunidad de Madrid) y
enseña cuántos conciertos da, de qué fechas y salas, y una muestra. Solo escribe en la salida.

Uso: python tools/probar_fuente.py ID [ID…]
"""
import collections
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper.fetch import Fetcher  # noqa: E402
from scraper.merge import Item  # noqa: E402
from scraper.pipeline import preparar  # noqa: E402
from scraper.registry import por_id  # noqa: E402
from scraper.sources.base import Ctx  # noqa: E402

hoy = date.today()
horizonte = hoy + timedelta(days=120)
S = por_id()
for sid in sys.argv[1:]:
    src = S[sid]
    print(f"\n## {sid} — {src.nombre} ({src.url})")
    ctx = Ctx(Fetcher(), hoy, horizonte)
    t0 = time.monotonic()
    try:
        evs = list(src.parser(ctx))
    except Exception as e:  # noqa: BLE001
        print(f"  ERROR: {type(e).__name__}: {e}")
        continue
    for e in evs:
        e.fuente = sid
    ok, fuera = preparar([Item(e, src) for e in evs], hoy, horizonte)
    print(f"  {len(evs)} eventos leídos en {ctx.pages} páginas ({time.monotonic() - t0:.0f} s); {len(ok)} dentro de "
          f"la ventana y la Comunidad; errores parciales: {ctx.errors[:5]}")
    print("  fuera:", {k: v for k, v in fuera.items() if not k.startswith("ejemplos")})
    if ok:
        fechas = sorted(i.ev.fecha for i in ok)
        print(f"  fechas: {fechas[0]} → {fechas[-1]}")
        print("  salas:", collections.Counter(i.ev.sala for i in ok).most_common(15))
        print("  con hora:", sum(bool(i.ev.hora) for i in ok), "· con precio:", sum(bool(i.ev.precio) for i in ok),
              "· con estilo:", sum(bool(i.ev.estilo) for i in ok))
    for i in ok[:40]:
        e = i.ev
        print(f"   - {e.fecha} {e.hora or '--:--'} · {e.artista[:60]} · {e.sala[:40]} · {e.precio or ''} · {e.estilo or ''}")

    # cómo encaja con la agenda actual (última lectura de todas las fuentes): con cuántos conciertos se une,
    # cuántos son nuevos y si aparecen conflictos (sala u hora) por nombrar distinto la misma sala
    import json  # noqa: E402

    from scraper.model import RawEvent  # noqa: E402
    from scraper.pipeline import unificar  # noqa: E402
    cache = json.loads((Path(__file__).resolve().parent.parent / "data" / "fuentes_cache.json").read_text())
    otros = [Item(RawEvent.from_dict(d), S[k]) for k, c in cache.items() if k in S and k != sid for d in c["eventos"]]
    for it in otros:
        it.ev.fuente = it.src.id
    otros, _ = preparar(otros, hoy, horizonte)
    recs = [r for r in unificar(otros + ok) if any(x["id"] == sid for x in r["fuentes"])]
    juntos = [r for r in recs if len({x["id"] for x in r["fuentes"]}) > 1]
    confl = [r for r in recs if r["conflictos"]]
    print(f"  en la agenda: {len(recs)} conciertos; {len(juntos)} unidos a los de otras fuentes, "
          f"{len(recs) - len(juntos)} nuevos; {len(confl)} con conflicto")
    for r in juntos[:15]:
        print(f"   = {r['fecha']} {r['artista'][:50]} · {r['sala'][:40]} · {[x['id'] for x in r['fuentes']]}")
    # los nuevos, con lo que haya ese día en la misma sala o con el mismo nombre (por si es el mismo y no se ha unido)
    from scraper.normalize import norm  # noqa: E402
    todos = unificar(otros)
    for r in [r for r in recs if r not in juntos][:120]:
        na, ns = norm(r["artista"]), norm(r["sala"])
        cerca = [o for o in todos if o["fecha"] == r["fecha"] and (
            (ns and norm(o["sala"]) and (ns in norm(o["sala"]) or norm(o["sala"]) in ns))
            or (na and (na in norm(o["artista"]) or norm(o["artista"]) in na)))]
        pista = " | ¿= " + "; ".join(f"{o['artista'][:30]} @ {o['sala'][:25]}" for o in cerca[:2]) if cerca else ""
        print(f"   + {r['fecha']} {r['artista'][:45]} · {r['sala'][:40]}{pista}")
    for r in confl[:15]:
        print(f"   ! {r['fecha']} {r['artista'][:50]} · {r['conflictos'][:1]}")
