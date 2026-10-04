"""Registro de fuentes. Para añadir una fuente: escribe su parser en scraper/sources/ y añade aquí una línea."""
from __future__ import annotations

from .model import Source
from .sources import agregadores as ag
from .sources import abiertos, blogs, conciertos_club as cc, enterticket, otras, rock_metal as rm, salas

S = Source

FUENTES: list[Source] = [
    # ---------------------------------------------------------------- A. agregadores generales
    S("cc_buscador", "conciertos.club (buscador semanal)", "https://conciertos.club/search.php", "agregador", 3, "alta",
      "conciertos.club", cc.buscador),
    S("cc_portada", "conciertos.club (portada Madrid)", "https://conciertos.club/madrid", "agregador", 3, "alta",
      "conciertos.club", cc.portada),
    S("cc_estilos", "conciertos.club (por estilo)", "https://conciertos.club/madrid/conciertos/estilos/", "agregador", 3,
      "alta", "conciertos.club", cc.estilos),
    S("laganzua", "La Ganzúa", "https://www.laganzua.net/conciertos/madrid/", "agregador", 3, "alta", "laganzua",
      ag.laganzua),
    S("cpm", "Conciertos por Madrid", "https://conciertospormadrid.com/", "agregador", 3, "media", "conciertospormadrid",
      ag.conciertospormadrid),
    S("madridenvivo", "Madrid en Vivo (asociación de salas)", "https://madridenvivo.com/buscador-avanzado/", "agregador",
      3, "alta", "madridenvivo", ag.madridenvivo, tope_seg=None),  # 10 s entre páginas: tiene su lectura aparte
    S("songkick", "Songkick Madrid", "https://www.songkick.com/metro-areas/28755-spain-madrid", "agregador", 3, "media",
      "songkick", ag.songkick),
    S("jacksonlive", "JacksOnLive (agenda de Madrid)", ag.JACKSON, "agregador", 3, "media", "jacksonlive",
      ag.jacksonlive, notas="Agenda independiente desde 2014. Lee sus páginas de estilo de Madrid: fecha y hora, "
                            "estilo, precio, sala y artistas."),
    S("totalstage", "Total Stage (agenda de la comunidad)", ag.TOTALSTAGE, "agregador", 3, "media",
      "conciertos.club", ag.totalstage,
      notas="Agenda que completan sus usuarios: una sola página con todos los próximos de Madrid. Va en el grupo de "
            "conciertos.club porque copia sus datos (medido: en 14 de 14 horas distintas entre webs da la de "
            "conciertos.club), así que no cuenta como confirmación independiente."),
    S("rockandblog", "Rock and Blog", "https://rockandblog.net/conciertos-rock-madrid/", "blog", 4, "media",
      "rockandblog", ag.rockandblog),
    S("tm_blog", "Blog de Ticketmaster (agenda rock)", "https://blog.ticketmaster.es/post/agenda-rock-2026-38621/",
      "agregador", 3, "media", "ticketmaster", ag.tm_blog),
    S("radar_cpm", "Radar Joven (programación en Conciertos por Madrid)", ag.RADAR_CPM, "agregador", 3, "media",
      "conciertospormadrid", ag.radar_cpm),
    # ---------------------------------------------------------------- B. rock, metal, AOR, prog
    S("thm", "TodoHeavyMetal", "https://www.todoheavymetal.com/index.php/agenda/amp", "agregador", 3, "media", "thm",
      otras.thm),
    S("metallegion", "Metal Legion", "https://metallegion.es/conciertos/", "agregador", 3, "media", "metallegion",
      rm.metallegion),
    S("metalcry", "Metalcry", "https://metalcry.com/conciertos/", "agregador", 3, "media", "metalcry", otras.metalcry,
      notas="Su hora es 20:00 por defecto: se ignora."),
    S("hellpress", "Hellpress (agenda)", "https://www.hellpress.com/agenda-conciertos/", "agregador", 3, "media",
      "hellpress", rm.hellpress),
    S("hellpress_melodico", "Hellpress (rock melódico)", "https://www.hellpress.com/tag/rock-melodico/", "blog", 4,
      "media", "hellpress", rm.hellpress_melodico, reconfirma=False),
    S("metalsymphony", "Metal Symphony (agenda de temporada)", "https://www.metalsymphony.com/agenda/", "agregador", 3,
      "media", "metalsymphony", otras.metalsymphony),
    S("rockforeveryone", "Rock for Everyone (agenda mensual Madrid)", "https://rockforeveryone.es/", "agregador", 3,
      "media", "rockforeveryone", otras.rockforeveryone),
    S("mariskal", "MariskalRock (guía)", "https://mariskalrock.com/guia-de-conciertos/", "agregador", 4, "baja",
      "mariskalrock", rm.mariskal, notas="Fiabilidad baja: mantiene fechas antiguas y no indica el año."),
    S("rockgle", "Rockgle", "https://www.rockgle.es/p/agenda-de-conciertos_07.html", "agregador", 4, "baja",
      "rockgle", rm.rockgle, notas="Fiabilidad baja."),
    S("madness", "Madness Live (promotora)", "https://www.madnesslive.es/es/14-conciertos-en-madrid", "promotora", 2,
      "alta", "madnesslive", rm.madness),
    S("getrock", "Get Rock (promotora)", "https://www.getrock.es/", "promotora", 2, "alta", "getrock", rm.getrock),
    S("neverland", "Neverland Concerts (calendario en Metal Symphony)",
      "https://www.metalsymphony.com/neverland-concerts-agenda-rock-progresivo-2026-2027/", "agregador", 3, "media",
      "metalsymphony", otras.neverland),
    S("rockprog_agenda", "Rock-Progresivo.com (agenda)",
      "https://www.rock-progresivo.com/agenda-de-conciertos-de-rock-progresivo/", "agregador", 3, "media", "rockprog",
      otras.rockprog_agenda),
    S("rockprog", "Rock-Progresivo.com (previas)",
      "https://www.rock-progresivo.com/seccion/cronicas-conciertos/previas-de-conciertos/", "blog", 4, "media",
      "rockprog", blogs.rockprog, reconfirma=False),
    S("dirtyrock", "Dirty Rock Magazine (giras)", "https://www.dirtyrock.info/category/giras/", "blog", 4, "media",
      "dirtyrock", blogs.dirtyrock, reconfirma=False),
    S("viriaor", "viriAOR (agenda)", "https://viriaor.wordpress.com/category/agenda-de-conciertos/", "blog", 4, "media",
      "viriaor", blogs.viriaor, reconfirma=False),
    S("diariorockero", "Diario de un Rockero", "https://www.diariodeunrockero.es/", "blog", 4, "media",
      "diariorockero", blogs.diariorockero, reconfirma=False),
    # ---------------------------------------------------------------- D. americana, country, folk, blues
    S("mutick", "Mutick / The Flying Pig (MomentaZos)", "https://mutick.com", "ticketera", 2, "alta", "mutick",
      otras.mutick),
    S("qconciertos", "Qconciertos (country, folk y provincia de Madrid)", "https://qconciertos.es/estilo/country/",
      "agregador", 3, "media", "qconciertos", otras.qconciertos),
    S("sbm", "Sociedad de Blues de Madrid", "https://www.sociedaddebluesdemadrid.com/", "promotora", 2, "alta", "sbm",
      otras.sbm),
    S("bigmama", "Big Mama Ballroom (blues)", "https://bigmamaballroom.com/conciertos-blues/", "sala", 1, "alta",
      "bigmama", otras.bigmama),
    # ---------------------------------------------------------------- E. webs oficiales de salas
    S("gruta77", "Gruta 77 (web oficial)", "https://gruta77.com/events/", "sala", 1, "alta", "gruta77",
      salas.PARSERS["gruta77"]),
    S("movistar", "Movistar Arena (web oficial)", "https://www.movistararena.es/", "sala", 1, "alta", "movistararena",
      salas.PARSERS["movistar"]),
    S("riviera", "La Riviera (web oficial)", "https://salariviera.com/conciertos/", "sala", 1, "alta", "riviera",
      salas.PARSERS["riviera"]),
    S("nazca", "Sala Nazca (web oficial)", "https://www.salanazcaconciertos.com/conciertos", "sala", 1, "alta", "nazca",
      salas.PARSERS["nazca"]),
    S("wagon", "Sala Wagon (web oficial)", "https://www.wagon.live/", "sala", 1, "alta", "wagon", salas.PARSERS["wagon"]),
    S("revi", "Revi Live / Revi Space (web oficial)", "https://revi.live/eventos/", "sala", 1, "alta", "revi",
      salas.PARSERS["revi"]),
    S("chango", "Sala Changó (web oficial)", "https://www.salachango.es/", "sala", 1, "alta", "chango",
      salas.PARSERS["chango"]),
    S("salabut", "Sala But (web oficial)", "https://www.salabut.es/agenda-conciertos/", "sala", 1, "alta", "salabut",
      salas.PARSERS["salabut"]),
    S("elsol", "Sala El Sol (web oficial)", "https://salaelsol.com/agenda/", "sala", 1, "alta", "elsol",
      salas.PARSERS["elsol"]),
    S("villanos", "Sala Villanos (web oficial)", "https://salavillanos.es/agenda/", "sala", 1, "alta", "villanos",
      salas.PARSERS["villanos"]),
    S("rockville", "RockVille (web oficial)", "https://rockville.es/programacion/", "sala", 1, "alta", "rockville",
      salas.PARSERS["rockville"]),
    S("funhouse", "Fun House (web oficial)", "https://www.funhousemusicbar.com/conciertos/", "sala", 1, "alta",
      "funhouse", salas.PARSERS["funhouse"]),
    S("wurlitzer", "Wurlitzer Ballroom (web oficial)", "https://wurlitzerballroom.com/agenda", "sala", 1, "alta",
      "wurlitzer", salas.PARSERS["wurlitzer"]),
    S("honky", "Honky Tonk (web oficial)", "https://clubhonky.com/programacion/", "sala", 1, "alta", "honky",
      salas.PARSERS["honky"]),
    S("silikona", "Silikona (web oficial)", "https://silikona.es/", "sala", 1, "alta", "silikona",
      salas.PARSERS["silikona"]),
    S("clamores", "Sala Clamores (web oficial)", "https://www.salaclamores.es/calendario", "sala", 1, "alta", "clamores",
      salas.PARSERS["clamores"]),
    S("galileo", "Galileo Galilei (web oficial)", "https://salagalileo.es/", "sala", 1, "alta", "galileo",
      otras.galileo, notas="Su hosting a veces responde con un captcha anti-bots; sus conciertos llegan también por "
                           "Madrid en Vivo y conciertos.club."),
    S("siroco", "Sala Siroco (web oficial)", "https://siroco.es/", "sala", 1, "alta", "siroco", salas.PARSERS["siroco"]),
    S("mobydick", "Moby Dick Club (web oficial)", "https://www.mobydickclub.com/", "sala", 1, "alta", "mobydick",
      salas.PARSERS["mobydick"]),
    S("independance", "Independance Club (web oficial)", "https://independanceclub.com/collections/conciertos", "sala", 1,
      "alta", "independance", salas.PARSERS["independance"]),
    S("salab", "Sala B (web oficial)", "https://www.salabmadrid.com/", "sala", 1, "alta", "salab", salas.PARSERS["salab"]),
    S("nuevacubierta", "La Nueva Cubierta, Leganés (web oficial)", "https://lanuevacubierta.com/eventos/", "sala", 1,
      "alta", "nuevacubierta", salas.PARSERS["nuevacubierta"], municipio_defecto="Leganés"),
    S("cafecentral", "Café Central (web oficial)", "https://cafecentralmadrid.com/programacion/", "sala", 1, "alta",
      "cafecentral", salas.PARSERS["cafecentral"], municipio_defecto="Madrid",
      notas="Café Central Ateneo y el auditorio de La Cátedra; las residencias de varias noches, una por noche."),
    # salas que publican su agenda con The Events Calendar (API de WordPress; comprobado el 3-10-2026)
    S("vistalegre", "Palacio Vistalegre (web oficial)", "https://www.palaciovistalegre.com/", "sala", 1, "alta",
      "vistalegre", salas.PARSERS["vistalegre"], municipio_defecto="Madrid"),
    S("eslava", "Teatro Eslava (web oficial)", "https://teatroeslava.com/conciertos/", "sala", 1, "alta", "eslava",
      salas.PARSERS["eslava"], municipio_defecto="Madrid"),
    S("elperroclub", "El Perro Club (web oficial)", "https://elperroclub.es/conciertos/", "sala", 1, "alta",
      "elperroclub", salas.PARSERS["elperroclub"], municipio_defecto="Madrid",
      notas="Sus conciertos; las sesiones de DJ, no."),
    S("tempo", "Tempo Audiophile Club (web oficial)", "https://tempoclub.es/", "sala", 1, "alta", "tempo",
      salas.PARSERS["tempo"], municipio_defecto="Madrid", notas="Sus conciertos; las sesiones de DJ, no."),
    S("ticketandroll", "TicketAndRoll (Hangar 48, Rincón del Arte Nuevo, Jazzville)", "https://ticketandroll.com/",
      "ticketera", 2, "alta", "ticketandroll", salas.ticketandroll, municipio_defecto="Madrid",
      notas="Páginas de cada sala en la ticketera: salas sin web propia legible."),
    S("enterticket", "Enterticket (Villanos y otras salas)", "https://www.enterticket.es/", "ticketera", 2, "alta",
      "enterticket", enterticket.enterticket,
      notas="Sus páginas de evento (las permite su robots.txt), a partir de su sitemap: solo conciertos en la Comunidad "
            "de Madrid. Cada día se abren las nuevas; lo ya visto se recuerda."),
    S("cclub_org", "entradas.conciertos.club (páginas de cada sala)", "https://entradas.conciertos.club/",
      "ticketera", 2, "alta", "conciertos.club", salas.cclub, municipio_defecto="Madrid",
      notas="Lo que publica cada sala en su página de la ticketera ('Organizado por …'): Café Berlín."),
    S("salas_js", "Intruso y Moe (webs oficiales)", "https://intrusobar.com/", "sala", 1, "alta", "salas_js",
      salas.salas_js, municipio_defecto="Madrid",
      notas="Sus webs pintan la agenda con JavaScript: se leen con un navegador real (no tienen robots.txt). "
            "Sin noches de poesía, monólogos ni DJ."),
    S("cafelapalma", "Café La Palma (web oficial)", "https://cafelapalma.com/es/agenda-de-conciertos/", "sala", 1, "alta",
      "cafelapalma", salas.PARSERS["cafelapalma"], municipio_defecto="Madrid",
      notas="Se toman sus conciertos; las sesiones de club (categoría Clubbing) no."),
    S("cadillac", "Cadillac Solitario (web oficial)", "https://cadillacsolitario.com/eventos/", "sala", 1, "alta",
      "cadillac", salas.PARSERS["cadillac"], municipio_defecto="Madrid"),
    S("dimequemequieres", "Dime que me Quieres (web oficial)", "https://conciertos.dimequemequieresbardecopas.com/",
      "sala", 1, "alta", "dimequemequieres", salas.PARSERS["dimequemequieres"], municipio_defecto="Madrid"),
    # datos abiertos del Ayuntamiento: lo que programan sus propios espacios (centros culturales, Conde Duque…)
    S("datos_madrid", "Agenda cultural del Ayuntamiento de Madrid (datos abiertos)", abiertos.URL, "institucional", 1,
      "alta", "datos_madrid", abiertos.datos_madrid, municipio_defecto="Madrid",
      notas="Conjunto 206974 de datos.madrid.es: actividades de tipo Música y conciertos de la programación destacada."),
    S("gotifiestas", "GotiFiestas (escena gótica y dark wave)", "https://www.gotifiestas.com/eventos/", "agregador", 3,
      "media", "gotifiestas", abiertos.gotifiestas, municipio_defecto="Madrid",
      notas="Su API pública de WordPress: conciertos y festivales (no fiestas ni sesiones de DJ), con sus géneros."),
    S("salirmadrid", "SalirMadrid (country y folk)", "https://salirmadrid.es/live-music-country-madrid", "agregador", 3,
      "media", "salirmadrid", abiertos.salirmadrid, municipio_defecto="Madrid",
      notas="Páginas de country y folk (JSON-LD). El estilo solo si el título lo dice: su etiqueta de género es amplia."),
]

