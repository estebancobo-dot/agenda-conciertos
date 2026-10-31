# Validación de la web publicada — 2026-10-31 20:46 UTC

https://estebancobo-dot.github.io/agenda-conciertos/ · código de main 2.55.0 · móvil con 4G lenta y CPU 6x

**163 bien · 2 avisos · 0 fallos**

## Publicación

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Conciertos sin clasificar | 6.1 | aviso > 5 % / fallo > 15 % | 189 de 3103 |
| ✅ | index.html publicado = el de main | — |  |  |
| ✅ | sw.js publicado = el de main | — |  |  |
| ✅ | Datos de la agenda recientes | 4.3 | aviso > 26 h / fallo > 50 h |  |
| ✅ | Conciertos próximos publicados | 3103 |  | mínimo 500 |
| ✅ | Ids únicos | 0 |  |  |
| ✅ | Cada concierto con id, fecha y artista | 0 |  |  |
| ✅ | Conciertos sin sala ni municipio | 0 |  |  |
| ✅ | Conciertos sin sala (la agenda no la dice) | 9 |  | Concierto apertura del 26º Cer (Las Rozas de Madrid), MÚSICA ANTIGUA ARANJUEZ. HIPPO (Aranjuez), Concierto clausura del 26º Cer (Las Rozas de Madrid), Lunares Flamencos en Libertad (Madrid) |
| ✅ | Imágenes solo por https | 0 |  |  |
| ✅ | Fichero de detalle de cada día | 0 |  |  |
| ✅ | El detalle trae todos los conciertos del día | 0 |  |  |
| ✅ | Detalle y agenda coinciden | 0 |  |  |
| ✅ | Miniaturas y fotos propias servidas | 0 |  |  |
| ✅ | Conciertos próximos sin origen del artista (ni confirmado ni estimado) | 14.7 | aviso > 30 % / fallo > 50 % | 457 de 3103; además 550 deducidos (nombre, grupo local, tributo…) |
| ✅ | Conciertos en 'Otros' (sin género propio) | 0.4 | aviso > 3 % / fallo > 10 % | 13 de 3103 |
| ✅ | Conciertos con etiqueta genérica ("Pop / Rock", "Músicas negras") | 5.8 | aviso > 8 % / fallo > 25 % | 180 de 3103 |
| ✅ | Conciertos sin ningún estilo | 21.2 | aviso > 30 % / fallo > 60 % | 658 de 3103 |
| ✅ | Última lectura completa de las agendas | 4.3 | aviso > 27 h / fallo > 50 h |  |
| ✅ | Fuentes sin alertas | 0 |  |  |

