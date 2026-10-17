# Validación de la web publicada — 2026-10-17 20:04 UTC

https://estebancobo-dot.github.io/agenda-conciertos/ · código de main 2.55.0 · móvil con 4G lenta y CPU 6x

**164 bien · 1 avisos · 0 fallos**

## Publicación

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Conciertos sin clasificar | 8.2 | aviso > 5 % / fallo > 15 % | 232 de 2840 |
| ✅ | index.html publicado = el de main | — |  |  |
| ✅ | sw.js publicado = el de main | — |  |  |
| ✅ | Datos de la agenda recientes | 0.1 | aviso > 26 h / fallo > 50 h |  |
| ✅ | Conciertos próximos publicados | 2840 |  | mínimo 500 |
| ✅ | Ids únicos | 0 |  |  |
| ✅ | Cada concierto con id, fecha y artista | 0 |  |  |
| ✅ | Conciertos sin sala ni municipio | 0 |  |  |
| ✅ | Conciertos sin sala (la agenda no la dice) | 18 |  | ENCUENTRO CORAL INTERNACIONAL  (Collado Villalba), XXIII MÚSICA ANTIGUA ARANJUEZ. (Aranjuez), FAHMI ALQHI (Aranjuez), Concierto Fiesta Nacional (Las Rozas de Madrid) |
| ✅ | Imágenes solo por https | 0 |  |  |
| ✅ | Fichero de detalle de cada día | 0 |  |  |
| ✅ | El detalle trae todos los conciertos del día | 0 |  |  |
| ✅ | Detalle y agenda coinciden | 0 |  |  |
| ✅ | Miniaturas y fotos propias servidas | 0 |  |  |
| ✅ | Conciertos próximos sin origen del artista (ni confirmado ni estimado) | 15.6 | aviso > 30 % / fallo > 50 % | 443 de 2840; además 408 deducidos (nombre, grupo local, tributo…) |
| ✅ | Conciertos en 'Otros' (sin género propio) | 0.2 | aviso > 3 % / fallo > 10 % | 7 de 2840 |
| ✅ | Conciertos con etiqueta genérica ("Pop / Rock", "Músicas negras") | 5.4 | aviso > 8 % / fallo > 25 % | 153 de 2840 |
| ✅ | Conciertos sin ningún estilo | 22.2 | aviso > 30 % / fallo > 60 % | 631 de 2840 |
| ✅ | Última lectura completa de las agendas | 4.0 | aviso > 27 h / fallo > 50 h |  |
| ✅ | Fuentes sin alertas | 0 |  |  |

