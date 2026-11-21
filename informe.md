# Validación de la web publicada — 2026-11-21 12:12 UTC

https://estebancobo-dot.github.io/agenda-conciertos/ · código de main 2.55.0 · móvil con 4G lenta y CPU 6x

**163 bien · 2 avisos · 0 fallos**

## Publicación

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ⚠️ | Conciertos sin sala (la agenda no la dice) | 32 |  | Lunares Flamencos en Libertad (Madrid), Plaza de Cascorro (Madrid), Concierto "Melodías inolvidabl (Majadahonda), Red Zone / King Crimson (Madrid) |
| ⚠️ | Conciertos sin clasificar | 10.2 | aviso > 5 % / fallo > 15 % | 279 de 2733 |
| ✅ | index.html publicado = el de main | — |  |  |
| ✅ | sw.js publicado = el de main | — |  |  |
| ✅ | Datos de la agenda recientes | 0.1 | aviso > 26 h / fallo > 50 h |  |
| ✅ | Conciertos próximos publicados | 2733 |  | mínimo 500 |
| ✅ | Ids únicos | 0 |  |  |
| ✅ | Cada concierto con id, fecha y artista | 0 |  |  |
| ✅ | Conciertos sin sala ni municipio | 0 |  |  |
| ✅ | Imágenes solo por https | 0 |  |  |
| ✅ | Fichero de detalle de cada día | 0 |  |  |
| ✅ | El detalle trae todos los conciertos del día | 0 |  |  |
| ✅ | Detalle y agenda coinciden | 0 |  |  |
| ✅ | Miniaturas y fotos propias servidas | 0 |  |  |
| ✅ | Conciertos próximos sin origen del artista (ni confirmado ni estimado) | 15.5 | aviso > 30 % / fallo > 50 % | 423 de 2733; además 530 deducidos (nombre, grupo local, tributo…) |
| ✅ | Conciertos en 'Otros' (sin género propio) | 0.5 | aviso > 3 % / fallo > 10 % | 14 de 2733 |
| ✅ | Conciertos con etiqueta genérica ("Pop / Rock", "Músicas negras") | 5.7 | aviso > 8 % / fallo > 25 % | 156 de 2733 |
| ✅ | Conciertos sin ningún estilo | 23.6 | aviso > 30 % / fallo > 60 % | 644 de 2733 |
| ✅ | Última lectura completa de las agendas | 0.1 | aviso > 27 h / fallo > 50 h |  |
| ✅ | Fuentes sin alertas | 0 |  |  |

