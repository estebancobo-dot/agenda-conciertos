# Versiones

## 2.5.0 — 2026-09-29

Revisión de la web en el móvil.

- **Errores corregidos**:
  - La foto de la ficha salía recortada: ahora se ve entera, sobre un fondo difuminado de la misma foto.
  - Si la foto no cargaba quedaba un hueco gris: ahora se ven las iniciales del artista.
  - El buscador solo buscaba en el día, la semana o el mes que tenías abierto: ahora busca en todas las fechas y avisa si los filtros ocultan resultados.
  - "Sin ficha en Discogs" aparecía aunque hubiera ficha de Discogs sin estilo.
  - Nombres de ciclos o de salas ("Villanos del Jazz") aparecían como si fueran estilos.
  - Los precios se mostraban como "50.0 EUR".
  - El selector de fecha de *Semana* salía cortado.
  - El botón para aplicar los filtros quedaba fuera de la pantalla.
- **Filtros**: los géneros aparecen como botones bajo el buscador y se activan con un toque. "Mi foco" desaparece: por defecto se ven todos los géneros salvo los **otros géneros** (electrónica, hip hop, jazz, latina…). El panel **Filtros** reúne el origen y los géneros, con el número de conciertos antes de aplicar. Cuando hay filtros activos se indica y se pueden quitar de un toque.
- **Vistas**: la cabecera es más compacta, con *Mes*, *Semana* y *Día* siempre a mano; Estilos, Fuentes, Informe, Versiones, CSV y el tema pasan al menú ☰.
  - Botón **Hoy** en las tres vistas.
  - *Mes* muestra el total del mes y oculta los días de otros meses.
  - *Semana* y *Día* tienen una tira de días con su número de conciertos.
  - En *Día* se puede deslizar a los lados para cambiar de día.
- **Tarjetas**: artista en grande, luego hora y sala. Si las webs no coinciden en la hora, se muestra la más repetida con "?".
- **Ficha**:
  - Datos en una lista con iconos: cuándo, dónde, estilo, origen y precio.
  - Si las webs no coinciden, cada versión aparece con cuántas webs la dan.
  - Botones para **añadir al calendario** del móvil y **compartir**.
  - Enlaces al artista en Spotify, Discogs, Wikipedia, AllMusic, Last.fm y MusicBrainz, y cómo se identificó al artista.
  - "Volver" regresa a la vista de la que vienes.

## 2.4.0 — 2026-09-29

- **Ritmo según cada plataforma** en lugar de una pausa fija de 2 s por web:
  - Webs de agendas y salas: 1 s de pausa desde que termina cada respuesta, o el Crawl-delay de su robots.txt si es mayor. Un servidor lento recibe así menos peticiones.
  - Discogs a su límite publicado: 60 peticiones/min con clave, 25 sin ella. Además vigila la cabecera `X-Discogs-Ratelimit-Remaining`.
  - MusicBrainz a 1 petición/s, que es su norma.
  - Last.fm a 4 peticiones/s (su máximo es 5).
  - Wikipedia y Wikidata de una en una, sin pausa fija, como pide Wikimedia.
  - Ante 429 o 503 se respeta `Retry-After` (o se esperan 10 s, 20 s…), se reintenta hasta 3 veces y se duplica la pausa con esa web.
- **Fichas en paralelo con las agendas**: en la ejecución diaria las fichas de artista (otras webs) se buscan mientras se leen las agendas, empezando por los artistas del día anterior. Al terminar las agendas se completan los artistas nuevos. Tope total: 40 minutos.
- Las ejecuciones de "solo fichas" sin nada pendiente no modifican datos ni vuelven a publicar la web.

## 2.3.0 — 2026-09-29

- **Fichas de artista cada 2 horas**: además de la actualización diaria, cada 2 horas se completan durante un máximo de 50 minutos las fichas pendientes, sin volver a leer las agendas. Cuando no quedan pendientes, termina en segundos.
- **Carga incremental**: cada artista se consulta una sola vez. Si a una ficha ya guardada le falta un paso añadido después (Wikidata, Last.fm), solo se hace ese paso. Si Wikidata identifica en Discogs un artista distinto del que se había asignado por nombre, se corrige.
- **Last.fm** (con `LASTFM_KEY`): último recurso para el estilo, solo si ni Discogs ni Wikipedia lo dan.
  - Se usan las etiquetas de los oyentes con al menos el 25 % del peso, y solo las que tienen equivalencia declarada en los estilos de Discogs. "seen live", "spanish" y similares se ignoran.
  - La identidad se toma del identificador de MusicBrainz en Wikidata. Sin él, se busca por nombre exacto y se marca como "coincidencia por nombre".
