"""Compara las capturas de la web con datos fijos (tests/test_web_capturas.py) con las de la validación anterior
(rama pruebas-web): qué vistas han cambiado de aspecto y cuánto. Es un aviso, no un fallo: muchos cambios son
queridos. Por cada vista que cambia deja una imagen con lo distinto en rojo (dif_*.png) junto a las capturas.

Uso: python tools/comparar_capturas.py CARPETA_ANTERIOR CARPETA_NUEVA
Escribe el resumen en la salida y, si existe, en $GITHUB_STEP_SUMMARY. Siempre termina bien.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image, ImageChops

UMBRAL = 0.002  # menos de un 0,2 % de los píxeles distintos: suavizado de letra, nada que mirar


def diferencia(a: Path, b: Path) -> tuple[float | None, Image.Image | None]:
    """Fracción de píxeles distintos (None si cambia el tamaño) y la imagen nueva con lo distinto en rojo."""
    x, y = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    if x.size != y.size:
        return None, None
    mascara = ImageChops.difference(x, y).convert("L").point(lambda v: 255 if v > 24 else 0)
    distintos = mascara.histogram()[255]
    marcada = Image.composite(Image.new("RGB", y.size, (230, 0, 0)), y, mascara)
    return distintos / (x.size[0] * x.size[1]), marcada


def comparar(antes: Path, ahora: Path) -> list[str]:
    filas = []
    for n in sorted(p for p in ahora.glob("*.png") if not p.name.startswith("dif_")):
        previa = antes / n.name
        if not previa.exists():
            filas.append(f"| {n.stem} | nueva (sin captura anterior) |")
            continue
        frac, marcada = diferencia(previa, n)
        if frac is None:
            filas.append(f"| {n.stem} | ⚠ cambia de tamaño ({Image.open(previa).size} → {Image.open(n).size}) |")
        elif frac > UMBRAL:
            marcada.save(ahora / f"dif_{n.name}")
            filas.append(f"| {n.stem} | ⚠ {frac:.1%} de la imagen cambia (dif_{n.name}) |")
        else:
            filas.append(f"| {n.stem} | igual |")
    return filas


def main() -> int:
    antes, ahora = Path(sys.argv[1]), Path(sys.argv[2])
    if not ahora.exists():
        print("No hay capturas nuevas que comparar")
        return 0
    filas = comparar(antes, ahora) if antes.exists() else ["| (todas) | sin capturas anteriores: se guardan para la próxima |"]
    cambios = sum("⚠" in f for f in filas)
    texto = "\n".join([f"### Aspecto de la web con datos fijos: {cambios} vista(s) cambian respecto a la validación anterior",
                       "", "| Vista | Comparación |", "|---|---|", *filas, ""])
    print(texto)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(texto + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
