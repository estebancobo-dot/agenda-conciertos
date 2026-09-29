# Agenda de conciertos · Comunidad de Madrid

Agenda automática y gratuita de los conciertos de los próximos 120 días en Madrid y los 179 municipios de la Comunidad, centrada en rock, metal, hard rock/AOR, prog, blues, americana/country/folk, punk/garage, pop/indie, cantautores y tributos.

**Web:** https://estebancobo-dot.github.io/agenda-conciertos/

## Qué hace

1. Cada día a las 05:00 UTC (7:00 en Madrid en verano, 6:00 en invierno) GitHub Actions visita unas 77 webs: agregadores, webs de metal y rock, blogs de giras, webs oficiales de salas y agendas municipales.
2. Respeta el `robots.txt` de cada web, hace como mucho 1 petición cada 2 segundos por web y se identifica con un User-Agent propio. Si una web lo prohíbe, no se lee y el informe lo dice.
3. Junta todo sin duplicados: el mismo concierto (misma fecha, misma sala, mismo artista) aparece una sola vez con todas sus fuentes.
4. **No inventa nada.** Cada dato tiene su fuente con enlace:
   - **Estilo**: solo el que da la fuente. Si ninguna lo da: "sin clasificar" (visible, con su propio filtro).
   - **Nacionalidad**: la de la fuente o, si no la da, la de MusicBrainz solo cuando hay una única coincidencia exacta del artista. Si no, "sin confirmar".
   - **Conflictos**: si dos webs no coinciden en hora, sala o cartel, se guardan ambas versiones y se marca "conflicto" con la explicación. Si la fuente de más prioridad confirma uno de los datos (1 web oficial de la sala · 2 promotora o ticketera · 3 agregador · 4 blog o foro), se da por resuelto y se anota.
5. Estados de cada concierto: **contrastado** (2 o más webs distintas), **1 fuente**, **conflicto** y **posiblemente cancelado** (ha dejado de aparecer en todas sus fuentes; no se borra hasta que pasa su fecha).
6. Publica la web y guarda los datos en `data/`:
   - `concerts.json` (todos los datos), `concerts.csv` (para Excel), `informe.json` (cómo fue cada fuente), `estado.json` (lecturas incrementales de los blogs).

## Usarlo desde el móvil

- **Ver la agenda**: abre la web. Pestañas: *Mes* (toca un día para verlo), *Semana*, *Día*, *Estilos*, *Fuentes*, *Informe* y *Versiones*. Los chips de colores filtran por categoría ("fuera de foco" está oculto por defecto) y el buscador filtra por artista, sala o municipio. Toca "Estilo, notas y fuentes" en un concierto para ver de dónde sale cada dato.
- **Descargar para Excel**: botón "⬇ CSV" arriba a la derecha.

### Lanzar la actualización a mano

1. Abre el repositorio en GitHub (en el navegador del móvil, mejor en "vista de escritorio" si no ves la pestaña).
2. Pestaña **Actions** → en la lista de la izquierda, **"Actualizar agenda y publicar web"**.
3. Botón **"Run workflow"** → deja la rama `main` → **"Run workflow"**.
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

## Fuentes

La lista completa, con su tipo, fiabilidad y cómo fue la última ejecución, está en la pestaña **Fuentes** de la web y en `data/informe.json`. Notas:

- **MariskalRock** y **Rockgle** tienen fiabilidad baja (mantienen fechas antiguas y no indican el año): si un concierto solo aparece ahí va como "1 fuente" con nota.
- **Metalcry** pone 20:00 por defecto: su hora se ignora.
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
