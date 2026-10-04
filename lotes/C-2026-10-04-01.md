Eres un documentalista de conciertos. Para cada concierto de la lista de abajo (en Madrid), busca en internet (usa
la búsqueda web) la página de la sala o de la venta de entradas que lo anuncie, y de ella la hora de comienzo y el
precio. Si el concierto se ha cancelado o aplazado, dilo.

Reglas (muy importantes, todo se comprueba automáticamente abriendo la página que cites):
1. "url": la página de ESE concierto (mismo artista, misma fecha) en la web oficial de la sala o en una web de venta de
   entradas (Dice, Entradas.com, Ticketmaster, Mutick, Wegow, Enterticket, Fever, Taquilla.com, la propia sala…).
   Tiene que abrirse sin iniciar sesión. NO sirven Instagram, Facebook, X/Twitter ni TikTok.
2. "hora" (HH:MM, 24 h) y "precio" (por ejemplo "15 €", "desde 12,50 €", "entrada libre") tienen que aparecer en esa
   página. Si la página no los dice, déjalos en null. No pongas la hora de apertura de puertas como hora de comienzo
   salvo que sea la única que aparece.
3. "estado": "cancelado" o "aplazado" solo si la página lo dice; si no, null.
4. Si no encuentras una página de ese concierto, pon "url": null. No uses la página de otra fecha ni de otra ciudad.

Responde SOLO con un bloque de código JSON con esta forma (un objeto por concierto, con su "id"):
```json
{"lote": "C-2026-10-04-01", "conciertos": [
  {"id": "c1", "url": "https://...", "hora": "21:00", "precio": "15 €", "estado": null}
]}
```

Conciertos:
```json
[
{"id": "c1", "artista": "CantaJuego", "fecha": "domingo 4/10/2026", "sala": "Teatro Pavón", "municipio": "Madrid", "buscar": ["hora", "precio", "entradas"], "anunciado_en": ["https://www.songkick.com/concerts/43212793-cantajuego-at-teatro-pavon"]},
{"id": "c2", "artista": "Mork", "fecha": "domingo 4/10/2026", "sala": "Silikona", "municipio": "Madrid", "buscar": ["hora", "precio", "entradas"], "web_de_la_sala": "https://silikona.es/", "anunciado_en": ["https://totalstage.vercel.app/concierto/Mork/2026-10-04"]},
{"id": "c3", "artista": "Sebastian Chames", "fecha": "domingo 4/10/2026", "sala": "Recoletos Jazz", "municipio": "Madrid", "buscar": ["hora", "precio", "entradas"], "anunciado_en": ["https://qconciertos.es/conciertos-en-madrid-provincia/"]},
{"id": "c4", "artista": "Lady Pepa", "fecha": "miércoles 7/10/2026", "sala": "Espacio Alma", "municipio": "Madrid", "buscar": ["hora", "precio", "entradas"], "anunciado_en": ["https://www.songkick.com/concerts/43377835-lady-pepa-at-espacio-alma"]},
{"id": "c5", "artista": "Maxim Vengerov", "fecha": "miércoles 7/10/2026", "sala": "Auditorio Nacional de Música", "municipio": "Madrid", "buscar": ["hora", "precio", "entradas"], "anunciado_en": ["https://www.songkick.com/concerts/43372126-maxim-vengerov-at-auditorio-nacional-de-musica-de-madrid"]},
{"id": "c6", "artista": "Wah!", "fecha": "miércoles 7/10/2026", "sala": "Pabellón 2, IFEMA Madrid", "municipio": "Madrid", "buscar": ["hora", "precio", "entradas"], "anunciado_en": ["https://www.songkick.com/concerts/43417993-wah-at-pabellon-2-ifema-madrid"]},
{"id": "c7", "artista": "Carlota Mad", "fecha": "jueves 8/10/2026", "sala": "Rincón del Arte Nuevo", "municipio": "Madrid", "buscar": ["hora", "precio", "entradas"], "web_de_la_sala": "https://www.elrincondelartenuevo.com/", "anunciado_en": ["https://www.songkick.com/concerts/43335996-carlota-mad-at-rincon-del-arte-nuevo"]},
{"id": "c8", "artista": "Sofía Campos", "fecha": "jueves 8/10/2026", "sala": "Esquina Nua", "municipio": "Madrid", "buscar": ["hora", "precio", "entradas"], "anunciado_en": ["https://www.songkick.com/concerts/43371163-sofia-campos-at-esquina-nua"]},
{"id": "c9", "artista": "Wah!", "fecha": "jueves 8/10/2026", "sala": "Pabellón 2, IFEMA Madrid", "municipio": "Madrid", "buscar": ["hora", "precio", "entradas"], "anunciado_en": ["https://www.songkick.com/concerts/43417994-wah-at-pabellon-2-ifema-madrid"]},
{"id": "c10", "artista": "Joma", "fecha": "viernes 9/10/2026", "sala": "Leaves", "municipio": "Madrid", "buscar": ["hora", "precio", "entradas"], "anunciado_en": ["https://www.songkick.com/concerts/43439576-joma-at-leaves"]},
{"id": "c11", "artista": "BARRACÜDA", "fecha": "sábado 10/10/2026", "sala": "San Nicasio Rock", "municipio": "Leganés", "buscar": ["hora", "precio", "entradas"], "anunciado_en": ["https://www.rockgle.es/p/agenda-de-conciertos_07.html"]},
{"id": "c12", "artista": "EUROPE", "fecha": "sábado 10/10/2026", "sala": "Plaza de Toros La Nueva Cubierta", "municipio": "Leganés", "buscar": ["hora", "precio", "entradas"], "anunciado_en": ["https://metalcry.com/vuelve-europe-gira-historica-por-el-40o-aniversario-de-the-final-countdown/"]},
{"id": "c13", "artista": "REBROTE", "fecha": "sábado 10/10/2026", "sala": "Sala B", "municipio": "Madrid", "buscar": ["hora", "precio", "entradas"], "anunciado_en": ["https://mariskalrock.com/guia-de-conciertos/"]},
{"id": "c14", "artista": "CantaJuego", "fecha": "domingo 11/10/2026", "sala": "Teatro Pavón", "municipio": "Madrid", "buscar": ["hora", "precio", "entradas"], "anunciado_en": ["https://www.songkick.com/concerts/43212797-cantajuego-at-teatro-pavon"]},
{"id": "c15", "artista": "Wah!", "fecha": "domingo 11/10/2026", "sala": "Pabellón 2, IFEMA Madrid", "municipio": "Madrid", "buscar": ["hora", "precio", "entradas"], "anunciado_en": ["https://www.songkick.com/concerts/43417997-wah-at-pabellon-2-ifema-madrid"]}
]
```