# Salas pedidas cuya web no tiene agenda legible (comprobado sep-2026). Se listan en el informe.
SIN_AGENDA_LEGIBLE = {
    "Sala Mon Live (monmadrid.es)": "La web no publica agenda de conciertos (solo información general).",
    "Sala Copérnico (salacopernico.es)": "La web muestra una 'cartelera orientativa' de ejemplo con fechas ficticias; no se usa.",
    "The RockLab, Coslada (therocklab.es)": "Web hecha con Wix sin fechas legibles en el HTML.",
    "Maravillas Club": "El dominio maravillasclub.es es una página de parking.",
    "Cadavra": "No se encontró una web oficial accesible (dominios probados sin respuesta).",
    "Sala La Trinchera": "No se encontró una web oficial accesible.",
    "Sala The Godfather": "No se encontró una web oficial accesible.",
    "Lula Club": "La web lulaclub.es no responde (tiempo de espera agotado).",
    "Sala Venom, Coslada": "No se encontró web propia (solo redes sociales).",
    "Sala Groove, Pinto": "La web no responde (conexión rechazada).",
    # comprobadas el 3-10-2026 (salas con muchos conciertos cuya web no se leía)
    "Café El Despertar (cafeeldespertar.com)": "Su robots.txt no permite leerla: se respeta.",
    "Thundercat (thundercatclub.com)": "La página de programación no trae fechas en el HTML y su calendario está vacío.",
    "Sala Vesta (salavesta.com)": "La web solo enlaza a sus publicaciones de Instagram (sin fechas).",
    "El Café de la Ópera (elcafedelaopera.com)": "Programación fija (cena cantada, jazz con piano) sin agenda con fechas.",
    "La Coquette": "Sin web propia: publica su programación solo en Instagram y Facebook.",
    "Barracudas Rock Bar": "Sin web propia encontrada (solo redes y ticketeras).",
    "New Restón, Valdemoro": "La web no responde (error SSL).",
    "Auditorio Miguel Ríos, Rivas": "Sin página de agenda propia; su programación aparece en la agenda municipal de Rivas.",
    "Sala Changó": "",
}
SIN_AGENDA_LEGIBLE.pop("Sala Changó")

