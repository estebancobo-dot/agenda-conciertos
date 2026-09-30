# Versiones

## 2.15.1 — 2026-09-30

- **La búsqueda es un filtro más, y se ve.** Antes, con un nombre escrito en "Buscar", la hoja de filtros no lo mostraba: al pulsar "Todos" seguían saliendo solo los resultados de la búsqueda y los recuentos no cuadraban.
  - La hoja avisa arriba de que hay una búsqueda activa y tiene un botón "Quitar búsqueda".
  - "Borrar filtros", tanto en la hoja como en la barra, también borra la búsqueda.
  - El resumen "Filtrando: búsqueda «…» · …" y el número del botón Filtros se actualizan a cada letra.
- **Fichas con tiempo de carga estable.** Antes dependía de dónde viniera la foto y de si sus datos estaban precargados:
  - La foto grande de conciertos.club y Discogs también se genera al publicar (720 px, unos 40 KB) y se sirve desde la web; antes se pedía el original, de 4 a 9 s con 4G.
  - Se precargan los datos de todos los días de la lista, no solo los primeros.
  - Los detalles ya descargados se reutilizan: la copia sin conexión los da al instante y los actualiza por detrás, y el navegador ya no pregunta cada vez si han cambiado. Si la red no responde, la web tira de la copia a los 3,5 s (antes 6 s).
- **Miniaturas propias también para Discogs.** En la prueba en vivo sus fotos eran ya las más lentas (unos 3,7 s cada una a 600 px), porque Discogs no deja pasar al redimensionador. Ahora se reducen al publicar, igual que las de conciertos.club (respetando robots.txt y el ritmo de cada servidor), y se sirven desde la propia web. Se descargan en paralelo, un hilo por servidor.

## 2.15.0 — 2026-09-30

Usabilidad y velocidad, medidas con un navegador real sobre la web publicada (móvil con 4G lenta; `tools/probar_web.py`, workflow "Probar la web en vivo"):

- **Miniaturas mucho más ligeras.** Las fotos de las agendas son carteles a tamaño completo (a veces de 1-2 MB, en servidores lentos): cada miniatura tardaba de mediana 3,3 s. Ahora se pide una copia reducida (Wikimedia en su tamaño pequeño; el resto a través de wsrv.nl, una CDN gratuita que redimensiona y guarda la copia). Las primeras 8 de cada vista se piden ya y con prioridad. Si la copia falla, se usa la original y, si no, las iniciales.
- **Miniaturas propias para conciertos.club** (más de 1.000 conciertos; su servidor tarda 4-9 s por imagen y wsrv.nl lo tiene bloqueado): al publicar se descarga cada cartel una sola vez, respetando su robots.txt y su ritmo, y se reduce a 160×160 (unos 5 KB). Se sirve desde la propia web, así que el service worker también la guarda. Cada día solo se hacen las nuevas, con un tope de tiempo. Para Discogs y conciertos.club no se intenta la copia de wsrv.nl, que los rechaza (antes se pedía la copia, fallaba y luego la original: el doble de tiempo); Fever usa su propio redimensionado.
- **Fuera las fotos genéricas**: la imagen de fondo que Madrid en Vivo pone a 392 conciertos, logos de salas… (las que la agenda usa para 4 artistas distintos o más). Mejor las iniciales que una foto que no es del artista.
- **Detalle más rápido**: al ver una lista se piden en segundo plano los detalles de sus días, y al tocar un concierto su ficha y su foto, así que al abrirlo ya están. La foto grande usa también copia reducida, con la miniatura de fondo mientras llega.
- **Volver deja la lista donde estabas**, tanto con el botón atrás del móvil como con "‹ Volver": en el mismo concierto y a la misma altura de pantalla.
- **Filtros más rápidos y claros**:
  - La hoja ya no se redibuja entera en cada toque: marcar un género o un estilo tarda unos 25 ms (antes, cientos de ms).
  - Un solo "Borrar filtros" (antes "Restablecer" en la hoja y "Quitar filtros" en la barra) y accesos rápidos: "Los de siempre", "Todos", "Ninguno".
  - Los estilos de cada género se despliegan con "Elegir estilos" y solo aparecen los que tienen conciertos. Lo elegido se ve al lado ("Solo: Thrash, Doom").
  - Las pastillas de género muestran cuántos conciertos hay.
  - Se cierra con ✕, tocando fuera o con Escape, sin aplicar cambios.
- **Listas más ágiles**: cada tarjeta se genera una vez y se reutiliza. En semanas con más de 200 conciertos se pintan ya los primeros y el resto justo después (pintar una semana: de ~190 a ~60-80 ms con la CPU de un móvil medio).
- **Vista mes**: al tocar un día, sus conciertos aparecen debajo del calendario, sin salir de la vista; el día elegido se marca y los fines de semana se distinguen.

