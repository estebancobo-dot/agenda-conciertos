## Lotes para completar datos

Aquí se publica, de uno en uno, lo que falta en la agenda y ninguna web leída automáticamente dice: el origen y el
estilo de artistas pequeños y la hora, el precio o la página oficial de conciertos sin confirmar.

**Cómo funciona**

1. Cada mañana (o al responder al anterior) aparece aquí un lote nuevo. Copia el bloque entero con el botón de copiar.
2. Pégalo en un **chat nuevo de Claude** (no en Code) y espera la respuesta. El chat busca en internet y devuelve un
   bloque JSON con cada dato, la página de donde sale y la frase exacta que lo dice.
3. Copia la respuesta entera del chat y pégala aquí como **comentario**.
4. En uno o dos minutos se contesta con el resultado y aparece el siguiente lote.

**Qué se comprueba antes de aceptar un dato**: se abre la página que cita el chat (respetando su robots.txt) y el dato
solo vale si la página nombra al artista (y la fecha, para un concierto), la frase citada está en la página y dice de
verdad ese país, esos estilos, esa hora o ese precio. Lo que no se pueda comprobar se rechaza con el motivo. Lo
aceptado se muestra en la web con su fuente y nunca pisa lo que dicen las webs de música o las agendas.

**Otros comentarios que entiende**: `siguiente` (salta el lote pendiente), `artistas` o `conciertos` (salta y pide
uno de ese tipo) y `estado` (cuánto queda).

No hace falta hacerlos todos: cada lote empieza por lo que más falta y por los conciertos más cercanos.
