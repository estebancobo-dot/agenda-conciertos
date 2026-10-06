# Versiones

## 2.71.1 — 2026-10-06

- Enlace de compra: las páginas de conciertos.club que ahora se leen llevan un enlace de promoción a otro evento ("The Vee Bees") o al primero de la sala, y quitaban el bueno de otra web (Muse, Carolina Durante, Cala Vento…). Ahora se salta un enlace que la web pone en las páginas de tres o más artistas, o cuya dirección describe otro concierto ("bal-bliss-en-vivo" para The Big Tigers), y se usa el de la siguiente página. Con los datos de hoy: 740 conciertos con enlace (antes 717); 34 lo ganan y 11 lo pierden, casi todos enlaces que eran de otro concierto o una noticia.

## 2.71.0 — 2026-10-06

**Triple check (agenda + web de la sala + página de compra): menos huecos por fallos propios.**

- Páginas de conciertos.club sin leer: un concierto que conciertos.club da desde su buscador, su portada y sus estilos tenía la misma dirección tres veces y se tomaba por un listado. Ahora cada concierto cuenta una vez: 452 conciertos recuperan su página (hora, precio y enlace de compra).
- Duplicados en la misma sala y día que no se unían: el posesivo inglés ("Munir Hossn" / "Munir Hossn’s MysticSamba", "Fabio Lione" / "Fabio Lione’s Dawn of Victory") y el estilo pegado al nombre ("LQDMS · Pop/Rock"). Revisados todos los pares del mismo día y sala: solo se unen esos 3.
- La web de la sala aún no ha publicado esa fecha: 434 conciertos en salas cuya web se lee son posteriores a la última fecha que esa web anuncia. No es que la sala no lo anuncie: la ficha lo dice ("anuncia hasta el …"), sin bajar la confirmación.

## 2.70.2 — 2026-10-06

- Nivel: los oyentes son los del artista de la ficha del concierto (la misma que da estilo y origen), no los de un trozo del título. "Blue Big Band" ya no lleva los 716 mil oyentes de "Blue", ni "MR. BLACK" los de "Black". Tampoco los espectáculos sobre otro artista ("A Night With The Beatles"). Con los datos de hoy, 215 conciertos con artista de 100.000 oyentes o más; revisados los que tienen un nombre distinto del título: son el cabeza de cartel (Gondwana, Accept, Temples…).

## 2.70.1 — 2026-10-06

- Revertida la 2.70.0: las reglas de origen vuelven a ser las de antes (se cambiaron sin aprobarlo).
- Pruebas nuevas, sin tocar el origen: recorrido completo con datos fijos y sin red (agendas, unión de conciertos, fichas, origen, nivel, enlace de compra, datos de la web y recalcular sin cambios) y la web en un navegador real con esos datos (filtros de origen, tarjeta, ficha con nivel y botón de compra), que corre en cada validación de la web.

## 2.69.0 — 2026-10-06

- Enlace de compra de Madrid en Vivo: la ficha de cada evento en su API (la que ya se lee para la hora, el precio y los estilos, sin peticiones nuevas) trae el enlace de venta que puso la sala (`venta_de_entradas_url`, 191 de 200 eventos). Se usa cuando es de una ticketera y de ese concierto: 62 de 200 en el diagnóstico (Fever, Geeticket…). Los demás no son de compra (Linktree, portada o programación de la sala) y no se ponen. Un mismo enlace para más de dos artistas es la taquilla general, no la de ese concierto, y tampoco se pone.
- Diagnóstico nuevo `diagnostico.yml` con `webs=mev`: campos de la ficha de Madrid en Vivo y dominios de sus enlaces de venta.

## 2.68.1 — 2026-10-06

- Fuera el lector genérico de webs de sala y su diagnóstico: medido, no aportaba nada (las 8 webs con datos estructurados ya eran fuentes).

- Nivel: los oyentes de Last.fm solo suben el nivel, nunca lo bajan ni lo crean solos por debajo de 100.000. Last.fm es mundial pero se usa poco en España y se queda corto con artistas españoles y latinos: pocos oyentes allí no prueban que un concierto sea pequeño.

## 2.68.0 — 2026-10-06

**Nivel del concierto (solo información, sin filtros).**

- Cada concierto tiene un nivel: "gran formato", "formato medio" o "formato íntimo", con su porqué en la ficha (por ejemplo "Movistar Arena: gran recinto · Muse: 7,1 M de oyentes en Last.fm"). La tarjeta solo marca el gran formato.
- Dos señales medibles. La primera es el tipo de recinto (`data/salas_tipo.json`, solo tipos y sin aforos: gran recinto, teatro o auditorio, sala grande, sala, club o bar, tablao, hotel, centro cultural; los centros culturales, teatros, auditorios e iglesias que no están en la lista se reconocen por el nombre). La segunda son los oyentes del artista en Last.fm (paso nuevo "audiencia" en las fichas).
- Los oyentes solo cuentan si Last.fm identificó al artista por su identificador de MusicBrainz: por el nombre solo, un homónimo famoso daría a un grupo local millones de oyentes que no son suyos. Tampoco cuentan en tributos, festivales, jams ni Candlelight.
- Sin ninguna de las dos señales no hay nivel: no se adivina. Con los datos de hoy (3151 conciertos), solo por el recinto: 143 de gran formato, 646 de formato medio, 2148 de formato íntimo y 214 sin nivel (plazas, aire libre y salas sin tipo). Los oyentes se irán sumando en las próximas pasadas de fichas.
- El lector genérico de webs de sala no se usa: el diagnóstico encontró solo 8 webs con datos estructurados, y todas eran ya fuentes.

## 2.67.0 — 2026-10-06

- Filtro de origen: "Resto del mundo" pasa a llamarse "Internacional".
- Comprobado antes de tocar nada: el origen y el estilo que dicen las páginas del concierto (web de la sala, página de entradas y agendas; hasta 4 por concierto y 6 por artista) ya se buscan en la pasada de fichas desde la fase N3/N4. De los 393 conciertos sin origen, en 338 esas páginas se leyeron y no lo dicen: no hay más que sacar de ahí.
- Diagnóstico nuevo (`diagnostico.yml` con `webs=salasweb`, `scraper/salas_web.py`): qué webs de sala publican sus conciertos con datos estructurados, para leerlas con un lector genérico.

## 2.66.0 — 2026-10-05

**Fuentes que ya no se pueden leer, validación que espera a la web publicada y acciones de GitHub al día.**

- **Fuente congelada** (`scraper/pipeline.py`, `fuentes_congeladas`, `marcar_congelado`): una fuente que no se lee bien desde hace más de 2 días (Sala Villanos, cuyo robots.txt no deja leerla desde el 1-10) está congelada. Lo que también anuncian otras webs vivas no cambia (70 de los 91 conciertos de Villanos salen también en conciertos.club, Madrid en Vivo…). Lo que **solo** anuncia ella: "sin reconfirmar" en la tarjeta, aviso en la ficha ("solo lo anuncia Sala Villanos, que no se puede leer desde el 1 de octubre: confírmalo antes de ir"), confirmación "sin confirmar", y a los 30 días sin poder reconfirmarse se oculta (sigue en los datos). La sala no se quita: sus conciertos siguen llegando por las agendas.
- **La validación espera a la web publicada** (`tools/validar_web.py`, `esperar_publicacion`): si arranca antes de que termine de publicarse la versión de main, espera (hasta 15 minutos) en vez de dar fallos de algo que aún no está publicado.
- **Validación nueva**: el conflicto de fecha en la tarjeta y la ficha, y el "sin reconfirmar" de las fuentes congeladas.
- **Acciones de GitHub**: `actions/checkout@v5` y `actions/setup-python@v6` (Node 24; GitHub retira Node 20).

## 2.65.0 — 2026-10-05

**Origen: lo que no es un artista deja de contar como "sin confirmar", y segunda búsqueda de los que quedan.**

- **Sin artista del que decir el origen** (`scraper/origen.py`, `sin_artista`): las jams ("Gumbo Jam", "THE FUCKING JAM"; no "Pearl Jam" ni "The Jam"), los conciertos Candlelight (un cuarteto o un pianista que no se nombra) y los festivales o certámenes (varios artistas) pasan a origen "no aplica". Con los datos de hoy, el origen desconocido baja de 516 a 394.
- **Lotes de origen** (`tools/lotes.py generar --tipo origen`, `lotes.yml` con `tipo=origen`): segunda búsqueda, solo del origen, de los artistas reales que siguen sin él aunque se preguntaran hace poco (una vez más: queda marcado "segunda"). Medido antes de decidir: entre los de nombre en inglés con origen conocido, en las salas pequeñas solo 1 de cada 3 es de España (Villanos 1 de 22, Wurlitzer 1 de 14), así que no se deduce nada por el nombre o la sala: se busca.

## 2.64.0 — 2026-10-05

**Tributos con su estilo como subgénero; partidos con "vs." en medio, ocultos.**

- En "Tributos y versiones", cada tributo tiene como subgénero el estilo al que suena ("Rock y metal", "Clásica y lírica"… de `estilo_tributo` o del grupo de sus estilos); los que no se sabe, en "Tributos y versiones (general)". Ninguno se queda sin subgénero (validación nueva).
- Partidos ocultos aunque el "vs." vaya en medio con un equipo o competición ("Movistar Estudiantes vs. Inveready Askatuak Gipuzkoa", "Real Madrid vs. Partizan…"); "Queen vs. ABBA. Candlelight" y "The Beatles VS The Rolling Stones" siguen siendo conciertos.

## 2.63.0 — 2026-10-05

**Subgénero "(general)" en cada género.**

- En el panel de estilos, cada género tiene un subgénero "(general)" (el primero, siempre a la vista): "Rock y metal (general)", "Jazz y swing (general)"… Agrupa los conciertos de ese género sin ningún estilo concreto (sus webs solo dicen "Rock" o "Jazz", o Discogs no da estilo). Así, al afinar por estilos se pueden elegir también esos, en vez de quedar fuera. Es una agrupación de la web, no un dato: el concierto no gana ningún estilo y su ficha sigue diciendo lo que dicen sus fuentes (`site/index.html`, `estilosDe`, `nomEstilo`).
- No hay "(general)" en "Sin clasificar", "Otros" ni "Tributos y versiones" (los tributos ya dicen en la ficha a qué suenan).
- Rendimiento: el grupo de cada estilo se calcula una vez (`grupoDeEstilo` con memoria).
- Validación nueva: marcar "Rock y metal (general)" deja justo los de rock sin estilo concreto.

## 2.62.0 — 2026-10-05

**Menos estilos "estimados" y más subgéneros.**

- **La etiqueta concreta de la agenda es un dato** (`scraper/normalizacion.py`, `estado_estilo`): "Post-Punk", "Jazz/Swing", "Cantautores"… dicen el estilo del concierto, como la agenda dice su hora o su precio: el estilo pasa a "conocido, según la agenda". Las etiquetas genéricas ("Pop / Rock", "Músicas negras") siguen siendo estimación. Last.fm identificado solo por el nombre sigue siendo estimación, salvo que otra web de música lo identifique y coincida (Shakira: también Wikipedia).
- **El consenso ya no deja sin grupo a un artista con votos repartidos** (`scraper/clasificar.py`, `por_consenso`): el principal siempre cuenta (salvo un empate de más de dos). Antes, con Discogs dando cuatro estilos distintos, ninguno llegaba a la cuarta parte del total y se usaba la agenda (Santiago Auserón, Pedro Pastor, Francisca Valenzuela).
- **Subgéneros desde las etiquetas** (`data/taxonomia.json`, `discogs`): "Pop / Rock" → Pop Rock, "Pop Latino" → Latin Pop, "Jazz Contemporáneo" → Contemporary Jazz, "jazz fusion" → Jazz-Rock, "Metal/Rock duro" → Hard Rock, "Ritmos cubanos" → Cubano, "Flamenco Capital" → Flamenco; la etiqueta entera se mira antes que sus partes. Y el subgénero del título ("Espectáculo flamenco", "Coro…") también cuando hay ficha pero sin estilo concreto.
- Con los datos de hoy: estilo estimado de 912 a 324 (conocido de 1420 a 2008); sin subgénero de 1250 a 1072.

