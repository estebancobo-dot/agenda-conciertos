# Validación de la web publicada — 2026-11-28 17:48 UTC

https://estebancobo-dot.github.io/agenda-conciertos/ · código de main 2.55.0 · móvil con 4G lenta y CPU 6x

**162 bien · 3 avisos · 0 fallos**

## Publicación

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Conciertos sin sala (la agenda no la dice) | 24 |  | XXXVIII FESTIVAL MÚSICA PLECTR (Aranjuez), Matritum Cantat en Mercado Pro (Madrid), Zambombas y panderetas en sinf (Las Rozas de Madrid), Coro de Actores (Madrid) |
| ⚠️ | Conciertos sin clasificar | 10.3 | aviso > 5 % / fallo > 15 % | 278 de 2700 |
| ⚠️ | Fuentes sin alertas | 14 |  | TodoHeavyMetal: posible cambio en la web: antes daba 16 conciertos (último éxito 2026-11-28); Metal Legion: posible cambio en la web: antes daba 35 conciertos (último éxito 2026-11-28); Metalcry: posi |
| ✅ | index.html publicado = el de main | — |  |  |
| ✅ | sw.js publicado = el de main | — |  |  |
| ✅ | Datos de la agenda recientes | 3.0 | aviso > 26 h / fallo > 50 h |  |
| ✅ | Conciertos próximos publicados | 2700 |  | mínimo 500 |
| ✅ | Ids únicos | 0 |  |  |
| ✅ | Cada concierto con id, fecha y artista | 0 |  |  |
| ✅ | Conciertos sin sala ni municipio | 0 |  |  |
| ✅ | Imágenes solo por https | 0 |  |  |
| ✅ | Fichero de detalle de cada día | 0 |  |  |
| ✅ | El detalle trae todos los conciertos del día | 0 |  |  |
| ✅ | Detalle y agenda coinciden | 0 |  |  |
| ✅ | Miniaturas y fotos propias servidas | 0 |  |  |
| ✅ | Conciertos próximos sin origen del artista (ni confirmado ni estimado) | 17.5 | aviso > 30 % / fallo > 50 % | 472 de 2700; además 532 deducidos (nombre, grupo local, tributo…) |
| ✅ | Conciertos en 'Otros' (sin género propio) | 0.6 | aviso > 3 % / fallo > 10 % | 16 de 2700 |
| ✅ | Conciertos con etiqueta genérica ("Pop / Rock", "Músicas negras") | 7.0 | aviso > 8 % / fallo > 25 % | 188 de 2700 |
| ✅ | Conciertos sin ningún estilo | 24.1 | aviso > 30 % / fallo > 60 % | 651 de 2700 |
| ✅ | Última lectura completa de las agendas | 5.8 | aviso > 27 h / fallo > 50 h |  |

