# Validación de la web publicada — 2026-10-03 14:55 UTC

https://estebancobo-dot.github.io/agenda-conciertos/ · código de main 2.44.0 · móvil con 4G lenta y CPU 6x

**145 bien · 7 avisos · 0 fallos**

## Publicación

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Conciertos sin sala (la agenda no la dice) | 21 |  | CONCIERTO DE DIRECTORES DE BAN (Aranjuez), XXIII MÚSICA ANTIGUA ARANJUEZ. (Aranjuez), XXIII MÚSICA ANTIGUA ARANJUEZ. (Aranjuez), ENCUENTRO CORAL INTERNACIONAL  (Collado Villalba) |
| ⚠️ | Conciertos próximos sin origen del artista (ni confirmado ni estimado) | 37.4 | aviso > 30 % / fallo > 50 % | 1056 de 2820; además 376 estimados por el nombre |
| ⚠️ | Conciertos sin clasificar | 10.6 | aviso > 5 % / fallo > 15 % | 300 de 2820 |
| ⚠️ | Conciertos sin ningún estilo | 37.8 | aviso > 30 % / fallo > 60 % | 1066 de 2820 |
| ⚠️ | Fuentes sin alertas | 2 |  | Sala Villanos (web oficial): su robots.txt ya no permite leerla (último éxito 2026-10-01, daba 99): se respeta; sus conciertos salen de su última lectura y de otras agendas; Sala Clamores (web oficial |
| ✅ | index.html publicado = el de main | — |  |  |
| ✅ | sw.js publicado = el de main | — |  |  |
| ✅ | Datos de la agenda recientes | 0.0 | aviso > 26 h / fallo > 50 h |  |
| ✅ | Conciertos próximos publicados | 2820 |  | mínimo 500 |
| ✅ | Ids únicos | 0 |  |  |
| ✅ | Cada concierto con id, fecha y artista | 0 |  |  |
| ✅ | Conciertos sin sala ni municipio | 0 |  |  |
| ✅ | Imágenes solo por https | 0 |  |  |
| ✅ | Fichero de detalle de cada día | 0 |  |  |
| ✅ | El detalle trae todos los conciertos del día | 0 |  |  |
| ✅ | Detalle y agenda coinciden | 0 |  |  |
| ✅ | Miniaturas y fotos propias servidas | 0 |  |  |
| ✅ | Conciertos en 'Otros' (sin género propio) | 0.5 | aviso > 3 % / fallo > 10 % | 14 de 2820 |
| ✅ | Conciertos con etiqueta genérica ("Pop / Rock", "Músicas negras") | 7.9 | aviso > 8 % / fallo > 25 % | 222 de 2820 |
| ✅ | Última lectura completa de las agendas | 5.0 | aviso > 27 h / fallo > 50 h |  |

## Funcional

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Historial de cambios en la ficha | aún sin cambios registrados |  |  |
| ✅ | La cabecera dice cuántos conciertos hay y cuándo se actualizó | 2820 conciertos · actualizado 3 oct, 16:52 |  |  |
| ✅ | Semana: salen justo los conciertos de los datos (con los filtros puestos) | 235 de 235 |  | faltan [] sobran [] días sin pintar 0 |
| ✅ | Semana: todos de esa semana y en orden de fecha | 0 |  |  |
| ✅ | Ficha: artista y sala de los datos | ENAMOR AL ARTE |  | esperado 'ENAMOR AL ARTE' en 'Jazzville' |
| ✅ | Ficha: enlaza a sus fuentes | 1 de 1 |  |  |
| ✅ | Filtro de un solo grupo (pop e indie): solo salen de ese grupo | 84 tarjetas |  | 0 de otros grupos |
| ✅ | 'Borrar filtros' deja la agenda sin filtros | — |  |  |
| ✅ | Subgéneros: buscando y marcando dos estilos de géneros distintos salen justo sus conciertos | ['Beat', 'Celtic']: 4 de 4 |  | {'n': 4, 'malos': 0, 'esperados': 4} |
| ✅ | Buscar un artista lo encuentra | Manu Míguez |  |  |
| ✅ | Filtros de origen: España, Latinoamérica, resto del mundo y sin confirmar cuadran | 2820 de 2820 |  | {'total': 2820, 'esc': 443, 'es': 819, 'lat': 99, 'ext': 385, 'nc': 1056, 'est': 376, 'na': 461} |
| ✅ | Mes: la lista del día son los conciertos de ese día | 56 de 56 |  |  |
| ✅ | Ficha: el enlace de compra de la página de entradas es el botón principal | Comprar entradas en Entradium ↗ |  | {'ok': True, 'texto': 'Comprar entradas en Entradium ↗', 'agotado': False, 'aviso': True} |
| ✅ | A media lista, el menú ☰ se abre a la vista | — |  |  |
| ✅ | A media lista, Filtros abre la hoja sin mover la lista | — |  |  |
| ✅ | A media lista, la lupa abre la búsqueda en la cabecera lista para escribir, sin mover la lista | — |  |  |
| ✅ | Buscar desde media lista y cancelar: vuelve a la misma tarjeta | 30 resultados |  |  |
| ✅ | Festivales: insignia y cartel en la ficha | 'FESTIVAL Pirata Madrid Festival': 7 de 7 |  |  |
| ✅ | Teloneros: el concierto sale al filtrar por el género del telonero (y la tarjeta lo dice) | rock y metal el 2026-10-03 |  | {'sale': True, 'tag': True} |
| ✅ | Salas: lista, búsqueda, página de la sala con su programación y Volver | 245 salas · Sala Villanos: 105 conciertos · volver a #salas |  | {'nombre': 'Sala Villanos', 'cards': 105, 'esperadas': 105, 'ics': 'calendario/sala-sala-villanos.ics', 'lateral': 0, 'filtro': ['La Riviera']} |
| ✅ | Calendario de la sala: suscripción (webcal, Google, Outlook) y .ics válido con sus conciertos | 109 eventos en calendario/sala-sala-villanos.ics |  | ['webcal://estebancobo-dot.github.io/agenda-conciertos/calendario/sala-sala-villanos.ics', 'https://calendar.google.com/calendar/render?cid=webcal%3A%2F%2Festebancobo-dot.github.io%2Fagenda-conciertos |
| ✅ | Calendarios por género: uno por género y se descargan | 20 géneros · 616 eventos en calendario/genero-rock-y-metal.i |  | {'n': 20, 'ics': 'calendario/genero-rock-y-metal.ics', 'ok': True, 'ev': 616} |
| ✅ | Fin de semana: viernes a domingo de la semana (también al cambiar de año), lo que dicen los datos | 2 de 2 bien |  |  |
| ✅ | Todos: todos los conciertos desde hoy en orden, con su total, pintado progresivo y saltos por meses | 1557 conciertos desde hoy · 69 pintados al abrir · 202 ms |  | {'pintadas': 69, 'orden': True, 'desdeHoy': True, 'n': 1557, 'cab': '1557 conciertos desde hoy', 'meses': 4, 'lateral': 0, 'salto': {'mes': '2026-11', 'dia': '2026-11-01', 'marcado': True}} |
| ✅ | Informe se abre | — |  |  |
| ✅ | Paso de días, semanas, meses y años (con cambios de hora y febrero) con las flechas | 103 de 103 pasos bien |  |  |
| ✅ | Enlace directo a una ficha la abre | RADIOSPHERE |  |  |
| ✅ | Peor caso semana del 19/10 (377 conciertos): con 'Todos' salen todos | 377 de 377 |  |  |

## UX

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Ficha: no se queda en 'Cargando…' | — |  |  |
| ✅ | Volver (atrás del navegador) deja la lista en el concierto que abriste | — |  |  |
| ✅ | Volver (botón ‹ Volver) deja la lista en el concierto que abriste | — |  |  |
| ✅ | Ficha con una sola foto (sin miniatura provisional encima) | 1 |  |  |
| ✅ | Filtros: al elegir géneros a mano no queda marcado ningún preajuste y el título dice 'a tu medida' | [] · '1 de 21 · a tu medida' |  |  |
| ✅ | Filtros: 'Habituales' queda marcado al elegirlo | ['def'] |  |  |
| ✅ | Filtros: la hoja es corta (géneros en chips; estilos en su propio panel) | 1548 | aviso > 2000 px / fallo > 3000 px |  |
| ✅ | Con filtros, la fila de chips tiene '✕ Quitar filtros' y deja la agenda sin filtros | — |  |  |
| ✅ | Chips de género: sin filtro solo 'Habituales' está marcado; al tocar uno se filtra por él y solo él sale relleno; al quitarlo se vuelve a 'Habituales' | ['pre'] → ['rock y metal'] → ['pre'] |  |  |
| ✅ | Búsqueda sin resultados lo dice | — |  |  |
| ✅ | La barra dice que se está buscando | Filtrando: búsqueda «Leiva» · Quitar filtros |  |  |
| ✅ | La búsqueda se ve dentro de la hoja de filtros | — |  |  |
| ✅ | 'Todos' (grupos) no borra la búsqueda a escondidas | — |  |  |
| ✅ | 'Borrar filtros' en la hoja quita también la búsqueda | — |  |  |
| ✅ | El cuadro de búsqueda queda vacío al borrar | — |  |  |
| ✅ | Mes: al tocar un día, su lista queda a la vista | — |  |  |
| ✅ | Semana: al bajar, la fecha completa del día se queda fija arriba | Viernes, 2 de octubre72 conciertos |  | {'pegada': True, 'fecha': '2026-10-02', 'texto': 'Viernes, 2 de octubre72 conciertos', 'marcado': '2026-10-02', 'alto': 161} |
| ✅ | Semana: la tira de días marca el día por el que vas | 2026-10-02 / 2026-10-02 |  |  |
| ✅ | Semana: lo fijo arriba (cabecera, tira y fecha) no ocupa más de un tercio de la pantalla | 201 | aviso > 281 px / fallo > 422 px |  |
| ✅ | Semana: tocar un día de la tira lleva justo a ese día | 2026-10-04 (pedido 2026-10-04) |  | {'pegada': True, 'fecha': '2026-10-04', 'texto': 'Mañana, domingo, 4 de octubre26 conciertos', 'marcado': '2026-10-04', 'alto': 161} |
| ✅ | Día: al bajar, la fecha completa se queda fija arriba con la tira de días | Viernes, 2 de octubre72 conciertos |  | {'pegada': True, 'fecha': '2026-10-02', 'texto': 'Viernes, 2 de octubre72 conciertos', 'marcado': '2026-10-02', 'alto': 161} |
| ✅ | Mes: al bajar por la lista del día, su fecha completa se queda fija arriba | Viernes, 2 de octubre72 conciertos |  | {'pegada': True, 'fecha': '2026-10-02', 'texto': 'Viernes, 2 de octubre72 conciertos', 'marcado': None, 'alto': 100} |
| ✅ | Al bajar por la lista, Buscar y Filtros siguen a mano en la cabecera (y arriba no se duplican) | — |  |  |
| ✅ | A media lista, ‹ semana › en la cabecera: pasa a la siguiente y deja su primer día a la vista | 2026-10-05 · '5–11 oct\n225 conciertos' |  | {'fecha': '2026-10-05', 'fija': True, 'titulo': '5–11 oct\n225 conciertos', 'cabecera': True} |
| ✅ | Cambiar de día, semana o mes desde media lista deja la vista nueva desde su principio; Hoy siempre a mano | 10 de 10 casos bien |  |  |
| ✅ | Fuentes: una tarjeta por web con estado, 14 días y datos; filtros y búsqueda; sin scroll lateral | 71 de 71 webs · 27 salas · 72 salas sin web leída |  | {'n': 27, 'total': 71, 'tiras': 71, 'metricas': 71, 'lateral': 0, 'salas': 72, 'bien': True, 'esperadas': 27, 'busca': True} |
| ✅ | Saltos de diseño (CLS) | 0 | aviso > 0.1  / fallo > 0.25  |  |
| ✅ | Semana sin conciertos: lo dice | — |  |  |
| ✅ | Peor caso semana del 19/10 (377 conciertos): volver deja la lista en el concierto | — |  |  |
| ✅ | Sin scroll lateral (móvil pequeño 320 px) | 0 |  | 0 px de más |
| ✅ | Botones con tamaño de dedo (≥ 32 px) | 0 |  |  |
| ✅ | Contraste de color suficiente (modo claro) | 0 |  |  |
| ✅ | Accesibilidad (axe-core): otros problemas graves (modo claro) | 0 |  |  |
| ✅ | Sin scroll lateral (ordenador 1366 px) | 0 |  | 0 px de más |
| ✅ | Sin scroll lateral (móvil en modo oscuro) | 0 |  | 0 px de más |
| ✅ | Modo oscuro: fondo oscuro | 22 |  |  |
| ✅ | Contraste de color suficiente (modo oscuro) | 0 |  |  |
| ✅ | Accesibilidad (axe-core): otros problemas graves (modo oscuro) | 0 |  |  |

## Rendimiento

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Filtros: abrir la hoja | 313 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Conciertos con miniatura propia (servida desde la web) | 100.0 |  | de 2099 con imagen; mínimo 97 % |
| ✅ | Conciertos con foto de ficha propia (servida desde la web) | 100.0 |  | de 2099 con imagen; mínimo 97 % |
| ✅ | Primera visita: datos y lista pintados | 2412 | aviso > 5000 ms / fallo > 8000 ms |  |
| ✅ | Primera visita: LCP | 2492 | aviso > 4000 ms / fallo > 6000 ms |  |
| ✅ | Primera visita: KB descargados | 264 | aviso > 1500 KB / fallo > 3000 KB |  |
| ✅ | Bajar despacio: miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas |  |
| ✅ | Bajar deprisa: al parar, miniaturas visibles cargadas en | 72 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Cambiar de semana (mediana de 3) | 260 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Abrir ficha desde la lista (datos) | 134 | aviso > 500 ms / fallo > 1500 ms |  |
| ✅ | Ficha completa (fuentes y precio) | 140 | aviso > 1500 ms / fallo > 4000 ms |  |
| ✅ | Foto de la ficha tras ver la lista 2 s (mediana) | 135 | aviso > 600 ms / fallo > 1500 ms |  |
| ✅ | Fichas cuya foto ya estaba descargada al abrir | 5 |  | 5 de 5 |
| ✅ | Ficha lejana (sin foto): datos | 87 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (discogs): datos | 46 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (discogs): foto | 57 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (conciertos.club): datos | 46 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (conciertos.club): foto | 69 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (otros): datos | 91 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (otros): foto | 96 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (wikimedia): datos | 45 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (wikimedia): foto | 54 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (madridenvivo): datos | 78 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (madridenvivo): foto | 83 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Filtros: 'Ninguno' | 122 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: aplicar | 201 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: borrar filtros | 205 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: 'Los de siempre' | 80 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: chip de grupo | 178 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Vista mes | 197 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Todos: pintar la lista | 202 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Segunda visita: lista pintada | 945 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Segunda visita: miniaturas visibles cargadas | 119 | aviso > 800 ms / fallo > 2500 ms |  |
| ✅ | Bloqueo de JavaScript más largo (CPU 6x) | 171 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Imágenes que no cargan | 0.0 | aviso > 1 % / fallo > 5 % |  |
| ✅ | Enlace directo a una ficha (visita nueva) | 2358 | aviso > 5000 ms / fallo > 9000 ms |  |
| ✅ | Vista día sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 9 | aviso > 1000 ms / fallo > 2500 ms | [9, 4, 3] |
| ✅ | Vista mes sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 43 | aviso > 1000 ms / fallo > 2500 ms | [43, 5, 13] |
| ✅ | Ficha sin caché: foto desde que se ve la ficha (peor de 4 al azar) | 85 | aviso > 1200 ms / fallo > 2500 ms | [65, 85, 72, 69] ['estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io'] |
| ✅ | Imágenes de las listas pedidas fuera de la web (wsrv.nl, agendas) | 0 |  |  |
| ✅ | Peor caso semana del 19/10 (377 conciertos): pintar con 'Todos' | 267 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Peor caso semana del 19/10 (377 conciertos): miniaturas de la primera pantalla | 24 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 19/10 (377 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 59 pantallas; peores [0, 0, 0]; pantallas con alguna sin cargar: 0 |
| ✅ | Peor caso semana del 19/10 (377 conciertos): bloqueo de JavaScript más largo al bajar | 0 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Peor caso semana del 19/10 (377 conciertos): bajando seguido, miniaturas a la vista sin cargar | 0.0 | aviso > 5 % / fallo > 15 % | 0 de 322 vistas en 12 s |
| ✅ | Peor caso semana del 19/10 (377 conciertos): bajando deprisa, al parar miniaturas visibles cargadas en | 156 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 19/10 (377 conciertos): foto de una ficha del final de la lista | 269 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Peor caso semana del 19/10 (377 conciertos): imágenes pedidas fuera de la web | 0 |  |  |
| ✅ | Peor caso día 03/10 (102 conciertos): miniaturas de la primera pantalla | 109 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso día 03/10 (102 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 17 pantallas |
| ✅ | Peor caso mes 10/2026 (1564 conciertos), día 17/10: al tocar el día, miniaturas visibles cargadas | 77 | aviso > 1000 ms / fallo > 2500 ms | desde el toque: 983 ms |

## Fallos

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Enlace a un concierto que ya no existe: lo dice y deja volver | — |  |  |
| ✅ | Detalle que no llega: se ve la ficha básica y avisa | — |  | ‹ Volver PD EL PEQUEÑO DE LOS DALTON No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 sábado, 3 de octubre 00:30 h 📍 Honky Tonk Madrid ·  |
| ✅ | Fotos que no cargan: sin iconos de imagen rota | 0 |  |  |
| ✅ | Agenda que no llega: mensaje claro para recargar | — |  | No se pudieron cargar los datos (data/concerts.json). Comprueba la conexión y recarga la página. |
| ✅ | Agenda lenta: indica 'Cargando…' y luego se pinta | — |  |  |
| ✅ | Sin taxonomía de estilos: la agenda sigue funcionando | — |  |  |
| ✅ | Sin conexión: la agenda se abre con la copia guardada | 100 | aviso > 4500 ms / fallo > 8000 ms |  |
| ✅ | Sin conexión: se ven los conciertos | — |  |  |
| ✅ | Sin conexión: una ficha no guardada avisa en vez de quedarse cargando | — |  | ‹ Volver E EPICA No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 domingo, 31 de enero Hora sin indicar 📍 La Riviera Madrid · Cómo llegar |
| ✅ | Errores de JavaScript en todo el recorrido | 0 |  |  |

## Otros

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Enlaces a las fuentes responden | 1 |  | https://madridenvivo.com/evento/thundercat-conciertos-16/ (404) |
| ✅ | Próximos 10 días: conciertos con enlace de compra directo | 82 de 555 |  | con cartel de gira 69, con hora 341 |
| ✅ | Todo por https (sin contenido mixto) | 0 |  |  |
| ✅ | Miniaturas de las agendas a través del proxy | 0 de 0 |  |  |
| ✅ | Errores en la consola | 0 |  |  |