## 2.61.0 — 2026-10-05

**Más precios y horas: precio con gastos de Songkick, hora y precio escritos en las páginas, hora habitual por día de la semana.**

- **Precio con gastos de gestión** (`scraper/entradas.py`, `confianza`, `aplicar_entradas`): Songkick da precio en sus páginas, pero con los gastos sumados (de media un 10 % más que el de la sala o la agenda), y por eso no pasaba el control de acierto. Ahora una web cuyo precio está siempre entre el de las demás y un 15 % por encima (82 % de 193 comparaciones en Songkick) vale para los conciertos sin precio, y la ficha dice "con gastos de gestión". Con los datos de hoy: 97 precios más.
- **Hora y precio escritos en el texto de la página** (`hora_precio_texto`): las webs de sala sin datos estructurados escriben "Apertura de puertas 20:30 · Concierto 21:00" o "Anticipada 12 € / Taquilla 15 €". Se leen del cuerpo de la página (sin menús, pie ni barras laterales; una sola hora de concierto, precios junto a "entrada", "anticipada", "taquilla"…) y solo se usan de las webs en las que aciertan (≥80 % en ≥3 conciertos con el dato ya sabido). Medido: Honky Tonk 12 de 12 horas, Wurlitzer 5 de 5, Get Rock 6 de 6; las que fallan (Las Rozas, noticias de giras) quedan fuera solas. Las páginas ya leídas se releen poco a poco con el lector nuevo.
- **Hora habitual por día de la semana** (`scraper/normalizacion.py`, `estimar_horas`): "los domingos la sala suele empezar a las 13:00" (Jazzville, vermut) además de la hora habitual de la sala. Medido dejando fuera cada concierto con hora: acierta 87 de cada 100. Se muestra como "≈" con su motivo.
- Diagnóstico nuevo: `diagnostico.yml` con `webs=huecos` (acierto de la hora y el precio del texto por web).

## 2.60.0 — 2026-10-05

**Origen deducido sin "probablemente"; Latinoamérica deducida en música latina; jams en pop/rock; fiestas de Halloween ocultas.**

- **Origen deducido** (`site/index.html`): lo que antes salía como "Probablemente España" con la bandera atenuada sale como "España" (o "Latinoamérica"), con la bandera normal; en la ficha, una línea dice de dónde se deduce ("Deducido: nombre en español", "agrupación local…", "banda tributo…"). El filtro "España (solo confirmados)" desaparece: "España" incluye los deducidos y "Origen sin confirmar" son los que no se pueden deducir. Quien lo tenía elegido pasa a "España".
- **Latinoamérica** (`scraper/pipeline.py`, `tributo_y_estimacion`): en música latina, un nombre en español se deduce como Latinoamérica (país sin concretar, 🌎) y cuenta en el filtro "Latinoamérica". En urbana no se deduce nada (hay mucho artista español y latino con nombre en español).
- **Jam sessions y micros abiertos** sin estilo en el título ni en la agenda: pop/rock (rock y metal + pop e indie), con el estilo "estimado" y el motivo en la ficha ("jam session: pop/rock por defecto"). Una jam con estilo en el título sigue con el suyo ("Jam Session Blues" → blues).
- **Fiestas de Halloween ocultas** (`scraper/aportes.py`, `no_es_concierto`): "… Halloween Party", "Halloween Takeover", "Fiesta de Halloween" (sin grupo anunciado); "fiesta de Halloween con X" y "Concierto especial Halloween" no. Lista revisable como el resto.
- Género del título: si coincide con el de la agenda ("Coro…" y "Música clásica"), la ficha dice "según el título" y el estilo es conocido.

## 2.59.0 — 2026-10-05

**Género y subgénero por el título; origen "probablemente España" por el tipo de grupo.**

- **El título dice el estilo** (`data/estilos_map.json` → `titulo_a_estilo`, `scraper/clasificar.py`, `estilo_de_titulo`): sin ficha del artista y sin estilo en la agenda (o solo uno genérico), el título da el género y un subgénero fijo. Ejemplos: "Coro…", "Coral…", "Orfeón…" → clásica y lírica · Choral; "barroco" → Baroque; "música antigua", "renacentista" → Renaissance; "bandas sonoras" → Score; "ópera", "zarzuela"; "boleros" → latina · Bolero; "tango", "cumbia"; "copla" → flamenco y copla · Copla; "big band", "swing"; "jam session blues" → blues; "folclore", "jota" → Folk. La orquesta solo con apellido (sinfónica, de cámara…): "Orquesta Mondragón" es un grupo de pop. No se aplica a los tributos. El estilo queda como "conocido", según "el título".
- **Origen estimado por el tipo de grupo** (`scraper/pipeline.py`, `pais_por_tipo_local`): "probablemente España" (estimación, con su motivo en la ficha) para coros, bandas de música, rondallas, orquestas municipales o de escuela; para lo que solo anuncia el programa cultural de un ayuntamiento (si el título no está en inglés); y para las bandas tributo o de versiones en salas de Madrid (no en grandes recintos ni en webs de giras).
- Con los datos de hoy: origen desconocido de 665 a 525; sin clasificar de 212 a 184; 86 conciertos ganan género o subgénero.

## 2.58.0 — 2026-10-05

**Sin duplicados por el ciclo delante del nombre ni por un título que cambia.**

- **Inverfest es un ciclo, no parte del artista** (`scraper/merge.py`, `separar_ciclo`): "Inverfest. Marwan", "INVERFEST 2026: NACHO SARRIA" e "Inverfest Fito & Fitipaldis" pasan a artista "Marwan", "NACHO SARRIA", "Fito & Fitipaldis" con el ciclo aparte. Así casan con las demás agendas y con las fichas del artista.
- **Las claves de los lotes** (`scraper/aportes.py`, `clave_artista`, `normalizar_claves`): las guardadas con el ciclo delante ("inverfest marwan") se leen como la del artista ("marwan"), sin perder lo aportado ni volver a preguntar por ellas.
- **El mismo concierto con otro título** (`scraper/pipeline.py`, `conciliar`): si la misma página (la misma URL) anuncia hoy ese día y en esa sala un único concierto con otro título, el registro anterior es ese mismo y no se arrastra como "posiblemente cancelado" (Cheo Pardo en Tempo el 28-11 salía dos veces: "CHEO PARDO FULL BANDA" y "PARDO FULL BANDA NY", ambos con p=793568). Si la URL la comparten varios conciertos (una agenda en una sola página), no se toca.
- **"Nueva fecha" a la vista** (`scraper/pipeline.py`, `nueva_fecha_anunciada`): si una web anuncia "nueva fecha" (en la URL de su página) para un artista que otras webs siguen dando otro día en la misma sala, los dos quedan con el conflicto de fecha y las dos versiones, sin elegir (Guille Galván en Condeduque: JacksOnLive, 21-1; conciertos.club, 22-1). La ficha dice quién anuncia la nueva fecha.

## 2.57.0 — 2026-10-04

**Tributos aparte: solo en "Tributos y versiones", fuera de los géneros habituales.**

- **Qué es un tributo** (`scraper/nombres.py`, `es_tributo`): lo dice el título ("tributo", "tribute", "homenaje", "versiones", "covers", "the music of"…; también "Tributo a Queen. Candlelight") o la agenda lo etiqueta así ("Versiones/Tributos"). "Banda de música de…" y "música de cámara" no lo son. Antes 39 títulos con "tributo" u "homenaje" no estaban marcados (Boys Still Cry: tributo a The Cure, Tributo a Rocío Jurado, Amythology, los Candlelight…).
- **Dónde salen**: solo en el grupo "Tributos y versiones" (no en rock, pop, jazz…), que pasa a "Más géneros": no está en los habituales ni en el filtro por defecto. Quien lo tenía elegido lo vuelve a añadir desde los filtros. Con los datos de hoy: 193 conciertos.
- **El estilo al que suenan** queda como detalle del artista: el de la agenda o el del homenajeado ("rock y metal", "Post-Punk"), en la ficha ("Tributo o banda de versiones · Rock y metal") y en `estilo_tributo`. No cuenta en los recuentos de subgéneros de los demás géneros. El estilo de un tributo es "conocido" (lo dice el título o la agenda).
- **Origen**: el de la banda tributo es el que cuenta para los filtros de origen; el del artista homenajeado se muestra aparte en la ficha.
- **Duplicados**: "Plaza de Toros La Nueva Cubierta" es La Nueva Cubierta (Europe salía dos veces).

## 2.56.0 — 2026-10-04

**Fuera lo que no es un concierto, y los lotes van a por lo que la web aún enseña como "sin confirmar".**

- **Reglas automáticas** (`scraper/aportes.py`, `no_es_concierto`): se ocultan por el título los partidos ("Real Madrid vs", "Movistar Estudiantes vs", de la agenda del Movistar Arena), las sesiones de DJ, las exposiciones, foros y charlas, karaoke y podcasts, humor, presentaciones de libros, cine y ferias del disco. Un título que dice "concierto", "en directo" o "live" nunca se oculta así. Con los datos de hoy: 31 eventos (15 de DJ, 6 exposiciones, 3 partidos…). Todos quedan en la lista revisable `ocultos.json` con su motivo, y un error se deshace con `tools/lotes.py mostrar`.
- **Ocultos solo en su sala**: lo que un lote marca como "no es un concierto" se oculta en las salas donde salió (la fiesta "TAYLOR SWIFT" de la Sala But), no si ese nombre da un concierto de verdad en otra.
- **Lotes**: preguntan también el origen de los artistas con origen solo estimado (bandera atenuada, "Origen sin confirmar" en los filtros) y no preguntan por lo oculto.

## 2.55.0 — 2026-10-04

**Fase D: lotes para completar con un chat lo que ninguna web leída dice, comprobado en la página que cita.**

- **Qué se pregunta**: de los artistas, el país (y la ciudad) y los estilos concretos, cuando no se saben o el origen sale de un artista identificado solo por su nombre (posible homónimo), y la identidad (web oficial, Bandcamp…). De los conciertos de los próximos 3 meses sin confirmar, sin hora o sin precio: la página de la sala o de la venta de entradas, la hora, el precio y si se ha cancelado. No se pregunta por tributos, Candlelight, jams ni sesiones fijas. Hoy: unos 860 artistas (≈43 lotes de 20) y 880 conciertos (≈59 lotes de 15), empezando por lo que más falta y lo más cercano. Lo ya preguntado no se repite en 30 días.
- **Cómo se comprueba** (`scraper/aportes.py`): cada dato llega con una página y la frase literal que lo dice. Se abre la página con el mismo lector que las agendas (robots.txt, identificación, ritmo; Instagram, Facebook, X, TikTok, YouTube, Spotify y Linktree no valen porque no se pueden leer) y solo se acepta si la página nombra al artista, la frase está en la página y dice ese país (gentilicio, país o ciudad), esos estilos, o, para un concierto, si la fecha, la hora y el precio están junto al nombre del artista o en los datos del evento de ese día (no en otro concierto de la misma página). Un enlace de una ticketera da el enlace de compra; una página de la web oficial de la sala, la confirmación de la sala. Si el chat no está seguro de la identidad, no se acepta nada de ese artista.
- **Cómo se aplica**: en cada lectura, solo donde falte el dato y sin pisar nunca a Discogs, MusicBrainz, Wikipedia, Wikidata, Last.fm ni a las agendas. El origen aportado es "conocido" con su página y su frase; el estilo es "conocido" si la página es de una web de música (Bandcamp, Discogs, MusicBrainz, Wikipedia, Last.fm, RateYourMusic) y "estimado" si no. Lo aportado vive en la rama `aportes` (`aportes.json` e informes de cada lote).
- **Lo más automático posible** (`.github/workflows/lotes.yml`): todo pasa en una incidencia de GitHub con la etiqueta "lotes". Cada mañana a las 7:25 (Madrid) se publica el siguiente lote listo para copiar; al pegar como comentario la respuesta del chat se comprueba, se contesta con lo aceptado y lo rechazado (y por qué), se guarda y se publica el siguiente. Entiende también `siguiente`, `artistas`, `conciertos` y `estado`. Solo procesa comentarios del dueño del repositorio. Si el chat dice que algo no es un concierto (un partido, cine…), el informe lo marca para revisar.
- **Lectura rápida a prueba de retrasos**: se decide por el tiempo desde la última lectura de todas las agendas (más de 5,5 horas), no por la hora de reloj; la tarea de las 09:40 UTC del 4-10 empezó a las 11:08 y se quedó sin lectura.
- **Mismo artista, mismo día, dos salas**: se unen en un concierto con el conflicto de sala a la vista aunque una misma web salga en los dos, salvo que esa web tenga una página de ese artista en cada sala (Candlelight en dos sedes sí son dos). Con los datos de hoy une 7 parejas repetidas (Papa Roach, The Silencers, Little Barrie, Barracüda…).
- Probado con páginas reales (diagnóstico `lotes`): 10 de 10 casos como se esperaba (datos correctos aceptados; país inventado, frase que no está, página de otro artista, hora y precio falsos y otra fecha rechazados).