## 2.14.2 — 2026-09-30

- **Nombres mal descodificados.** Si una web no declara su juego de caracteres y el contenido es UTF-8 válido, se lee como UTF-8, en lugar de adivinarlo. El 29/09 la adivinanza falló con Revi: "Brujería" salió "Brujer├Ła", "Eskóbula" salió "Esk├│bula"…
- Esas copias rotas de lecturas anteriores ya no se arrastran como "¿cancelado?": no eran conciertos aparte. En la ejecución del 30/09 eran 4 de los 9 "posiblemente cancelados".

## 2.14.1 — 2026-09-30

- **Fase 1b: `main` ya no guarda datos.** La rama `datos` se creó bien en la primera pasada (un solo commit con los 7 archivos generados), así que se quitan de `main`. Las ejecuciones los traen de esa rama; para tenerlos en local, `python tools/datos.py`.
- El informe indica con qué versión se clasificaron los conciertos cuando la última pasada solo completó fichas ("2.14.1 (agendas leídas con la 2.10.0)").

## 2.14.0 — 2026-09-30

Fase 4 de mejoras (identidad de artistas y UX):

- **Nacionalidad desde MusicBrainz también en la ficha.** Si MusicBrainz identifica al artista (por Wikidata o por ser el único con ese nombre exacto), su país cuenta. Con los datos de hoy pasan de 628 a 722 los conciertos con origen confirmado.
- **Last.fm con identidad confirmada.** Si Last.fm encontró al artista solo por el nombre y MusicBrainz tiene su identificador, se vuelve a consultar Last.fm con ese identificador (284 artistas). Así sus etiquetas dejan de ser "posible homónimo" y cuentan en el consenso. Si Last.fm no conoce el identificador, se anota y no se repite.
- **Estados vacíos que explican el porqué.** "No hay conciertos anunciados este día" o, si los ocultan los filtros, cuáles son y un botón "Ver N conciertos ocultos".
- **Conflictos más claros en las tarjetas**: "⚠ hora sin confirmar", "⚠ sala sin confirmar"… en lugar de "datos distintos".
- **Accesibilidad**: botones y filtros más grandes para el dedo y foco visible al navegar con el teclado.

## 2.13.0 — 2026-09-30

Fase 3 de mejoras (duplicados y vigilancia de las fuentes):

- **Menos conciertos duplicados.** Con los datos de hoy se juntan 9 que salían dos veces:
  - Un concierto que la misma web anuncia dos veces con horas distintas es uno solo, con la hora en conflicto: Devin Townsend (20:30 y 21:00), Accept, Parquesvr, Avulsed, Nate Smith. Las sesiones de un mismo espectáculo (Candlelight, tributos, ballet, musicales…) siguen separadas.
  - Nombres con "& Friends", "feat.", "&"… y siglas con puntos: Mikky Dee y "MIkkey Dee & Friends"; P.H.A.T y "Jazz con sabor a Club 26: P.H.A.T. (Italia)".
- **Avisos de fuentes.** El informe marca las que llevan 3 días o más sin leerse bien y las que de repente dan muchos menos conciertos de lo habitual (menos del 30 %), que suele ser un cambio de diseño de la web.
  - Si hay alguna, se abre un issue en GitHub ("Fuentes de la agenda con problemas"), que llega por correo. Se actualiza solo y se cierra cuando todas vuelven a leerse bien.

## 2.12.0 — 2026-09-30

Fase 2 de mejoras (web más rápida y a prueba de fallos):

- **La web descarga 4 veces menos al abrir.** Antes bajaba `concerts.json` entero (6,8 MB; 600 KB comprimido). Ahora baja una agenda ligera (1 MB; 150 KB comprimido) con lo que necesitan el calendario, las listas, los filtros y la búsqueda. Las fuentes, la ficha, el precio y las notas se piden al abrir un concierto, solo los de ese día (unos 6 KB de media).
  - `concerts.json` se sigue publicando igual. Si la agenda ligera faltara, la web usa `concerts.json` como antes.
- **Funciona sin conexión o si GitHub Pages falla**: guarda una copia de la web y de los últimos datos vistos, y la usa si la red no responde en 6 segundos.
- **Aviso de datos viejos**: si la última actualización tiene más de 30 horas, la cabecera lo indica.
- **Carga más agradable**: esqueletos en lugar de "Cargando…" (también al abrir un concierto) y miniaturas con tamaño fijo, para que la página no salte al cargar las fotos.

## 2.11.0 — 2026-09-30

Fase 1 de mejoras (tolerancia a fallos y horarios):

