"""Abre (o actualiza) un issue en GitHub cuando alguna fuente necesita que se mire a mano.

Lee data/informe.json ("alertas": fuentes que llevan días sin leerse, que han dejado de dar conciertos o dan
muchos menos de lo habitual). Hay como mucho un issue abierto con la etiqueta `alerta-fuentes`:
  - si hay alertas y no hay issue, se abre (GitHub avisa por correo a quien vigila el repositorio);
  - si ya existe, se actualiza su texto (sin notificar otra vez);
  - si ya no hay alertas, se cierra con un comentario.
Necesita la CLI `gh` y GH_TOKEN (en GitHub Actions ya están). Nunca hace fallar la ejecución.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ETIQUETA = "alerta-fuentes"
TITULO = "Fuentes de la agenda con problemas"


def gh(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], cwd=RAIZ, capture_output=True, text=True, check=False)


def cuerpo(informe: dict) -> str:
    lineas = [f"- {a}" for a in informe.get("alertas", [])]
    return ("Algunas fuentes necesitan que se revisen a mano (quizá han cambiado de diseño). Mientras tanto se usan "
            "sus conciertos de la última lectura completa (hasta 14 días).\n\n" + "\n".join(lineas) +
            f"\n\nInforme del {informe.get('generado', '?')} (versión {informe.get('version', '?')}). "
            "Este issue se actualiza solo y se cierra cuando dejan de fallar.")


def main() -> int:
    try:
        informe = json.loads((RAIZ / "data" / "informe.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    alertas = informe.get("alertas", [])
    r = gh("issue", "list", "--label", ETIQUETA, "--state", "open", "--json", "number")
    if r.returncode != 0:
        print(f"No se pudo consultar los issues: {r.stderr[-200:]}")
        return 0
    abiertos = [i["number"] for i in json.loads(r.stdout or "[]")]
    if alertas and abiertos:
        gh("issue", "edit", str(abiertos[0]), "--body", cuerpo(informe))
        print(f"Issue #{abiertos[0]} actualizado ({len(alertas)} alertas)")
    elif alertas:
        gh("label", "create", ETIQUETA, "--color", "d93f0b", "--description", "Avisos automáticos de las fuentes",
           "--force")
        r = gh("issue", "create", "--title", TITULO, "--label", ETIQUETA, "--body", cuerpo(informe))
        print(r.stdout.strip() or r.stderr[-200:])
    elif abiertos:
        for n in abiertos:
            gh("issue", "close", str(n), "--comment", "Todas las fuentes vuelven a leerse bien.")
        print("Sin alertas: issue cerrado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
