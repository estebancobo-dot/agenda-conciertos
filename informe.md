# Validación de la web publicada — 2026-11-07 15:55 UTC

https://estebancobo-dot.github.io/agenda-conciertos/ · código de main 2.55.0 · móvil con 4G lenta y CPU 6x

**162 bien · 4 avisos · 0 fallos**

## Publicación

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Conciertos sin clasificar | 7.3 | aviso > 5 % / fallo > 15 % | 215 de 2946 |
| ⚠️ | Fuentes sin alertas | 2 |  | Total Stage (agenda de la comunidad): lleva 4 días sin leerse bien (último éxito 2026-11-03, daba 461); Revi Live / Revi Space (web oficial): lleva 7 días sin leerse bien (último éxito 2026-10-31, dab |
| ✅ | index.html publicado = el de main | — |  |  |
| ✅ | sw.js publicado = el de main | — |  |  |
| ✅ | Datos de la agenda recientes | 5.7 | aviso > 26 h / fallo > 50 h |  |
| ✅ | Conciertos próximos publicados | 2946 |  | mínimo 500 |
| ✅ | Ids únicos | 0 |  |  |
| ✅ | Cada concierto con id, fecha y artista | 0 |  |  |
| ✅ | Conciertos sin sala ni municipio | 0 |  |  |
| ✅ | Conciertos sin sala (la agenda no la dice) | 14 |  | MÚSICA Y DANZA. LAS CUATRO EST (Aranjuez), XXXIII MÚSICA ANTIGUA ARANJUEZ (Aranjuez), MÚSICA Y DANZA. ORQUESTA SINFÓ (Aranjuez), Concierto clausura del 26º Cer (Las Rozas de Madrid) |
| ✅ | Imágenes solo por https | 0 |  |  |
| ✅ | Fichero de detalle de cada día | 0 |  |  |
| ✅ | El detalle trae todos los conciertos del día | 0 |  |  |
| ✅ | Detalle y agenda coinciden | 0 |  |  |
| ✅ | Miniaturas y fotos propias servidas | 0 |  |  |
| ✅ | Conciertos próximos sin origen del artista (ni confirmado ni estimado) | 15.1 | aviso > 30 % / fallo > 50 % | 445 de 2946; además 523 deducidos (nombre, grupo local, tributo…) |
| ✅ | Conciertos en 'Otros' (sin género propio) | 0.4 | aviso > 3 % / fallo > 10 % | 12 de 2946 |
| ✅ | Conciertos con etiqueta genérica ("Pop / Rock", "Músicas negras") | 5.4 | aviso > 8 % / fallo > 25 % | 158 de 2946 |
| ✅ | Conciertos sin ningún estilo | 22.4 | aviso > 30 % / fallo > 60 % | 661 de 2946 |
| ✅ | Última lectura completa de las agendas | 5.7 | aviso > 27 h / fallo > 50 h |  |

## Funcional

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Fuente que ya no se puede leer: «sin reconfirmar» en la tarjeta y la ficha | 17 conciertos |  |  |
| ✅ | La cabecera dice cuántos conciertos hay y cuándo se actualizó | 2946 conciertos · actualizado 7 nov, 11:15 |  |  |
| ✅ | Semana: salen justo los conciertos de los datos (con los filtros puestos) | 241 de 241 |  | faltan [] sobran [] días sin pintar 0 |
| ✅ | Semana: todos de esa semana y en orden de fecha | 0 |  |  |
| ✅ | Ficha: artista y sala de los datos | Concierto de Blues |  | esperado 'Concierto de Blues' en 'La Coquette' |
| ✅ | Ficha: enlaza a sus fuentes | 3 de 3 |  |  |
| ✅ | Filtro de un solo grupo (pop e indie): solo salen de ese grupo | 89 tarjetas |  | 0 de otros grupos |
| ✅ | 'Borrar filtros' deja la agenda sin filtros | — |  |  |
| ✅ | Subgéneros: buscando y marcando dos estilos de géneros distintos salen justo sus conciertos | ['Jangle Pop', 'AOR']: 4 de 4 |  | {'n': 4, 'malos': 0, 'esperados': 4} |
| ✅ | Subgénero «(general)»: salen los del género sin estilo concreto, y solo esos | Rock y metal (general): 244 |  | {'n': 244, 'malos': 0} |
| ✅ | Tributos: su estilo como subgénero (todos tienen uno) | 200 tributos, 39 de rock |  | {'n': 200, 'sin': 0, 'rock': 39, 'ej': []} |
| ✅ | Buscar un artista lo encuentra | Henry Semler |  |  |
| ✅ | Buscar encuentra también conciertos de géneros ocultos por el filtro | Dixon |  |  |
| ✅ | Filtros de origen: España, Latinoamérica, internacional y sin confirmar cuadran | 2946 de 2946 |  | {'total': 2946, 'es': 1208, 'lat': 116, 'ext': 401, 'nc': 445, 'na': 776, 'otra': 0} |
| ✅ | Mes: la lista del día son los conciertos de ese día | 6 de 6 |  |  |
| ✅ | Ficha: el enlace de compra de la página de entradas es el botón principal | Comprar entradas en Mutick ↗ |  | {'ok': True, 'texto': 'Comprar entradas en Mutick ↗', 'agotado': False, 'aviso': False} |
| ✅ | A media lista, el menú ☰ se abre a la vista | — |  |  |
| ✅ | A media lista, Filtros abre la hoja sin mover la lista | — |  |  |
| ✅ | A media lista, la lupa abre la búsqueda en la cabecera lista para escribir, sin mover la lista | — |  |  |
| ✅ | Buscar desde media lista y cancelar: vuelve a la misma tarjeta | 35 resultados |  |  |
| ✅ | Festivales: insignia y cartel en la ficha | 'FESTIVAL Lilith ´s Dauughters Fest (Itinerum': 2 de 2 |  |  |
| ✅ | Teloneros: el concierto sale al filtrar por el género del telonero (y la tarjeta lo dice) | pop comercial el 2026-11-07 |  | {'sale': True, 'tag': True} |
| ✅ | Salas: lista, búsqueda, página de la sala con su programación y Volver | 244 salas · Sala El Sol: 125 conciertos · volver a #salas |  | {'nombre': 'Sala El Sol', 'cards': 125, 'esperadas': 125, 'ics': 'calendario/sala-sala-el-sol.ics', 'lateral': 0, 'filtro': ['La Riviera']} |
| ✅ | Calendario de la sala: suscripción (webcal, Google, Outlook) y .ics válido con sus conciertos | 138 eventos en calendario/sala-sala-el-sol.ics |  | ['webcal://estebancobo-dot.github.io/agenda-conciertos/calendario/sala-sala-el-sol.ics', 'https://calendar.google.com/calendar/render?cid=webcal%3A%2F%2Festebancobo-dot.github.io%2Fagenda-conciertos%2 |
| ✅ | Calendarios por género: uno por género y se descargan | 20 géneros · 674 eventos en calendario/genero-rock-y-metal.i |  | {'n': 20, 'ics': 'calendario/genero-rock-y-metal.ics', 'ok': True, 'ev': 674} |
| ✅ | Historial de cambios en la ficha (y aviso en la tarjeta) | 163 conciertos con cambios · 7 novPrecio: 34,5 € – 77 € → 38 |  | ['7 novPrecio: 34,5 € – 77 € → 38 €', '7 novPrecio: 34,5 € – 77 € → 38 €', '6 novPrecio: 34,5 € – 77 € → 38 €', '6 novPrecio: 34,5 € – 77 € → 38 €', '6 novPrecio: 34,5 € – 77 € → 38 €', '5 novPrecio:  |
| ✅ | Fin de semana: viernes a domingo de la semana (también al cambiar de año), lo que dicen los datos | 2 de 2 bien |  |  |
| ✅ | Todos: todos los conciertos desde hoy en orden, con su total, pintado progresivo y saltos por meses | 1417 de 2946 conciertos desde hoy · 60 pintados al abrir · 1 |  | {'pintadas': 60, 'orden': True, 'desdeHoy': True, 'n': 1417, 'cab': '1417 de 2946 conciertos desde hoy', 'meses': 7, 'lateral': 0, 'salto': {'mes': '2026-12', 'dia': '2026-12-01', 'marcado': True}} |
| ✅ | Confirmación: nivel y motivos en la ficha; filtro 'Solo confirmados' | 1006 confirmados · 1422 probables · 518 sin confirmar · fich |  | {'con': 2946, 'n': 56, 'c': 1006, 'p': 1422, 's': 518, 'bien': True} |
| ✅ | Estado de estilo y origen en la ficha (sin etiqueta si es un dato conocido) y recuento en Fuentes (N3/N4) | ficha: ['Estimado'] · ['Estilo', 'Dato conocido: 2076'] |  | Datos de cada concierto
Estilo
Dato conocido: 2076
Estimado: 269
No aplica: 428
No encontrado: 225
Origen
Dato conocido: 1156
Estimado: 589
No aplica: 780
No encontrado: 473
Hora
Dato conocido: 2516
E |
| ✅ | Conflicto de fecha en la tarjeta y la ficha | 2 fechas |  | ⚠ Las webs no coinciden
Fecha
sábado, 7 de noviembre
3 webs: conciertos.club
domingo, 8 de noviembre
1 web: Sala But
La web oficial de la sala lo anuncia otro día. Confírmalo allí antes de ir. |
| ✅ | Nivel del concierto: «gran formato» en la tarjeta y nivel con su porqué en la ficha | 158 de gran formato · 'Live Las Ventas: gran recinto' |  |  |
| ✅ | Fase B: guardar en Mis conciertos (★), Novedades y artistas similares | guardado y en la lista: True · ★: 1 · 24 conciertos nuevos · |  |  |
| ✅ | Informe se abre | — |  |  |
| ✅ | Paso de días, semanas, meses y años (con cambios de hora y febrero) con las flechas | 103 de 103 pasos bien |  |  |
| ✅ | Enlace directo a una ficha la abre | LITTLE DEVILS |  |  |
| ✅ | Peor caso semana del 09/11 (425 conciertos): con 'Todos' salen todos | 425 de 425 |  |  |

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
| ✅ | Por defecto se dice cuántos conciertos de otros géneros quedan ocultos, con un botón para verlos | 1529 conciertos más de otros géneros (jazz, flamenco, soul,  |  |  |
| ✅ | Búsqueda sin resultados lo dice | — |  |  |
| ✅ | La barra dice que se está buscando | Filtrando: búsqueda «Leiva» · Quitar filtros · Compartir |  |  |
| ✅ | La búsqueda se ve dentro de la hoja de filtros | — |  |  |
| ✅ | 'Todos' (grupos) no borra la búsqueda a escondidas | — |  |  |
| ✅ | 'Borrar filtros' en la hoja quita también la búsqueda | — |  |  |
| ✅ | El cuadro de búsqueda queda vacío al borrar | — |  |  |
| ✅ | Mes: al tocar un día, su lista queda a la vista | — |  |  |
| ✅ | Semana: al bajar, la fecha completa del día se queda fija arriba | Viernes, 6 de noviembre50 conciertos |  | {'pegada': True, 'fecha': '2026-11-06', 'texto': 'Viernes, 6 de noviembre50 conciertos', 'marcado': '2026-11-06', 'alto': 170} |
| ✅ | Semana: la tira de días marca el día por el que vas | 2026-11-06 / 2026-11-06 |  |  |
| ✅ | Semana: lo fijo arriba (cabecera, tira y fecha) no ocupa más de un tercio de la pantalla | 210 | aviso > 281 px / fallo > 422 px |  |
| ✅ | Semana: tocar un día de la tira lleva justo a ese día | 2026-11-08 (pedido 2026-11-08) |  | {'pegada': True, 'fecha': '2026-11-08', 'texto': 'Mañana, domingo, 8 de noviembre34 conciertos', 'marcado': '2026-11-08', 'alto': 170} |
| ✅ | Día: al bajar, la fecha completa se queda fija arriba con la tira de días | Hoy, sábado, 7 de noviembre60 conciertos |  | {'pegada': True, 'fecha': '2026-11-07', 'texto': 'Hoy, sábado, 7 de noviembre60 conciertos', 'marcado': '2026-11-07', 'alto': 170} |
| ✅ | Mes: al bajar por la lista del día, su fecha completa se queda fija arriba | Hoy, sábado, 7 de noviembre60 conciertos |  | {'pegada': True, 'fecha': '2026-11-07', 'texto': 'Hoy, sábado, 7 de noviembre60 conciertos', 'marcado': None, 'alto': 109} |
| ✅ | Al bajar por la lista, Buscar y Filtros siguen a mano en la cabecera (y arriba no se duplican) | — |  |  |
| ✅ | A media lista, ‹ semana › en la cabecera: pasa a la siguiente y deja su primer día a la vista | 2026-11-09 · '9–15 nov\n203 conciertos' |  | {'fecha': '2026-11-09', 'fija': True, 'titulo': '9–15 nov\n203 conciertos', 'cabecera': True} |
| ✅ | Cambiar de día, semana o mes desde media lista deja la vista nueva desde su principio; Hoy siempre a mano | 10 de 10 casos bien |  |  |
| ✅ | Fuentes: una tarjeta por web con estado, 14 días y datos; filtros y búsqueda; sin scroll lateral | 83 de 83 webs · 32 salas · 68 salas sin web leída |  | {'n': 32, 'total': 83, 'tiras': 83, 'metricas': 83, 'lateral': 0, 'salas': 68, 'bien': True, 'esperadas': 32, 'busca': True} |
| ✅ | Saltos de diseño (CLS) | 0 | aviso > 0.1  / fallo > 0.25  |  |
| ✅ | Semana sin conciertos: lo dice | — |  |  |
| ✅ | Peor caso semana del 09/11 (425 conciertos): volver deja la lista en el concierto | — |  |  |
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
| ✅ | Ordenador: la ficha se abre al lado de la lista (la lista sigue a la vista) y Escape la cierra | al lado · cerrada |  | {'hash': '#semana/2026-11-02', 'lado': True, 'marcado': True, 'lateral': 0} |

## Rendimiento

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Primera visita: LCP | 4020 | aviso > 4000 ms / fallo > 6000 ms |  |
| ✅ | Conciertos con miniatura propia (servida desde la web) | 100.0 |  | de 2306 con imagen; mínimo 97 % |
| ✅ | Conciertos con foto de ficha propia (servida desde la web) | 100.0 |  | de 2306 con imagen; mínimo 97 % |
| ✅ | Primera visita: datos y lista pintados | 3940 | aviso > 5000 ms / fallo > 8000 ms |  |
| ✅ | Primera visita: KB descargados | 493 | aviso > 1500 KB / fallo > 3000 KB |  |
| ✅ | Bajar despacio: miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas |  |
| ✅ | Bajar deprisa: al parar, miniaturas visibles cargadas en | 81 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Cambiar de semana (mediana de 3) | 335 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Abrir ficha desde la lista (datos) | 174 | aviso > 500 ms / fallo > 1500 ms |  |
| ✅ | Ficha completa (fuentes y precio) | 180 | aviso > 1500 ms / fallo > 4000 ms |  |
| ✅ | Foto de la ficha tras ver la lista 2 s (mediana) | 203 | aviso > 600 ms / fallo > 1500 ms |  |
| ✅ | Fichas cuya foto ya estaba descargada al abrir | 5 |  | 5 de 5 |
| ✅ | Ficha lejana (discogs): datos | 180 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (discogs): foto | 189 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (wikimedia): datos | 97 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (wikimedia): foto | 102 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (sin foto): datos | 31 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (otros): datos | 157 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (otros): foto | 172 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (conciertos.club): datos | 103 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (conciertos.club): foto | 112 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (madridenvivo): datos | 150 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (madridenvivo): foto | 154 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Filtros: abrir la hoja | 287 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: 'Ninguno' | 105 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: aplicar | 202 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: borrar filtros | 234 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: 'Los de siempre' | 76 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: chip de grupo | 206 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Vista mes | 194 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Todos: pintar la lista | 178 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Segunda visita: lista pintada | 1191 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Segunda visita: miniaturas visibles cargadas | 101 | aviso > 800 ms / fallo > 2500 ms |  |
| ✅ | Bloqueo de JavaScript más largo (CPU 6x) | 246 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Imágenes que no cargan | 0.0 | aviso > 1 % / fallo > 5 % |  |
| ✅ | Enlace directo a una ficha (visita nueva) | 4045 | aviso > 5000 ms / fallo > 9000 ms |  |
| ✅ | Vista día sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 14 | aviso > 1000 ms / fallo > 2500 ms | [14, 4, 4] |
| ✅ | Vista mes sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 10 | aviso > 1000 ms / fallo > 2500 ms | [5, 5, 10] |
| ✅ | Ficha sin caché: foto desde que se ve la ficha (peor de 4 al azar) | 69 | aviso > 1200 ms / fallo > 2500 ms | [63, 69, 69, 64] ['estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io'] |
| ✅ | Imágenes de las listas pedidas fuera de la web (wsrv.nl, agendas) | 0 |  |  |
| ✅ | Peor caso semana del 09/11 (425 conciertos): pintar con 'Todos' | 285 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Peor caso semana del 09/11 (425 conciertos): miniaturas de la primera pantalla | 46 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 09/11 (425 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 69 pantallas; peores [0, 0, 0]; pantallas con alguna sin cargar: 0 |
| ✅ | Peor caso semana del 09/11 (425 conciertos): bloqueo de JavaScript más largo al bajar | 0 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Peor caso semana del 09/11 (425 conciertos): bajando seguido, miniaturas a la vista sin cargar | 0.0 | aviso > 5 % / fallo > 15 % | 0 de 331 vistas en 12 s |
| ✅ | Peor caso semana del 09/11 (425 conciertos): bajando deprisa, al parar miniaturas visibles cargadas en | 191 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 09/11 (425 conciertos): foto de una ficha del final de la lista | 358 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Peor caso semana del 09/11 (425 conciertos): imágenes pedidas fuera de la web | 0 |  |  |
| ✅ | Peor caso día 14/11 (113 conciertos): miniaturas de la primera pantalla | 135 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso día 14/11 (113 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 19 pantallas |
| ✅ | Peor caso mes 11/2026 (1431 conciertos), día 07/11: al tocar el día, miniaturas visibles cargadas | 91 | aviso > 1000 ms / fallo > 2500 ms | desde el toque: 1025 ms |

## Fallos

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Enlace a un concierto que ya no existe: lo dice y deja volver | — |  |  |
| ✅ | Detalle que no llega: se ve la ficha básica y avisa | — |  | ‹ Volver La Gorra No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 sábado, 7 de noviembreEmpieza en 7 h 17 min 00:15 h 📍 Honky Tonk Madri |
| ✅ | Fotos que no cargan: sin iconos de imagen rota | 0 |  |  |
| ✅ | Agenda que no llega: mensaje claro para recargar | — |  | No se pudieron cargar los datos (data/concerts.json). Comprueba la conexión y recarga la página. |
| ✅ | Agenda lenta: indica 'Cargando…' y luego se pinta | — |  |  |
| ✅ | Sin taxonomía de estilos: la agenda sigue funcionando | — |  |  |
| ✅ | Sin conexión: la agenda se abre con la copia guardada | 120 | aviso > 4500 ms / fallo > 8000 ms |  |
| ✅ | Sin conexión: se ven los conciertos | — |  |  |
| ✅ | Sin conexión: una ficha no guardada avisa en vez de quedarse cargando | — |  | ‹ Volver Foto: (imagen del anuncio) Hippotraktor No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 jueves, 6 de mayo Hora por confirmar: l |
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
| ✅ | Próximos 10 días: conciertos con enlace de compra directo | 178 de 629 |  | con cartel de gira 165, con hora 531 |
| ✅ | Todo por https (sin contenido mixto) | 0 |  |  |
| ✅ | Miniaturas de las agendas a través del proxy | 0 de 0 |  |  |
| ✅ | Errores en la consola | 0 |  |  |
