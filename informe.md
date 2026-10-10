# Validación de la web publicada — 2026-10-10 19:55 UTC

https://estebancobo-dot.github.io/agenda-conciertos/ · código de main 2.55.0 · móvil con 4G lenta y CPU 6x

**163 bien · 3 avisos · 0 fallos**

## Publicación

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Conciertos sin clasificar | 7.3 | aviso > 5 % / fallo > 15 % | 217 de 2973 |
| ⚠️ | Fuentes sin alertas | 1 |  | Sala Villanos (web oficial): su robots.txt ya no permite leerla (último éxito 2026-10-01, daba 99): se respeta; sus conciertos salen de su última lectura y de otras agendas, y de su venta de entradas  |
| ✅ | index.html publicado = el de main | — |  |  |
| ✅ | sw.js publicado = el de main | — |  |  |
| ✅ | Datos de la agenda recientes | 3.8 | aviso > 26 h / fallo > 50 h |  |
| ✅ | Conciertos próximos publicados | 2973 |  | mínimo 500 |
| ✅ | Ids únicos | 0 |  |  |
| ✅ | Cada concierto con id, fecha y artista | 0 |  |  |
| ✅ | Conciertos sin sala ni municipio | 0 |  |  |
| ✅ | Conciertos sin sala (la agenda no la dice) | 19 |  | XXIII MÚSICA ANTIGUA ARANJUEZ. (Aranjuez), ENCUENTRO CORAL INTERNACIONAL  (Collado Villalba), XXIII MÚSICA ANTIGUA ARANJUEZ. (Aranjuez), FAHMI ALQHI (Aranjuez) |
| ✅ | Imágenes solo por https | 0 |  |  |
| ✅ | Fichero de detalle de cada día | 0 |  |  |
| ✅ | El detalle trae todos los conciertos del día | 0 |  |  |
| ✅ | Detalle y agenda coinciden | 0 |  |  |
| ✅ | Miniaturas y fotos propias servidas | 0 |  |  |
| ✅ | Conciertos próximos sin origen del artista (ni confirmado ni estimado) | 14.8 | aviso > 30 % / fallo > 50 % | 439 de 2973; además 464 deducidos (nombre, grupo local, tributo…) |
| ✅ | Conciertos en 'Otros' (sin género propio) | 0.3 | aviso > 3 % / fallo > 10 % | 8 de 2973 |
| ✅ | Conciertos con etiqueta genérica ("Pop / Rock", "Músicas negras") | 4.7 | aviso > 8 % / fallo > 25 % | 141 de 2973 |
| ✅ | Conciertos sin ningún estilo | 21.2 | aviso > 30 % / fallo > 60 % | 631 de 2973 |
| ✅ | Última lectura completa de las agendas | 3.8 | aviso > 27 h / fallo > 50 h |  |