## 2.54.0 — 2026-10-04

**Nueva fuente: JacksOnLive.**

- **JacksOnLive** (jacksonlive.es, agenda independiente desde 2014): antes figuraba como "bloquea el acceso automático"; hoy su robots.txt deja leerla y responde. Se leen sus 17 páginas de estilo de Madrid, que traen cada concierto con fecha y hora, estilo, precio, sala con municipio y artistas (unas 20 páginas por lectura). Medido hoy: 344 conciertos dentro de las fechas de la agenda; 284 ya los teníamos y unos 60 son nuevos (los conciertos gratuitos de la Hispanidad en Sol, Plaza de España y Plaza Mayor, Film Symphony Orchestra, Ainhoa Arteta, Estrella Morente, Califato ¾, Tanxugueiras, Inverfest en el Price y Condeduque…). Es independiente de conciertos.club (en las horas en que no coinciden da otras), así que sí cuenta como confirmación. Sus páginas de concierto traen los enlaces de entradas y se leen como las demás.
- **Salas con paréntesis**: "Sala Villanos (Antigua Caracol)", "Palacio de los deportes de Madrid (Movistar Arena)", "Recinto Festivales Madrid (Iberdrola Music)" se reconocen por el nombre sin paréntesis o por el de dentro. Alias nuevos: Teatro Circo Price, Condeduque, Auditorio Nacional de Música, Teatro Rialto, Music Station Príncipe Pío, Babylon Club y Espacio Alma.
- El mismo artista el mismo día en dos salas se une (con el conflicto de sala a la vista) aunque una web ponga el ciclo delante ("Inverfest. Blanca Paloma").
- Revisadas y no añadidas: Fever (sus conciertos de Madrid son 48 grandes que ya salen de 3 a 5 webs; ya se reconoce como venta de entradas), Stairway to Rock, This Is Rock y DeRuting como blogs de giras (probados con el lector de anuncios de giras: 0 conciertos nuevos, y DeRuting confundía la sala), Hellpress noticias y festivales (noticias y festivales de fuera; su agenda ya se lee).
- Diagnóstico: modo `URL@claves` (forma de los datos incrustados) y la prueba de una fuente lista sus conciertos nuevos con lo que haya ese día en la misma sala.

## 2.53.0 — 2026-10-04

**Nueva fuente: Total Stage.**

- **Total Stage** (totalstage.vercel.app, agenda que completan sus usuarios): una sola página con todos los próximos de Madrid, con fecha, hora, sala y estilo. Su robots.txt deja leerla. Medido hoy: 455 conciertos, 415 ya los teníamos; da la hora de 50 conciertos que no la tenían, unos 20 conciertos nuevos dentro de las fechas de la agenda Copia los datos de conciertos.club (en las 14 horas en que las webs no coinciden da siempre la de conciertos.club), así que va en su grupo y no cuenta como confirmación independiente. Sus páginas de concierto no dicen más que el listado: no se leen.
- Revisadas y no añadidas (sin agenda propia o sin conciertos que falten): Ruta 66, Rock and Roll Army, DeRuting y Guía del Ocio (artículos y crónicas), Heart of Gold (promotora con giras por España y pocas fechas en Madrid; esas ya salen de sus ticketeras), Mondo Sonoro (su web rechaza al lector, 403: se respeta). El calendario de Dirty Rock lleva sin usarse desde 2020; su sección de giras ya se leía.

## 2.52.0 — 2026-10-04

**Fase C: rellenar huecos con lo que ya está permitido leer, y estimaciones medidas.**

- **Más páginas de los conciertos con huecos**: las páginas de concierto y de entradas se leen primero en los conciertos a los que les falta la hora, el precio, el enlace de entradas o la confirmación, y en esos, hasta 3 webs distintas (antes, una por concierto y por orden de fecha). Había 2.018 páginas sin leer de conciertos con huecos. Mismas reglas: robots.txt y ritmo; Madrid en Vivo no se lee así (su API ya da esos datos).
- **Todas las fechas de un artista**: la biografía ("banda madrileña de…") se busca en las páginas de todas sus fechas (hasta 6), no solo en las de la primera. 80 artistas sin origen tienen varias fechas (310 conciertos).
- **Hora habitual de la sala** (estimada): en las salas que casi siempre empiezan a la misma hora (al menos 5 conciertos con hora y el 70 % a la misma), los conciertos sin hora muestran "≈ 21:00" y la ficha dice por qué ("la sala suele empezar a las 18:30: 16 de sus 16 conciertos con hora"). Con los datos de hoy, 72 conciertos.
- **Origen estimado por las agendas**: "probablemente España" cuando solo lo anuncian Madrid en Vivo o conciertos.club (agendas de salas madrileñas con grupos locales), el nombre no tiene palabras en inglés y no es de jazz, blues, latina, urbana, soul o músicas del mundo (géneros en los que esas agendas traen muchos artistas de fuera). Medido con los conciertos de origen conocido: acierta 3 de cada 4 (78 de 105), como la estimación por el nombre. Se muestra como estimación.
- No se hace: el estilo por la sala (medido: solo 5 salas programan casi siempre un estilo y cubriría 10 de 258 conciertos sin estilo; además, el estilo lo da una web de música).
- Efecto inmediato con los datos de hoy: origen desconocido de 882 a 774; hora desconocida de 334 a 286. Lo demás se nota según avancen las pasadas.

## 2.51.0 — 2026-10-04

**Fase B: Mis conciertos, Novedades y artistas similares.** Todo en el propio móvil, sin cuentas.

- **Mis conciertos**: botón **☆ Guardar** en la ficha de cada concierto; los guardados llevan **★** en la tarjeta y tienen su página (menú ☰ → Mis conciertos), con **📅 Todos a mi calendario**. La web guarda cómo era cada concierto al guardarlo y **avisa si cambia** de fecha, hora o sala, si parece cancelado o si desaparece de las agendas ("Hora: 21:00 → 22:00"), con un punto en el botón del menú; "Entendido" lo da por visto. Los conciertos que cambian de fecha o de sala siguen guardados (conservan su identificador).
- **Novedades**: los conciertos que han aparecido desde tu última visita (o en los últimos 7 o 30 días), ordenados por la fecha del concierto y con tus filtros; en las listas, la marca **Nuevo**. La primera visita cuenta los 2 últimos días.
- **Artistas similares**: en la ficha, "Si te gusta…": hasta 6 conciertos próximos de otros artistas con el mismo estilo concreto, y por qué ("mismo estilo: Garage Rock").
- Validación en la web publicada: guardar, ★, Mis conciertos, Novedades y similares.

## 2.50.2 — 2026-10-04

Revisión de calidad con los datos de la mañana:
- **Jams con otro nombre**: "Jam Session Blues" (Madrid en Vivo) y "MOE BLUES JAM SESSION" (web de Moe) se unen: sin el nombre de la sala son las mismas palabras. "Jazz jam" y "blues jam" siguen separados.
- **Enterticket**: fuera las raves y noches de club ("Iboga Rave presenta…", "Twist Club e Iboga presentan: Hospitality…"); "Rat-Zinger + KOP | Sala Mon" ya no pone la sala como artista invitado.
- **Fichas sin rellenar** ("BAND NAME") y noches sin artista ("PIANO BAR"): origen "no aplica".
- Validación: la comprobación del enlace directo a una ficha fallaba con los festivales (su título lleva delante la etiqueta "Festival"); era la prueba, no la web.
- Cifras de la mañana (2.803 conciertos próximos): estilo 859 conocidos, 1.380 estimados, 306 no aplica y 258 desconocidos; origen 940, 422, 559 y 882; hora 2.338 conocidas, 131 sin acuerdo entre webs y 334 desconocidas; precio 1.932 y 871. Ya no quedan artistas sin mirar.

## 2.50.1 — 2026-10-03

- Enterticket: las fichas de evento guardadas antes de leer el identificador de Spotify del artista se vuelven a mirar ya (antes, cada 3 días), para que la identificación por Spotify empiece en la próxima lectura.
- Biografías en las páginas del concierto: una página de entradas que no deja leerla (403 de Giglon u OneBox) ya no cuenta como error que se repite en cada pasada.
- Primera pasada con N3/N4/N5: estilo conocido de 775 a 842 conciertos; origen conocido de 850 a 920; hora conocida de 2.096 a 2.409 (desconocida de 717 a 363); precio conocido de 1.604 a 1.989. Quedan 948 artistas por mirar, que se completan en las pasadas de cada 2 horas.

## 2.50.0 — 2026-10-03

**N3/N4 (segunda parte): artistas identificados por su página de Spotify.** Enterticket da el identificador de Spotify de cada artista. Si MusicBrainz no encontró al artista por su nombre (o encontró varios homónimos), se le pregunta qué artista tiene enlazada esa página de Spotify: es el artista exacto, sin riesgo de homónimos, y de su ficha salen su país y sus géneros. Solo con un único artista en el evento (con varios no se sabe de quién es el identificador). En la ficha se dice: "identificado por su página de Spotify (dada por Enterticket), enlazada en MusicBrainz". Con los datos de hoy, 26 de los 45 conciertos de Enterticket no tenían origen conocido.

## 2.49.1 — 2026-10-03

**N5: hora, precio y sala con su estado.** Como el estilo y el origen: conocido (y de qué web), estimado (la hora, si las webs no coinciden: se enseñan las dos) o desconocido tras buscar (qué webs lo anuncian sin darlo). En la ficha se ve solo cuando falta el dato; en la página de Fuentes, el recuento de los cinco datos. Con los datos de hoy (antes de las horas de Madrid en Vivo): hora 2.096 conocidas, 89 sin acuerdo y 717 desconocidas; precio 1.604 y 1.298; sala 2.881 y 21.

## 2.49.0 — 2026-10-03

**N5 (primera parte): horas y precios de Madrid en Vivo.** Su buscador no da la hora (467 conciertos sin hora solo estaban en Madrid en Vivo). La ficha de cada evento sí la tiene (y el precio, o si la entrada es libre), y su API pública la da en las mismas peticiones que ya se hacían para los estilos (100 eventos por petición, con los 10 s que pide su robots.txt): las mismas que antes, con un campo más. Si hay varios pases, se apuntan todos en la nota. Solo si la ficha es del mismo día que el evento; lo que ya dice el listado no se toca.

## 2.48.4 — 2026-10-03

- Conflictos de fecha falsos con la web de la sala: "Blues & Roots" (jam de los lunes en Intruso) salía con otra fecha los días 12, 19 y 26. Ahora se contrasta solo hasta donde publica **cada sala** (una fuente puede leer varias webs: Intruso publica una semana; Moe, un mes) y una **serie** que la web anuncia varios días (jam semanal, ciclo) no se toma por otra fecha del mismo concierto. Quedan los 3 conflictos reales (Tortoise y dos de Café Central).
- Alias: "Sala Moon" (así la escribe Songkick) es Sala Mon Live (Los Palmeras, el mismo día en las dos).

## 2.48.3 — 2026-10-03

- Contraste: la etiqueta "Estimado" de la ficha no llegaba al contraste mínimo en modo claro (lo detectó la validación de la web publicada). El estado se ve ahora en el punto y el borde de color; el texto, con el color normal.