NO_USAR = {
    # Quitadas el 30-09-2026: fallaron en todas las ejecuciones desde que existen (nunca dieron conciertos)
    "Ticketle": "Responde 403 (acceso prohibido) a todas las peticiones desde GitHub.",
    "Bandsintown": "Responde 403 (acceso prohibido) a todas las peticiones desde GitHub.",
    "Radar Joven (comunidad.madrid)": "Responde 404 a todas las peticiones desde GitHub; su programación se lee de Conciertos por Madrid.",
    "FORCE Magazine": "No responde o no publica conciertos legibles en ninguna de las ejecuciones.",
    "Agendas municipales de Getafe, Alcobendas, Arganda del Rey, San Sebastián de los Reyes y Coslada":
        "Bloqueo (403 o verificación antirobots), error de certificado o sin respuesta en todas las ejecuciones.",
    "IndyRock": "Bloquea el acceso automático.",
    "La Hora del Blues": "Bloquea el acceso automático.",
    "Foro Azkena, Zona-Zero": "Foros: solo consulta manual (ver README).",
    # probadas el 2-10-2026 (fase 4, géneros con pocos conciertos)
    "DotheReggae (agenda de reggae)": "Responde 403 (acceso prohibido) desde GitHub; el reggae llega por conciertos.club (reggae-ska).",
    "Café Libertad 8 (cantautores)": "Su página de conciertos devuelve una imagen en vez de la agenda; sus conciertos llegan por conciertos.club.",
    "esMadrid (agenda de música)": "La página no trae las fechas en el HTML (se cargan después con JavaScript).",
    "Comunidad de Madrid (agenda de actividades)": "La dirección de la agenda responde 404.",
    "Festify Indie": "La página llega vacía (los conciertos se cargan con JavaScript).",
    # probadas el 2-10-2026 para Americana y folk
    "Houston Party (promotora)": "Publica fechas sin año ni sala; sus artistas llegan por otras fuentes.",
    "NocheMAD": "Los mismos conciertos que SalirMadrid (ya se lee).",
    "El Corte Inglés (entradas)": "Responde 403 (acceso prohibido) desde GitHub.",
    "Folklore Plaza Castilla": "La web no responde.",
}


def por_id() -> dict[str, Source]:
    return {s.id: s for s in FUENTES}


# ---------------------------------------------------------------- F. agendas municipales
def _municipales():
    from .normalize import norm
    from .sources import municipios as mu
    for muni, (url, lector) in mu.AGENDAS.items():
        FUENTES.append(S(f"muni_{norm(muni).replace(' ', '_')}", f"Agenda municipal de {muni}", url, "institucional", 2,
                         "media", f"muni_{norm(muni)}", mu.hacer(muni, url, lector), municipio_defecto=muni))
    SIN_AGENDA_LEGIBLE.update(mu.SIN_AGENDA)


_municipales()