- **Horario nuevo.** La ejecución completa arranca a las 03:10 UTC (05:10 en Madrid en verano, 04:10 en invierno) y termina antes de las 7. Las pasadas de cada 2 horas van de 05:40 a 23:40 UTC: de madrugada no hay ninguna que pueda retrasar la completa.
- **Rama `datos`.** Los datos generados ya no se guardan en `main`, sino en una rama aparte con un único commit que se reemplaza cada vez: el repositorio deja de crecer unos 10 MB al día.
  - La primera ejecución crea la rama a partir de los datos de `main`.
  - Si al empezar no se pueden traer los datos, no se rastrea ni se guarda nada, para no machacar lo guardado con datos incompletos.
  - Dos ejecuciones que guarden a la vez siguen uniendo sus cachés, como antes.
- **Informe: la última lectura completa queda registrada** (fecha, duración, fuentes que funcionaron) aunque luego las pasadas de cada 2 horas rehagan el informe. Antes el informe decía "duración 22 s" tras un reintento.

## 2.10.1 — 2026-09-30

- **Homónimos en Discogs.** Si la ficha de Discogs no tiene una identidad segura (encontrada solo por el nombre, con otro nombre o con el sufijo de homónimos de Discogs, "Martin (14)") y contradice a todo lo demás (la pone solo fuera de foco y la agenda y las otras webs solo en foco, o al revés), se trata como posible homónimo: no decide el género y la ficha del concierto lo explica.
  - Sho-Hai: el identificador de Discogs de su Wikidata apunta a "The Hate", un grupo de death metal. Vuelve a hip hop ("Otros géneros").
  - También Martín (tributo), Pitbul, Hammond York…
  - Con el mismo nombre hace falta la contradicción de dos agendas o de otra web de música: una sola agenda también se equivoca (a Efdemin, DJ de techno, Songkick lo etiqueta "rock").
- **Informe por grupo:** los grupos anteriores se copian al empezar (antes "entran/salen" salía casi todo a 0).
- El conjunto de control pasa a 49 artistas (con los homónimos).

## 2.10.0 — 2026-09-30

Clasificación más consistente y grupo nuevo:

- **Nuevo grupo "Synthwave y dark wave".**
  - Synthwave y todo el neo synthwave actual: retrowave, outrun, darksynth, dreamwave, chillsynth, sovietwave, spacesynth.
  - Darkwave, coldwave y minimal wave; synth-pop y tecnopop; EBM, electro-industrial, aggrotech y futurepop; italo-disco, electroclash, chillwave, vaporwave, witch house y dungeon synth.
  - Antes toda la electrónica iba a "Otros géneros": Suicide Commando, Combichrist, Aviador Dro o Mind Enterprises no aparecían en ningún filtro de foco. El resto de la electrónica (techno, house…) sigue en "Otros géneros".
- **Un género no vota contra su propio estilo.** Si una web dice "Indie Pop", el "Pop" genérico ya no cuenta aparte. La Monja Enana, Kuve o Jimena Amarillo vuelven a "Indie y pop-rock".
- **La agenda cuenta en el consenso** como una web más, con menos peso que Discogs. Una sola agenda no desplaza al estilo principal de Discogs; varias que coinciden, sí.
- **Especialidad de la web.** Si Last.fm identifica al artista solo por el nombre y el concierto viene de una agenda de metal (o de rock, o de blues) que coincide, se acepta. Vuelven EUROPE, Frozen Soul, Fleshcrawl, Bloodhunter… que habían quedado sin clasificar.
- **Si ningún estilo de Discogs está en la taxonomía** (Techno, House…), el género decide solo, con todo su peso.
- "Música ligera", "Balada" y "Pop melódico" van a "Otros géneros". "Pop electrónico" y "Electropop" se tratan como etiquetas genéricas.
- **Conjunto de control:** 46 artistas reales con su grupo correcto (y los que no deben tener) congelados en los tests. Cualquier cambio que los rompa falla antes de publicarse.
- **Informe: conciertos por grupo**, con cuántos entran y salen de cada grupo respecto a la ejecución anterior y ejemplos.

## 2.9.1 — 2026-09-30

Más falsos géneros corregidos:

- **"Pop e indie" pasa a llamarse "Indie y pop-rock"** y solo incluye estilos concretos:
  - Entran indie rock, indie pop, pop rock, power pop, shoegaze, new wave…
  - El pop comercial y latino (género Pop sin uno de esos estilos: baladas, Europop, "Pop Latino"…) va a "Otros géneros".
  - Shakira, Ruth Lorenzo o Sofía Ellar ya no salen en ese filtro.
  - La etiqueta "Pop" a secas de una agenda se trata como genérica.