- **Wikipedia más rápida**: si no existe la página con el nombre del artista, no se prueban las variantes "(banda)", "(grupo musical)" y "(cantante)". Son 3 peticiones menos por cada grupo desconocido.
- El origen de Wikidata, Wikipedia o Discogs sustituye al de MusicBrainz, que es solo por coincidencia de nombre.

## 2.2.0 — 2026-09-29

- **Wikidata**: se lee su página `Special:EntityData`, que es la única vía que permite su robots.txt. A partir de la página de Wikipedia del artista se obtienen:
  - sus identificadores exactos en Discogs, AllMusic, Spotify, MusicBrainz y Last.fm;
  - el país de origen;
  - la foto de Commons.
- Con el identificador de Discogs que da Wikidata, la ficha de Discogs ya no depende del nombre y se resuelven homónimos como "Europe". Si Wikidata no lo da, se sigue exigiendo una única coincidencia exacta.
- Origen: Wikidata pasa por delante de Wikipedia y Discogs (país de origen o nacionalidad, solo si Wikidata da uno solo).
- La ficha del concierto enlaza directamente a AllMusic, Spotify, MusicBrainz y Last.fm cuando Wikidata los da, y explica cómo se identificó al artista.
- Claves gratuitas opcionales, guardadas como *secrets* de GitHub:
  - `DISCOGS_TOKEN`: 60 peticiones/min en vez de 25, así que las fichas se completan en menos días.
  - `LASTFM_KEY` y `TICKETMASTER_KEY`: quedan preparadas para próximas versiones.

## 2.1.1 — 2026-09-29

- **robots.txt**: nuevo intérprete conforme a RFC 9309 con comodines `*` y `$`. El módulo estándar de Python no los entiende y, por ejemplo, habría permitido la API de Deezer, cuyo robots.txt dice `Disallow: /*`. Comprobado con los robots.txt reales: todas las URL que ya se usaban siguen permitidas.
- La herramienta de captura guarda también el código de respuesta, las cabeceras de límite de peticiones y el cuerpo de los errores.

## 2.1.0 — 2026-09-29

**Ficha musical del artista (estilo, origen y foto) desde webs de música, no desde la agenda o la sala.**

- Fuentes verificadas desde GitHub: **Discogs** (API pública sin clave: estilos y géneros de sus discos, foto y origen del perfil) y **Wikipedia** en español e inglés (ficha con Género(s), Origen y foto de Wikimedia Commons). **AllMusic** bloquea todo acceso automático (403, incluso en robots.txt): solo se enlaza su buscador. La Fonoteca (403) y el buscador de Bandcamp (prohibido por robots.txt) no se pueden usar; la API de Wikipedia/Wikidata tampoco (robots.txt).
- Identidad: un dato solo se asigna si el artista se identifica sin ambigüedad (una única coincidencia exacta en Discogs, respetando tildes; una página de Wikipedia de un grupo o músico con ese título). Los homónimos (p. ej. "Europe" en Discogs) quedan sin ficha.
- La taxonomía de referencia pasa a ser la de **Discogs**; los géneros de Wikipedia se traducen a ella solo por equivalencia literal.
- Nacionalidad: fuente del concierto → Wikipedia → Discogs → MusicBrainz (marcada como "coincidencia por nombre"). Bandera en lugar del icono del globo.
- Fichas guardadas en `data/artistas.json` (se renuevan cada 180 días; los no encontrados se reintentan a los 30). Máx. 30 min por ejecución, respetando las 25 peticiones/min de Discogs: los artistas pendientes se completan en los días siguientes, empezando por los conciertos en foco más próximos.
- **Ficha detallada** de cada concierto: foto (Commons, Discogs o, si no hay, la imagen del anuncio), fecha, sala con enlace a su web y a cómo llegar, estilo con su fuente, origen con bandera, precio con su fuente, estado en lenguaje claro (confirmado por la web de la sala, varias webs, conflicto…). Las fuentes quedan plegadas al final salvo si hay conflicto.
- **Tarjetas** más simples: foto, hora, artista, sala, bandera y estilo. La etiqueta de la agenda se muestra con borde discontinuo para distinguirla del estilo de una web de música.
- **Filtros**: panel "Géneros" con atajos (Mi foco, Todo, Ninguno), recuento de cada grupo y qué estilos de Discogs incluye; nuevo filtro por origen (españoles, extranjeros, sin confirmar).
- El ciclo ("Radar Joven", "Las Noches de Río Babel"…) se separa del nombre del artista.
- Se guarda de qué web sale el precio y si la web oficial de la sala confirma el concierto.

