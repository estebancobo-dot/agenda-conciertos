"""Abre, actualiza o cierra el issue `alerta-web` según la última validación de la web publicada.

Lee SALIDA/resultados.json (tools/validar_web.py). Si hay fallos y no hay issue abierto, lo abre (GitHub avisa por
correo); si ya existe, actualiza su texto; si ya no hay fallos, lo cierra con un comentario. Los avisos no abren
issue: se ven en el resumen de la ejecución y en la rama `pruebas-web`. Nunca hace fallar la ejecución.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ETIQUETA = "alerta-web"
TITULO = "La web publicada no pasa la validación automática"


def gh(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=False)


def main() -> int:
    salida = Path(sys.argv[1] if len(sys.argv) > 1 else "pruebas")
    try:
        r = json.loads((salida / "resultados.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    fallos = [c for c in r.get("comprobaciones", []) if c["estado"] == "fallo"]
    run = os.environ.get("RUN_URL", "")
    cuerpo = ("La validación automática de la web publicada ha encontrado fallos:\n\n" +
              "\n".join(f"- **{c['categoria']}** · {c['nombre']}: `{str(c['valor'])[:80]}` {c['umbral']} "
                        f"{c['detalle'][:200]}" for c in fallos) +
              f"\n\nValidación del {r.get('fecha')} ({r.get('resumen')}). Detalle y capturas: {run} y la rama "
              "`pruebas-web`. Este issue se actualiza solo y se cierra cuando la web vuelve a pasar.")
    x = gh("issue", "list", "--label", ETIQUETA, "--state", "open", "--json", "number")
    if x.returncode != 0:
        print(f"No se pudo consultar los issues: {x.stderr[-200:]}")
        return 0
    abiertos = [i["number"] for i in json.loads(x.stdout or "[]")]
    if fallos and abiertos:
        gh("issue", "edit", str(abiertos[0]), "--body", cuerpo)
        print(f"Issue #{abiertos[0]} actualizado ({len(fallos)} fallos)")
    elif fallos:
        gh("label", "create", ETIQUETA, "--color", "b60205", "--description", "Validación automática de la web",
           "--force")
        x = gh("issue", "create", "--title", TITULO, "--label", ETIQUETA, "--body", cuerpo)
        print(x.stdout.strip() or x.stderr[-200:])
    elif abiertos:
        for n in abiertos:
            gh("issue", "close", str(n), "--comment", f"La web vuelve a pasar la validación ({r.get('resumen')}).")
        print("Sin fallos: issue cerrado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