## Funcional

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | La cabecera dice cuántos conciertos hay y cuándo se actualizó | 2973 conciertos · actualizado 10 oct, 18:07 |  |  |
| ✅ | Semana: salen justo los conciertos de los datos (con los filtros puestos) | 201 de 201 |  | faltan [] sobran [] días sin pintar 0 |
| ✅ | Semana: todos de esa semana y en orden de fecha | 0 |  |  |
| ✅ | Ficha: artista y sala de los datos | AMALIA TOBOSO |  | esperado 'AMALIA TOBOSO' en 'Jazzville' |
| ✅ | Ficha: enlaza a sus fuentes | 1 de 1 |  |  |
| ✅ | Filtro de un solo grupo (pop e indie): solo salen de ese grupo | 71 tarjetas |  | 0 de otros grupos |
| ✅ | 'Borrar filtros' deja la agenda sin filtros | — |  |  |
| ✅ | Subgéneros: buscando y marcando dos estilos de géneros distintos salen justo sus conciertos | ['Bluegrass', 'Speed Metal']: 5 de 5 |  | {'n': 5, 'malos': 0, 'esperados': 5} |
| ✅ | Subgénero «(general)»: salen los del género sin estilo concreto, y solo esos | Rock y metal (general): 272 |  | {'n': 272, 'malos': 0} |
| ✅ | Tributos: su estilo como subgénero (todos tienen uno) | 192 tributos, 38 de rock |  | {'n': 192, 'sin': 0, 'rock': 38, 'ej': []} |
| ✅ | Buscar un artista lo encuentra | EUROPE 40 ANIVERSARIO |  |  |
| ✅ | Buscar encuentra también conciertos de géneros ocultos por el filtro | VERSIONA-T (BY KIRAZ) |  |  |
| ✅ | Filtros de origen: España, Latinoamérica, internacional y sin confirmar cuadran | 2973 de 2973 |  | {'total': 2973, 'es': 1183, 'lat': 132, 'ext': 488, 'nc': 439, 'na': 731, 'otra': 0} |
| ✅ | Mes: la lista del día son los conciertos de ese día | 46 de 46 |  |  |
| ✅ | Ficha: el enlace de compra de la página de entradas es el botón principal | Comprar entradas en Notikumi ↗ |  | {'ok': True, 'texto': 'Comprar entradas en Notikumi ↗', 'agotado': False, 'aviso': True} |
| ✅ | A media lista, el menú ☰ se abre a la vista | — |  |  |
| ✅ | A media lista, Filtros abre la hoja sin mover la lista | — |  |  |
| ✅ | A media lista, la lupa abre la búsqueda en la cabecera lista para escribir, sin mover la lista | — |  |  |
| ✅ | Buscar desde media lista y cancelar: vuelve a la misma tarjeta | 47 resultados |  |  |
| ✅ | Festivales: insignia y cartel en la ficha | 'FESTIVAL Molded in Blackness Fest': 2 de 2 |  |  |
| ✅ | Teloneros: el concierto sale al filtrar por el género del telonero (y la tarjeta lo dice) | synth y dark wave el 2026-10-10 |  | {'sale': True, 'tag': True} |
| ✅ | Salas: lista, búsqueda, página de la sala con su programación y Volver | 257 salas · Sala El Sol: 111 conciertos · volver a #salas |  | {'nombre': 'Sala El Sol', 'cards': 111, 'esperadas': 111, 'ics': 'calendario/sala-sala-el-sol.ics', 'lateral': 0, 'filtro': ['La Riviera']} |
| ✅ | Calendario de la sala: suscripción (webcal, Google, Outlook) y .ics válido con sus conciertos | 119 eventos en calendario/sala-sala-el-sol.ics |  | ['webcal://estebancobo-dot.github.io/agenda-conciertos/calendario/sala-sala-el-sol.ics', 'https://calendar.google.com/calendar/render?cid=webcal%3A%2F%2Festebancobo-dot.github.io%2Fagenda-conciertos%2 |
| ✅ | Calendarios por género: uno por género y se descargan | 20 géneros · 695 eventos en calendario/genero-rock-y-metal.i |  | {'n': 20, 'ics': 'calendario/genero-rock-y-metal.ics', 'ok': True, 'ev': 695} |
| ✅ | Historial de cambios en la ficha (y aviso en la tarjeta) | 150 conciertos con cambios · 4 octPrecio: desde 49,24 € → 49 |  | ['4 octPrecio: desde 49,24 € → 49€', '29 septAparece en la agenda'] |
| ✅ | Fin de semana: viernes a domingo de la semana (también al cambiar de año), lo que dicen los datos | 2 de 2 bien |  |  |
| ✅ | Todos: todos los conciertos desde hoy en orden, con su total, pintado progresivo y saltos por meses | 1507 de 2973 conciertos desde hoy · 51 pintados al abrir · 1 |  | {'pintadas': 51, 'orden': True, 'desdeHoy': True, 'n': 1507, 'cab': '1507 de 2973 conciertos desde hoy', 'meses': 7, 'lateral': 0, 'salto': {'mes': '2026-11', 'dia': '2026-11-01', 'marcado': True}} |
| ✅ | Confirmación: nivel y motivos en la ficha; filtro 'Solo confirmados' | 1208 confirmados · 1323 probables · 442 sin confirmar · fich |  | {'con': 2973, 'n': 80, 'c': 1208, 'p': 1323, 's': 442, 'bien': True} |
| ✅ | Estado de estilo y origen en la ficha (sin etiqueta si es un dato conocido) y recuento en Fuentes (N3/N4) | ficha: ['No encontrado'] · ['Estilo', 'Dato conocido: 2231'] |  | Datos de cada concierto
Estilo
Dato conocido: 2231
Estimado: 302
No aplica: 262
No encontrado: 244
Origen
Dato conocido: 1272
Estimado: 552
No aplica: 735
No encontrado: 480
Hora
Dato conocido: 2638
E |
| ✅ | Conflicto de fecha en la tarjeta y la ficha | 2 fechas |  | ⚠ Las webs no coinciden
Fecha
sábado, 7 de noviembre
3 webs: conciertos.club
domingo, 8 de noviembre
1 web: Sala But
La web oficial de la sala lo anuncia otro día. Confírmalo allí antes de ir. |
| ✅ | Fuente que ya no se puede leer: «sin reconfirmar» en la tarjeta y la ficha | 20 conciertos |  |  |
| ✅ | Nivel del concierto: «gran formato» en la tarjeta y nivel con su porqué en la ficha | 164 de gran formato · 'La Nueva Cubierta: gran recinto' |  |  |
| ✅ | Fase B: guardar en Mis conciertos (★), Novedades y artistas similares | guardado y en la lista: True · ★: 1 · 56 conciertos nuevos · |  |  |
| ✅ | Informe se abre | — |  |  |
| ✅ | Paso de días, semanas, meses y años (con cambios de hora y febrero) con las flechas | 103 de 103 pasos bien |  |  |
| ✅ | Enlace directo a una ficha la abre | NOCHE DE HALLOWEN dela mano de ANDRES DUENDE |  |  |
| ✅ | Peor caso semana del 12/10 (394 conciertos): con 'Todos' salen todos | 394 de 394 |  |  |

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
| ✅ | Por defecto se dice cuántos conciertos de otros géneros quedan ocultos, con un botón para verlos | 1466 conciertos más de otros géneros (jazz, flamenco, soul,  |  |  |
| ✅ | Búsqueda sin resultados lo dice | — |  |  |
| ✅ | La barra dice que se está buscando | Filtrando: búsqueda «Leiva» · Quitar filtros · Compartir |  |  |
| ✅ | La búsqueda se ve dentro de la hoja de filtros | — |  |  |
| ✅ | 'Todos' (grupos) no borra la búsqueda a escondidas | — |  |  |
| ✅ | 'Borrar filtros' en la hoja quita también la búsqueda | — |  |  |
| ✅ | El cuadro de búsqueda queda vacío al borrar | — |  |  |
| ✅ | Mes: al tocar un día, su lista queda a la vista | — |  |  |
| ✅ | Semana: al bajar, la fecha completa del día se queda fija arriba | Viernes, 9 de octubre57 conciertos |  | {'pegada': True, 'fecha': '2026-10-09', 'texto': 'Viernes, 9 de octubre57 conciertos', 'marcado': '2026-10-09', 'alto': 170} |
| ✅ | Semana: la tira de días marca el día por el que vas | 2026-10-09 / 2026-10-09 |  |  |
| ✅ | Semana: lo fijo arriba (cabecera, tira y fecha) no ocupa más de un tercio de la pantalla | 210 | aviso > 281 px / fallo > 422 px |  |
| ✅ | Semana: tocar un día de la tira lleva justo a ese día | 2026-10-11 (pedido 2026-10-11) |  | {'pegada': True, 'fecha': '2026-10-11', 'texto': 'Mañana, domingo, 11 de octubre28 conciertos', 'marcado': '2026-10-11', 'alto': 170} |
| ✅ | Día: al bajar, la fecha completa se queda fija arriba con la tira de días | Viernes, 9 de octubre57 conciertos |  | {'pegada': True, 'fecha': '2026-10-09', 'texto': 'Viernes, 9 de octubre57 conciertos', 'marcado': '2026-10-09', 'alto': 170} |
| ✅ | Mes: al bajar por la lista del día, su fecha completa se queda fija arriba | Viernes, 9 de octubre57 conciertos |  | {'pegada': True, 'fecha': '2026-10-09', 'texto': 'Viernes, 9 de octubre57 conciertos', 'marcado': None, 'alto': 109} |
| ✅ | Al bajar por la lista, Buscar y Filtros siguen a mano en la cabecera (y arriba no se duplican) | — |  |  |
| ✅ | A media lista, ‹ semana › en la cabecera: pasa a la siguiente y deja su primer día a la vista | 2026-10-12 · '12–18 oct\n217 conciertos' |  | {'fecha': '2026-10-12', 'fija': True, 'titulo': '12–18 oct\n217 conciertos', 'cabecera': True} |
| ✅ | Cambiar de día, semana o mes desde media lista deja la vista nueva desde su principio; Hoy siempre a mano | 10 de 10 casos bien |  |  |
| ✅ | Fuentes: una tarjeta por web con estado, 14 días y datos; filtros y búsqueda; sin scroll lateral | 83 de 83 webs · 33 salas · 65 salas sin web leída |  | {'n': 33, 'total': 83, 'tiras': 83, 'metricas': 83, 'lateral': 0, 'salas': 65, 'bien': True, 'esperadas': 33, 'busca': True} |
| ✅ | Saltos de diseño (CLS) | 0 | aviso > 0.1  / fallo > 0.25  |  |
| ✅ | Semana sin conciertos: lo dice | — |  |  |
| ✅ | Peor caso semana del 12/10 (394 conciertos): volver deja la lista en el concierto | — |  |  |
| ✅ | Sin scroll lateral (móvil pequeño 320 px) | 0 |  | 0 px de más |
| ✅ | Botones con tamaño de dedo (≥ 32 px) | 0 |  |  |
| ✅ | Contraste de color suficiente (modo claro) | 0 |  |  |
| ✅ | Accesibilidad (axe-core): otros problemas graves (modo claro) | 0 |  |  |
| ✅ | Sin scroll lateral (ordenador 1366 px) | 0 |  | 0 px de más |
| ✅ | Sin scroll lateral (móvil en modo oscuro) | 0 |  | 0 px de más |
| ✅ | Modo oscuro: fondo oscuro | 22 |  |  |
| ✅ | Contraste de color suficiente (modo oscuro) | 0 |  |  |
| ✅ | Accesibilidad (axe-core): otros problemas graves (modo oscuro) | 0 |  |  |
| ✅ | Modos de vista: lista, compacta y cuadrícula; la compacta enseña más conciertos; se recuerda al volver | lista: 3 · compacta: 4 · cuadricula: 2 en pantalla · guardad |  | {'lista': {'bien': True, 'enPantalla': 3}, 'compacta': {'bien': True, 'enPantalla': 4}, 'cuadricula': {'bien': True, 'enPantalla': 2}} |
| ✅ | Ordenador: la ficha se abre al lado de la lista (la lista sigue a la vista) y Escape la cierra | al lado · cerrada |  | {'hash': '#semana/2026-10-05', 'lado': True, 'marcado': True, 'lateral': 0} |

## Rendimiento

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Conciertos con miniatura propia (servida desde la web) | 100.0 |  | de 2370 con imagen; mínimo 97 % |
| ✅ | Conciertos con foto de ficha propia (servida desde la web) | 100.0 |  | de 2370 con imagen; mínimo 97 % |
| ✅ | Primera visita: datos y lista pintados | 3143 | aviso > 5000 ms / fallo > 8000 ms |  |
| ✅ | Primera visita: LCP | 3224 | aviso > 4000 ms / fallo > 6000 ms |  |
| ✅ | Primera visita: KB descargados | 371 | aviso > 1500 KB / fallo > 3000 KB |  |
| ✅ | Bajar despacio: miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas |  |
| ✅ | Bajar deprisa: al parar, miniaturas visibles cargadas en | 75 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Cambiar de semana (mediana de 3) | 273 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Abrir ficha desde la lista (datos) | 188 | aviso > 500 ms / fallo > 1500 ms |  |
| ✅ | Ficha completa (fuentes y precio) | 195 | aviso > 1500 ms / fallo > 4000 ms |  |
| ✅ | Foto de la ficha tras ver la lista 2 s (mediana) | 169 | aviso > 600 ms / fallo > 1500 ms |  |
| ✅ | Fichas cuya foto ya estaba descargada al abrir | 5 |  | 5 de 5 |
| ✅ | Ficha lejana (wikimedia): datos | 228 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (wikimedia): foto | 237 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (conciertos.club): datos | 58 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (conciertos.club): foto | 62 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (discogs): datos | 118 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (discogs): foto | 123 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (sin foto): datos | 40 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (otros): datos | 65 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (otros): foto | 114 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (madridenvivo): datos | 175 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (madridenvivo): foto | 195 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Filtros: abrir la hoja | 297 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: 'Ninguno' | 115 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: aplicar | 212 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: borrar filtros | 233 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: 'Los de siempre' | 93 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: chip de grupo | 184 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Vista mes | 195 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Todos: pintar la lista | 190 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Segunda visita: lista pintada | 1113 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Segunda visita: miniaturas visibles cargadas | 83 | aviso > 800 ms / fallo > 2500 ms |  |
| ✅ | Bloqueo de JavaScript más largo (CPU 6x) | 256 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Imágenes que no cargan | 0.0 | aviso > 1 % / fallo > 5 % |  |
| ✅ | Enlace directo a una ficha (visita nueva) | 3232 | aviso > 5000 ms / fallo > 9000 ms |  |
| ✅ | Vista día sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 5 | aviso > 1000 ms / fallo > 2500 ms | [4, 4, 5] |
| ✅ | Vista mes sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 6 | aviso > 1000 ms / fallo > 2500 ms | [6, 5, 4] |
| ✅ | Ficha sin caché: foto desde que se ve la ficha (peor de 4 al azar) | 118 | aviso > 1200 ms / fallo > 2500 ms | [108, 118, 68, 88] ['estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io'] |
| ✅ | Imágenes de las listas pedidas fuera de la web (wsrv.nl, agendas) | 0 |  |  |
| ✅ | Peor caso semana del 12/10 (394 conciertos): pintar con 'Todos' | 319 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Peor caso semana del 12/10 (394 conciertos): miniaturas de la primera pantalla | 43 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 12/10 (394 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 63 pantallas; peores [0, 0, 0]; pantallas con alguna sin cargar: 0 |
| ✅ | Peor caso semana del 12/10 (394 conciertos): bloqueo de JavaScript más largo al bajar | 0 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Peor caso semana del 12/10 (394 conciertos): bajando seguido, miniaturas a la vista sin cargar | 0.0 | aviso > 5 % / fallo > 15 % | 0 de 345 vistas en 12 s |
| ✅ | Peor caso semana del 12/10 (394 conciertos): bajando deprisa, al parar miniaturas visibles cargadas en | 158 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 12/10 (394 conciertos): foto de una ficha del final de la lista | 280 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Peor caso semana del 12/10 (394 conciertos): imágenes pedidas fuera de la web | 0 |  |  |
| ✅ | Peor caso día 10/10 (104 conciertos): miniaturas de la primera pantalla | 129 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso día 10/10 (104 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 17 pantallas |
| ✅ | Peor caso mes 10/2026 (1231 conciertos), día 16/10: al tocar el día, miniaturas visibles cargadas | 95 | aviso > 1000 ms / fallo > 2500 ms | desde el toque: 1038 ms |

## Fallos

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Enlace a un concierto que ya no existe: lo dice y deja volver | — |  |  |
| ✅ | Detalle que no llega: se ve la ficha básica y avisa | — |  | ‹ Volver VERSIONA-T (BY KIRAZ) No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 sábado, 10 de octubreEmpieza en 2 h 32 min 00:30 h 📍 Honk |
| ✅ | Fotos que no cargan: sin iconos de imagen rota | 0 |  |  |
| ✅ | Agenda que no llega: mensaje claro para recargar | — |  | No se pudieron cargar los datos (data/concerts.json). Comprueba la conexión y recarga la página. |
| ✅ | Agenda lenta: indica 'Cargando…' y luego se pinta | — |  |  |
| ✅ | Sin taxonomía de estilos: la agenda sigue funcionando | — |  |  |
| ✅ | Sin conexión: la agenda se abre con la copia guardada | 109 | aviso > 4500 ms / fallo > 8000 ms |  |
| ✅ | Sin conexión: se ven los conciertos | — |  |  |
| ✅ | Sin conexión: una ficha no guardada avisa en vez de quedarse cargando | — |  | ‹ Volver Foto: (imagen del anuncio) Thirty Seconds To Mars No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 jueves, 8 de abril 21:00 h 📍  |
| ✅ | Errores de JavaScript en todo el recorrido | 0 |  |  |

## Seguridad

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | La web declara su política de seguridad del contenido | — |  |  |
| ✅ | La política no bloquea nada de la propia web | 0 |  |  |

## Otros

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Enlaces a las fuentes responden | 2 |  | https://madridenvivo.com/evento/fun-house-conciertos-8/ (404); https://www.tixxlab.com/eventDetails/421 (Error) |
| ✅ | Próximos 10 días: conciertos con enlace de compra directo | 158 de 576 |  | con cartel de gira 149, con hora 493 |
| ✅ | Todo por https (sin contenido mixto) | 0 |  |  |
| ✅ | Miniaturas de las agendas a través del proxy | 0 de 0 |  |  |
| ✅ | Errores en la consola | 0 |  |  |