## 2.48.2 — 2026-10-03

**N1: webs de sala con el listado incompleto.** Si la web de una sala no anuncia un concierto en ella que dan 3 o más webs independientes (Papa Roach en Vistalegre, en 8 webs), su listado no está completo (solo lo de su promotora, o una parte) y su silencio ya no baja la confirmación de los demás. La página de Fuentes lo dice en esa sala. Con los datos de hoy: 6 webs de sala (La Riviera, Wagon, Changó, Sala But, Independance, Vistalegre) y los conciertos marcados como "la web de la sala no lo anuncia" bajan de 54 a 23.

## 2.48.1 — 2026-10-03

**N3/N4: más orígenes y estilos leídos en las páginas del concierto.**

- La biografía del artista ("banda madrileña de garage rock") se busca en **hasta 4 páginas** del concierto, una por web, empezando por la de la **sala** y la de **entradas**, que son las que suelen traerla (antes, las 2 primeras de las agendas). También en la **descripción incrustada** de las webs que se montan con JavaScript (Enterticket). Las fichas sin origen o sin estilo se vuelven a mirar con esta regla en las próximas pasadas.
- Títulos que son solo el tipo de evento ("Noches de Piano Jazz", "Concierto de versiones", "COVERS LIVE", "Concierto de Otoño", "Concierto"): origen "no aplica" en vez de desconocido (66 conciertos más con los datos de hoy). Los nombres reales no se tocan ("Los Conciertos de Radio 3", "The Covers").

## 2.48.0 — 2026-10-03

**N3 y N4 (primera parte): estilo y origen de cada concierto, siempre con su estado.**

- Cada concierto dice en su ficha el **estado** de su estilo y de su origen: **dato conocido** (lo dice una web de música, o la agenda con una frase, y de cuál), **estimado** (deducido: etiqueta de la agenda, homenajeado de un tributo, nombre en español… con el motivo), **no aplica** (musicales, jam sessions, festivales con varios artistas) o **desconocido tras buscar**, con **dónde se ha buscado** y qué respondió cada web ("Discogs: sin coincidencia exacta", "MusicBrainz: 3 artistas homónimos"). Nada queda sin procesar. En la página de Fuentes, el recuento.
- **Homónimos**: lo que viene de un artista encontrado **solo por su nombre** (Last.fm sin identificador) ya no se da por conocido sino por estimado, y el origen se muestra como "Probablemente…". Ejemplo: "LANDA" salía con la biografía de un músico checo.
- **Orígenes que se contradicen**: si otra web da otro país para el mismo artista, se muestran las dos versiones ("Otras webs dicen otra cosa"). Con los datos de hoy, 36 conciertos: Sofía Ellar (Discogs Reino Unido, MusicBrainz España), Francisca Valenzuela (Wikipedia EE. UU., MusicBrainz Chile)… Suele ser lugar de nacimiento frente a nacionalidad.
- **Más artistas buscables**: el intérprete se saca del título en "ESPECTÁCULO FLAMENCO: CLAUDIA CRUZ", "HALLOWEEN! FRUIT TONES", "'Apolo Brass', presenta…", "INOIDEL GONZÁLEZ QUARTET" (también sin "Quartet"), "Yasuharu Takanashi’s"… Nunca "PEPE" a secas de "PEPE Y SU TUMBAO".
- Los musicales ("WICKED, El Musical") ya cuentan como origen "no aplica".
- Con los datos de hoy, antes de estas mejoras: estilo 773 conocidos, 1.477 estimados, 306 no aplica y 264 desconocidos; origen 847, 454, 499 y 1.020.

## 2.47.0 — 2026-10-03

**N2: fuentes difíciles, por vías permitidas** (nunca saltándose un robots.txt).

- **Enterticket**, la ticketera de Villanos (cuya web prohíbe leerla en su robots.txt desde el 1 de octubre): su robots.txt sí permite sus páginas de evento y su sitemap. Se leen los conciertos en la Comunidad de Madrid con sus datos (sala, fecha y hora, precio, artistas); cada día solo las páginas nuevas (150 como máximo) y lo ya visto se recuerda. Primera lectura: 48 conciertos (Vistalegre, La Riviera, Mon, Movistar Arena, Wagon, Sala B, But, Intruso…), 14 nuevos y ningún conflicto. Sin sesiones de DJ ni fiestas. En la página de Fuentes, el aviso de Villanos dice por dónde siguen llegando sus conciertos.
- **Café Berlín**, por su página en entradas.conciertos.club, donde publica cada concierto la propia sala: 36 conciertos, 12 nuevos y ningún conflicto. Sale de la lista de salas sin agenda legible. No cuenta como confirmación aparte de conciertos.club (es la misma web).
- **Intruso y Moe**, con un **navegador real**: sus webs pintan la agenda con JavaScript y no tienen robots.txt. El navegador se identifica igual, respeta el robots.txt de la página y de cada petición que hace (las prohibidas se cortan), va al mismo ritmo y no descarga imágenes. Sin noches de poesía, monólogos ni DJ. Primera lectura: 33 conciertos (Intruso solo publica la semana siguiente; Moe, el mes), 8 nuevos y ningún conflicto. Dos sesiones del mismo día que solo comparten el nombre de la sala ("INTRUSO JAZZ SESSION" / "INTRUSO ACID JAM!") ya no se toman por el mismo concierto.
- El Despertar sigue sin leerse: su robots.txt lo prohíbe y no vende en ninguna ticketera legible; sus conciertos llegan por las agendas.
- Diagnóstico: modos `crudo:URL@enlaces:patrón`, `crudo:URL@json` (datos incrustados) y `render:URL` (con navegador).

## 2.46.0 — 2026-10-03

**N1: confirmación auditada.**

- **La web de la sala lo anuncia otro día**: si la web oficial de la sala tiene al mismo artista en otra fecha cercana (±45 días) y nada el día que dice la agenda, el concierto muestra un conflicto de **fecha** con las dos versiones y quién da cada una, y queda sin confirmar ("La web de la sala lo anuncia el …"). Con los datos de hoy: Tortoise (Sala But dice el 8 de noviembre y conciertos.club el 7) y dos conciertos de Café Central (su web dice el 23 de octubre y Madrid en Vivo el 23 de noviembre).
- **Sin falsos "no lo anuncia la sala"**: no se contrasta con la web de una sala si hoy da muchos menos conciertos de lo habitual (lectura a medias o diseño cambiado) o si hoy falló y se usa su última lectura.
- **Datos de la última lectura**: cuando todas las webs que anuncian un concierto han fallado hoy y se usa su última lectura buena, la confirmación lo dice ("se usa su última lectura (del …)") y no pasa de **probable**.
- **Enlaces de compra genéricos**: un enlace de compra que aparece en conciertos de artistas distintos (la página general de una sala o de un promotor) ya no se toma como el de cada concierto ni suma confirmación (160 conciertos lo tenían mal).
- **Auditoría por fuente** en la página de Fuentes: cuántos conciertos de las agendas contradice la web de cada sala (otra fecha, o nada ese día).

## 2.45.0 — 2026-10-03

**Fase A: fiabilidad.**

- **Confirmación de cada concierto**: no se exige un número de webs (muchos conciertos pequeños solo los anuncia un sitio y no se pierden), se dice quién lo confirma. **Confirmado**: lo anuncia la web oficial de la sala o el programa municipal, o se vende en una ticketera y sale en otras agendas, o lo recogen varias agendas independientes. **Probable**: dos agendas, o una de mucha confianza (Madrid en Vivo). **Sin confirmar**: una sola agenda poco fiable, webs que no coinciden, o la web de la sala no anuncia nada ese día. En la ficha, el nivel con sus motivos ("Lo anuncia Honky Tonk", "A la venta en Dice", "En 3 agendas o blogs…"); en la tarjeta, ✓ si está confirmado; en Filtros, **Confirmación** (todos, probable o confirmado, solo confirmados). Con los datos de hoy: 896 confirmados, 1.618 probables y 306 sin confirmar. Un enlace de compra de la misma web que una agenda ya contada no suma.
- **Búsqueda activa en la web de la sala**: cuando la web oficial de una sala se lee entera y no anuncia nada ese día, el concierto lo dice y baja su confirmación (solo hasta la última fecha que publica esa web).
- **Duplicados con otro nombre en la misma sala y día**: "THE DOORS ARE OPEN (Trib The Doors)" = "EL GRAN TRIBUTO A THE DOORS", "EMMA SWIFT (AUST-USA)" = "Emma Swift with Luther Russell", "CARO CAXI" = "CARO TAXI", "O.M.N.I" = "OMNI", "BLISS (Muse Tribute)" = "BLISS. TRIBUTO A MUSE"… (por las palabras que los distinguen, y a una hora cercana). No: "Tributo a Queen" / "Tributo a Mecano". Revisado sobre los datos de hoy: 10 unidos, los 10 bien.
- **Salas**: una sola grafía cuando solo cambian mayúsculas o tildes ("TEATRO SALÓN CERVANTES" → "Teatro Salón Cervantes"); **propuestas de salas repetidas** con otro nombre en la página de Fuentes, para revisar; alias nuevos (Condeduque, Café Libertad 8, Canopy by Hilton).
- Validación en la web publicada: nivel y motivos en la ficha y filtro "Solo confirmados". Tests de todo lo anterior.

## 2.44.0 — 2026-10-03

**Más salas** (segunda tanda; cada una probada en real desde GitHub con la agenda actual):

- **El Perro Club**: 51 conciertos, 35 nuevos, ningún conflicto. El estilo de cada concierto sale de su título ("ALBERTO BALLESTEROS (Pop · Rock · Folk)"); sus sesiones de DJ no.
- **Tempo Audiophile Club**: 53 conciertos, 17 nuevos (antes no se podía leer: su API de eventos sí). 3 conflictos que quedan a la vista: un nombre distinto en otra agenda ("Juan Zelada" / "Joao Selva") y un espectáculo con dos pases el mismo día.
- **TicketAndRoll**, la ticketera de salas pequeñas: sus páginas de **Hangar 48** (tiene dos), **Rincón del Arte Nuevo** y **Jazzville**, tres salas sin web propia legible: 21 conciertos, 5 nuevos, ningún conflicto. "JAVIER MACARRO EN JAZZVILLE" → JAVIER MACARRO.
- En los títulos, lo de entre paréntesis solo se toma como estilo si nombra un género: "(Chile)", "(Berlín)" o "(Feat: …)" no.
- **Teatro Eslava** (10 conciertos, 3 nuevos) y **Palacio Vistalegre** (17, 1 nuevo): su web oficial confirma los que ya traían las agendas. Sin el nombre de la gira en el título ("John Pollón – La Gira Láctea – Tour 2026" → John Pollón).
- Probadas sin agenda legible: Sala Uni, Fulanita de Tal, Live Las Ventas, Café Berlín. Pendiente: Círculo de Bellas Artes (mezcla conciertos con exposiciones y charlas).

## 2.43.0 — 2026-10-03

**Dos vistas nuevas.**

- **Finde**: los conciertos del viernes al domingo de esa semana, aunque cambie el mes o el año (el del 31 de diciembre es del viernes 1 al domingo 3 de enero). Con ‹ ›, deslizar de lado, la tira de los tres días y "Hoy" (de lunes a jueves, el fin de semana que viene).
- **Todos**: todos los conciertos desde hoy en una sola lista, con los filtros y la búsqueda. Un subgénero con dos conciertos a tres meses de distancia sale seguido. Arriba, el total y una fila de meses para saltar (se marca el mes por el que vas).

**Cómo se cargan las listas**: la web descarga una vez la agenda ligera (todos los conciertos próximos, unos 200 KB comprimidos, guardada en el móvil para la siguiente visita) y filtra, busca y pinta en el propio móvil, sin pedir nada más; el detalle de cada concierto se pide al abrirlo. Lo que se reparte es el pintado: los primeros ~30 conciertos al momento y el resto de días según te acercas. "Todos" con 1.500 conciertos se abre en menos de una décima de segundo. La búsqueda en todas las fechas usa ahora el mismo pintado progresivo.

