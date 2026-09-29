# Agenda de conciertos · Comunidad de Madrid

Agenda automática y gratuita de los conciertos de los próximos 120 días en Madrid y los 179 municipios de la Comunidad, centrada en rock, metal, hard rock/AOR, prog, blues, americana/country/folk, punk/garage, pop/indie, cantautores y tributos.

**Web:** https://estebancobo-dot.github.io/agenda-conciertos/

## Qué hace

1. Cada día a las 05:00 UTC (7:00 en Madrid en verano, 6:00 en invierno) GitHub Actions visita unas 77 webs: agregadores, webs de metal y rock, blogs de giras, webs oficiales de salas y agendas municipales.
2. Respeta el `robots.txt` de cada web, hace como mucho 1 petición cada 2 segundos por web y se identifica con un User-Agent propio. Si una web lo prohíbe, no se lee y el informe lo dice.
3. Junta todo sin duplicados: el mismo concierto (misma fecha, misma sala, mismo artista) aparece una sola vez con todas sus fuentes.
4. **No inventa nada.** Cada dato tiene su fuente con enlace:
   - **Estilo**: lo da una web de música, no la agenda ni la sala: **Discogs** (estilos de sus discos) o, si no, **Wikipedia** (traducido a los estilos de Discogs). Solo si el artista se identifica sin ambigüedad. Si no tiene ficha, se muestra la etiqueta de la agenda marcada como tal; si tampoco hay: "sin clasificar". Wikidata aporta los identificadores exactos del artista en Discogs, AllMusic, Spotify, MusicBrainz y Last.fm, lo que evita confundir homónimos. AllMusic no permite el acceso automático: solo se enlaza.
   - Si un artista no tiene estilo ni en Discogs ni en Wikipedia y está guardada `LASTFM_KEY`, se usan las etiquetas de los oyentes de **Last.fm** que tienen equivalencia en Discogs. Se marcan como tales.
   - **Nacionalidad**: la de la fuente del concierto; si no, la de Wikidata, Wikipedia o Discogs; como último recurso MusicBrainz (única coincidencia exacta, marcada como "coincidencia por nombre"). Si no, "sin confirmar".
   - **Foto**: de Wikimedia Commons (vía Wikipedia) o Discogs, con su crédito; si no hay, la imagen del anuncio del concierto.
   - **Conflictos**: si dos webs no coinciden en hora, sala o cartel, se guardan ambas versiones y se marca "conflicto" con la explicación. Si la fuente de más prioridad confirma uno de los datos (1 web oficial de la sala · 2 promotora o ticketera · 3 agregador · 4 blog o foro), se da por resuelto y se anota.
5. Estados de cada concierto: **contrastado** (2 o más webs distintas), **1 fuente**, **conflicto** y **posiblemente cancelado** (ha dejado de aparecer en todas sus fuentes; no se borra hasta que pasa su fecha).
6. Publica la web y guarda los datos en `data/`:
   - `concerts.json` (todos los datos), `concerts.csv` (para Excel), `informe.json` (cómo fue cada fuente), `estado.json` (lecturas incrementales de los blogs).

## Usarlo desde el móvil

- **Ver la agenda**: abre la web. Pestañas: *Mes* (toca un día para verlo), *Semana*, *Día*, *Estilos*, *Fuentes*, *Informe* y *Versiones*. Toca un concierto para abrir su ficha (foto, estilo, origen, precio, sala y de dónde sale cada dato). El botón **Géneros** abre el panel de filtros ("Mi foco" oculta lo que está fuera de foco); también se filtra por origen (españoles/extranjeros) y con el buscador.
- **Descargar para Excel**: botón "⬇ CSV" arriba a la derecha.

### Cuándo se actualiza

- **Conciertos**: una vez al día, a las 05:00 UTC. Se vuelven a leer todas las agendas, porque es la única forma de detectar cambios de hora o cancelaciones.
- **Fichas de artista** (estilo, origen, foto): cada artista se consulta una sola vez y se guarda en `data/artistas.json`. Cada 2 horas se completan los pendientes durante un máximo de 50 minutos, sin tocar las agendas. Cuando ya no quedan pendientes, esa ejecución termina en segundos.

### Lanzar la actualización a mano

1. Abre el repositorio en GitHub (en el navegador del móvil, mejor en "vista de escritorio" si no ves la pestaña).
2. Pestaña **Actions** → en la lista de la izquierda, **"Actualizar agenda y publicar web"**.
3. Botón **"Run workflow"** → deja la rama `main` → **"Run workflow"**. Si marcas **"Solo fichas de artista"**, no se leen las agendas y solo se completan fichas.
4. Tarda entre 20 y 45 minutos. Cuando el círculo se ponga verde, la web ya está actualizada.

### Añadir una sala al diccionario de alias

Sirve para que "Lab Wagon", "Sala Lab" y "Wagon" cuenten como la misma sala.

1. En GitHub abre `data/salas_alias.json` y pulsa el lápiz (✏️ *Edit*).
2. Copia un bloque existente y cámbialo, por ejemplo:
   ```json
   {"nombre": "Sala Nueva", "municipio": "Getafe", "alias": ["sala nueva", "la nueva", "nueva getafe"]},
   ```
   Los alias se escriben en minúsculas, sin tildes ni signos. Si dos salas se parecen pero son distintas, añádelas a `"distintas"`.
3. Pulsa **Commit changes**. Se usará en la siguiente actualización.

### Añadir una corrección manual