## Funcional

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | La cabecera dice cuántos conciertos hay y cuándo se actualizó | 2733 conciertos · actualizado 21 nov, 13:07 |  |  |
| ✅ | Semana: salen justo los conciertos de los datos (con los filtros puestos) | 233 de 233 |  | faltan [] sobran [] días sin pintar 0 |
| ✅ | Semana: todos de esa semana y en orden de fecha | 0 |  |  |
| ✅ | Ficha: artista y sala de los datos | Jam Session Blues |  | esperado 'Jam Session Blues' en 'Moe' |
| ✅ | Ficha: enlaza a sus fuentes | 2 de 2 |  |  |
| ✅ | Filtro de un solo grupo (sin clasificar): solo salen de ese grupo | 48 tarjetas |  | 0 de otros grupos |
| ✅ | 'Borrar filtros' deja la agenda sin filtros | — |  |  |
| ✅ | Subgéneros: buscando y marcando dos estilos de géneros distintos salen justo sus conciertos | ['Soft Rock', 'Arena Rock']: 7 de 7 |  | {'n': 7, 'malos': 0, 'esperados': 7} |
| ✅ | Subgénero «(general)»: salen los del género sin estilo concreto, y solo esos | Rock y metal (general): 234 |  | {'n': 234, 'malos': 0} |
| ✅ | Tributos: su estilo como subgénero (todos tienen uno) | 169 tributos, 37 de rock |  | {'n': 169, 'sin': 0, 'rock': 37, 'ej': []} |
| ✅ | Buscar un artista lo encuentra | Óscar Avendaño y Reposado |  |  |
| ✅ | Buscar encuentra también conciertos de géneros ocultos por el filtro | Metropop |  |  |
| ✅ | Filtros de origen: España, Latinoamérica, internacional y sin confirmar cuadran | 2733 de 2733 |  | {'total': 2733, 'es': 1169, 'lat': 86, 'ext': 350, 'nc': 423, 'na': 705, 'otra': 0} |
| ✅ | Mes: la lista del día son los conciertos de ese día | 4 de 4 |  |  |
| ✅ | Ficha: el enlace de compra de la página de entradas es el botón principal | Comprar entradas en Entradium ↗ |  | {'ok': True, 'texto': 'Comprar entradas en Entradium ↗', 'agotado': False, 'aviso': True} |
| ✅ | A media lista, el menú ☰ se abre a la vista | — |  |  |
| ✅ | A media lista, Filtros abre la hoja sin mover la lista | — |  |  |
| ✅ | A media lista, la lupa abre la búsqueda en la cabecera lista para escribir, sin mover la lista | — |  |  |
| ✅ | Buscar desde media lista y cancelar: vuelve a la misma tarjeta | 33 resultados |  |  |
| ✅ | Festivales: insignia y cartel en la ficha | 'FESTIVAL Mad Psych Fest': 2 de 2 |  |  |
| ✅ | Teloneros: el concierto sale al filtrar por el género del telonero (y la tarjeta lo dice) | punk y garage el 2026-11-21 |  | {'sale': True, 'tag': True} |
| ✅ | Salas: lista, búsqueda, página de la sala con su programación y Volver | 249 salas · Sala El Sol: 130 conciertos · volver a #salas |  | {'nombre': 'Sala El Sol', 'cards': 130, 'esperadas': 130, 'ics': 'calendario/sala-sala-el-sol.ics', 'lateral': 0, 'filtro': ['La Riviera']} |
| ✅ | Calendario de la sala: suscripción (webcal, Google, Outlook) y .ics válido con sus conciertos | 137 eventos en calendario/sala-sala-el-sol.ics |  | ['webcal://estebancobo-dot.github.io/agenda-conciertos/calendario/sala-sala-el-sol.ics', 'https://calendar.google.com/calendar/render?cid=webcal%3A%2F%2Festebancobo-dot.github.io%2Fagenda-conciertos%2 |
| ✅ | Calendarios por género: uno por género y se descargan | 20 géneros · 629 eventos en calendario/genero-rock-y-metal.i |  | {'n': 20, 'ics': 'calendario/genero-rock-y-metal.ics', 'ok': True, 'ev': 629} |
| ✅ | Historial de cambios en la ficha (y aviso en la tarjeta) | 46 conciertos con cambios · 20 novVuelve a anunciarse |  | ['20 novVuelve a anunciarse', '9 novDeja de aparecer en las webs donde se anunciaba', '29 octAparece en la agenda'] |
| ✅ | Fin de semana: viernes a domingo de la semana (también al cambiar de año), lo que dicen los datos | 2 de 2 bien |  |  |
| ✅ | Todos: todos los conciertos desde hoy en orden, con su total, pintado progresivo y saltos por meses | 1368 de 2733 conciertos desde hoy · 70 pintados al abrir · 1 |  | {'pintadas': 70, 'orden': True, 'desdeHoy': True, 'n': 1368, 'cab': '1368 de 2733 conciertos desde hoy', 'meses': 7, 'lateral': 0, 'salto': {'mes': '2026-12', 'dia': '2026-12-01', 'marcado': True}} |
| ✅ | Confirmación: nivel y motivos en la ficha; filtro 'Solo confirmados' | 927 confirmados · 1274 probables · 532 sin confirmar · ficha |  | {'con': 2733, 'n': 86, 'c': 927, 'p': 1274, 's': 532, 'bien': True} |
| ✅ | Estado de estilo y origen en la ficha (sin etiqueta si es un dato conocido) y recuento en Fuentes (N3/N4) | ficha: ['No encontrado'] · ['Estilo', 'Dato conocido: 1850'] |  | Datos de cada concierto
Estilo
Dato conocido: 1850
Estimado: 242
No aplica: 407
No encontrado: 291
Origen
Dato conocido: 1025
Estimado: 597
No aplica: 714
No encontrado: 454
Hora
Dato conocido: 2294
E |
| ✅ | Conflicto de fecha en la tarjeta y la ficha | 2 fechas |  | ⚠ Las webs no coinciden
Fecha
miércoles, 25 de noviembre
4 webs: Palacio Vistalegre, La Ganzúa, Songkick Madrid, JacksOnLive
martes, 24 de noviembre
1 web: JacksOnLive
JacksOnLive anuncia una nueva fe |
| ✅ | Nivel del concierto: «gran formato» en la tarjeta y nivel con su porqué en la ficha | 146 de gran formato · 'Rockville: club o bar · Metallica: 5, |  |  |
| ✅ | Fase B: guardar en Mis conciertos (★), Novedades y artistas similares | guardado y en la lista: True · ★: 1 · 317 conciertos nuevos  |  |  |
| ✅ | Informe se abre | — |  |  |
| ✅ | Paso de días, semanas, meses y años (con cambios de hora y febrero) con las flechas | 103 de 103 pasos bien |  |  |
| ✅ | Enlace directo a una ficha la abre | Clearwater Companion |  |  |
| ✅ | Peor caso semana del 23/11 (451 conciertos): con 'Todos' salen todos | 451 de 451 |  |  |

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
| ✅ | Por defecto se dice cuántos conciertos de otros géneros quedan ocultos, con un botón para verlos | 1365 conciertos más de otros géneros (jazz, flamenco, soul,  |  |  |
| ✅ | Búsqueda sin resultados lo dice | — |  |  |
| ✅ | La barra dice que se está buscando | Filtrando: búsqueda «Leiva» · Quitar filtros · Compartir |  |  |
| ✅ | La búsqueda se ve dentro de la hoja de filtros | — |  |  |
| ✅ | 'Todos' (grupos) no borra la búsqueda a escondidas | — |  |  |
| ✅ | 'Borrar filtros' en la hoja quita también la búsqueda | — |  |  |
| ✅ | El cuadro de búsqueda queda vacío al borrar | — |  |  |
| ✅ | Mes: al tocar un día, su lista queda a la vista | — |  |  |
| ✅ | Semana: al bajar, la fecha completa del día se queda fija arriba | Viernes, 20 de noviembre55 conciertos |  | {'pegada': True, 'fecha': '2026-11-20', 'texto': 'Viernes, 20 de noviembre55 conciertos', 'marcado': '2026-11-20', 'alto': 170} |
| ✅ | Semana: la tira de días marca el día por el que vas | 2026-11-20 / 2026-11-20 |  |  |
| ✅ | Semana: lo fijo arriba (cabecera, tira y fecha) no ocupa más de un tercio de la pantalla | 210 | aviso > 281 px / fallo > 422 px |  |
| ✅ | Semana: tocar un día de la tira lleva justo a ese día | 2026-11-22 (pedido 2026-11-22) |  | {'pegada': True, 'fecha': '2026-11-22', 'texto': 'Mañana, domingo, 22 de noviembre29 conciertos', 'marcado': '2026-11-22', 'alto': 170} |
| ✅ | Día: al bajar, la fecha completa se queda fija arriba con la tira de días | Hoy, sábado, 21 de noviembre70 conciertos |  | {'pegada': True, 'fecha': '2026-11-21', 'texto': 'Hoy, sábado, 21 de noviembre70 conciertos', 'marcado': '2026-11-21', 'alto': 170} |
| ✅ | Mes: al bajar por la lista del día, su fecha completa se queda fija arriba | Hoy, sábado, 21 de noviembre70 conciertos |  | {'pegada': True, 'fecha': '2026-11-21', 'texto': 'Hoy, sábado, 21 de noviembre70 conciertos', 'marcado': None, 'alto': 109} |
| ✅ | Al bajar por la lista, Buscar y Filtros siguen a mano en la cabecera (y arriba no se duplican) | — |  |  |
| ✅ | A media lista, ‹ semana › en la cabecera: pasa a la siguiente y deja su primer día a la vista | 2026-11-23 · '23–29 nov\n237 conciertos' |  | {'fecha': '2026-11-23', 'fija': True, 'titulo': '23–29 nov\n237 conciertos', 'cabecera': True} |
| ✅ | Cambiar de día, semana o mes desde media lista deja la vista nueva desde su principio; Hoy siempre a mano | 10 de 10 casos bien |  |  |
| ✅ | Fuentes: una tarjeta por web con estado, 14 días y datos; filtros y búsqueda; sin scroll lateral | 87 de 87 webs · 33 salas · 63 salas sin web leída |  | {'n': 33, 'total': 87, 'tiras': 87, 'metricas': 87, 'lateral': 0, 'salas': 63, 'bien': True, 'esperadas': 33, 'busca': True} |
| ✅ | Saltos de diseño (CLS) | 0 | aviso > 0.1  / fallo > 0.25  |  |
| ✅ | Semana sin conciertos: lo dice | — |  |  |
| ✅ | Peor caso semana del 23/11 (451 conciertos): volver deja la lista en el concierto | — |  |  |
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
| ✅ | Ordenador: la ficha se abre al lado de la lista (la lista sigue a la vista) y Escape la cierra | al lado · cerrada |  | {'hash': '#semana/2026-11-16', 'lado': True, 'marcado': True, 'lateral': 0} |

## Rendimiento

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Conciertos con miniatura propia (servida desde la web) | 100.0 |  | de 2088 con imagen; mínimo 97 % |
| ✅ | Conciertos con foto de ficha propia (servida desde la web) | 100.0 |  | de 2088 con imagen; mínimo 97 % |
| ✅ | Primera visita: datos y lista pintados | 3585 | aviso > 5000 ms / fallo > 8000 ms |  |
| ✅ | Primera visita: LCP | 3656 | aviso > 4000 ms / fallo > 6000 ms |  |
| ✅ | Primera visita: KB descargados | 475 | aviso > 1500 KB / fallo > 3000 KB |  |
| ✅ | Bajar despacio: miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas |  |
| ✅ | Bajar deprisa: al parar, miniaturas visibles cargadas en | 53 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Cambiar de semana (mediana de 3) | 182 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Abrir ficha desde la lista (datos) | 140 | aviso > 500 ms / fallo > 1500 ms |  |
| ✅ | Ficha completa (fuentes y precio) | 145 | aviso > 1500 ms / fallo > 4000 ms |  |
| ✅ | Foto de la ficha tras ver la lista 2 s (mediana) | 152 | aviso > 600 ms / fallo > 1500 ms |  |
| ✅ | Fichas cuya foto ya estaba descargada al abrir | 5 |  | 5 de 5 |
| ✅ | Ficha lejana (discogs): datos | 91 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (discogs): foto | 159 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (wikimedia): datos | 110 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (wikimedia): foto | 164 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (otros): datos | 49 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (otros): foto | 131 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (conciertos.club): datos | 56 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (conciertos.club): foto | 132 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Ficha lejana (sin foto): datos | 32 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (madridenvivo): datos | 66 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Ficha lejana (madridenvivo): foto | 138 | aviso > 3000 ms / fallo > 8000 ms |  |
| ✅ | Filtros: abrir la hoja | 285 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: 'Ninguno' | 101 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: aplicar | 186 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: borrar filtros | 189 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: 'Los de siempre' | 74 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Filtros: chip de grupo | 165 | aviso > 300 ms / fallo > 800 ms |  |
| ✅ | Vista mes | 158 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Todos: pintar la lista | 164 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Segunda visita: lista pintada | 1003 | aviso > 1500 ms / fallo > 3000 ms |  |
| ✅ | Segunda visita: miniaturas visibles cargadas | 79 | aviso > 800 ms / fallo > 2500 ms |  |
| ✅ | Bloqueo de JavaScript más largo (CPU 6x) | 188 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Imágenes que no cargan | 0.3 | aviso > 1 % / fallo > 5 % | net::ERR_BLOCKED_BY_ORB https://wsrv.nl/?url=https%3A%2F%2Fsjuuujieewmyiqtcxkps.supabase.co%2Fstorage%2Fv1%2Fobject%2Fsign%2Fcarteles%2F70069e22; net::ERR_BLOCKED_BY_ORB https://sjuuujieewmyiqtcxkps.s |
| ✅ | Enlace directo a una ficha (visita nueva) | 3532 | aviso > 5000 ms / fallo > 9000 ms |  |
| ✅ | Vista día sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 20 | aviso > 1000 ms / fallo > 2500 ms | [14, 3, 20] |
| ✅ | Vista mes sin caché: miniaturas visibles cargadas (peor de 3 fechas al azar) | 11 | aviso > 1000 ms / fallo > 2500 ms | [4, 5, 11] |
| ✅ | Ficha sin caché: foto desde que se ve la ficha (peor de 4 al azar) | 82 | aviso > 1200 ms / fallo > 2500 ms | [56, 52, 61, 82] ['estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io', 'estebancobo-dot.github.io'] |
| ✅ | Imágenes de las listas pedidas fuera de la web (wsrv.nl, agendas) | 0 |  |  |
| ✅ | Peor caso semana del 23/11 (451 conciertos): pintar con 'Todos' | 209 | aviso > 700 ms / fallo > 1500 ms |  |
| ✅ | Peor caso semana del 23/11 (451 conciertos): miniaturas de la primera pantalla | 136 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 23/11 (451 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 73 pantallas; peores [0, 0, 0]; pantallas con alguna sin cargar: 0 |
| ✅ | Peor caso semana del 23/11 (451 conciertos): bloqueo de JavaScript más largo al bajar | 0 | aviso > 300 ms / fallo > 1000 ms |  |
| ✅ | Peor caso semana del 23/11 (451 conciertos): bajando seguido, miniaturas a la vista sin cargar | 0.0 | aviso > 5 % / fallo > 15 % | 0 de 329 vistas en 12 s |
| ✅ | Peor caso semana del 23/11 (451 conciertos): bajando deprisa, al parar miniaturas visibles cargadas en | 144 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso semana del 23/11 (451 conciertos): foto de una ficha del final de la lista | 285 | aviso > 800 ms / fallo > 2000 ms |  |
| ✅ | Peor caso semana del 23/11 (451 conciertos): imágenes pedidas fuera de la web | 0 |  |  |
| ✅ | Peor caso día 21/11 (123 conciertos): miniaturas de la primera pantalla | 221 | aviso > 1000 ms / fallo > 2500 ms |  |
| ✅ | Peor caso día 21/11 (123 conciertos): bajando despacio, miniaturas sin cargar a los 0,4 s (peor pantalla) | 0 | aviso > 1 miniaturas / fallo > 3 miniaturas | 21 pantallas |
| ✅ | Peor caso mes 12/2026 (1002 conciertos), día 19/12: al tocar el día, miniaturas visibles cargadas | 51 | aviso > 1000 ms / fallo > 2500 ms | desde el toque: 944 ms |

## Fallos

| | Comprobación | Valor | Umbral | Detalle |
|---|---|---|---|---|
| ✅ | Enlace a un concierto que ya no existe: lo dice y deja volver | — |  |  |
| ✅ | Detalle que no llega: se ve la ficha básica y avisa | — |  | ‹ Volver M Foto: (imagen del anuncio) Metropop No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 sábado, 21 de noviembreEmpieza en 11 h 15 |
| ✅ | Fotos que no cargan: sin iconos de imagen rota | 0 |  |  |
| ✅ | Agenda que no llega: mensaje claro para recargar | — |  | No se pudieron cargar los datos (data/concerts.json). Comprueba la conexión y recarga la página. |
| ✅ | Agenda lenta: indica 'Cargando…' y luego se pinta | — |  |  |
| ✅ | Sin taxonomía de estilos: la agenda sigue funcionando | — |  |  |
| ✅ | Sin conexión: la agenda se abre con la copia guardada | 95 | aviso > 4500 ms / fallo > 8000 ms |  |
| ✅ | Sin conexión: se ven los conciertos | — |  |  |
| ✅ | Sin conexión: una ficha no guardada avisa en vez de quedarse cargando | — |  | ‹ Volver Foto: (imagen del anuncio) The Muggs No se pudieron cargar las fuentes y el precio: comprueba la conexión. 📅 jueves, 20 de mayo Hora sin indicar 📍 Revi |
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
| ✅ | Próximos 10 días: conciertos con enlace de compra directo | 161 de 658 |  | con cartel de gira 170, con hora 535 |
| ✅ | Todo por https (sin contenido mixto) | 0 |  |  |
| ✅ | Miniaturas de las agendas a través del proxy | 0 de 0 |  |  |
| ✅ | Errores en la consola | 0 |  |  |