- Validación en la web publicada: el fin de semana (también uno que cruza de año) con lo que dicen los datos; Todos en orden, con su total y los saltos por meses. Accesibilidad (axe) sin fallos y sin scroll lateral a 320 px, en claro y oscuro.

## 2.42.3 — 2026-10-03

- **Sala Clamores vuelve a leerse**: rehízo su web y la agenda pasó de la portada a su página de calendario (el lector daba 0 conciertos y saltó el aviso de cambio en la web). Lector nuevo: día, hora, precio y estilo de cada concierto ("Manu Míguez (Folk)"), sin sus noches de club ni de comedia. Probado en real: 27 conciertos, 18 se unen a los que ya teníamos, 9 nuevos, ningún conflicto.
- **Aviso claro cuando una sala cambia su robots.txt** (Sala Villanos, desde el 1-10): ya no dice "posible cambio en la web", sino que su robots.txt no permite leerla y se respeta; sus conciertos salen de su última lectura y de otras agendas.

## 2.42.2 — 2026-10-03

**Historial de cambios sin ruido** (revisado sobre el primer día real: 31 conciertos con "cambios", casi todos falsos):

- La hora, el precio y los artistas del cartel solo se apuntan como cambio si lo dicen **las mismas webs antes y después**: el primer día se apuntaban como cambios las horas de Café La Palma (su web oficial, recién añadida, manda sobre Madrid en Vivo) y los nombres que traían las salas nuevas.
- Un nombre que es el del cabeza escrito de otra forma ("RADAR JOVEN 2026: ASHLEYS", "GRUMPYS", "DOOMZDEI – El Perro Club") no es "otro artista en el cartel".
- "8 €" → "8-10 €" es más detalle, no otro precio.
- "Deja de aparecer" y "vuelve" en menos de 3 días (una lectura incompleta) no quedan; un cambio de sala que se deshace (la web de Revi alterna entre sus dos salas), tampoco.
- Se borran los cambios apuntados con las reglas anteriores.

**Validación de la web**: dos fallos de la propia prueba, no de la web. Pulsaba "Hoy" cuando está oculto con razón (con un filtro de género, la semana actual empieza ya en hoy), y al filtrar por un género no contaba los conciertos donde toca en el cartel un artista de ese género. Probado entero en local con los datos de hoy: salas, calendarios e historial, bien.

## 2.42.1 — 2026-10-03

Revisión de la lectura de las 23:40 (hora de Madrid), la primera con el cartel de los festivales y las fuentes de datos abiertos:

- **Falsos "¿cancelado?"** (3 de 11):
  - un concierto anterior con el nombre de antes de un alias nuevo ("El Perro de la parte de atrás del coche", hoy "El Perro Club") ya no se da por cancelado: al comparar salas se usan los nombres canónicos de las dos. Lo mismo evita que el historial apunte un falso "cambio de sala" cuando solo cambia cómo se escribe;
  - el mismo festival anunciado con y sin la palabra "Festival" ("Cadena 100 Por Ellas Festival 2026" = "Cadena 100 Por Ellas 2026") se reconoce como uno: todas las palabras que lo distinguen coinciden.
- **Cambio de sala el mismo día** (ItineruM pasa de Revi Space a Revi Live en la web de Revi): ya no sale uno "¿cancelado?" y otro nuevo, sino el mismo concierto, con "Sala: antes → ahora" en su historial.
- Los otros 7 "¿cancelado?" son reales: han desaparecido de las webs donde se anunciaban.
- "Sin clasificar" sube de 225 a 291 por las actividades municipales sin género en su descripción (datos abiertos del Ayuntamiento, 65) y por Songkick; no es un fallo: siguen a la vista en su grupo.

## 2.42.0 — 2026-10-03

**Salas cuya web no leíamos.** Las que más conciertos tenían sin que ninguno lo confirmara su web oficial (página de Fuentes). Para cada una se buscó su web y se probó desde GitHub (robots.txt, cómo publica las fechas):

- **Nuevas fuentes** (web oficial, prioridad 1), probadas en real con la agenda actual: ningún conflicto.
  - **Café Central** (Café Central Ateneo y el auditorio de La Cátedra): 42 conciertos, 27 se unen a los que ya teníamos y 15 nuevos. Las residencias de varias noches (de jueves a sábado, por ejemplo) salen una por noche.
  - **Café La Palma**: 34 conciertos, 16 nuevos. Solo lo que la sala marca como concierto (sus sesiones de club, no).
  - **Cadillac Solitario**: 27 conciertos, 15 nuevos, con su precio y "Tributo"/"Versiones" como estilo ("Matasuegras – Tributo Pop-Rock" → Matasuegras).
  - **Dime que me Quieres**: 20 conciertos, 2 nuevos y el estilo de cada uno (pop, indie, versiones de rock…).
  - Las tres últimas usan la API pública de su calendario (The Events Calendar, de WordPress): un lector común sirve para cualquier sala que lo use.
- **No se pueden leer**, con el motivo en la página de Fuentes: El Despertar (su robots.txt no lo permite: se respeta), Intruso Bar y Moe (la página se monta en el navegador), Rincón del Arte Nuevo, Thundercat, Sala Vesta y El Café de la Ópera (sin fechas en la web), La Coquette, Jazzville y Barracudas (sin web propia: solo redes sociales). Sus conciertos siguen llegando por Madrid en Vivo y conciertos.club.
- **Salas con dos nombres**, ahora una sola: "El Despertar Café" = "Café El Despertar", "Sala UNI" = "Sala Uni", "JazzVille", "Sala Barracudas"… y la web oficial de cada sala nueva para su página de sala.
- Diagnóstico: lista de salas candidatas y lectura de la API de The Events Calendar.

## 2.41.0 — 2026-10-03

**Gestión de conciertos, fase 7: historial de cambios, calendarios suscribibles y páginas de sala.**

- **Historial de cambios de cada concierto**: en cada lectura se compara cada concierto con la anterior y se apunta, con el día en que se vio, si cambia la **hora**, la **fecha**, el **precio** o la sala, si pasa a **cancelado o aplazado** o a **entradas agotadas** (con la web que lo dice), si **aparecen artistas en el cartel**, si **deja de anunciarse** o si **vuelve**. Sale en la ficha ("Historial de cambios", con el día en que apareció en la agenda) y, durante una semana, como aviso en la tarjeta ("hora cambiada", "fecha cambiada"…). Para que no haya ruido: un dato que aparece (una hora que no estaba) no es un cambio; una hora o un precio que pasa a salir de otra web (la página de entradas en vez de la agenda) tampoco; y un cambio que se deshace en 3 días se borra. Medido sobre los datos reales de los últimos 4 días: 1-2 cambios de hora y 3 cancelaciones al día.
- **Cambios de fecha**: si un concierto deja de anunciarse en su día y en las mismas webs aparece otro día en la misma sala con el mismo artista, es el mismo concierto con fecha nueva: conserva su enlace (y quien lo tuviera guardado no lo pierde) y su historial dice "Fecha: antes → ahora", en vez de salir uno "¿cancelado?" y otro nuevo. Solo si la pareja es única (un artista con dos fechas en la sala no se toca).
- **Calendarios suscribibles** (Google Calendar, Apple Calendar, Outlook): uno por **sala** y uno por **género** (con los conciertos donde toca en el cartel un artista de ese género). Se actualizan solos cada pocas horas: conciertos nuevos, cambios de hora o fecha (mismo evento, se corrige) y cancelados (marcados). Sin hora anunciada, el concierto ocupa el día entero. En el menú, **Calendarios**.
- **Páginas de sala**: su programación completa (sin filtros), cómo llegar, su web, su calendario para suscribirse y de dónde salen sus conciertos (si leemos su web oficial o solo agendas generales). Se llega desde la ficha de cada concierto (el nombre de la sala es un enlace), desde la búsqueda (las salas que coinciden salen arriba) y desde **Salas**, en el menú: las ~200 salas con conciertos, con buscador por sala o municipio.
- Validación en la web publicada: lista de salas, búsqueda, página de una sala con su programación y Volver, suscripción y .ics válido con sus conciertos, calendarios por género, e historial en la ficha. Accesibilidad (axe) sin fallos en las páginas nuevas, en claro y oscuro.
- Tests del historial (qué se apunta y qué no, cambios de fecha) y de los calendarios.

## 2.40.0 — 2026-10-03

**Gestión de conciertos, fase 6: tolerancia a fallos.**

- **Tiempo máximo por fuente** (8 minutos; Madrid en Vivo, que tiene su lectura aparte, sin tope): una web que se atasca o no acaba ya no retrasa toda la lectura. Se queda con lo que haya leído y el resto sale de su última lectura buena (como cuando falla); en la página de Fuentes sale como "Lectura parcial" con el motivo.
- **Detección de cambios en las webs**, además de la de "da muchos menos conciertos de lo habitual": aviso si una fuente deja de dar un dato que daba (la hora, la sala o el estilo: de ≥60 % de sus conciertos a ≤10 %) o pone de golpe casi todo el mismo día (síntoma típico de un lector que ya no entiende las fechas). Sale en las alertas y en su tarjeta de Fuentes.
- **Texto mal descodificado** ("Ed├®n", "CafÃ© BerlÃ­n", "Brujer├Ła"): se repara palabra a palabra cuando el resultado es inequívoco (letras normales del español y vecinas); si no, se deja como está. Los 5 casos reales (todos de la web de Revi) quedan bien ("Brujería", "MötorHits", "Eskóbula") y se unen con el mismo concierto de otras agendas: 3 duplicados menos. Si alguno no se pudiera reparar y ese día en esa sala hay otro concierto bien escrito, se descarta como duplicado.
- Tests de las tres cosas.

## 2.39.0 — 2026-10-03

**Gestión de conciertos, fase 5: página de Fuentes profesional.**

- Resumen arriba: webs leídas, cuántas funcionan en la última lectura, conciertos próximos y cuántos confirman 2 o más webs; reparto por tipo.
- **Filtros por tipo** (salas, promotoras y ticketeras, agregadores, blogs y prensa, institucionales) y **"Con problemas"**, y **búsqueda**.
- **Una tarjeta por web**: estado de la última lectura en claro (Funciona, Lectura parcial, Falló · con su caché, robots.txt no deja, Revisar…), tipo y prioridad, tiempo de lectura, y **los últimos 14 días** (un cuadro por día: verde, todas las lecturas bien; ámbar, alguna falló; rojo, ninguna; gris, sin datos). El historial empieza a llenarse con esta versión.
- **Fiabilidad medida** sobre sus conciertos: cuántos tiene y cuántos solo ella; qué parte confirma otra web independiente; **cuándo coincide** con las demás (si en un conflicto de hora, sala o cartel su versión es la minoritaria, lleva la contraria); en cuántos da el precio y el estilo. Con una explicación de cada dato.
- **Salas con conciertos cuya web no leemos**: las que tienen varios conciertos próximos y ninguno confirmado por su web oficial (candidatas a fuente nueva), con el motivo si su web ya se comprobó.
- Salas sin agenda legible y **webs probadas y descartadas**, con su motivo.
- Validación en la web publicada: una tarjeta por web con su tira y sus datos, filtros, búsqueda y sin scroll lateral.

## 2.38.0 — 2026-10-02

**Americana y folk: más fuentes.** El grupo tenía 88 conciertos, casi todos Folk y Folk Rock (61); de sus subgéneros (country, country rock, bluegrass, southern rock, honky tonk, hillbilly, western swing, cajun, zydeco, celta, neofolk) apenas había 3 de bluegrass y 2 de celta. Se buscaron agendas para todos y se probó cada una desde GitHub:

