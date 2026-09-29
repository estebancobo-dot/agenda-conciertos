# Versiones

## 2.7.1 — 2026-09-29

- Discogs: su buscador aún lista algunas fichas borradas; al abrirlas daban 404 y se reintentaban en cada ejecución (Los Deltonos). Ahora se registran como "sin ficha en Discogs" con el motivo, y el estilo sigue viniendo de Last.fm.

## 2.7.0 — 2026-09-29

Primera versión después de la baseline: versión 2.6.1, commit `c2b68d0` (datos de la ejecución del 29-09-2026 a las 19:28 UTC).

- **Ya no se pierde lo que aporta una web que no se puede leer.**
  - Antes, si una fuente fallaba, sus conciertos se conservaban, pero los que compartía con otras webs perdían lo que ella aportaba: su nombre entre las fuentes, el contraste, el precio o la confirmación de la sala. El 29-09 eso bajó los contrastados de 686 a 661.
  - Ahora se guarda la última lectura completa de cada fuente (`data/fuentes_cache.json`). Si hoy falla, o solo se lee en parte, entran sus conciertos de esa lectura, con el aviso "Dato de la última lectura completa de X (fecha)".
  - Esa lectura se usa durante 14 días como máximo.
- **Reintentos:**
  - Dentro de la ejecución, las webs que fallan (403, antirobots, sin respuesta, error) se vuelven a leer una vez, tras 90 segundos.
  - Cada 2 horas, la ejecución de fichas vuelve a leer las que siguen fallando. Suele tocar otra máquina de GitHub, y los bloqueos del 29-09 dependían de la máquina: en una nueva captura, las mismas webs respondieron bien. Si alguna responde, se rehace la agenda con ella y con la última lectura del resto.
- **Ritmo por servidor, no por web.** Varias webs pequeñas alojadas en el mismo servidor compartido cuentan como una sola, para que su cortafuegos no vea ráfagas desde GitHub.
- **Lectura más rápida:**
  - 16 fuentes a la vez, empezando por las más lentas.
  - Madrid en Vivo, que marca la duración de toda la ejecución porque su robots.txt pide 10 segundos entre peticiones, ya no lee "Artes escénicas", "Musicales" ni "Clubbing": no son conciertos. Sus actos anteriores de esos estilos se retiran sin marcarse como cancelados.
- **Un `--solo` o un reintento ya no vacía la agenda:** las fuentes no leídas entran con su última lectura.
- El informe indica, por fuente, si funcionó al reintentar y cuántos conciertos se mantienen de su última lectura.

## 2.6.1 — 2026-09-29

- **Ejecuciones solapadas.** Si la ejecución de fichas y la de agendas coincidían, la segunda en terminar chocaba al guardar y perdía todo su trabajo. Le pasó a la primera ejecución completa de la 2.6.0: se perdieron 42 minutos de rastreo. Ahora `tools/guardar_datos.py`:
  - parte del último `main`;
  - une las fichas de artista de ambas ejecuciones, quedándose con la consulta más reciente de cada artista;
  - conserva los conciertos de la ejecución que ha leído las agendas;
  - vuelve a aplicar las fichas y reintenta la subida si otra se adelanta.
- Cada ejecución arranca con el último `main`, no con el código del momento en que se lanzó.

## 2.6.0 — 2026-09-29

- **Agendas municipales rehechas.** Las 21 direcciones anteriores no daban ningún concierto: unas habían cambiado (404) y otras no se leían bien. Se han comprobado una a una desde GitHub.
  - **Se leen 11 agendas:** Alcalá de Henares (CulturAlcalá), Aranjuez, Collado Villalba, Las Rozas, Leganés, Alcorcón, Boadilla, Torrejón (Teatro J. M. Rodero), Valdemoro (Teatro Juan Prado), Pinto y Móstoles. Lectores nuevos para microdatos schema.org/Event, calendarios FullCalendar de Drupal y 6 formatos propios.
  - **Se siguen intentando a diario:** Getafe (no responde a GitHub), Alcobendas y Arganda (403), San Sebastián de los Reyes (verificación antirobots, ahora detectada) y Coslada (error de certificado).
  - **Sin agenda legible** (explicado en el informe): Fuenlabrada, Majadahonda, Parla, Pozuelo y Rivas.
  - Filtro de música más estricto:
    - Cuenta el título o una expresión inequívoca en la descripción ("concierto", "recital", "tributo a"…), no cualquier mención a la música.
    - Se descartan talleres, exposiciones, inscripciones y plenos.
- **Rockgle:** ha cambiado de formato (bloques con 🎸 📅 📍) y se ha rehecho su lector. Se quita el parámetro `?m=0`, que desde GitHub acababa en una verificación de Google (429).
- **Rock-Progresivo (previas) y Diario de un Rockero:** no reconocían los enlaces a sus artículos (nuevas estructuras `/entrada/AAAA/MM/` y `/conciertos/entrada/`).
- **Tolerancia a fallos en las fichas de artista:**
  - Se guardan cada 50 artistas y con escritura atómica: un corte a mitad nunca deja el archivo roto.
  - El paso de guardar en el repositorio se ejecuta aunque el rastreo falle o se corte, porque el rastreo tiene su propio límite de 100 minutos.

## 2.5.1 — 2026-09-29

- Si el identificador de Discogs que da Wikidata apunta a una ficha borrada o fusionada (le pasaba a Los Deltonos), se busca en Discogs por el nombre, con la regla de siempre: una única coincidencia exacta.
- Si un paso de la ficha de artista falla por un error (de red o de la web consultada), ya no se guarda durante 180 días: en la siguiente ejecución se repite solo ese paso.

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
