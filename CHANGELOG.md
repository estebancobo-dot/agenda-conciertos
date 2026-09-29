# Versiones

## 2.0.0 — 2026-09-29

Primera versión automática (la 1.x fue la agenda manual hecha en el chat).

- Rastreo diario (GitHub Actions, 05:00 UTC y a mano) de 77 fuentes: agregadores (conciertos.club por semanas, portada y 12 estilos; La Ganzúa; Conciertos por Madrid; Madrid en Vivo con su petición de "cargar más"; Songkick; Rock and Blog; blog de Ticketmaster; Radar Joven), webs de rock y metal (TodoHeavyMetal, Metal Legion, Metalcry, Hellpress, Metal Symphony, Rock for Everyone, MariskalRock, Rockgle, Madness Live, Get Rock, Neverland, Rock-Progresivo, FORCE), blogs de giras con lectura incremental (Dirty Rock, viriAOR, Diario de un Rockero), americana y blues (Mutick/The Flying Pig, Qconciertos, Sociedad de Blues de Madrid, Big Mama), 22 webs oficiales de salas y 21 agendas municipales.
- Respeto de robots.txt (RFC 9309, incluido `Crawl-delay`), 1 petición cada 2 s por web y User-Agent identificable.
- Filtro por los 179 municipios de la Comunidad de Madrid (`data/municipios.json`); se descartan otras provincias aunque la sala se llame igual.
- Deduplicación: misma fecha + misma sala normalizada (`data/salas_alias.json`) + artista con similitud ≥ 90 (rapidfuzz), comparando también con los invitados y admitiendo prefijos de ciclo ("Las Noches de Río Babel. …").
- Conflictos de hora, sala y cartel: se guardan todas las versiones y se marca "conflicto"; si la fuente de mayor prioridad confirma el dato, se resuelve y se anota.
- Estados: contrastado (2+ webs distintas), 1 fuente, conflicto y posiblemente cancelado (cuando deja de aparecer en todas sus fuentes y estas funcionaron).
- Correcciones manuales (`data/correcciones.json`): descartes, conflictos y notas.
- Estilo solo el de la fuente, traducido a categoría con `data/estilos_map.json` y a Discogs con `data/taxonomia.json`.
- Nacionalidad: la de la fuente o, si no hay, MusicBrainz solo con una única coincidencia exacta.
- Salidas: `data/concerts.json`, `data/concerts.csv` (Excel), `data/informe.json`, `data/estado.json`.
- Web móvil (GitHub Pages) con vistas Mes, Semana, Día, Estilos, Fuentes, Informe y Versiones, filtros por categoría y buscador.
- Tests con pytest sobre HTML real de cada fuente, deduplicación y correcciones.