- **SalirMadrid** (páginas de country y folk, JSON-LD): 26 conciertos, 19 ya los teníamos y 7 nuevos (Moonshine Wagon, Nick Mitchell Maiato, The Pink Stones, The Santos Gómes…). Su etiqueta de género es amplia (pone "folk" a Morat), así que el estilo solo se toma cuando el título lo dice ("Moonshine Wagon (Country)"). Sin las fiestas de después ni sesiones de DJ.
- **Qconciertos: folk** además de country.
- **conciertos.club: world music** (celta, músicas del mundo): no trae conciertos nuevos, pero da su etiqueta a los que ya estaban.
- Alias de salas: Palacio de Deportes = Movistar Arena (une los de Morat); con el de El Perro Club de la 2.37.0 se une además un duplicado que ya existía (Grumpys + Petricor).
- Probadas y descartadas: Houston Party (fechas sin año ni sala, y sus artistas ya llegan por otras fuentes), NocheMAD (mismos datos que SalirMadrid), páginas de género de Songkick (ya leemos todo Songkick con su género), El Corte Inglés (403), Taquilla (404), Folklore Plaza Castilla (no responde), Diariofolk (sin agenda), jam de bluegrass de Deviolines (fecha de 2022).

## 2.37.0 — 2026-10-02

**Gestión de conciertos, fase 4: fuentes nuevas para los géneros con menos conciertos.**

Antes, por grupo: synth y dark wave 25 conciertos, cantautores 26, reggae 14, músicas del mundo 32. Se buscaron agendas para ellos y se comprobó cada una desde GitHub (robots.txt y qué publica) antes de usarla:

- **Agenda cultural del Ayuntamiento de Madrid** (datos abiertos, datos.madrid.es): lo que programan sus propios espacios (centros culturales de los 21 distritos, Conde Duque, CentroCentro, Matadero, bibliotecas…). Unos 145 conciertos en los próximos 100 días, con hora y precio (casi todos gratis), ninguno repetido con las demás fuentes. Solo las actividades de tipo Música y los conciertos de la programación destacada; sin audiciones de alumnos ni actos infantiles. El estilo, el que dice su título o su descripción (coral, jazz, zarzuela, boleros…), y solo si nombra un único género.
- **GotiFiestas** (escena gótica, dark wave, EBM, post-punk), por su API pública: conciertos y festivales (no fiestas ni sesiones de DJ) con fecha, hora, sala, precio, cartel y sus géneros. De 17 conciertos, 13 ya los teníamos y ahora tienen su género concreto (EBM, Darkwave…), y 4 son nuevos.
- **conciertos.club: reggae/ska** se lee también.
- Probadas y descartadas (en la página de Fuentes, con el motivo): DotheReggae (403), Café Libertad 8 (devuelve una imagen), esMadrid y Festify Indie (fechas con JavaScript), agenda de la Comunidad de Madrid (404).
- Alias de salas: Nazca Music Live = Sala Nazca, El Perro de la Parte de Atrás del Coche = El Perro Club, Fotomatón bar- sala de conciertos = Fotomatón Bar, Sala Mon Madrid Conciertos = Sala Mon Live.
- En una agenda institucional, otra ficha (otra URL) es otro acto: dos coros distintos el mismo día ya no se unen por empezar igual.
- Diagnóstico: `probar:ID` ejecuta el lector completo de una fuente y dice cómo encaja con la agenda actual (cuántos se unen, cuántos son nuevos, conflictos); `crudo:URL` y `candidatas`. Se lanza desde cualquier rama, para probar una fuente antes de llevarla a la lectura real.

## 2.36.0 — 2026-10-02

**Gestión de conciertos, fase 3: conciertos con varios artistas (festivales, teloneros, ciclos).**

- **Festivales**: se reconocen por su nombre y salen con su **insignia** y **todo su cartel**. El mismo festival anunciado con otro nombre en otra agenda se une ("Pirata Festival 2026 Madrid" = "Pirata Madrid Festival (Boikot, Evaristo…)"; "Dark Christmas Festival: Diorama" = "Dark Christmas Festival Madrid 2026"), y las variantes de su nombre ya no aparecen como si fueran artistas ("Saurom Juglar Festival 2026" como invitado del "SAUROM JUGLAR FEST").
- **Songkick**: sus festivales (páginas /festivals/) salen con su nombre ("Cadena 100 Por Ellas 2026", "CODE 23 Aniversario", "Hallowfest 2026") y todo el cartel; antes se archivaban con el primer artista de la lista ("Rosana", "Vieze Asbak").
- **Cartel desde el título**, solo cuando es inequívoco: "FESTIVAL X (A, B, C y más)" o "X FEST: A y B" (con "y más" se avisa de que el cartel no está completo). Un espectáculo ("MILLION DOLAR QUARTET: ELVIS PRESLEY, JOHNNY CASH…") o un dúo con "&" no se separan.
- **Artistas dentro de un ciclo o festival**: "JAZZ CON SABOR A CLUB 26: MININO BRAVO (Festival JazzMadrid)" → Minino Bravo, con el ciclo aparte (46 conciertos); "Mad Psych Fest: JOSH MEADER TRIO" → Josh Meader Trio dentro del Mad Psych Fest.
- **Fichas de los teloneros y artistas de festivales** (después de las de los cabezas de cartel): país y género de cada uno en la ficha del concierto ("También tocan" / "Cartel del festival"). Un concierto sale también al **filtrar por el género de su telonero**, y la tarjeta lo dice ("+ Punk y garage", con quién). Un festival sin estilo propio toma el de su cartel.
- Al cambiar el título de un concierto (por separar el ciclo o unir un festival) **conserva su enlace** y su fecha de primera vez, y no aparece como "¿cancelado?".
- El lector de páginas guarda también los artistas (performer), el nombre y el tipo del evento. Diagnóstico del cartel (`diagnostico.yml`, webs=cartel).
- Validación en la web publicada: insignia y cartel de un festival, y concierto que sale por el género de su telonero.

## 2.35.0 — 2026-10-02

**Navegación de fechas desde cualquier punto de la lista, en las tres vistas.**

- Cambiar de día, semana o mes (tira de días, flechas ‹ ›, deslizar, Hoy) desde media lista deja la vista nueva **desde su principio**, justo bajo la cabecera: la tira de 7 días y el primer concierto, o la cuadrícula del mes. Antes, en la vista de día, tocar otro día de la tira o deslizar dejaba la lista del día nuevo a la misma altura (a media lista o en blanco). Si estabas arriba del todo, no se mueve nada.
- **Hoy**, siempre que no estés ya en hoy: ahora también en el mes actual con otro día elegido (antes no salía) y en la semana actual cuando vas por otro día; en la semana lleva a la lista de hoy (antes se quedaba en el lunes). Cuando no hace falta se oculta sin quitar su hueco, para que el título no salte.
- **Deslizar de lado** también en la semana (sobre la lista) y en el mes (sobre la cuadrícula), como ya pasaba en el día, con un pequeño desplazamiento en el sentido del cambio (desactivado si el móvil pide menos movimiento).
- La cabecera del día dice **"Hoy, …"** y **"Mañana, …"**.
- Validación en la web publicada: 11 casos nuevos (cada forma de cambiar de fecha en cada vista, desde media lista, y cuándo se ve Hoy).

## 2.34.1 — 2026-10-02

- **Fotos de Wikimedia Commons sin miniatura propia** (Rajery, Messa…): la ficha guardaba la dirección `commons.wikimedia.org/wiki/Special:FilePath/…`, que el robots.txt de Wikimedia prohíbe a los lectores automáticos; la miniatura no se podía hacer y la web pedía la foto fuera. Ahora se guarda la dirección directa de `upload.wikimedia.org` (la misma a la que redirige) y, si el archivo es más pequeño que la miniatura pedida, se usa el original. Test.

## 2.34.0 — 2026-10-02

**Gestión de conciertos, fase 2: lecturas separadas y más frecuentes.**

- Madrid en Vivo se lee **aparte, cada noche a las 01:20 UTC** (03:20 en Madrid): pide 10 s entre peticiones (su robots.txt) y tardaba 38 de los 45 minutos de la lectura completa.
- La **lectura completa de las 03:10 UTC** lee las otras 63 fuentes en pocos minutos y usa la de Madrid en Vivo de un par de horas antes; cuenta como lectura completa.
- **Lecturas rápidas de todas las agendas (menos Madrid en Vivo) a las 09:40, 15:40 y 21:40 UTC**: conciertos nuevos, cambios y cancelaciones cada 6 horas en vez de una vez al día. Van dentro de esas pasadas de fichas (no como tareas aparte: en la cola de GitHub una tarea en espera se cancela si llega otra). El resto de pasadas siguen igual (reintento de las que fallaron, fichas y páginas de entradas).
- Nuevas opciones: `python -m scraper --sin id1,id2` (todas menos esas) y `--minutos-fichas N` (tope para fichas de artista en una lectura de agendas).
- El informe explica el nuevo calendario. Test de integración: las fuentes leídas aparte entran con su última lectura y no se pierde ningún concierto.

## 2.33.1 — 2026-10-01

Revisión de la primera pasada real (1.521 páginas leídas: 473 conciertos con enlace de compra, 397 con cartel de gira, 29 precios, 2 cancelados, 1 aplazado, 1 agotado):
- Un blog de agenda de una ticketera (blog.ticketmaster.es) salía como "Comprar entradas en Ticketmaster" y una página de contacto como enlace de compra: la fuente solo cuenta como página de entradas si su URL es de ese concierto, y se descartan blogs, contacto, información legal, ayuda…
- Logos (de la sala o de la ticketera) no cuentan como cartel de la gira.
- Nombres legibles de ticketeras (los enlaces de afiliado de La Ganzúa son Ticketmaster; Movingtickets, Ticket&Roll, Enterticket…) y enlaces sin parámetros de seguimiento.
- Horas: de 938 conciertos sin hora, 88 tienen una página fiable con hora, pero 85 están sin hora porque sus fuentes no coinciden: la página es una de esas mismas versiones, así que el conflicto se sigue enseñando en vez de elegir una.

## 2.33.0 — 2026-10-01

**Gestión de conciertos, fase 1: páginas de concierto y de entradas.**

- Nuevo lector (`scraper/entradas.py`) de la página de cada concierto (web de la sala, agenda) y de la página de entradas que enlaza. Solo toma lo que la página dice en sus datos estructurados (schema.org, los que lee Google) y en sus enlaces:
  - **Enlace de compra directo** ("Comprar entradas en Mutick ↗"), como botón principal de la ficha: el de la propia fuente si ya es una ticketera, el que da la web de la sala o, si no, el de la agenda. Nunca la portada genérica de una ticketera ni enlaces de páginas que listan muchos conciertos.
  - **Hora y precio que falten** (nunca se pisa lo que ya dicen las fuentes), solo de webs cuya hora/precio coincide con lo que ya sabemos en ≥80 % de los casos: se mide en cada pasada. Hay webs que ponen "20:00" a todo (Conciertos por Madrid, Wurlitzer, Metalcry en el diagnóstico): así se quedan fuera solas. La ficha dice de qué web sale.
  - **Agotado, cancelado o aplazado**, solo si la página lo dice: aviso en la tarjeta y en la ficha, con enlace a quien lo dice.
  - **Cartel de la gira** publicado por la sala, la promotora o la página de entradas (no las fotos de perfil de las agendas, ni imágenes de relleno, ni la misma foto del artista). En la ficha, una sola cabecera deslizable: foto del artista ↔ cartel, con puntitos. Se sirve como copia reducida propia, como las fotos.
- Diagnóstico previo con páginas reales (200 de concierto, 64 de entradas): hora fiable en conciertos.club, La Ganzúa, Villanos, Gruta 77, Mutick, Silikona; ticketeras legibles: Mutick, Movingtickets, Fever, Entradium, DICE, Eventbrite, Ticket&Roll, JF Promotickets. Ticketmaster, Giglon, Tomaticket y OneBox bloquean la lectura (403) y Enterticket la prohíbe en su robots.txt: se enlazan, pero no se leen.
- Se lee en las pasadas de fichas (cada 2 h) con el tiempo que les sobra: primero los conciertos más cercanos, con caché (`paginas.json` en la rama de datos; se relee a los 3 días si el concierto es en menos de 2 semanas, si no a los 10). Madrid en Vivo no se lee (10 s por página y casi nunca enlaza a las entradas). Una web que falla 3 veces se deja para la siguiente pasada.
- La validación diaria comprueba en la web publicada que el enlace de compra es el botón principal y anota cuántos conciertos tienen enlace, hora y cartel.

## 2.32.0 — 2026-10-01