## Funcional

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | La cabecera dice cuántos conciertos hay y cuándo se actualizó | 2700 conciertos · actualizado 28 nov, 15:48 |  |  |
| ✅ | Semana: salen justo los conciertos de los datos (con los filtros puestos) | 257 de 257 |  | faltan [] sobran [] días sin pintar 0 |
| ✅ | Semana: todos de esa semana y en orden de fecha | 0 |  |  |
| ✅ | Ficha: artista y sala de los datos | SUDAKJAZZ |  | esperado 'SUDAKJAZZ' en 'Intruso Bar' |
| ✅ | Ficha: enlaza a sus fuentes | 1 de 1 |  |  |
| ✅ | Filtro de un solo grupo (pop e indie): solo salen de ese grupo | 86 tarjetas |  | 0 de otros grupos |
| ✅ | 'Borrar filtros' deja la agenda sin filtros | — |  |  |
| ✅ | Subgéneros: buscando y marcando dos estilos de géneros distintos salen justo sus conciertos | ['Brit Pop', 'AOR']: 4 de 4 |  | {'n': 4, 'malos': 0, 'esperados': 4} |
| ✅ | Subgénero «(general)»: salen los del género sin estilo concreto, y solo esos | Rock y metal (general): 263 |  | {'n': 263, 'malos': 0} |
| ✅ | Tributos: su estilo como subgénero (todos tienen uno) | 153 tributos, 35 de rock |  | {'n': 153, 'sin': 0, 'rock': 35, 'ej': []} |
| ✅ | Buscar un artista lo encuentra | De dónde somos cuando creamos |  |  |
| ✅ | Buscar encuentra también conciertos de géneros ocultos por el filtro | Instrumentos occidentales y orientales: un encuentro musical |  |  |
| ✅ | Filtros de origen: España, Latinoamérica, internacional y sin confirmar cuadran | 2700 de 2700 |  | {'total': 2700, 'es': 1176, 'lat': 82, 'ext': 331, 'nc': 472, 'na': 639, 'otra': 0} |
| ✅ | Mes: la lista del día son los conciertos de ese día | 6 de 6 |  |  |
| ✅ | Ficha: el enlace de compra de la página de entradas es el botón principal | Comprar entradas en Entradium ↗ |  | {'ok': True, 'texto': 'Comprar entradas en Entradium ↗', 'agotado': False, 'aviso': False} |
| ✅ | A media lista, el menú ☰ se abre a la vista | — |  |  |
| ✅ | A media lista, Filtros abre la hoja sin mover la lista | — |  |  |
| ✅ | A media lista, la lupa abre la búsqueda en la cabecera lista para escribir, sin mover la lista | — |  |  |
| ✅ | Buscar desde media lista y cancelar: vuelve a la misma tarjeta | 35 resultados |  |  |
| ✅ | Festivales: insignia y cartel en la ficha | 'FESTIVAL SAUROM JUGLAR FEST MADRID': 3 de 3 |  |  |
| ✅ | Teloneros: el concierto sale al filtrar por el género del telonero (y la tarjeta lo dice) | rock y metal el 2026-11-28 |  | {'sale': True, 'tag': True} |
| ✅ | Salas: lista, búsqueda, página de la sala con su programación y Volver | 255 salas · Sala El Sol: 159 conciertos · volver a #salas |  | {'nombre': 'Sala El Sol', 'cards': 159, 'esperadas': 159, 'ics': 'calendario/sala-sala-el-sol.ics', 'lateral': 0, 'filtro': ['La Riviera']} |
| ✅ | Calendario de la sala: suscripción (webcal, Google, Outlook) y .ics válido con sus conciertos | 166 eventos en calendario/sala-sala-el-sol.ics |  | ['webcal://estebancobo-dot.github.io/agenda-conciertos/calendario/sala-sala-el-sol.ics', 'https://calendar.google.com/calendar/render?cid=webcal%3A%2F%2Festebancobo-dot.github.io%2Fagenda-conciertos%2 |
| ✅ | Calendarios por género: uno por género y se descargan | 20 géneros · 648 eventos en calendario/genero-rock-y-metal.i |  | {'n': 20, 'ics': 'calendario/genero-rock-y-metal.ics', 'ok': True, 'ev': 648} |
| ✅ | Historial de cambios en la ficha (y aviso en la tarjeta) | 169 conciertos con cambios · 21 novPrecio: 16,51€ → Anticipa |  | ['21 novPrecio: 16,51€ → Anticipada: 15€ Taquilla: 18€', '13 novPrecio: Anticipada: 15€ Taquilla: 18€ → 16,51€', '29 septAparece en la agenda'] |
| ✅ | Fin de semana: viernes a domingo de la semana (también al cambiar de año), lo que dicen los datos | 2 de 2 bien |  |  |
| ✅ | Todos: todos los conciertos desde hoy en orden, con su total, pintado progresivo y saltos por meses | 1397 de 2700 conciertos desde hoy · 63 pintados al abrir · 1 |  | {'pintadas': 63, 'orden': True, 'desdeHoy': True, 'n': 1397, 'cab': '1397 de 2700 conciertos desde hoy', 'meses': 7, 'lateral': 0, 'salto': {'mes': '2026-12', 'dia': '2026-12-01', 'marcado': True}} |
| ✅ | Confirmación: nivel y motivos en la ficha; filtro 'Solo confirmados' | 905 confirmados · 1309 probables · 486 sin confirmar · ficha |  | {'con': 2700, 'n': 95, 'c': 905, 'p': 1309, 's': 486, 'bien': True} |
| ✅ | Estado de estilo y origen en la ficha (sin etiqueta si es un dato conocido) y recuento en Fuentes (N3/N4) | ficha: ['No encontrado', 'Estimado', 'No encontrado'] · ['Es |  | Datos de cada concierto
Estilo
Dato conocido: 1821
Estimado: 270
No aplica: 375
No encontrado: 274
Origen
Dato conocido: 1006
Estimado: 597
No aplica: 644
No encontrado: 493
Hora
Dato conocido: 2218
E |
| ✅ | Conflicto de fecha en la tarjeta y la ficha | 2 fechas |  | ⚠ Las webs no coinciden
Fecha
viernes, 22 de enero
5 webs: conciertos.club, JacksOnLive, Festify Indie, MariskalRock
jueves, 21 de enero
1 web: JacksOnLive
JacksOnLive anuncia una nueva fecha; otras w |
| ✅ | Nivel del concierto: «gran formato» en la tarjeta y nivel con su porqué en la ficha | 139 de gran formato · 'La Nueva Cubierta: gran recinto · Acc |  |  |
| ✅ | Fase B: guardar en Mis conciertos (★), Novedades y artistas similares | guardado y en la lista: True · ★: 1 · 60 conciertos nuevos · |  |  |
| ✅ | Informe se abre | — |  |  |
| ✅ | Paso de días, semanas, meses y años (con cambios de hora y febrero) con las flechas | 103 de 103 pasos bien |  |  |
| ✅ | Enlace directo a una ficha la abre | ROCKSPEL CHRISTMAS |  |  |
| ✅ | Peor caso semana del 07/12 (361 conciertos): con 'Todos' salen todos | 361 de 361 |  |  |

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
| ✅ | Por defecto se dice cuántos conciertos de otros géneros quedan ocultos, con un botón para verlos | 1303 conciertos más de otros géneros (jazz, flamenco, soul,  |  |  |
| ✅ | Búsqueda sin resultados lo dice | — |  |  |
| ✅ | La barra dice que se está buscando | Filtrando: búsqueda «Leiva» · Quitar filtros · Compartir |  |  |
| ✅ | La búsqueda se ve dentro de la hoja de filtros | — |  |  |
| ✅ | 'Todos' (grupos) no borra la búsqueda a escondidas | — |  |  |
| ✅ | 'Borrar filtros' en la hoja quita también la búsqueda | — |  |  |
| ✅ | El cuadro de búsqueda queda vacío al borrar | — |  |  |
| ✅ | Mes: al tocar un día, su lista queda a la vista | — |  |  |
| ✅ | Semana: al bajar, la fecha completa del día se queda fija arriba | Viernes, 27 de noviembre58 conciertos |  | {'pegada': True, 'fecha': '2026-11-27', 'texto': 'Viernes, 27 de noviembre58 conciertos', 'marcado': '2026-11-27', 'alto': 170} |
| ✅ | Semana: la tira de días marca el día por el que vas | 2026-11-27 / 2026-11-27 |  |  |
| ✅ | Semana: lo fijo arriba (cabecera, tira y fecha) no ocupa más de un tercio de la pantalla | 210 | aviso > 281 px / fallo > 422 px |  |
| ✅ | Semana: tocar un día de la tira lleva justo a ese día | 2026-11-29 (pedido 2026-11-29) |  | {'pegada': True, 'fecha': '2026-11-29', 'texto': 'Mañana, domingo, 29 de noviembre33 conciertos', 'marcado': '2026-11-29', 'alto': 170} |
| ✅ | Día: al bajar, la fecha completa se queda fija arriba con la tira de días | Hoy, sábado, 28 de noviembre63 conciertos |  | {'pegada': True, 'fecha': '2026-11-28', 'texto': 'Hoy, sábado, 28 de noviembre63 conciertos', 'marcado': '2026-11-28', 'alto': 170} |
| ✅ | Mes: al bajar por la lista del día, su fecha completa se queda fija arriba | Hoy, sábado, 28 de noviembre63 conciertos |  | {'pegada': True, 'fecha': '2026-11-28', 'texto': 'Hoy, sábado, 28 de noviembre63 conciertos', 'marcado': None, 'alto': 109} |
| ✅ | Al bajar por la lista, Buscar y Filtros siguen a mano en la cabecera (y arriba no se duplican) | — |  |  |
| ✅ | A media lista, ‹ semana › en la cabecera: pasa a la siguiente y deja su primer día a la vista | 2026-11-30 · '30 nov–6 dic\n189 conciertos' |  | {'fecha': '2026-11-30', 'fija': True, 'titulo': '30 nov–6 dic\n189 conciertos', 'cabecera': True} |
| ✅ | Cambiar de día, semana o mes desde media lista deja la vista nueva desde su principio; Hoy siempre a mano | 10 de 10 casos bien |  |  |
| ✅ | Fuentes: una tarjeta por web con estado, 14 días y datos; filtros y búsqueda; sin scroll lateral | 87 de 87 webs · 33 salas · 71 salas sin web leída |  | {'n': 33, 'total': 87, 'tiras': 87, 'metricas': 87, 'lateral': 0, 'salas': 71, 'bien': True, 'esperadas': 33, 'busca': True} |
| ✅ | Saltos de diseño (CLS) | 0 | aviso > 0.1  / fallo > 0.25  |  |
| ✅ | Semana sin conciertos: lo dice | — |  |  |
| ✅ | Peor caso semana del 07/12 (361 conciertos): volver deja la lista en el concierto | — |  |  |
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
| ✅ | Ordenador: la ficha se abre al lado de la lista (la lista sigue a la vista) y Escape la cierra | al lado · cerrada |  | {'hash': '#semana/2026-11-23', 'lado': True, 'marcado': True, 'lateral': 0} |

## Rendimiento

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Conciertos con miniatura propia (servida desde la web) | 100.0 |  | de 2001 con imagen; mínimo 97 % |
| ✅ | Conciertos con foto de ficha propia (servida desde la web) | 100.0 |  | de 2001 con imagen; mínimo 97 % |
| ✅ | Primera visita: datos y lista pintados | 3484 | aviso > 5000 ms / fallo > 8000 ms |  |
| ✅ | Primera visita: LCP | 3528 | aviso > 4000 ms / fallo > 6000 ms |  |
| ✅ | Primera visita: KB descargados | 478 | aviso > 1500 KB / fallo > 3000 KB |  |
| ✅ | Bajar despacio: miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas |  |
| ✅ | Bajar deprisa: al parar, miniaturas visibles cargadas en | 36 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Cambiar de semana (mediana de 3) | 169 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Abrir ficha desde la lista (datos) | 113 | aviso > 500 ms / fallo > 1500 ms |  |
| ✅ | Ficha completa (fuentes y precio) | 116 | aviso > 1500 ms / fallo > 4000 ms |  |
| ✅ | Foto de la ficha tras ver la lista 2 s (mediana) | 177 | aviso > 600 ms / fallo > 1500 ms |  |
| ✅ | Fichas cuya foto ya estaba descargada al abrir | 5 |  | 5 de 5 |
| ✅ | Ficha lejana (discogs): datos | 148 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (discogs): foto | 153 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (sin foto): datos | 71 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (wikimedia): datos | 84 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (wikimedia): foto | 88 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (otros): datos | 30 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (otros): foto | 51 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (conciertos.club): datos | 120 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (conciertos.club): foto | 123 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (madridenvivo): datos | 64 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (madridenvivo): foto | 102 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Filtros: abrir la hoja | 222 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: 'Ninguno' | 88 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: aplicar | 168 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: borrar filtros | 183 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: 'Los de siempre' | 88 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: chip de grupo | 145 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Vista mes | 159 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Todos: pintar la lista | 146 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Segunda visita: lista pintada | 693 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Segunda visita: miniaturas visibles cargadas | 69 | aviso > 800 ms / fallo > 2500 ms |  |
| ✅ | Bloqueo de JavaScript más largo (CPU 6x) | 185 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Imágenes que no cargan | 0.0 | aviso > 1 % / fallo > 5 % |  |
| ✅ | Enlace directo a una ficha (visita nueva) | 3590 | aviso > 5000 ms / fallo > 9000 ms |  |
| ✅ | Vista día sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 20 | aviso > 1000 ms / fallo > 2500 ms | [20, 3, 17] |
| ✅ | Vista mes sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 9 | aviso > 1000 ms / fallo > 2500 ms | [5, 9, 7] |
| ✅ | Ficha sin caché: foto desde que se ve la ficha (peor de 4 al azar) | 86 | aviso > 1200 ms / fallo > 2500 ms | [65, 59, 52, 86] ['estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io'] |
| ✅ | Imágenes de las listas pedidas fuera de la web (wsrv.nl, agendas) | 0 |  |  |
| ✅ | Peor caso semana del 07/12 (361 conciertos): pintar con 'Todos' | 223 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Peor caso semana del 07/12 (361 conciertos): miniaturas de la primera pantalla | 19 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 07/12 (361 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 1 | aviso > 1 miniaturas / fallo > 3 miniaturas | 58 pantallas; peores [0, 0, 1]; pantallas con alguna sin cargar: 1 |
| ✅ | Peor caso semana del 07/12 (361 conciertos): bloqueo de JavaScript más largo al bajar | 0 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Peor caso semana del 07/12 (361 conciertos): bajando seguido, miniaturas a la vista sin cargar | 0.0 | aviso > 5 % / fallo > 15 % | 0 de 318 vistas en 12 s |
| ✅ | Peor caso semana del 07/12 (361 conciertos): bajando deprisa, al parar miniaturas visibles cargadas en | 68 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 07/12 (361 conciertos): foto de una ficha del final de la lista | 288 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Peor caso semana del 07/12 (361 conciertos): imágenes pedidas fuera de la web | 1 |  | doc.conciertos.club |
| ✅ | Peor caso día 28/11 (113 conciertos): miniaturas de la primera pantalla | 78 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso día 28/11 (113 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 19 pantallas |
| ✅ | Peor caso mes 12/2026 (1304 conciertos), día 19/12: al tocar el día, miniaturas visibles cargadas | 52 | aviso > 1000 ms / fallo > 2500 ms | desde el toque: 925 ms |

## Fallos

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Enlace a un concierto que ya no existe: lo dice y deja volver | — |  |  |
| ✅ | Detalle que no llega: se ve la ficha básica y avisa | — |  | ‹ Volver TOPPER CHOPPER No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 sábado, 28 de noviembreEmpieza en 5 h 39 min 00:30 h 📍 Honky Ton |
| ✅ | Fotos que no cargan: sin iconos de imagen rota | 0 |  |  |
| ✅ | Agenda que no llega: mensaje claro para recargar | — |  | No se pudieron cargar los datos (data/concerts.json). Comprueba la conexión y recarga la página. |
| ✅ | Agenda lenta: indica 'Cargando…' y luego se pinta | — |  |  |
| ✅ | Sin taxonomía de estilos: la agenda sigue funcionando | — |  |  |
| ✅ | Sin conexión: la agenda se abre con la copia guardada | 106 | aviso > 4500 ms / fallo > 8000 ms |  |
| ✅ | Sin conexión: se ven los conciertos | — |  |  |
| ✅ | Sin conexión: una ficha no guardada avisa en vez de quedarse cargando | — |  | ‹ Volver Foto: (imagen del anuncio) WALLS No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 jueves, 27 de mayo Hora sin indicar 📍 Movistar |
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
| ✅ | Próximos 10 días: conciertos con enlace de compra directo | 148 de 563 |  | con cartel de gira 149, con hora 440 |
| ✅ | Todo por https (sin contenido mixto) | 0 |  |  |
| ✅ | Miniaturas de las agendas a través del proxy | 0 de 0 |  |  |
| ✅ | Errores en la consola | 0 |  |  |