## 2.0.2 — 2026-09-29

- Radar Joven: la web de la Comunidad de Madrid responde 404 a todas las peticiones desde GitHub (incluido robots.txt). Se sigue intentando a diario y, mientras tanto, se lee la programación completa del ciclo publicada por Conciertos por Madrid (nueva fuente `radar_cpm`).
- Galileo Galilei: su hosting (SiteGround) responde a veces con un captcha anti-bots. Ahora se detecta y el informe lo muestra como "bloqueado_antibots" en lugar de "funcionó sin resultados". Esto vale para cualquier web que responda con un captcha o una verificación de Cloudflare o Imunify.
- Invitados: se descartan los textos de relleno que no son artistas ("invitados especiales", "y más", "banda invitada", "por confirmar", "DJ", ofertas de entradas…).
- Salas: "Shoko" y "Shoko Live", o "Fotomatón" y "Fotomatón Bar", cuentan como la misma sala (se ignoran las palabras genéricas "live" y "bar" al comparar). Revi Live y Revi Space siguen siendo distintas.

## 2.0.1 — 2026-09-29

- Una fuente leída solo en parte (páginas caídas o tope de tiempo) ya no provoca "posiblemente cancelado" en sus conciertos (en la primera ejecución Madrid en Vivo se cortó por tiempo y marcó 30 por error).
- La comparación con la ejecución anterior tiene en cuenta todas las salas de un registro en conflicto de sala.
- Madrid en Vivo: tope de tiempo ampliado a 40 minutos (su servidor responde lento).
- El informe distingue "web inaccesible" de "robots.txt lo prohíbe".
- MusicBrainz: pausa de 1,5 s entre consultas para evitar errores 503.
- No se repite como invitado el título largo del propio artista.

## 2.0.0 — 2026-09-29

Primera versión automática (la 1.x fue la agenda manual hecha en el chat).

- Rastreo diario (GitHub Actions, 05:00 UTC y a mano) de 77 fuentes: agregadores (conciertos.club por semanas, portada y 12 estilos; La Ganzúa; Conciertos por Madrid; Madrid en Vivo con su petición de "cargar más"; Songkick; Rock and Blog; blog de Ticketmaster; Radar Joven), webs de rock y metal (TodoHeavyMetal, Metal Legion, Metalcry, Hellpress, Metal Symphony, Rock for Everyone, MariskalRock, Rockgle, Madness Live, Get Rock, Neverland, Rock-Progresivo, FORCE), blogs de giras con lectura incremental (Dirty Rock, viriAOR, Diario de un Rockero), americana y blues (Mutick/The Flying Pig, Qconciertos, Sociedad de Blues de Madrid, Big Mama), 22 webs oficiales de salas y 21 agendas municipales.
- Respeto de robots.txt (RFC 9309, incluido `Crawl-delay`), 1 petición cada 2 s por web y User-Agent identificable.
- Filtro por los 179 municipios de la Comunidad de Madrid (`data/municipios.json`); se descartan otras provincias aunque la sala se llame igual.
- Deduplicación: misma fecha + misma sala normalizada (`data/salas_alias.json`) + artista con similitud ≥ 90 (rapidfuzz), comparando también con los invitados y admitiendo prefijos de ciclo ("Las Noches de Río Babel. …").
- Conflictos de hora, sala y cartel: se guardan todas las versiones y se marca "conflicto"; si la fuente de mayor prioridad confirma el dato, se resuelve y se anota.
- Estados: contrastado (2+ webs distintas), 1 fuente, conflicto y posiblemente cancelado (cuando deja de aparecer en todas sus fuentes y estas funcionaron).
- Correcciones manuales (`data/correcciones.json`): descartes, conflictos y notas.
- Estilo solo el de la fuente, traducido a categoría con `data/estilos_map.json` y a Discogs con `data/taxonomia.json`.
- Nacionalidad: la de la fuente o, si no hay, MusicBrainz solo con una única coincidencia exacta.
- Salidas: `data/concerts.json`, `data/concerts.csv` (Excel), `data/informe.json`, `data/estado.json`.
- Web móvil (GitHub Pages) con vistas Mes, Semana, Día, Estilos, Fuentes, Informe y Versiones, filtros por categoría y buscador.
- Tests con pytest sobre HTML real de cada fuente, deduplicación y correcciones.
