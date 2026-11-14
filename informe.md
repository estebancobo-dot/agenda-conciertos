# Validación de la web publicada — 2026-11-14 16:05 UTC

https://estebancobo-dot.github.io/agenda-conciertos/ · código de main 2.55.0 · móvil con 4G lenta y CPU 6x

**162 bien · 4 avisos · 0 fallos**

## Publicación

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Conciertos sin clasificar | 7.4 | aviso > 5 % / fallo > 15 % | 193 de 2619 |
| ⚠️ | Fuentes sin alertas | 2 |  | Total Stage (agenda de la comunidad): lleva 10 días sin leerse bien (último éxito 2026-11-03, daba 461); Revi Live / Revi Space (web oficial): lleva 13 días sin leerse bien (último éxito 2026-10-31, d |
| ✅ | index.html publicado = el de main | — |  |  |
| ✅ | sw.js publicado = el de main | — |  |  |
| ✅ | Datos de la agenda recientes | 19.1 | aviso > 26 h / fallo > 50 h |  |
| ✅ | Conciertos próximos publicados | 2619 |  | mínimo 500 |
| ✅ | Ids únicos | 0 |  |  |
| ✅ | Cada concierto con id, fecha y artista | 0 |  |  |
| ✅ | Conciertos sin sala ni municipio | 0 |  |  |
| ✅ | Conciertos sin sala (la agenda no la dice) | 13 |  | Concierto clausura del 26º Cer (Las Rozas de Madrid), CANCIONES DE NUESTRA VIDA (Boadilla del Monte), Jarana (Madrid), Lunares Flamencos en Libertad (Madrid) |
| ✅ | Imágenes solo por https | 0 |  |  |
| ✅ | Fichero de detalle de cada día | 0 |  |  |
| ✅ | El detalle trae todos los conciertos del día | 0 |  |  |
| ✅ | Detalle y agenda coinciden | 0 |  |  |
| ✅ | Miniaturas y fotos propias servidas | 0 |  |  |
| ✅ | Conciertos próximos sin origen del artista (ni confirmado ni estimado) | 14.4 | aviso > 30 % / fallo > 50 % | 376 de 2619; además 419 deducidos (nombre, grupo local, tributo…) |
| ✅ | Conciertos en 'Otros' (sin género propio) | 0.3 | aviso > 3 % / fallo > 10 % | 8 de 2619 |
| ✅ | Conciertos con etiqueta genérica ("Pop / Rock", "Músicas negras") | 4.6 | aviso > 8 % / fallo > 25 % | 121 de 2619 |
| ✅ | Conciertos sin ningún estilo | 22.1 | aviso > 30 % / fallo > 60 % | 578 de 2619 |
| ✅ | Última lectura completa de las agendas | 19.1 | aviso > 27 h / fallo > 50 h |  |

## Funcional

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Fuente que ya no se puede leer: «sin reconfirmar» en la tarjeta y la ficha | 15 conciertos |  |  |
| ✅ | La cabecera dice cuántos conciertos hay y cuándo se actualizó | 2619 conciertos · actualizado 13 nov, 21:56 |  |  |
| ✅ | Semana: salen justo los conciertos de los datos (con los filtros puestos) | 211 de 211 |  | faltan [] sobran [] días sin pintar 0 |
| ✅ | Semana: todos de esa semana y en orden de fecha | 0 |  |  |
| ✅ | Ficha: artista y sala de los datos | Jam Session Blues |  | esperado 'Jam Session Blues' en 'Moe' |
| ✅ | Ficha: enlaza a sus fuentes | 2 de 2 |  |  |
| ✅ | Filtro de un solo grupo (pop e indie): solo salen de ese grupo | 73 tarjetas |  | 0 de otros grupos |
| ✅ | 'Borrar filtros' deja la agenda sin filtros | — |  |  |
| ✅ | Subgéneros: buscando y marcando dos estilos de géneros distintos salen justo sus conciertos | ['Modern Electric Blues', 'Jangle Pop']: 5 de 5 |  | {'n': 5, 'malos': 0, 'esperados': 5} |
| ✅ | Subgénero «(general)»: salen los del género sin estilo concreto, y solo esos | Rock y metal (general): 210 |  | {'n': 210, 'malos': 0} |
| ✅ | Tributos: su estilo como subgénero (todos tienen uno) | 162 tributos, 33 de rock |  | {'n': 162, 'sin': 0, 'rock': 33, 'ej': []} |
| ✅ | Buscar un artista lo encuentra | Blinduck |  |  |
| ✅ | Buscar encuentra también conciertos de géneros ocultos por el filtro | Rhythm Shakers |  |  |
| ✅ | Filtros de origen: España, Latinoamérica, internacional y sin confirmar cuadran | 2619 de 2619 |  | {'total': 2619, 'es': 1077, 'lat': 103, 'ext': 359, 'nc': 376, 'na': 704, 'otra': 0} |
| ✅ | Mes: la lista del día son los conciertos de ese día | 6 de 6 |  |  |
| ✅ | Ficha: el enlace de compra de la página de entradas es el botón principal | Comprar entradas en DICE ↗ |  | {'ok': True, 'texto': 'Comprar entradas en DICE ↗', 'agotado': False, 'aviso': True} |
| ✅ | A media lista, el menú ☰ se abre a la vista | — |  |  |
| ✅ | A media lista, Filtros abre la hoja sin mover la lista | — |  |  |
| ✅ | A media lista, la lupa abre la búsqueda en la cabecera lista para escribir, sin mover la lista | — |  |  |
| ✅ | Buscar desde media lista y cancelar: vuelve a la misma tarjeta | 39 resultados |  |  |
| ✅ | Festivales: insignia y cartel en la ficha | 'FESTIVAL Santuario Fest 2026': 7 de 7 |  |  |
| ✅ | Teloneros: el concierto sale al filtrar por el género del telonero (y la tarjeta lo dice) | synth y dark wave el 2026-11-14 |  | {'sale': True, 'tag': True} |
| ✅ | Salas: lista, búsqueda, página de la sala con su programación y Volver | 245 salas · Sala El Sol: 127 conciertos · volver a #salas |  | {'nombre': 'Sala El Sol', 'cards': 127, 'esperadas': 127, 'ics': 'calendario/sala-sala-el-sol.ics', 'lateral': 0, 'filtro': ['La Riviera']} |
| ✅ | Calendario de la sala: suscripción (webcal, Google, Outlook) y .ics válido con sus conciertos | 134 eventos en calendario/sala-sala-el-sol.ics |  | ['webcal://estebancobo-dot.github.io/agenda-conciertos/calendario/sala-sala-el-sol.ics', 'https://calendar.google.com/calendar/render?cid=webcal%3A%2F%2Festebancobo-dot.github.io%2Fagenda-conciertos%2 |
| ✅ | Calendarios por género: uno por género y se descargan | 20 géneros · 622 eventos en calendario/genero-rock-y-metal.i |  | {'n': 20, 'ics': 'calendario/genero-rock-y-metal.ics', 'ok': True, 'ev': 622} |
| ✅ | Historial de cambios en la ficha (y aviso en la tarjeta) | 103 conciertos con cambios · 10 novPrecio: 12 € – 14 € → 14  |  | ['10 novPrecio: 12 € – 14 € → 14 € – 18 €', '9 novPrecio: 12 € – 14 € → 14 € – 18 €', '9 novPrecio: 12 € – 14 € → 14 € – 18 €', '9 novPrecio: 12 € – 14 € → 14 € – 18 €', '1 novPrecio: 14 € – 18 € → 12 |
| ✅ | Fin de semana: viernes a domingo de la semana (también al cambiar de año), lo que dicen los datos | 2 de 2 bien |  |  |
| ✅ | Todos: todos los conciertos desde hoy en orden, con su total, pintado progresivo y saltos por meses | 1281 de 2619 conciertos desde hoy · 64 pintados al abrir · 1 |  | {'pintadas': 64, 'orden': True, 'desdeHoy': True, 'n': 1281, 'cab': '1281 de 2619 conciertos desde hoy', 'meses': 7, 'lateral': 0, 'salto': {'mes': '2026-12', 'dia': '2026-12-01', 'marcado': True}} |
| ✅ | Confirmación: nivel y motivos en la ficha; filtro 'Solo confirmados' | 867 confirmados · 1264 probables · 488 sin confirmar · ficha |  | {'con': 2619, 'n': 76, 'c': 867, 'p': 1264, 's': 488, 'bien': True} |
| ✅ | Estado de estilo y origen en la ficha (sin etiqueta si es un dato conocido) y recuento en Fuentes (N3/N4) | ficha: datos conocidos · ['Estilo', 'Dato conocido: 1927'] |  | Datos de cada concierto
Estilo
Dato conocido: 1927
Estimado: 232
No aplica: 399
No encontrado: 218
Origen
Dato conocido: 1113
Estimado: 521
No aplica: 720
No encontrado: 422
Hora
Dato conocido: 2346
E |
| ✅ | Conflicto de fecha en la tarjeta y la ficha | 2 fechas |  | ⚠ Las webs no coinciden
Fecha
lunes, 16 de noviembre
4 webs: conciertos.club, La Ganzúa, Songkick Madrid
domingo, 15 de noviembre
1 web: Movistar Arena
La web oficial de la sala lo anuncia otro día. C |
| ✅ | Nivel del concierto: «gran formato» en la tarjeta y nivel con su porqué en la ficha | 148 de gran formato · 'Movistar Arena: gran recinto · Yandel |  |  |
| ✅ | Fase B: guardar en Mis conciertos (★), Novedades y artistas similares | guardado y en la lista: True · ★: 1 · 13 conciertos nuevos · |  |  |
| ✅ | Informe se abre | — |  |  |
| ✅ | Paso de días, semanas, meses y años (con cambios de hora y febrero) con las flechas | 103 de 103 pasos bien |  |  |
| ✅ | Enlace directo a una ficha la abre | Camo & Krooked |  |  |
| ✅ | Peor caso semana del 16/11 (432 conciertos): con 'Todos' salen todos | 432 de 432 |  |  |

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
| ✅ | Por defecto se dice cuántos conciertos de otros géneros quedan ocultos, con un botón para verlos | 1338 conciertos más de otros géneros (jazz, flamenco, soul,  |  |  |
| ✅ | Búsqueda sin resultados lo dice | — |  |  |
| ✅ | La barra dice que se está buscando | Filtrando: búsqueda «Leiva» · Quitar filtros · Compartir |  |  |
| ✅ | La búsqueda se ve dentro de la hoja de filtros | — |  |  |
| ✅ | 'Todos' (grupos) no borra la búsqueda a escondidas | — |  |  |
| ✅ | 'Borrar filtros' en la hoja quita también la búsqueda | — |  |  |
| ✅ | El cuadro de búsqueda queda vacío al borrar | — |  |  |
| ✅ | Mes: al tocar un día, su lista queda a la vista | — |  |  |
| ✅ | Semana: al bajar, la fecha completa del día se queda fija arriba | Viernes, 13 de noviembre57 conciertos |  | {'pegada': True, 'fecha': '2026-11-13', 'texto': 'Viernes, 13 de noviembre57 conciertos', 'marcado': '2026-11-13', 'alto': 170} |
| ✅ | Semana: la tira de días marca el día por el que vas | 2026-11-13 / 2026-11-13 |  |  |
| ✅ | Semana: lo fijo arriba (cabecera, tira y fecha) no ocupa más de un tercio de la pantalla | 210 | aviso > 281 px / fallo > 422 px |  |
| ✅ | Semana: tocar un día de la tira lleva justo a ese día | 2026-11-15 (pedido 2026-11-15) |  | {'pegada': True, 'fecha': '2026-11-15', 'texto': 'Mañana, domingo, 15 de noviembre25 conciertos', 'marcado': '2026-11-15', 'alto': 170} |
| ✅ | Día: al bajar, la fecha completa se queda fija arriba con la tira de días | Hoy, sábado, 14 de noviembre64 conciertos |  | {'pegada': True, 'fecha': '2026-11-14', 'texto': 'Hoy, sábado, 14 de noviembre64 conciertos', 'marcado': '2026-11-14', 'alto': 170} |
| ✅ | Mes: al bajar por la lista del día, su fecha completa se queda fija arriba | Hoy, sábado, 14 de noviembre64 conciertos |  | {'pegada': True, 'fecha': '2026-11-14', 'texto': 'Hoy, sábado, 14 de noviembre64 conciertos', 'marcado': None, 'alto': 109} |
| ✅ | Al bajar por la lista, Buscar y Filtros siguen a mano en la cabecera (y arriba no se duplican) | — |  |  |
| ✅ | A media lista, ‹ semana › en la cabecera: pasa a la siguiente y deja su primer día a la vista | 2026-11-16 · '16–22 nov\n212 conciertos' |  | {'fecha': '2026-11-16', 'fija': True, 'titulo': '16–22 nov\n212 conciertos', 'cabecera': True} |
| ✅ | Cambiar de día, semana o mes desde media lista deja la vista nueva desde su principio; Hoy siempre a mano | 10 de 10 casos bien |  |  |
| ✅ | Fuentes: una tarjeta por web con estado, 14 días y datos; filtros y búsqueda; sin scroll lateral | 83 de 83 webs · 32 salas · 66 salas sin web leída |  | {'n': 32, 'total': 83, 'tiras': 83, 'metricas': 83, 'lateral': 0, 'salas': 66, 'bien': True, 'esperadas': 32, 'busca': True} |
| ✅ | Saltos de diseño (CLS) | 0 | aviso > 0.1  / fallo > 0.25  |  |
| ✅ | Semana sin conciertos: lo dice | — |  |  |
| ✅ | Peor caso semana del 16/11 (432 conciertos): volver deja la lista en el concierto | — |  |  |
| ✅ | Sin scroll lateral (móvil pequeño 320 px) | 0 |  | 0 px de más |
| ✅ | Botones con tamaño de dedo (≥ 32 px) | 0 |  |  |
| ✅ | Contraste de color suficiente (modo claro) | 0 |  |  |
| ✅ | Accesibilidad (axe-core): otros problemas graves (modo claro) | 0 |  |  |
| ✅ | Sin scroll lateral (ordenador 1366 px) | 0 |  | 0 px de más |
| ✅ | Sin scroll lateral (móvil en modo oscuro) | 0 |  | 0 px de más |
| ✅ | Modo oscuro: fondo oscuro | 22 |  |  |
| ✅ | Contraste de color suficiente (modo oscuro) | 0 |  |  |
| ✅ | Accesibilidad (axe-core): otros problemas graves (modo oscuro) | 0 |  |  |
| ✅ | Modos de vista: lista, compacta y cuadrícula; la compacta enseña más conciertos; se recuerda al volver | lista: 2 · compacta: 5 · cuadricula: 2 en pantalla · guardad |  | {'lista': {'bien': True, 'enPantalla': 2}, 'compacta': {'bien': True, 'enPantalla': 5}, 'cuadricula': {'bien': True, 'enPantalla': 2}} |
| ✅ | Ordenador: la ficha se abre al lado de la lista (la lista sigue a la vista) y Escape la cierra | al lado · cerrada |  | {'hash': '#semana/2026-11-09', 'lado': True, 'marcado': True, 'lateral': 0} |

## Rendimiento

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Conciertos con miniatura propia (servida desde la web) | 100.0 |  | de 2114 con imagen; mínimo 97 % |
| ✅ | Conciertos con foto de ficha propia (servida desde la web) | 100.0 |  | de 2114 con imagen; mínimo 97 % |
| ✅ | Primera visita: datos y lista pintados | 3530 | aviso > 5000 ms / fallo > 8000 ms |  |
| ✅ | Primera visita: LCP | 3576 | aviso > 4000 ms / fallo > 6000 ms |  |
| ✅ | Primera visita: KB descargados | 469 | aviso > 1500 KB / fallo > 3000 KB |  |
| ✅ | Bajar despacio: miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas |  |
| ✅ | Bajar deprisa: al parar, miniaturas visibles cargadas en | 39 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Cambiar de semana (mediana de 3) | 183 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Abrir ficha desde la lista (datos) | 295 | aviso > 500 ms / fallo > 1500 ms |  |
| ✅ | Ficha completa (fuentes y precio) | 307 | aviso > 1500 ms / fallo > 4000 ms |  |
| ✅ | Foto de la ficha tras ver la lista 2 s (mediana) | 152 | aviso > 600 ms / fallo > 1500 ms |  |
| ✅ | Fichas cuya foto ya estaba descargada al abrir | 5 |  | 5 de 5 |
| ✅ | Ficha lejana (otros): datos | 145 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (otros): foto | 150 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (wikimedia): datos | 74 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (wikimedia): foto | 90 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (discogs): datos | 113 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (discogs): foto | 120 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (sin foto): datos | 48 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (conciertos.club): datos | 90 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (conciertos.club): foto | 102 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (madridenvivo): datos | 90 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (madridenvivo): foto | 111 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Filtros: abrir la hoja | 221 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: 'Ninguno' | 92 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: aplicar | 151 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: borrar filtros | 195 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: 'Los de siempre' | 74 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: chip de grupo | 155 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Vista mes | 142 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Todos: pintar la lista | 147 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Segunda visita: lista pintada | 733 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Segunda visita: miniaturas visibles cargadas | 92 | aviso > 800 ms / fallo > 2500 ms |  |
| ✅ | Bloqueo de JavaScript más largo (CPU 6x) | 179 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Imágenes que no cargan | 0.0 | aviso > 1 % / fallo > 5 % |  |
| ✅ | Enlace directo a una ficha (visita nueva) | 3522 | aviso > 5000 ms / fallo > 9000 ms |  |
| ✅ | Vista día sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 16 | aviso > 1000 ms / fallo > 2500 ms | [3, 16, 7] |
| ✅ | Vista mes sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 7 | aviso > 1000 ms / fallo > 2500 ms | [7, 5, 6] |
| ✅ | Ficha sin caché: foto desde que se ve la ficha (peor de 4 al azar) | 104 | aviso > 1200 ms / fallo > 2500 ms | [70, 104, 84, 52] ['estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io'] |
| ✅ | Imágenes de las listas pedidas fuera de la web (wsrv.nl, agendas) | 0 |  |  |
| ✅ | Peor caso semana del 16/11 (432 conciertos): pintar con 'Todos' | 222 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Peor caso semana del 16/11 (432 conciertos): miniaturas de la primera pantalla | 27 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 16/11 (432 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 70 pantallas; peores [0, 0, 0]; pantallas con alguna sin cargar: 0 |
| ✅ | Peor caso semana del 16/11 (432 conciertos): bloqueo de JavaScript más largo al bajar | 0 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Peor caso semana del 16/11 (432 conciertos): bajando seguido, miniaturas a la vista sin cargar | 0.0 | aviso > 5 % / fallo > 15 % | 0 de 328 vistas en 12 s |
| ✅ | Peor caso semana del 16/11 (432 conciertos): bajando deprisa, al parar miniaturas visibles cargadas en | 85 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 16/11 (432 conciertos): foto de una ficha del final de la lista | 300 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Peor caso semana del 16/11 (432 conciertos): imágenes pedidas fuera de la web | 0 |  |  |
| ✅ | Peor caso día 14/11 (115 conciertos): miniaturas de la primera pantalla | 91 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso día 14/11 (115 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 20 pantallas |
| ✅ | Peor caso mes 11/2026 (1020 conciertos), día 21/11: al tocar el día, miniaturas visibles cargadas | 72 | aviso > 1000 ms / fallo > 2500 ms | desde el toque: 960 ms |

## Fallos

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Enlace a un concierto que ya no existe: lo dice y deja volver | — |  |  |
| ✅ | Detalle que no llega: se ve la ficha básica y avisa | — |  | ‹ Volver LD Foto: (imagen del anuncio) LITTLE DEVILS No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 sábado, 14 de noviembreEmpieza en 7 |
| ✅ | Fotos que no cargan: sin iconos de imagen rota | 0 |  |  |
| ✅ | Agenda que no llega: mensaje claro para recargar | — |  | No se pudieron cargar los datos (data/concerts.json). Comprueba la conexión y recarga la página. |
| ✅ | Agenda lenta: indica 'Cargando…' y luego se pinta | — |  |  |
| ✅ | Sin taxonomía de estilos: la agenda sigue funcionando | — |  |  |
| ✅ | Sin conexión: la agenda se abre con la copia guardada | 97 | aviso > 4500 ms / fallo > 8000 ms |  |
| ✅ | Sin conexión: se ven los conciertos | — |  |  |
| ✅ | Sin conexión: una ficha no guardada avisa en vez de quedarse cargando | — |  | ‹ Volver Foto: (imagen del anuncio) Scorpions No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 sábado, 8 de mayo Hora sin indicar 📍 Movis |
| ✅ | Errores de JavaScript en todo el recorrido | 0 |  |  |

## Seguridad

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | La web declara su política de seguridad del contenido | — |  |  |
| ✅ | La política no bloquea nada de la propia web | 0 |  |  |

## Otros

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Enlaces a las fuentes responden | 2 |  | https://madridenvivo.com/evento/conciertos-de-micro-abierto-cantautor-12/ (404); https://madridenvivo.com/evento/thundercat-pop-rock-3/ (404) |
| ✅ | Próximos 10 días: conciertos con enlace de compra directo | 192 de 630 |  | con cartel de gira 212, con hora 526 |
| ✅ | Todo por https (sin contenido mixto) | 0 |  |  |
| ✅ | Miniaturas de las agendas a través del proxy | 0 de 0 |  |  |
| ✅ | Errores en la consola | 0 |  |  |