- **Hoja de filtros más clara.**
  - Géneros: "Habituales · Todos · Ninguno" en el control de arriba ("Ninguno" sustituye al enlace "Desmarcar todos" que estaba suelto en medio). Si eliges a mano, no queda marcado ningún preajuste y el título lo dice: "Géneros · 2 de 21 · a tu medida" (desaparece el botón "Personalizado").
  - Cada sección dice a la derecha qué tienes elegido (géneros, origen; los estilos, en "Afinar por estilos").
  - El botón de abajo se llama "Por defecto" (antes "Quitar todo", que en realidad volvía a los habituales) y se apaga cuando ya está todo por defecto.
- Comprobado el ir y volver: lo aplicado se ve igual al reabrir la hoja; cerrar con ✕ no aplica nada.

## 2.31.1 — 2026-10-01

- **Quitar todos los filtros, a la vista.** En la lista, con algún filtro puesto, la fila de chips empieza por "✕ Quitar filtros". En la hoja, el botón de abajo a la izquierda se llama "Quitar todo" (antes "Restablecer") y se apaga cuando no hay nada que quitar. "Quitar todos" de los géneros pasa a "Desmarcar todos los géneros" para no confundirlo.

## 2.31.0 — 2026-10-01

- **Elegir subgéneros directamente** (p. ej. Bluegrass + Post-Punk). El panel de estilos tiene buscador ("blue", "post…") sobre los estilos de todos los géneros: primero los de los géneros elegidos y luego el resto, plegados. Marcar un estilo elige su género; antes había que elegir primero los géneros a mano y, si no, el panel solo decía "Elige antes algún género".
- **Desde "Habituales" o "Todos", al marcar el primer estilo se filtra solo por los estilos marcados** (antes seguían todos los demás géneros enteros: "Ver 1451 conciertos" en vez de 33). Un interruptor, "Incluir también los demás géneros", los recupera si se quieren.
- **"Quitar estilos"** deja los géneros como estaban antes de marcar estilos.
- La validación diaria lo comprueba en la web publicada (buscar y marcar dos estilos de géneros distintos: salen justo sus conciertos).

## 2.30.1 — 2026-10-01

- En la fila de géneros de la lista, los elegidos pasan delante (justo tras "Habituales"): al tocar uno que estaba a la derecha, la fila volvía al principio y no se veía por qué estabas filtrando.

## 2.30.0 — 2026-10-01

- **La lupa ya no te sube al principio.** Abre la búsqueda en la propia cabecera, lista para escribir, sin mover la lista. Al escribir salen los resultados (de todas las fechas); Cancelar (o borrar el texto) vuelve a la lista exactamente en la tarjeta en la que estabas.
- **Chips de género con el sentido de las apps actuales** (Material 3, iOS, Google Maps, Airbnb): elegido = relleno oscuro con ✓; sin elegir = solo contorno. Antes era al revés en la práctica: por defecto todos salían "marcados". Ahora, sin filtro de género solo está marcado "Habituales"; al tocar un género se filtra por él y sale relleno; tocando otros se añaden; al quitar el último se vuelve a "Habituales".
- **Hoja de filtros más corta y clara** (de ~3.500 px de scroll a ~1.500):
  - Preajuste como control segmentado: **Habituales · Todos · Personalizado**. Se marca el que está activo; si cambias algo a mano, se marca "Personalizado".
  - Géneros como chips que se ajustan en filas (antes, 22 tarjetas con descripción; la descripción sigue al mantener el dedo o pasar el ratón).
  - Estilos en su propio panel ("Afinar por estilos ›"), solo de los géneros elegidos, con los 12 con más conciertos y "Ver los N estilos".
  - Origen del artista: la opción elegida, rellena (mismo criterio que los chips).
- La validación diaria comprueba todo esto en la web publicada (lupa sin mover la lista y vuelta a la misma tarjeta, chips, preajuste, alto de la hoja).

## 2.29.1 — 2026-10-01

- Los países de frases de Wikipedia se vuelven a calcular en cada pasada, como los de la agenda y Last.fm: con la 2.28.0 la regla ya no los daba, pero los conciertos conservaban el país que tenían (8 conciertos próximos con un país de otra persona: "Carey", "Martín", "Shaka & Elektra"…). Quedan los 7 buenos.

## 2.29.0 — 2026-10-01

- **‹ periodo › y Hoy siempre a mano.** Al bajar por la lista, la fila de navegación (flechas, fecha del periodo y Hoy) se iba hacia arriba y había que volver al principio para cambiar de semana o de mes. Ahora, cuando esa fila desaparece, el título de la app en la cabecera fija deja su sitio a la misma navegación en compacto: "‹ 12–18 oct · 207 conciertos · Hoy ›" (semana), "‹ Oct 2026 ›" (mes), "‹ Sáb, 10 oct ›" (día). No añade altura. Al avanzar o volver a hoy, el periodo nuevo queda listo para leer justo debajo de la cabecera (tira de días y primer día, o la cuadrícula del mes).
- La validación diaria lo comprueba a media lista en la web publicada.

## 2.28.0 — 2026-10-01

- **Origen desde Wikipedia: fuera los falsos.** La búsqueda en todo Wikipedia (2.25.0) dio país a 29 artistas, pero en 15 era de otra persona: nombres cortos o genéricos que salen en frases ajenas ("Jazz" → la banda británica James Taylor Quartet, "Carey" → Mariah Carey, "Blues", "Martin" → Diego Martín, "Kraak" → Kraak & Smaak…). Ahora el nombre tiene que salir en la frase como nombre propio completo (con mayúscula, sin otra palabra con mayúscula pegada ni empezar a mitad de nombre) y el gentilicio pegado a él. Los hallazgos guardados se vuelven a comprobar con esta regla: quedan los 14 buenos (Megara, No Way Out, 31 Fam, Malón, Nirvana…).
- **Nombre como palabra entera** también al leer las agendas: "martin" ya no coincide con "Martínez". Se pierde solo un país mal puesto ("tributo a U2": la banda tributo no es irlandesa).
- La pasada de fichas vuelve a aplicar las fichas a todos los conciertos cuando cambia la versión, aunque no haya artistas nuevos que consultar (si no, una regla corregida no llegaba a la web hasta la lectura de la noche).

## 2.27.0 — 2026-10-01

- **El menú ☰ funciona a cualquier altura de la lista.** Se abría arriba del todo de la página, fuera de la pantalla si habías bajado: parecía que no hacía nada. Ahora se abre siempre bajo el botón.
- **Buscar y Filtros siempre a mano.** Al bajar por la lista, cuando la barra de búsqueda y filtros se va hacia arriba, aparecen dos iconos en la cabecera fija (lupa y filtros, con el número de filtros activos). Filtros abre la hoja ahí mismo, sin mover la lista; Buscar sube a la caja de búsqueda y la deja lista para escribir (la búsqueda es en todas las fechas). Arriba del todo no salen, para no duplicar la barra.
- La validación diaria lo comprueba a media lista en la web publicada.

## 2.26.0 — 2026-10-01

- **La fecha del día se queda fija arriba al bajar por la lista**, igual en mes, semana y día: una sola línea con la fecha completa y cuántos conciertos hay ("Viernes, 9 de octubre · 58 conciertos"). Al llegar al día siguiente, su cabecera empuja a la anterior.
- **Semana: la tira de días marca el día por el que vas** mientras bajas. Tocar un día de la tira lleva justo a su cabecera (antes, con semanas largas, se quedaba a mitad de camino porque las tarjetas cambiaban de alto durante el desplazamiento suave).
- **Día: la tira de la semana también se queda fija**, para cambiar de día sin subir. Arriba, el mes y el año; la fecha completa va en la cabecera del día, sin repetirla.
- **Validación del paso de fechas**: la validación diaria recorre con las flechas ‹ › las tres vistas de un día a otro, de una semana a otra, de un mes al siguiente, de un año al siguiente (y vuelta), por los cambios de hora de octubre y marzo y por febrero, y al cambiar de vista y con "Hoy". En cada paso comprueba la dirección, el título, la tira de 7 días, la cuadrícula del mes (días y columna del día 1) y que los conciertos sean justo los de esas fechas. Hoy: 103 de 103 pasos bien.
- **Pasadas de fichas que no se cortan**: si el reintento de agendas tarda (el de las 10:00 tardó 41 min), las fichas usan solo el tiempo que queda del paso. Antes el paso se cortaba a los 100 min y esa pasada no actualizaba los conciertos ni publicaba la web (las fichas consultadas sí se guardaban).
- Contraste del día marcado en la tira: si el día ya había pasado, el estilo de "día pasado" le quitaba el fondo oscuro y el texto quedaba claro sobre claro (lo detectó la validación con axe). La comprobación de accesibilidad cubre ahora también la vista día.
- Lo fijo ocupa como mucho ~200 px de 844 en un móvil (cabecera, tira y fecha). La validación diaria lo comprueba en las tres vistas, junto con que la tira marque el día correcto y que el salto a un día sea exacto.

## 2.25.0 — 2026-10-01

- **Filtro de origen con Latinoamérica aparte**: España (confirmados y probables, estos con la bandera atenuada), España (solo confirmados), Latinoamérica, Resto del mundo y Origen sin confirmar. Medido sobre 692 artistas con país confirmado, el "probablemente España" por el nombre acierta el 76 %, y casi todos los fallos son latinoamericanos (un nombre en español no distingue España de Latinoamérica): así se ve aparte. La validación diaria comprueba que las opciones reparten todos los conciertos sin dejar ninguno fuera ni contar ninguno dos veces.
- **Origen buscado en todo Wikipedia**: para quien sigue sin origen, la búsqueda de Wikipedia (API oficial) encuentra frases como "la banda madrileña X" en artículos de festivales, sellos u otros grupos, aunque el artista no tenga artículo propio. Con la misma regla estricta que en las agendas: el gentilicio pegado al nombre.

## 2.24.0 — 2026-10-01

- **Madrid en Vivo: los estilos de cada concierto.** Su buscador solo da la categoría ("Pop / Rock", "Músicas negras"), pero cada evento tiene además sus estilos ("#Folk-Rock", "#Indie"…). Ahora se leen de la API pública de WordPress de la web (permitida por su robots.txt), en bloques de 100 eventos y con los 10 s entre peticiones que pide. Son el estilo del concierto según la agenda; si un evento no tiene ninguno reconocible, se queda la categoría. Esto ataca la mayor fuente de etiquetas genéricas (~490 conciertos).

## 2.23.0 — 2026-10-01

Lo aprendido con el diagnóstico de páginas reales (workflow "Diagnóstico de páginas de agenda"):

- **Las páginas de Madrid en Vivo no describen al artista** (solo el título), y de ahí salen casi todas las etiquetas "Pop / Rock". Leyendo la agenda no se puede concretar su estilo; hace falta una web de música.
- **Discogs: también los discos sueltos.** Unos 200 artistas estaban identificados en Discogs, pero sin estilo, porque solo se miraban sus "masters" y los grupos pequeños casi nunca tienen. Ahora se leen también sus discos (género, estilo y el país donde se editaron: si todos se editaron en el mismo país, ese es su origen, "Discogs (país de edición de todos sus discos)").
- **Discogs: entre homónimos, el de España.** Si hay varios artistas con el mismo nombre y solo el perfil de uno dice que es de España, es ese (el concierto es en Madrid). Se marca así en la ficha y, como toda identidad por el nombre, se descarta si contradice a la agenda.
- **Estilo leído en la agenda**: también entre paréntesis detrás del nombre ("JOSH MEADER TRIO (Jazz-Fusión / 21:00 horas)", "Clarence Bekker Band (Soul & Funk)") y en las frases sobre el artista ("miaw es un dúo de pop experimental… Su música… shoegaze, trip-hop"). Más papeles para el origen (soprano, tenor, director…) y "el productor y DJ alemán más conocido como STVW".
- **Bandcamp y Deezer no se usan**: su robots.txt no permite las búsquedas automáticas.
- La lectura completa ya no se rompe con un título sin letras (solo símbolos u otro alfabeto).

## 2.22.0 — 2026-10-01

Catálogo más inteligente: géneros con entidad propia, estilo leído en la página del concierto, origen de tributos y origen estimado por el nombre.