## Funcional

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | La cabecera dice cuántos conciertos hay y cuándo se actualizó | 2840 conciertos · actualizado 17 oct, 22:01 |  |  |
| ✅ | Semana: salen justo los conciertos de los datos (con los filtros puestos) | 232 de 232 |  | faltan [] sobran [] días sin pintar 0 |
| ✅ | Semana: todos de esa semana y en orden de fecha | 0 |  |  |
| ✅ | Ficha: artista y sala de los datos | JESSVARAL Y FRAN.TV |  | esperado 'JESSVARAL Y FRAN.TV' en 'Jazzville' |
| ✅ | Ficha: enlaza a sus fuentes | 1 de 1 |  |  |
| ✅ | Filtro de un solo grupo (pop e indie): solo salen de ese grupo | 78 tarjetas |  | 0 de otros grupos |
| ✅ | 'Borrar filtros' deja la agenda sin filtros | — |  |  |
| ✅ | Subgéneros: buscando y marcando dos estilos de géneros distintos salen justo sus conciertos | ['Jangle Pop', 'Electric Blues']: 7 de 7 |  | {'n': 7, 'malos': 0, 'esperados': 7} |
| ✅ | Subgénero «(general)»: salen los del género sin estilo concreto, y solo esos | Rock y metal (general): 261 |  | {'n': 261, 'malos': 0} |
| ✅ | Tributos: su estilo como subgénero (todos tienen uno) | 181 tributos, 37 de rock |  | {'n': 181, 'sin': 0, 'rock': 37, 'ej': []} |
| ✅ | Buscar un artista lo encuentra | LA MERIENDA con BLUE POISON |  |  |
| ✅ | Buscar encuentra también conciertos de géneros ocultos por el filtro | METROPOP |  |  |
| ✅ | Filtros de origen: España, Latinoamérica, internacional y sin confirmar cuadran | 2840 de 2840 |  | {'total': 2840, 'es': 1107, 'lat': 112, 'ext': 460, 'nc': 443, 'na': 718, 'otra': 0} |
| ✅ | Mes: la lista del día son los conciertos de ese día | 54 de 54 |  |  |
| ✅ | Ficha: el enlace de compra de la página de entradas es el botón principal | Comprar entradas en Giglon ↗ |  | {'ok': True, 'texto': 'Comprar entradas en Giglon ↗', 'agotado': False, 'aviso': True} |
| ✅ | A media lista, el menú ☰ se abre a la vista | — |  |  |
| ✅ | A media lista, Filtros abre la hoja sin mover la lista | — |  |  |
| ✅ | A media lista, la lupa abre la búsqueda en la cabecera lista para escribir, sin mover la lista | — |  |  |
| ✅ | Buscar desde media lista y cancelar: vuelve a la misma tarjeta | 41 resultados |  |  |
| ✅ | Festivales: insignia y cartel en la ficha | 'FESTIVAL Cadena 100 Por Ellas 2026': 10 de 10 |  |  |
| ✅ | Teloneros: el concierto sale al filtrar por el género del telonero (y la tarjeta lo dice) | punk y garage el 2026-10-17 |  | {'sale': True, 'tag': True} |
| ✅ | Salas: lista, búsqueda, página de la sala con su programación y Volver | 231 salas · Sala El Sol: 123 conciertos · volver a #salas |  | {'nombre': 'Sala El Sol', 'cards': 123, 'esperadas': 123, 'ics': 'calendario/sala-sala-el-sol.ics', 'lateral': 0, 'filtro': ['La Riviera']} |
| ✅ | Calendario de la sala: suscripción (webcal, Google, Outlook) y .ics válido con sus conciertos | 135 eventos en calendario/sala-sala-el-sol.ics |  | ['webcal://estebancobo-dot.github.io/agenda-conciertos/calendario/sala-sala-el-sol.ics', 'https://calendar.google.com/calendar/render?cid=webcal%3A%2F%2Festebancobo-dot.github.io%2Fagenda-conciertos%2 |
| ✅ | Calendarios por género: uno por género y se descargan | 20 géneros · 679 eventos en calendario/genero-rock-y-metal.i |  | {'n': 20, 'ics': 'calendario/genero-rock-y-metal.ics', 'ok': True, 'ev': 679} |
| ✅ | Historial de cambios en la ficha (y aviso en la tarjeta) | 113 conciertos con cambios · 10 octPrecio: 16,50€ → Anticipa |  | ['10 octPrecio: 16,50€ → Anticipada: 15€ Taquilla: 18€', '29 septAparece en la agenda'] |
| ✅ | Fin de semana: viernes a domingo de la semana (también al cambiar de año), lo que dicen los datos | 2 de 2 bien |  |  |
| ✅ | Todos: todos los conciertos desde hoy en orden, con su total, pintado progresivo y saltos por meses | 1461 de 2840 conciertos desde hoy · 64 pintados al abrir · 1 |  | {'pintadas': 64, 'orden': True, 'desdeHoy': True, 'n': 1461, 'cab': '1461 de 2840 conciertos desde hoy', 'meses': 7, 'lateral': 0, 'salto': {'mes': '2026-11', 'dia': '2026-11-01', 'marcado': True}} |
| ✅ | Confirmación: nivel y motivos en la ficha; filtro 'Solo confirmados' | 1053 confirmados · 1368 probables · 419 sin confirmar · fich |  | {'con': 2840, 'n': 97, 'c': 1053, 'p': 1368, 's': 419, 'bien': True} |
| ✅ | Estado de estilo y origen en la ficha (sin etiqueta si es un dato conocido) y recuento en Fuentes (N3/N4) | ficha: ['No encontrado'] · ['Estilo', 'Dato conocido: 2075'] |  | Datos de cada concierto
Estilo
Dato conocido: 2075
Estimado: 297
No aplica: 280
No encontrado: 251
Origen
Dato conocido: 1210
Estimado: 493
No aplica: 723
No encontrado: 477
Hora
Dato conocido: 2423
E |
| ✅ | Conflicto de fecha en la tarjeta y la ficha | 2 fechas |  | ⚠ Las webs no coinciden
Fecha
miércoles, 25 de noviembre
5 webs: Palacio Vistalegre, La Ganzúa, Conciertos por Madrid, Songkick Madrid, JacksOnLive
martes, 24 de noviembre
1 web: JacksOnLive
JacksOnLi |
| ✅ | Nivel del concierto: «gran formato» en la tarjeta y nivel con su porqué en la ficha | 163 de gran formato · 'Movistar Arena: gran recinto' |  |  |
| ✅ | Fase B: guardar en Mis conciertos (★), Novedades y artistas similares | guardado y en la lista: True · ★: 1 · 84 conciertos nuevos · |  |  |
| ✅ | Informe se abre | — |  |  |
| ✅ | Paso de días, semanas, meses y años (con cambios de hora y febrero) con las flechas | 103 de 103 pasos bien |  |  |
| ✅ | Enlace directo a una ficha la abre | LA GORRA |  |  |
| ✅ | Peor caso semana del 19/10 (416 conciertos): con 'Todos' salen todos | 416 de 416 |  |  |

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
| ✅ | Por defecto se dice cuántos conciertos de otros géneros quedan ocultos, con un botón para verlos | 1379 conciertos más de otros géneros (jazz, flamenco, soul,  |  |  |
| ✅ | Búsqueda sin resultados lo dice | — |  |  |
| ✅ | La barra dice que se está buscando | Filtrando: búsqueda «Leiva» · Quitar filtros · Compartir |  |  |
| ✅ | La búsqueda se ve dentro de la hoja de filtros | — |  |  |
| ✅ | 'Todos' (grupos) no borra la búsqueda a escondidas | — |  |  |
| ✅ | 'Borrar filtros' en la hoja quita también la búsqueda | — |  |  |
| ✅ | El cuadro de búsqueda queda vacío al borrar | — |  |  |
| ✅ | Mes: al tocar un día, su lista queda a la vista | — |  |  |
| ✅ | Semana: al bajar, la fecha completa del día se queda fija arriba | Viernes, 16 de octubre60 conciertos |  | {'pegada': True, 'fecha': '2026-10-16', 'texto': 'Viernes, 16 de octubre60 conciertos', 'marcado': '2026-10-16', 'alto': 170} |
| ✅ | Semana: la tira de días marca el día por el que vas | 2026-10-16 / 2026-10-16 |  |  |
| ✅ | Semana: lo fijo arriba (cabecera, tira y fecha) no ocupa más de un tercio de la pantalla | 210 | aviso > 281 px / fallo > 422 px |  |
| ✅ | Semana: tocar un día de la tira lleva justo a ese día | 2026-10-18 (pedido 2026-10-18) |  | {'pegada': True, 'fecha': '2026-10-18', 'texto': 'Mañana, domingo, 18 de octubre30 conciertos', 'marcado': '2026-10-18', 'alto': 170} |
| ✅ | Día: al bajar, la fecha completa se queda fija arriba con la tira de días | Hoy, sábado, 17 de octubre64 conciertos |  | {'pegada': True, 'fecha': '2026-10-17', 'texto': 'Hoy, sábado, 17 de octubre64 conciertos', 'marcado': '2026-10-17', 'alto': 170} |
| ✅ | Mes: al bajar por la lista del día, su fecha completa se queda fija arriba | Hoy, sábado, 17 de octubre64 conciertos |  | {'pegada': True, 'fecha': '2026-10-17', 'texto': 'Hoy, sábado, 17 de octubre64 conciertos', 'marcado': None, 'alto': 109} |
| ✅ | Al bajar por la lista, Buscar y Filtros siguen a mano en la cabecera (y arriba no se duplican) | — |  |  |
| ✅ | A media lista, ‹ semana › en la cabecera: pasa a la siguiente y deja su primer día a la vista | 2026-10-19 · '19–25 oct\n213 conciertos' |  | {'fecha': '2026-10-19', 'fija': True, 'titulo': '19–25 oct\n213 conciertos', 'cabecera': True} |
| ✅ | Cambiar de día, semana o mes desde media lista deja la vista nueva desde su principio; Hoy siempre a mano | 10 de 10 casos bien |  |  |
| ✅ | Fuentes: una tarjeta por web con estado, 14 días y datos; filtros y búsqueda; sin scroll lateral | 82 de 82 webs · 32 salas · 60 salas sin web leída |  | {'n': 32, 'total': 82, 'tiras': 82, 'metricas': 82, 'lateral': 0, 'salas': 60, 'bien': True, 'esperadas': 32, 'busca': True} |
| ✅ | Saltos de diseño (CLS) | 0 | aviso > 0.1  / fallo > 0.25  |  |
| ✅ | Semana sin conciertos: lo dice | — |  |  |
| ✅ | Peor caso semana del 19/10 (416 conciertos): volver deja la lista en el concierto | — |  |  |
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
| ✅ | Ordenador: la ficha se abre al lado de la lista (la lista sigue a la vista) y Escape la cierra | al lado · cerrada |  | {'hash': '#semana/2026-10-12', 'lado': True, 'marcado': True, 'lateral': 0} |

## Rendimiento

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Conciertos con miniatura propia (servida desde la web) | 100.0 |  | de 2241 con imagen; mínimo 97 % |
| ✅ | Conciertos con foto de ficha propia (servida desde la web) | 100.0 |  | de 2241 con imagen; mínimo 97 % |
| ✅ | Primera visita: datos y lista pintados | 3109 | aviso > 5000 ms / fallo > 8000 ms |  |
| ✅ | Primera visita: LCP | 3160 | aviso > 4000 ms / fallo > 6000 ms |  |
| ✅ | Primera visita: KB descargados | 399 | aviso > 1500 KB / fallo > 3000 KB |  |
| ✅ | Bajar despacio: miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas |  |
| ✅ | Bajar deprisa: al parar, miniaturas visibles cargadas en | 45 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Cambiar de semana (mediana de 3) | 195 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Abrir ficha desde la lista (datos) | 109 | aviso > 500 ms / fallo > 1500 ms |  |
| ✅ | Ficha completa (fuentes y precio) | 114 | aviso > 1500 ms / fallo > 4000 ms |  |
| ✅ | Foto de la ficha tras ver la lista 2 s (mediana) | 143 | aviso > 600 ms / fallo > 1500 ms |  |
| ✅ | Fichas cuya foto ya estaba descargada al abrir | 5 |  | 5 de 5 |
| ✅ | Ficha lejana (wikimedia): datos | 170 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (wikimedia): foto | 173 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (sin foto): datos | 70 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (discogs): datos | 92 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (discogs): foto | 95 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (otros): datos | 162 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (otros): foto | 207 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (conciertos.club): datos | 44 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (conciertos.club): foto | 80 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (madridenvivo): datos | 153 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (madridenvivo): foto | 160 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Filtros: abrir la hoja | 285 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: 'Ninguno' | 112 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: aplicar | 192 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: borrar filtros | 203 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: 'Los de siempre' | 101 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: chip de grupo | 152 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Vista mes | 184 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Todos: pintar la lista | 155 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Segunda visita: lista pintada | 744 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Segunda visita: miniaturas visibles cargadas | 74 | aviso > 800 ms / fallo > 2500 ms |  |
| ✅ | Bloqueo de JavaScript más largo (CPU 6x) | 181 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Imágenes que no cargan | 0.2 | aviso > 1 % / fallo > 5 % | 503 https://estebancobo-dot.github.io/agenda-conciertos/miniaturas/cab98f8188f8f274.webp |
| ✅ | Enlace directo a una ficha (visita nueva) | 3423 | aviso > 5000 ms / fallo > 9000 ms |  |
| ✅ | Vista día sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 49 | aviso > 1000 ms / fallo > 2500 ms | [20, 49, 6] |
| ✅ | Vista mes sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 41 | aviso > 1000 ms / fallo > 2500 ms | [41, 5, 4] |
| ✅ | Ficha sin caché: foto desde que se ve la ficha (peor de 4 al azar) | 55 | aviso > 1200 ms / fallo > 2500 ms | [55, 53, 53, 51] ['estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io'] |
| ✅ | Imágenes de las listas pedidas fuera de la web (wsrv.nl, agendas) | 0 |  |  |
| ✅ | Peor caso semana del 19/10 (416 conciertos): pintar con 'Todos' | 210 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Peor caso semana del 19/10 (416 conciertos): miniaturas de la primera pantalla | 33 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 19/10 (416 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 67 pantallas; peores [0, 0, 0]; pantallas con alguna sin cargar: 0 |
| ✅ | Peor caso semana del 19/10 (416 conciertos): bloqueo de JavaScript más largo al bajar | 0 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Peor caso semana del 19/10 (416 conciertos): bajando seguido, miniaturas a la vista sin cargar | 0.0 | aviso > 5 % / fallo > 15 % | 0 de 345 vistas en 12 s |
| ✅ | Peor caso semana del 19/10 (416 conciertos): bajando deprisa, al parar miniaturas visibles cargadas en | 113 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 19/10 (416 conciertos): foto de una ficha del final de la lista | 297 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Peor caso semana del 19/10 (416 conciertos): imágenes pedidas fuera de la web | 0 |  |  |
| ✅ | Peor caso día 23/10 (102 conciertos): miniaturas de la primera pantalla | 79 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso día 23/10 (102 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 17 pantallas |
| ✅ | Peor caso mes 11/2026 (931 conciertos), día 07/11: al tocar el día, miniaturas visibles cargadas | 39 | aviso > 1000 ms / fallo > 2500 ms | desde el toque: 917 ms |

## Fallos

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Enlace a un concierto que ya no existe: lo dice y deja volver | — |  |  |
| ✅ | Detalle que no llega: se ve la ficha básica y avisa | — |  | ‹ Volver METROPOP No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 sábado, 17 de octubreEmpieza en 2 h 23 min 00:30 h 📍 Honky Tonk Madrid |
| ✅ | Fotos que no cargan: sin iconos de imagen rota | 0 |  |  |
| ✅ | Agenda que no llega: mensaje claro para recargar | — |  | No se pudieron cargar los datos (data/concerts.json). Comprueba la conexión y recarga la página. |
| ✅ | Agenda lenta: indica 'Cargando…' y luego se pinta | — |  |  |
| ✅ | Sin taxonomía de estilos: la agenda sigue funcionando | — |  |  |
| ✅ | Sin conexión: la agenda se abre con la copia guardada | 90 | aviso > 4500 ms / fallo > 8000 ms |  |
| ✅ | Sin conexión: se ven los conciertos | — |  |  |
| ✅ | Sin conexión: una ficha no guardada avisa en vez de quedarse cargando | — |  | ‹ Volver Foto: (imagen del anuncio) Quevedo No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 jueves, 15 de abril Hora por confirmar: las  |
| ✅ | Errores de JavaScript en todo el recorrido | 0 |  |  |

## Seguridad

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | La web declara su política de seguridad del contenido | — |  |  |
| ✅ | La política no bloquea nada de la propia web | 0 |  |  |

## Otros

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Enlaces a las fuentes responden | 1 |  | https://madridenvivo.com/evento/concierto-ricon-del-arte-pop-rock-8/ (404) |
| ✅ | Próximos 10 días: conciertos con enlace de compra directo | 157 de 592 |  | con cartel de gira 183, con hora 495 |
| ✅ | Todo por https (sin contenido mixto) | 0 |  |  |
| ✅ | Miniaturas de las agendas a través del proxy | 0 de 0 |  |  |
| ✅ | Errores en la consola | 0 |  |  |