## Funcional

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | La cabecera dice cuántos conciertos hay y cuándo se actualizó | 3103 conciertos · actualizado 31 oct, 17:26 |  |  |
| ✅ | Semana: salen justo los conciertos de los datos (con los filtros puestos) | 220 de 220 |  | faltan [] sobran [] días sin pintar 0 |
| ✅ | Semana: todos de esa semana y en orden de fecha | 0 |  |  |
| ✅ | Ficha: artista y sala de los datos | MARTIN GARCIA CANCIÓN |  | esperado 'MARTIN GARCIA CANCIÓN' en 'Café Libertad 8' |
| ✅ | Ficha: enlaza a sus fuentes | 1 de 1 |  |  |
| ✅ | Filtro de un solo grupo (pop e indie): solo salen de ese grupo | 77 tarjetas |  | 0 de otros grupos |
| ✅ | 'Borrar filtros' deja la agenda sin filtros | — |  |  |
| ✅ | Subgéneros: buscando y marcando dos estilos de géneros distintos salen justo sus conciertos | ['AOR', 'Jangle Pop']: 4 de 4 |  | {'n': 4, 'malos': 0, 'esperados': 4} |
| ✅ | Subgénero «(general)»: salen los del género sin estilo concreto, y solo esos | Rock y metal (general): 269 |  | {'n': 269, 'malos': 0} |
| ✅ | Tributos: su estilo como subgénero (todos tienen uno) | 214 tributos, 44 de rock |  | {'n': 214, 'sin': 0, 'rock': 44, 'ej': []} |
| ✅ | Buscar un artista lo encuentra | Hallowfest 2026 |  |  |
| ✅ | Buscar encuentra también conciertos de géneros ocultos por el filtro | Cuban Brunch: 3ª Temporada con Atempo |  |  |
| ✅ | Filtros de origen: España, Latinoamérica, internacional y sin confirmar cuadran | 3103 de 3103 |  | {'total': 3103, 'es': 1244, 'lat': 123, 'ext': 429, 'nc': 457, 'na': 850, 'otra': 0} |
| ✅ | Mes: la lista del día son los conciertos de ese día | 4 de 4 |  |  |
| ✅ | Ficha: el enlace de compra de la página de entradas es el botón principal | Comprar entradas en DICE ↗ |  | {'ok': True, 'texto': 'Comprar entradas en DICE ↗', 'agotado': False, 'aviso': False} |
| ✅ | A media lista, el menú ☰ se abre a la vista | — |  |  |
| ✅ | A media lista, Filtros abre la hoja sin mover la lista | — |  |  |
| ✅ | A media lista, la lupa abre la búsqueda en la cabecera lista para escribir, sin mover la lista | — |  |  |
| ✅ | Buscar desde media lista y cancelar: vuelve a la misma tarjeta | 50 resultados |  |  |
| ✅ | Festivales: insignia y cartel en la ficha | 'FESTIVAL Hallowfest 2026': 24 de 24 |  |  |
| ✅ | Teloneros: el concierto sale al filtrar por el género del telonero (y la tarjeta lo dice) | rock y metal el 2026-10-31 |  | {'sale': True, 'tag': True} |
| ✅ | Salas: lista, búsqueda, página de la sala con su programación y Volver | 233 salas · Sala El Sol: 121 conciertos · volver a #salas |  | {'nombre': 'Sala El Sol', 'cards': 121, 'esperadas': 121, 'ics': 'calendario/sala-sala-el-sol.ics', 'lateral': 0, 'filtro': ['La Riviera']} |
| ✅ | Calendario de la sala: suscripción (webcal, Google, Outlook) y .ics válido con sus conciertos | 131 eventos en calendario/sala-sala-el-sol.ics |  | ['webcal://estebancobo-dot.github.io/agenda-conciertos/calendario/sala-sala-el-sol.ics', 'https://calendar.google.com/calendar/render?cid=webcal%3A%2F%2Festebancobo-dot.github.io%2Fagenda-conciertos%2 |
| ✅ | Calendarios por género: uno por género y se descargan | 20 géneros · 700 eventos en calendario/genero-rock-y-metal.i |  | {'n': 20, 'ics': 'calendario/genero-rock-y-metal.ics', 'ok': True, 'ev': 700} |
| ✅ | Historial de cambios en la ficha (y aviso en la tarjeta) | 163 conciertos con cambios · 24 octFecha: mar, 24 nov → sáb, |  | ['24 octFecha: mar, 24 nov → sáb, 24 oct', '3 octAparece en la agenda'] |
| ✅ | Fin de semana: viernes a domingo de la semana (también al cambiar de año), lo que dicen los datos | 2 de 2 bien |  |  |
| ✅ | Todos: todos los conciertos desde hoy en orden, con su total, pintado progresivo y saltos por meses | 1482 de 3103 conciertos desde hoy · 51 pintados al abrir · 1 |  | {'pintadas': 51, 'orden': True, 'desdeHoy': True, 'n': 1482, 'cab': '1482 de 3103 conciertos desde hoy', 'meses': 7, 'lateral': 0, 'salto': {'mes': '2026-11', 'dia': '2026-11-01', 'marcado': True}} |
| ✅ | Confirmación: nivel y motivos en la ficha; filtro 'Solo confirmados' | 1059 confirmados · 1591 probables · 453 sin confirmar · fich |  | {'con': 3103, 'n': 100, 'c': 1059, 'p': 1591, 's': 453, 'bien': True} |
| ✅ | Estado de estilo y origen en la ficha (sin etiqueta si es un dato conocido) y recuento en Fuentes (N3/N4) | ficha: datos conocidos · ['Estilo', 'Dato conocido: 2205'] |  | Datos de cada concierto
Estilo
Dato conocido: 2205
Estimado: 300
No aplica: 461
No encontrado: 203
Origen
Dato conocido: 1202
Estimado: 622
No aplica: 856
No encontrado: 489
Hora
Dato conocido: 2648
E |
| ✅ | Conflicto de fecha en la tarjeta y la ficha | 2 fechas |  | ⚠ Las webs no coinciden
Fecha
miércoles, 4 de noviembre
6 webs: Fun House, conciertos.club, Total Stage, Madrid en Vivo
lunes, 2 de noviembre
1 web: Fun House
Fun House anuncia una nueva fecha; otras  |
| ✅ | Nivel del concierto: «gran formato» en la tarjeta y nivel con su porqué en la ficha | 155 de gran formato · 'Live Las Ventas: gran recinto' |  |  |
| ✅ | Fase B: guardar en Mis conciertos (★), Novedades y artistas similares | guardado y en la lista: True · ★: 1 · 35 conciertos nuevos · |  |  |
| ✅ | Informe se abre | — |  |  |
| ✅ | Paso de días, semanas, meses y años (con cambios de hora y febrero) con las flechas | 103 de 103 pasos bien |  |  |
| ✅ | Enlace directo a una ficha la abre | POLAROIDS |  |  |
| ✅ | Peor caso semana del 02/11 (411 conciertos): con 'Todos' salen todos | 411 de 411 |  |  |

## UX

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Ficha: no se queda en 'Cargando…' | — |  |  |
| ✅ | Volver (atrás del navegador) deja la lista en el concierto que abriste | — |  |  |
| ✅ | Volver (botón ‹ Volver) deja la lista en el concierto que abriste | — |  |  |
| ✅ | Ficha con una sola foto (sin miniatura provisional encima) | 1 |  |  |
| ✅ | Filtros: al elegir géneros a mano no queda marcado ningún preajuste y el título dice 'a tu medida' | [] · '1 de 21 · a tu medida' |  |  |
| ✅ | Filtros: el preajuste por defecto ('Rock, pop y afines') queda marcado al elegirlo | ['def'] |  |  |
| ✅ | Filtros: la hoja es corta (géneros en chips; estilos en su propio panel) | 1978 | aviso > 2000 px / fallo > 3000 px |  |
| ✅ | Con filtros, la fila de chips tiene '✕ Quitar filtros' y deja la agenda sin filtros | — |  |  |
| ✅ | Chips de género: sin filtro solo el preajuste está marcado; al tocar uno se filtra por él y solo él sale relleno; al quitarlo se vuelve al preajuste | ['pre'] → ['rock y metal'] → ['pre'] |  |  |
| ✅ | Por defecto se dice cuántos conciertos de otros géneros quedan ocultos, con un botón para verlos | 1621 conciertos más de otros géneros (jazz, flamenco, soul,  |  |  |
| ✅ | Búsqueda sin resultados lo dice | — |  |  |
| ✅ | La barra dice que se está buscando | Filtrando: búsqueda «Leiva» · Quitar filtros · Compartir |  |  |
| ✅ | La búsqueda se ve dentro de la hoja de filtros | — |  |  |
| ✅ | 'Todos' (grupos) no borra la búsqueda a escondidas | — |  |  |
| ✅ | 'Borrar filtros' en la hoja quita también la búsqueda | — |  |  |
| ✅ | El cuadro de búsqueda queda vacío al borrar | — |  |  |
| ✅ | Mes: al tocar un día, su lista queda a la vista | — |  |  |
| ✅ | Semana: al bajar, la fecha completa del día se queda fija arriba | Viernes, 30 de octubre45 conciertos |  | {'pegada': True, 'fecha': '2026-10-30', 'texto': 'Viernes, 30 de octubre45 conciertos', 'marcado': '2026-10-30', 'alto': 170} |
| ✅ | Semana: la tira de días marca el día por el que vas | 2026-10-30 / 2026-10-30 |  |  |
| ✅ | Semana: lo fijo arriba (cabecera, tira y fecha) no ocupa más de un tercio de la pantalla | 210 | aviso > 281 px / fallo > 422 px |  |
| ✅ | Semana: tocar un día de la tira lleva justo a ese día | 2026-11-01 (pedido 2026-11-01) |  | {'pegada': True, 'fecha': '2026-11-01', 'texto': 'Mañana, domingo, 1 de noviembre36 conciertos', 'marcado': '2026-11-01', 'alto': 170} |
| ✅ | Día: al bajar, la fecha completa se queda fija arriba con la tira de días | Hoy, sábado, 31 de octubre51 conciertos |  | {'pegada': True, 'fecha': '2026-10-31', 'texto': 'Hoy, sábado, 31 de octubre51 conciertos', 'marcado': '2026-10-31', 'alto': 170} |
| ✅ | Mes: al bajar por la lista del día, su fecha completa se queda fija arriba | Hoy, sábado, 31 de octubre51 conciertos |  | {'pegada': True, 'fecha': '2026-10-31', 'texto': 'Hoy, sábado, 31 de octubre51 conciertos', 'marcado': None, 'alto': 109} |
| ✅ | Al bajar por la lista, Buscar y Filtros siguen a mano en la cabecera (y arriba no se duplican) | — |  |  |
| ✅ | A media lista, ‹ semana › en la cabecera: pasa a la siguiente y deja su primer día a la vista | 2026-11-02 · '2–8 nov\n209 conciertos' |  | {'fecha': '2026-11-02', 'fija': True, 'titulo': '2–8 nov\n209 conciertos', 'cabecera': True} |
| ✅ | Cambiar de día, semana o mes desde media lista deja la vista nueva desde su principio; Hoy siempre a mano | 10 de 10 casos bien |  |  |
| ✅ | Fuentes: una tarjeta por web con estado, 14 días y datos; filtros y búsqueda; sin scroll lateral | 82 de 82 webs · 32 salas · 63 salas sin web leída |  | {'n': 32, 'total': 82, 'tiras': 82, 'metricas': 82, 'lateral': 0, 'salas': 63, 'bien': True, 'esperadas': 32, 'busca': True} |
| ✅ | Saltos de diseño (CLS) | 0 | aviso > 0.1  / fallo > 0.25  |  |
| ✅ | Semana sin conciertos: lo dice | — |  |  |
| ✅ | Peor caso semana del 02/11 (411 conciertos): volver deja la lista en el concierto | — |  |  |
| ✅ | Sin scroll lateral (móvil pequeño 320 px) | 0 |  | 0 px de más |
| ✅ | Botones con tamaño de dedo (≥ 32 px) | 0 |  |  |
| ✅ | Contraste de color suficiente (modo claro) | 0 |  |  |
| ✅ | Accesibilidad (axe-core): otros problemas graves (modo claro) | 0 |  |  |
| ✅ | Sin scroll lateral (ordenador 1366 px) | 0 |  | 0 px de más |
| ✅ | Sin scroll lateral (móvil en modo oscuro) | 0 |  | 0 px de más |
| ✅ | Modo oscuro: fondo oscuro | 22 |  |  |
| ✅ | Contraste de color suficiente (modo oscuro) | 0 |  |  |
| ✅ | Accesibilidad (axe-core): otros problemas graves (modo oscuro) | 0 |  |  |
| ✅ | Modos de vista: lista, compacta y cuadrícula; la compacta enseña más conciertos; se recuerda al volver | lista: 3 · compacta: 5 · cuadricula: 2 en pantalla · guardad |  | {'lista': {'bien': True, 'enPantalla': 3}, 'compacta': {'bien': True, 'enPantalla': 5}, 'cuadricula': {'bien': True, 'enPantalla': 2}} |
| ✅ | Ordenador: la ficha se abre al lado de la lista (la lista sigue a la vista) y Escape la cierra | al lado · cerrada |  | {'hash': '#semana/2026-10-26', 'lado': True, 'marcado': True, 'lateral': 0} |

## Rendimiento

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Filtros: abrir la hoja | 333 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Conciertos con miniatura propia (servida desde la web) | 100.0 |  | de 2450 con imagen; mínimo 97 % |
| ✅ | Conciertos con foto de ficha propia (servida desde la web) | 100.0 |  | de 2450 con imagen; mínimo 97 % |
| ✅ | Primera visita: datos y lista pintados | 3863 | aviso > 5000 ms / fallo > 8000 ms |  |
| ✅ | Primera visita: LCP | 3944 | aviso > 4000 ms / fallo > 6000 ms |  |
| ✅ | Primera visita: KB descargados | 501 | aviso > 1500 KB / fallo > 3000 KB |  |
| ✅ | Bajar despacio: miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas |  |
| ✅ | Bajar deprisa: al parar, miniaturas visibles cargadas en | 64 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Cambiar de semana (mediana de 3) | 251 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Abrir ficha desde la lista (datos) | 136 | aviso > 500 ms / fallo > 1500 ms |  |
| ✅ | Ficha completa (fuentes y precio) | 142 | aviso > 1500 ms / fallo > 4000 ms |  |
| ✅ | Foto de la ficha tras ver la lista 2 s (mediana) | 169 | aviso > 600 ms / fallo > 1500 ms |  |
| ✅ | Fichas cuya foto ya estaba descargada al abrir | 5 |  | 5 de 5 |
| ✅ | Ficha lejana (discogs): datos | 188 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (discogs): foto | 194 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (otros): datos | 46 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (otros): foto | 58 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (wikimedia): datos | 189 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (wikimedia): foto | 205 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (sin foto): datos | 116 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (conciertos.club): datos | 62 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (conciertos.club): foto | 93 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (madridenvivo): datos | 122 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (madridenvivo): foto | 161 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Filtros: 'Ninguno' | 107 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: aplicar | 187 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: borrar filtros | 226 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: 'Los de siempre' | 104 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: chip de grupo | 211 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Vista mes | 186 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Todos: pintar la lista | 182 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Segunda visita: lista pintada | 1201 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Segunda visita: miniaturas visibles cargadas | 96 | aviso > 800 ms / fallo > 2500 ms |  |
| ✅ | Bloqueo de JavaScript más largo (CPU 6x) | 262 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Imágenes que no cargan | 0.0 | aviso > 1 % / fallo > 5 % |  |
| ✅ | Enlace directo a una ficha (visita nueva) | 4067 | aviso > 5000 ms / fallo > 9000 ms |  |
| ✅ | Vista día sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 5 | aviso > 1000 ms / fallo > 2500 ms | [5, 5, 5] |
| ✅ | Vista mes sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 45 | aviso > 1000 ms / fallo > 2500 ms | [4, 4, 45] |
| ✅ | Ficha sin caché: foto desde que se ve la ficha (peor de 4 al azar) | 74 | aviso > 1200 ms / fallo > 2500 ms | [67, 74, 68, 74] ['estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io'] |
| ✅ | Imágenes de las listas pedidas fuera de la web (wsrv.nl, agendas) | 0 |  |  |
| ✅ | Peor caso semana del 02/11 (411 conciertos): pintar con 'Todos' | 320 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Peor caso semana del 02/11 (411 conciertos): miniaturas de la primera pantalla | 43 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 02/11 (411 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 67 pantallas; peores [0, 0, 0]; pantallas con alguna sin cargar: 0 |
| ✅ | Peor caso semana del 02/11 (411 conciertos): bloqueo de JavaScript más largo al bajar | 0 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Peor caso semana del 02/11 (411 conciertos): bajando seguido, miniaturas a la vista sin cargar | 0.0 | aviso > 5 % / fallo > 15 % | 0 de 355 vistas en 12 s |
| ✅ | Peor caso semana del 02/11 (411 conciertos): bajando deprisa, al parar miniaturas visibles cargadas en | 163 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 02/11 (411 conciertos): foto de una ficha del final de la lista | 377 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Peor caso semana del 02/11 (411 conciertos): imágenes pedidas fuera de la web | 0 |  |  |
| ✅ | Peor caso día 14/11 (105 conciertos): miniaturas de la primera pantalla | 141 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso día 14/11 (105 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 18 pantallas |
| ✅ | Peor caso mes 11/2026 (1614 conciertos), día 07/11: al tocar el día, miniaturas visibles cargadas | 90 | aviso > 1000 ms / fallo > 2500 ms | desde el toque: 987 ms |

## Fallos

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Enlace a un concierto que ya no existe: lo dice y deja volver | — |  |  |
| ✅ | Detalle que no llega: se ve la ficha básica y avisa | — |  | ‹ Volver EF Foto: (imagen del anuncio) Eclipse: Flako, Figurex, Akali No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 sábado, 31 de octu |
| ✅ | Fotos que no cargan: sin iconos de imagen rota | 0 |  |  |
| ✅ | Agenda que no llega: mensaje claro para recargar | — |  | No se pudieron cargar los datos (data/concerts.json). Comprueba la conexión y recarga la página. |
| ✅ | Agenda lenta: indica 'Cargando…' y luego se pinta | — |  |  |
| ✅ | Sin taxonomía de estilos: la agenda sigue funcionando | — |  |  |
| ✅ | Sin conexión: la agenda se abre con la copia guardada | 127 | aviso > 4500 ms / fallo > 8000 ms |  |
| ✅ | Sin conexión: se ven los conciertos | — |  |  |
| ✅ | Sin conexión: una ficha no guardada avisa en vez de quedarse cargando | — |  | ‹ Volver Foto: (imagen del anuncio) Opus Kink No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 jueves, 29 de abril 21:30 h 📍 Fun House Ma |
| ✅ | Errores de JavaScript en todo el recorrido | 0 |  |  |

## Seguridad

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | La web declara su política de seguridad del contenido | — |  |  |
| ✅ | La política no bloquea nada de la propia web | 0 |  |  |

## Otros

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Enlaces a las fuentes responden | 0 |  |  |
| ✅ | Próximos 10 días: conciertos con enlace de compra directo | 166 de 594 |  | con cartel de gira 193, con hora 499 |
| ✅ | Todo por https (sin contenido mixto) | 0 |  |  |
| ✅ | Miniaturas de las agendas a través del proxy | 0 de 0 |  |  |
| ✅ | Errores en la consola | 0 |  |  |