1. Abre `data/correcciones.json` → ✏️ *Edit*.
2. Añade una línea dentro de `"correcciones"` (sepárala de la anterior con una coma):
   - Descartar un concierto erróneo:
     ```json
     {"tipo": "descarte", "fecha": "2026-11-07", "artistas": ["Grupo X"], "salas": ["Sala Y"], "nota": "Fue en 2025.", "verificado": "2026-10-01"}
     ```
   - Marcar un conflicto (si hay varios registros que coinciden se fusionan en uno con todas las versiones):
     ```json
     {"tipo": "conflicto", "fecha": "2026-11-07", "artistas": ["Grupo X"], "nota": "Sala But según A; Sala Mon según B.", "verificado": "2026-10-01"}
     ```
   - Solo añadir una nota: `"tipo": "nota"`.
   `artistas` y `salas` son listas: basta con que coincida uno. También puedes usar `"hora": "21:30"` o `"municipio": "Madrid"`.
3. **Commit changes**.

### Añadir una fuente

1. Captura su HTML real: **Actions → "Capturar HTML de una fuente" → Run workflow** y escribe `nombre https://la-web/agenda`. El HTML queda en la carpeta `capturas/` (respetando su robots.txt).
2. Escribe el parser en `scraper/sources/` (una función que devuelve `RawEvent` con fecha, artista, sala, ciudad y la URL de la fuente; hay ejemplos para listados, JSON-LD, tablas y blogs). Para salas que publican "TÍTULO · FECHA · HORA" basta con `salas.secuencia`.
3. Regístrala en `scraper/registry.py` con su tipo y prioridad (1 sala oficial, 2 promotora/ticketera, 3 agregador, 4 blog/foro).
4. Añade un test en `tests/test_parsers.py` con el HTML guardado en `tests/fixtures/`.
5. Actualiza `CHANGELOG.md` con una nueva versión.

## Claves gratuitas (opcionales)

Todo funciona sin claves. Con ellas, algunas webs dejan hacer más consultas o dan más datos. Cada clave se guarda en GitHub como *secret*, así que nunca aparece en el código ni en la web.

**Cómo guardar una clave en GitHub (desde el móvil):**
1. Abre el repositorio en el navegador en "vista de escritorio".
2. Ve a **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
3. En *Name* escribe el nombre exacto (por ejemplo `DISCOGS_TOKEN`) y en *Secret* pega la clave. Pulsa **Add secret**.
4. Se usará en la siguiente actualización.

**1. `DISCOGS_TOKEN` (recomendada, 2 minutos).** Con ella Discogs admite 60 consultas/min en vez de 25, así que las fichas de todos los artistas se completan en menos días.
1. Crea una cuenta gratuita en https://www.discogs.com, o entra con la tuya.
2. Ve a https://www.discogs.com/settings/developers.
3. Pulsa **Generate new token** y copia el texto que aparece.
4. Guárdalo en GitHub con el nombre `DISCOGS_TOKEN`.

**2. `LASTFM_KEY` (recomendada).** Last.fm da etiquetas de estilo votadas por los oyentes y una lista de artistas similares. Es útil sobre todo para grupos pequeños que no están en Discogs ni en Wikipedia.
1. Crea una cuenta gratuita en https://www.last.fm/join.
2. Ve a https://www.last.fm/api/account/create y rellena el formulario:
   - *Application name*: "Agenda conciertos Madrid".
   - Descripción: puede ser la misma.
   - *Callback URL*: déjalo vacío.
3. Copia la **API key**. No hace falta el *Shared secret*.
4. Guárdala en GitHub con el nombre `LASTFM_KEY`.

**3. `TICKETMASTER_KEY` (baja prioridad).** Solo en torno al 4 % de los conciertos que publican las agendas enlazan a Ticketmaster. Casi todos son en salas grandes (La Riviera, Movistar Arena, But, Wagon), que ya se leen desde sus webs oficiales. Serviría para confirmar horas y precios en esas salas.
1. Crea una cuenta en https://developer-acct.ticketmaster.com/user/register.
2. En **My Apps** abre la app que se crea automáticamente y copia la **Consumer Key**.
3. Guárdala en GitHub con el nombre `TICKETMASTER_KEY`.

## Fuentes

La lista completa, con su tipo, fiabilidad y cómo fue la última ejecución, está en la pestaña **Fuentes** de la web y en `data/informe.json`. Notas:

- **MariskalRock** y **Rockgle** tienen fiabilidad baja (mantienen fechas antiguas y no indican el año): si un concierto solo aparece ahí va como "1 fuente" con nota.
- **Metalcry** pone 20:00 por defecto: su hora se ignora.
- **Radar Joven**: la web de la Comunidad de Madrid no responde a GitHub; la programación se toma de Conciertos por Madrid.
- **Galileo Galilei** a veces responde con un captcha anti-bots (el informe lo indica); sus conciertos llegan igualmente por Madrid en Vivo y conciertos.club.
- **No se usan** porque bloquean el acceso automático o fallan: IndyRock, JacksOnLive, La Hora del Blues.
- **Foros (solo consulta manual, no se rastrean)**: Foro Azkena y Zona-Zero — útiles para confirmar a mano rumores o cambios de sala.

## Para desarrolladores

```bash
pip install -r requirements.txt
python -m pytest -q          # tests (usan HTML guardado, sin internet)
python -m scraper            # rastreo completo (requiere internet)
python -m scraper --solo gruta77,villanos --sin-musicbrainz
```

Estructura: `scraper/sources/` (parsers), `scraper/merge.py` (deduplicación y conflictos), `scraper/correcciones.py`, `scraper/musicbrainz.py`, `scraper/pipeline.py` (orquestador), `site/index.html` (web), `data/` (diccionarios y resultados).
