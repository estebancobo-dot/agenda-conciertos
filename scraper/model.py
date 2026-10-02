"""Modelo de evento en bruto tal como lo da una fuente."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date


@dataclass
class RawEvent:
    fecha: date
    artista: str
    url: str                       # URL donde la fuente publica este concierto (o la página del listado)
    sala: str = ""
    ciudad: str | None = None      # texto de ciudad/municipio tal y como lo da la fuente
    hora: str | None = None
    invitados: list[str] = field(default_factory=list)
    precio: str | None = None
    estilo: str | None = None      # estilo tal cual lo da la fuente
    nacionalidad: str | None = None  # solo si la fuente la da
    nota: str | None = None        # aviso propio de la fuente (p. ej. año deducido)
    imagen: str | None = None      # imagen del evento que publica la fuente (cartel o foto)
    tipo: str | None = None        # "festival" si la fuente lo dice (Songkick: /festivals/)
    fuente: str = ""               # id de la fuente (lo rellena el orquestador)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["fecha"] = self.fecha.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "RawEvent":
        from datetime import date as _date
        campos = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        campos["fecha"] = _date.fromisoformat(d["fecha"])
        return cls(**campos)


@dataclass
class Source:
    id: str
    nombre: str
    url: str
    tipo: str               # sala | promotora | ticketera | agregador | blog | institucional
    prioridad: int          # 1 sala/recinto oficial · 2 promotora/ticketera · 3 agregador · 4 blog/foro
    fiabilidad: str         # alta | media | baja
    grupo: str              # misma web = mismo grupo (para contar fuentes independientes)
    parser: object = None   # función parse(ctx) -> iterable[RawEvent]
    reconfirma: bool = True  # False en lecturas incrementales (blogs): su ausencia no implica cancelación
    municipio_defecto: str | None = None  # municipio implícito si la fuente solo cubre un lugar
    notas: str = ""
    tope_seg: float | None = 480  # tiempo máximo de lectura; lo que no dé tiempo sale de su última lectura buena

    def meta(self) -> dict:
        return {k: getattr(self, k) for k in ("id", "nombre", "url", "tipo", "prioridad", "fiabilidad", "grupo",
                                               "reconfirma", "notas")}