- **"Otros géneros" se reparte en 11 grupos propios**, con sus estilos de Discogs como el resto: jazz y swing, soul, funk y R&B, flamenco y copla, urbana y hip hop, latina, electrónica, clásica y lírica (los Candlelight incluidos), reggae y dub, músicas del mundo, pop comercial, y musicales y espectáculos. "Otros" queda solo para lo que no es de ningún género (infantil, karaoke, tardeo): de 1.299 conciertos a 11. La taxonomía incluye ahora los géneros y estilos de Discogs de Jazz, Funk / Soul, Hip Hop, Latin, Classical, Reggae, Stage & Screen y toda la electrónica. En los filtros salen en "Más géneros". Quien tenía marcado "Otros géneros" los sigue viendo todos.
- **El estilo, también desde la página del concierto**: "Claim es un grupo murciano de rock alternativo y post punk" → Alternative Rock y Post-Punk. Cuenta como la etiqueta de una agenda más, así que concreta las etiquetas paraguas ("Pop / Rock", "Músicas negras") y da estilo a quien no tiene ficha. Sin ficha, los estilos de Discogs que nombran las propias etiquetas ("Jazz/Swing" → Swing). Conciertos sin estilo: de 2.060 a ~1.580 antes de leer las páginas.
- **Lo que dice la página de la agenda se aplica siempre**: antes, el origen leído allí se perdía si el artista no estaba en ninguna web de música, que es justo el caso de los grupos locales.
- **Tributos con dos orígenes**: el de la banda tributo (el del concierto) y el del artista homenajeado ("Tributo a Fleetwood Mac" → Fleetwood Mac, Reino Unido). Si el tributo no tiene estilo, se usa el del homenajeado.
- **Origen estimado por el nombre**: si ninguna fuente dice de dónde es y el nombre está claramente en español ("Felipe Arce Cuarteto", "Lucía Fernández"), sale como "probablemente España", con la bandera atenuada y el motivo en la ficha. No se estima en festivales, ciclos, latina ni urbana. Cuenta en el filtro "Españoles" y no en "Origen sin confirmar". Las palabras propias del español y del inglés salen de las frecuencias de wordfreq (data/palabras.json).
- La validación diaria mide la calidad del catálogo: conciertos en "Otros", sin clasificar, con etiqueta genérica, sin estilo y sin origen.

## 2.21.0 — 2026-10-01

- **Fichas más rápidas**: 75 minutos por pasada (antes 45), 8 artistas a la vez y primero los que no tienen origen. Una pasada ya recorre todos los pendientes.
- **Origen de tributos y espectáculos con intérprete**: no se buscan en webs de música (la banda tributo no es el artista homenajeado), pero se lee lo que dice la página de la agenda. Por ejemplo, "THE RUMORS: TRIBUTO FLEETWOOD MAC" → «The Rumors, banda tributo madrileña» y "ESPECTÁCULO FLAMENCO: CLAUDIA CRUZ" → lo que diga de Claudia Cruz.
- **Más estricto con la página de la agenda**: el gentilicio tiene que ir pegado al nombre del artista ("Mala Luna Band es un grupo madrileño", "la banda valenciana Neon Collective"). Antes, en la página de Alchemy Project (tributo a Dire Straits), «la banda inglesa» se refería a Dire Straits y le ponía Reino Unido. Los orígenes leídos en textos se recalculan siempre con la regla actual.
- Las páginas de agenda borradas (404), vetadas por robots.txt (Instagram, calendarios) o con captcha ya no cuentan como error ni se repiten en cada pasada.

## 2.20.1 — 2026-09-30

- Miniaturas y fotos de ficha guardadas en la rama `miniaturas` del repositorio, en vez de la caché de GitHub Actions (que caduca y se llenaba con una copia por ejecución). Es un único commit sin historial: cada ejecución sube solo las fotos nuevas y quita las de conciertos que ya no están.
- Las miniaturas se piden unas 2 pantallas antes de que lleguen (antes, 150 px), y los días de la lista se pintan también antes. Ahora que las fotos son propias y pesan ~6 KB, al bajar la lista ya están cuando llegan.
- Validación del peor caso: la semana, el día y el mes con más conciertos (ahora la semana del 5 de octubre, con 320), con el filtro "Todos", sin caché. Mide huecos sin foto mientras se baja seguido: fallo si pasan del 15 %.
- Accesibilidad: las tablas del informe que se desplazan de lado se pueden recorrer con el teclado.

## 2.20.0 — 2026-09-30

Origen del artista con otro enfoque. Antes solo se buscaba en las webs de música (Wikidata, Wikipedia, Discogs, MusicBrainz y Last.fm por etiquetas) y 1.657 de 2.643 conciertos próximos se quedaban sin origen. De esos:

- **~200 no tienen un artista del que decir el origen**: "Concierto de Blues" (79), "Concierto de Jazz" (52), jam sessions, micros abiertos, karaoke. Pasan a "no aplica", como los espectáculos.
- **Lo que dice la propia agenda.** En la página del concierto se buscan frases explícitas sobre el artista: "la banda madrileña X", "el cantautor argentino X", "procedentes de Glasgow". Solo cuentan si la frase nombra al artista y el texto da un único país. Dónde vive ("afincada en Madrid") no cuenta. La ficha muestra la frase y la web de la que sale.
- **Biografía de Last.fm** ("X is a Spanish band from Madrid") y **perfil de Discogs** sin la fórmula "from…" ("Spanish punk rock band").
- **MusicBrainz**: si no tiene el país del artista, se usa su zona o su lugar de inicio (Madrid → España).
- **Last.fm identificado solo por el nombre**: se acepta la etiqueta "spanish" para quien toca en Madrid. Otro país no, porque podría ser un homónimo.

Solo con lo que ya estaba guardado, los conciertos sin origen bajan de 1.657 a ~1.417. Las páginas de las agendas y las biografías se consultan en las pasadas de fichas (cada 2 horas, con el mismo ritmo y robots.txt de siempre), así que la cifra seguirá bajando en los próximos días. La validación diaria avisa si más del 40 % de los conciertos próximos siguen sin origen.

## 2.19.0 — 2026-09-30

- **Todas las fotos se sirven desde la propia web.** Antes solo las de conciertos.club y Discogs. El resto (Madrid en Vivo, 679 conciertos; Songkick, Wikimedia, Fever…) se reducía al vuelo con wsrv.nl, que solo es rápido con fotos que alguien ya ha pedido. La primera vez tardaba 1-3 s por foto, por eso los listados de un día o de un mes y la foto de la ficha iban unas veces rápido y otras lento. Ahora cada foto se descarga una vez al publicar (respetando robots.txt y el ritmo de cada web), se reduce a miniatura (160 px, ~6 KB) y a foto de ficha (720 px) y se sirve desde GitHub Pages. Las de los conciertos más próximos van primero.
- Hasta 8 miniaturas a la vez (antes 4): las propias son pequeñas y salen del mismo servidor.
- **La validación ya no se engaña con cachés calientes.** Cada vez elige días, meses y fichas al azar y los abre en un navegador sin caché, como la primera vez que los mira alguien. Además mide qué parte de las fotos es propia (mínimo 97 %) y cuántas imágenes se piden fuera de la web.
- **Contraste corregido.** Los números de los chips y los días pasados de la tira de la semana tenían poco contraste. La validación ahora lo comprueba en semana, mes, ficha e informe, en modo claro y oscuro, y cuenta como fallo si vuelve a pasar.

## 2.18.0 — 2026-09-30

- **Validación automática de la web publicada** (`tools/validar_web.py`, workflow "Validar la web publicada"). Se lanza sola después de cada publicación y una vez al día, sobre la web real, con un navegador real que imita un móvil de gama media-baja (4G lenta, CPU 6x). Tiene unas 90 comprobaciones con umbral fijo, en 6 bloques: publicación, funcional, UX, rendimiento, gestión de fallos y otros. Si algo falla, abre el issue `alerta-web` (aviso por correo), que se cierra solo al arreglarse. Sustituye a la antigua "Probar la web en vivo", que solo medía y no decidía si algo estaba bien o mal.
- **Una publicación ya no puede dejar código antiguo.** La ejecución diaria prepara la web con el código más reciente de `main`, aunque hubiera empezado antes de un cambio. Si aun así la web publicada no coincide con `main`, la validación la vuelve a publicar sola.
- Ficha sin conexión o con el detalle caído: el precio ya no se queda en "Cargando…" (encontrado por la validación de fallos).

## 2.17.1 — 2026-09-30

- **La ficha enseña una sola foto.** Se quita el apaño de la 2.17.0 (foto pequeña borrosa y la grande encima al llegar). Ahora las fotos de ficha de los conciertos que tienes en pantalla se descargan en segundo plano mientras miras la lista: de 2 en 2, con prioridad baja, solo cuando ya han llegado las miniaturas y nunca con el ahorro de datos activado. Al abrir la ficha, la foto ya está en el móvil y sale directamente. Si aún no ha llegado, se ve el recuadro con las iniciales y la foto aparece en cuanto llega, sin que la página salte.

## 2.17.0 — 2026-09-30

Scroll, fichas y vista mes en móviles reales (las pruebas anteriores no reproducían bien el uso real: bajaban la lista con pausas y sobre cachés ya calientes):

- **Fotos por orden de llegada a la pantalla.** Antes, en una semana con 200 conciertos, el navegador pedía decenas de fotos a la vez y competían entre sí por la red: las que tenías delante esperaban a las de más abajo. Ahora entran en una cola cuando están cerca de la pantalla y se piden de 4 en 4, siempre primero las que estás viendo.
- **Los días de la lista se pintan cuando te acercas a ellos**, no todos de golpe justo cuando empiezas a bajar (eso trababa el scroll).
- **La ficha se abre al instante** con lo que ya se sabe (artista, fecha, sala, estilo, foto pequeña); las fuentes, el precio y los enlaces se rellenan al llegar ("Cargando…"). La foto pequeña se ve nítida enseguida y la grande la sustituye cuando se ha descargado.
- **Vista mes**: al tocar un día, la pantalla baja hasta su lista y la resalta, para que se vea que ha cambiado.
- **Rendimiento medido en tu propio móvil** (Informe → "Rendimiento en este móvil"): cuánto tarda cada miniatura desde que aparece, cada ficha, cada lista y los bloqueos. No se envía a ningún sitio; con "Copiar estos datos" se pueden pasar para analizarlos.
- Prueba en vivo más dura: CPU 6 veces más lenta y scroll seguido, sin pausas.

## 2.16.0 — 2026-09-30

**Origen de los artistas: muchos menos "sin confirmar"** (antes, 1.925 de 2.643):

- **Nombre limpio para buscar la ficha.** Si la agenda mezcla el artista con el ciclo, el festival, la gira o un aviso ("Fiestas de Boadilla del Monte 2026. Siloé", "Inverfest. Sho-Hai", "Kiko Veneno - Gira 2026", "ACCEPT 50º ANIVERSARIO", "THE SILENCERS (UK) en Madrid - CAMBIA A NAZCA"), la ficha se busca también con el nombre limpio. Con varios artistas ("LA BANDA EN OBRAS & MC CLAN"), también con el cabeza de cartel. Así salen estilo, foto y origen. Hay 285 nombres nuevos que las pasadas de fichas irán completando.
  - Las bandas tributo y los espectáculos ("Queen vs. ABBA. Candlelight", "LA VAN GOGH (TRIB. LA OREJA DE VAN GOGH)") solo se buscan por su título, nunca con la ficha del homenajeado.
- **El país que pone la propia agenda en el título**: "(UK)", "(USA)", "(ITALIA)", "(FR)"…
- **Más países reconocidos** en el lugar de origen de Wikipedia y en los perfiles de Discogs: "U.S", estados de EE. UU. ("Franklin, Tennessee"), China, Bolivia, Filipinas, Malí, Túnez, Kazajistán…
- **Etiquetas de país de Last.fm** ("spanish", "british"…), solo si Last.fm identificó al artista por su identificador de MusicBrainz y todas coinciden.
- **Teatro, musicales y danza: "No aplica"** en lugar de "Origen sin confirmar" (no son artistas), y ya no salen al filtrar por "Origen sin confirmar".

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
