"""Genera data/palabras.json: palabras propias del español y del inglés (frecuencias de wordfreq).

Sirve para estimar, solo cuando ninguna fuente dice de dónde es un artista, si su nombre está en español
("Felipe Arce Cuarteto", "Los Amados") o en inglés ("80 Rednecks"). No se usa en la ejecución diaria
(no hace falta instalar wordfreq): solo para regenerar la lista.

Uso: pip install wordfreq && python tools/generar_palabras.py
"""
import json
import unicodedata
from pathlib import Path

from wordfreq import top_n_list, zipf_frequency


def norm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


es, fuerte, en = set(), set(), set()
for w in top_n_list("es", 60000):
    if w.isalpha() and len(w) >= 2:
        # se compara con el inglés de la forma sin tildes: "máx" → "max" es inglés, "martín" → "martin" también
        a, b = zipf_frequency(w, "es"), max(zipf_frequency(w, "en"), zipf_frequency(norm(w), "en"))
        if a >= 2.5 and a - b >= 0.4:
            es.add(norm(w))
        if a >= 2.5 and a - b >= 1.0:
            fuerte.add(norm(w))
for w in top_n_list("en", 40000):
    if w.isalpha() and len(w) >= 2:
        a, b = zipf_frequency(w, "en"), zipf_frequency(w, "es")
        if a >= 3.0 and a - b >= 1.0:
            en.add(norm(w))
comunes = es & en
salida = {"_descripcion": "Palabras propias del español y del inglés (wordfreq, tools/generar_palabras.py).",
          "es": sorted(es - comunes), "es_fuerte": sorted((fuerte & es) - comunes), "en": sorted(en - comunes)}
Path(__file__).resolve().parent.parent.joinpath("data", "palabras.json").write_text(
    json.dumps(salida, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
print(len(salida["es"]), len(salida["en"]))
