"""Café Berlín: su programa en HTML (día, mes sin año, nombre, hora, precio, enlace de compra); sin Berlín Club."""
from datetime import date

from scraper.sources.salas import berlin_parse


def tarjeta(clase, dia, mes, nombre, h5, compra):
    return f"""<div class="isotope-item all {clase}"><article class="programas-lista-programa"><div class="row">
<div class="fecha-evento"><div><div class="evento-fecha-dia-nombre">Mié</div><div class="evento-fecha-dia">{dia}</div>
<div class="pb-2 evento-fecha-mes">{mes}</div></div></div><div class="programa-informacion">
<a href="https://berlincafe.es/programa/{nombre.lower().replace(' ', '-')}/"><h2 class="h1 my-0">{nombre}</h2></a>
<h5 class="my-0 font-400"> {h5} </h5></div><div><a class="btn-entradas" href="{compra}">ENTRADAS</a></div></div>
</article></div>"""


HTML = "".join([
    tarjeta("cafe-berlin", "07", "Oct", "Kike M. Fin de Gira", "20:00 <br/> Entradas desde: 14€",
            "https://cafeberlinentradas.com/events/kike-m"),
    tarjeta("berlin-club", "08", "Oct", "Sesión DJ", "00:30", "https://x.com/dj"),
    tarjeta("cafe-berlin", "09", "Ene", "Concierto de enero", "22:30 <br/> Entradas desde: 16,58€",
            "https://dice.fm/event/abc"),
    tarjeta("cafe-berlin", "01", "Sep", "Ya pasó", "20:00", "https://dice.fm/event/old"),
    tarjeta("cafe-berlin", "25", "Oct", "Blokk Sessions", "21:30", "https://dice.fm/event/b2"),
    tarjeta("cafe-berlin", "25", "Oct", "Blokk Sessions", "19:00", "https://dice.fm/event/b1"),
])


def test_berlin():
    evs = {e.artista: e for e in berlin_parse(HTML, "https://berlincafe.es/programas/", date(2026, 10, 6))}
    assert set(evs) == {"Kike M. Fin de Gira", "Concierto de enero", "Blokk Sessions"}  # sin Berlín Club ni lo pasado
    assert (evs["Blokk Sessions"].hora, evs["Blokk Sessions"].nota) == ("19:00", "Varios pases: 19:00, 21:30.")
    k = evs["Kike M. Fin de Gira"]
    assert (k.fecha, k.hora, k.precio, k.sala) == (date(2026, 10, 7), "20:00", "14 €", "Café Berlín")
    assert k.entradas == "https://cafeberlinentradas.com/events/kike-m"
    assert evs["Concierto de enero"].fecha == date(2027, 1, 9)  # sin año: enero es del año siguiente
    assert evs["Concierto de enero"].precio == "16,58 €"