- **Estilos ambiguos de Discogs.** "Instrumental", "Experimental", "Lounge", "Ambient", "Fusion"… existen en varios géneros, y la taxonomía los tenía bajo Rock. Por eso un pianista neoclásico (Martin Kohlstedt), un productor electrónico (Sabiwa) o Zenet salían en "Rock y metal". Ahora su grupo lo deciden los géneros del artista en Discogs, que también entran en el consenso.
- **Espectáculos con holograma y los infantiles** (CantaJuego…) van a "Otros géneros".

## 2.9.0 — 2026-09-30

- **MusicBrainz entra en el consenso de géneros** (peso 0,9, entre Discogs y Last.fm).
  - Sus géneros los vota la comunidad con un vocabulario cerrado. Se usan los que tienen al menos una cuarta parte de los votos del más votado. Ejemplo, Deep Purple: hard rock 28, rock 14, heavy metal 13, progressive rock 8.
  - Identidad: el identificador de MusicBrainz en Wikidata (exacto) o la única coincidencia exacta del nombre (la misma búsqueda que ya daba la nacionalidad, sin repetir consultas).
  - Ritmo de 1 petición por segundo (su norma). Los ~1.550 artistas guardados se completan en las próximas ejecuciones.
- **Traducción de sus géneros a Discogs:**
  - Literal, o por sinónimo (nwobhm → Heavy Metal, symphonic prog → Prog Rock, americana → Folk/Country…).
  - Si no hay, por la palabra que define la familia ("melodic metalcore" → metal, "rock en español" → rock, "trap latino" → hip hop).
  - Se traducen 790 de sus 2.209 géneros; los que quedan fuera son sobre todo músicas lejanas a esta agenda.
- **Revisado AllMusic y similares:**
  - AllMusic no tiene API: su soporte dice que sus datos son de un tercero y no puede redistribuirlos. La API de TiVo (antes Rovi), de donde salen, es solo comercial.
  - TheAudioDB tiene clave gratuita, pero sus géneros son muy generales ("Rock/Pop").
  - Spotify pide una aplicación de desarrollador y sus géneros no siempre están disponibles.
  - No se añaden.

## 2.8.0 — 2026-09-30

**Clasificación por géneros sin falsos positivos**

- **No se busca como artista lo que no es un concierto.** Si la agenda lo presenta como teatro, musical, danza, humor, infantil, magia, circo o cine, el título no se busca en las webs de música.
  - Ejemplo: el musical "Los Miserables" (Teatro Apolo) salía como el grupo punk chileno del mismo nombre, con su estilo y su origen.
  - Esos espectáculos van a "Otros géneros" y se retira el origen que venía de ese homónimo.
- **Consenso ponderado de las webs de música** en lugar de "todos los géneros que aparezcan".
  - Cada estilo cuenta según su fuente (Discogs 1, Last.fm 0,8, Wikipedia 0,6) y su posición en la lista (el principal va primero).
  - Un género secundario solo cuenta si pesa al menos el 60 % del principal y el 25 % del total.
  - Ejemplo: Shakira ya no aparece en "Rock y metal"; queda en "Otros géneros" (latina) y "Pop e indie".
  - Con este cambio, los conciertos en 3 o 4 géneros bajan de 115 a 12.
- **Last.fm por coincidencia de nombre es una evidencia débil:**
  - Vale la mitad.
  - Si es la única, solo cuenta donde coincide con la agenda.
  - Ejemplo: un título genérico como "Eternal" ya no se convierte en un grupo de doom metal. La ficha explica por qué se descarta.
- **Etiquetas genéricas de las agendas** ("Pop / Rock", "Músicas negras"):
  - Ya no se tratan como si el concierto fuera de los dos géneros a la vez: se marcan como genéricas y solo cuentan si no hay otra etiqueta más concreta.
  - En el panel de filtros se pueden excluir.
- **"R&B" moderno** (Blaya y similares) ya no se clasifica como blues, sino como Funk / Soul.
- **Filtros por estilo:**
  - Cada género muestra su árbol completo de estilos de Discogs (antes solo algunos), indicando cuántos conciertos hay de cada uno.
  - Se pueden elegir estilos concretos, por ejemplo solo "Hard Rock" y "Stoner Rock" dentro de "Rock y metal".
- **Ficha del concierto:** muestra el género y de qué webs sale, e indica si es por consenso, si la etiqueta es genérica o si se descartó una coincidencia dudosa.

**Fuentes**

- **Quitadas 9 fuentes** que fallaron en todas las ejecuciones desde que existen, y quedan listadas en "No se usan":
  - Ticketle y Bandsintown (403).
  - Radar Joven en comunidad.madrid (404). Su programación sigue llegando por Conciertos por Madrid.
  - FORCE Magazine.
  - Las agendas municipales de Getafe, Alcobendas, Arganda, San Sebastián de los Reyes y Coslada.

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
