"""Cartel de los conciertos con varios artistas: festivales, teloneros y ciclos (fase 3 de la gestión de conciertos).

Las agendas anuncian un mismo festival de formas distintas: "Pirata Festival 2026 Madrid", "Pirata Madrid Festival
(Boikot, Evaristo, benito Kamelas, Reincidentes y más)", "SAUROM JUGLAR FEST: SAUROM"… y Songkick lo llama por el
primer artista de su lista ("Rosana" para el Cadena 100 Por Ellas). Aquí:

- es_festival(titulo): el título es el de un festival (no el de un artista que toca *en* un festival: en
  "MININO BRAVO (Festival JazzMadrid)" el festival solo va entre paréntesis y es su ciclo).
- clave_festival(titulo): el nombre del festival sin año, "Madrid", "Festival"/"Fest"… para reconocer el mismo
  festival en varias agendas ("Pirata Festival 2026 Madrid" = "Pirata Madrid Festival").
- cartel_de_titulo(titulo): el cartel cuando el título lo da de forma inequívoca: "FESTIVAL X (A, B, C y más)" o
  "X FEST: A, B y C". Solo con nombre de festival delante: "MILLION DOLAR QUARTET: ELVIS PRESLEY, JOHNNY CASH…"
  es un espectáculo, no un cartel, y "Kraak & Smaak" es un grupo, no dos.

Nada se deduce: los artistas son los que dicen las agendas (sus listas de artistas o el propio título).
"""
from __future__ import annotations

import re

from .normalize import clean, es_generico, es_relleno, norm

_FEST = re.compile(r"\b(fest|festival|festivales|weekender|all ?dayer)\b")
_PARENTESIS = re.compile(r"\([^()]*\)")
# palabras que no distinguen un festival de otro
_VACIAS = {"madrid", "festival", "fest", "en", "de", "del", "la", "el", "los", "las", "y", "edicion", "the", "music",
           "primer", "primera", "segundo", "segunda", "tercer", "tercera", "i", "ii", "iii", "iv", "v", "vi", "vii",
           "viii", "ix", "x", "xi", "xii", "xx", "xxi"}
_MAS = re.compile(r"^(y |and |\+ )?(mas|muchos mas|muchas mas|mucho mas|more|otros|otras|mas artistas|"
                  r"mas bandas|mas grupos|invitados|artistas invitados|por confirmar|sorpresas?)$")
_AVISO = re.compile(r"\s+[-–—]\s+(se aplaza|aplazado|cancelado|suspendido|nueva fecha|cambia a|sold out|agotad)", re.I)


def es_festival(titulo: str | None) -> bool:
    """El título es el de un festival (la palabra fuera de los paréntesis)."""
    return bool(_FEST.search(norm(_PARENTESIS.sub(" ", titulo or ""))))


def nombre_festival(titulo: str) -> str:
    """El nombre del festival tal cual, sin la lista de artistas entre paréntesis ni avisos ("- SE APLAZA a 2027")."""
    t = _AVISO.split(titulo or "")[0]
    m = re.match(r"^(.+?)\s*\(([^()]+)\)\s*$", t)
    if m and es_festival(m.group(1)) and len(_lista(m.group(2))[0]) >= 2:
        t = m.group(1)
    m = re.match(r"^([^:]+?)\s*:\s*(.+)$", t)
    if m and es_festival(m.group(1)) and not es_festival(m.group(2)) and _lista(m.group(2))[0]:
        t = m.group(1)
    return clean(t)


def clave_festival(titulo: str | None) -> str:
    """Nombre del festival para compararlo entre agendas: sin año, sin 'Madrid', sin 'Festival'/'Fest'."""
    if not es_festival(titulo):
        return ""
    t = norm(_PARENTESIS.sub(" ", nombre_festival(titulo or "")))
    t = re.split(r"\s+[-–—]\s+", t)[0]
    palabras = [p for p in re.findall(r"[a-z0-9]+", t) if p not in _VACIAS and not re.fullmatch(r"(19|20)\d\d", p)]
    return " ".join(sorted(set(palabras)))


def _lista(texto: str) -> tuple[list[str], bool]:
    """'A, B, C y más' → (['A', 'B', 'C'], incompleto=True). Separa por comas, punto y coma, ' y ', ' e ', ' + ' y
    ' / ' (nunca por '&': 'Layo & Bushwacka!' es un dúo)."""
    partes = [clean(p) for p in re.split(r"\s*[,;]\s*|\s+(?:y|e|\+|/)\s+", texto or "") if clean(p)]
    incompleto = False
    out: list[str] = []
    for p in partes:
        if _MAS.match(norm(p)):
            incompleto = True
            continue
        if es_relleno(p) or es_generico(p) or len(p) > 60:
            continue
        out.append(p)
    return out, incompleto


def cartel_de_titulo(titulo: str | None) -> tuple[str | None, list[str], bool]:
    """(nombre del festival, artistas, cartel incompleto) cuando el título lo da de forma inequívoca; si no,
    (None, [], False)."""
    t = _AVISO.split(titulo or "")[0]
    m = re.match(r"^(.+?)\s*\(([^()]+)\)\s*$", t)
    if m and es_festival(m.group(1)):
        artistas, inc = _lista(m.group(2))
        if len(artistas) >= 2:
            return clean(m.group(1)), artistas, inc
    m = re.match(r"^([^:]+?)\s*:\s*(.+)$", t)
    if m and es_festival(m.group(1)) and not es_festival(m.group(2)):
        artistas, inc = _lista(m.group(2))
        if artistas:
            return clean(m.group(1)), artistas, inc
    return None, [], False


def mismo_festival(a: str, b: str) -> bool:
    ka, kb = clave_festival(a), clave_festival(b)
    return bool(ka) and ka == kb
