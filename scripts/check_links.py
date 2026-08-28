#!/usr/bin/env python3
"""Comprueba que los enlaces internos del libro resuelven.

Cubre dos formas de enlace:

* **A otro capítulo**, `](fichero.qmd)` o `](fichero.qmd#ancla)`. Verifica
  que el fichero existe y que el ancla, si la hay, se corresponde con una
  cabecera de ese fichero o con un identificador explícito `{#id}`.
* **Dentro del mismo capítulo**, `](#ancla)`. Verifica el ancla contra las
  cabeceras del propio fichero.

Los títulos de los callouts (`# Título` dentro de un bloque `:::`) **no**
generan ancla en Quarto, así que aquí tampoco cuentan. Es justo el error
que este script existe para pillar: si queréis enlazar a un callout, dadle
un id explícito con `::: {#mi-id .callout-note}`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Enlaces markdown a un .qmd, con ancla opcional: ](fichero.qmd#ancla)
LINK = re.compile(r"\]\((?!https?:)([^)\s#]+\.qmd)(?:#([^)\s]+))?\)")
# Enlaces a una sección del mismo fichero: ](#ancla)
LINK_LOCAL = re.compile(r"\]\(#([^)\s]+)\)")
FENCE = re.compile(r"^\s*(?:`{3,}|~{3,})")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
EXPLICIT_ID = re.compile(r"\{#([^}\s.][^}\s]*)")


def slug(texto: str) -> str:
    """Reproduce el identificador que Pandoc genera para una cabecera."""
    texto = re.sub(r"\{[^}]*\}", "", texto)  # atributos {.unnumbered}
    texto = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", texto)  # enlaces
    texto = re.sub(r"[`*_]", "", texto)  # formato
    texto = texto.strip().lower()

    salida = []
    for caracter in texto:
        if caracter == " ":
            salida.append("-")
        elif caracter.isalnum() or caracter in "-_.":
            salida.append(caracter)
        # el resto de la puntuación se descarta, como hace Pandoc

    resultado = re.sub(r"-{2,}", "-", "".join(salida)).strip("-")
    # Pandoc elimina todo lo que precede a la primera letra
    primera = re.search(r"[^\W\d_]", resultado, re.UNICODE)
    return resultado[primera.start() :] if primera else resultado


def anclas(fichero: Path) -> set[str]:
    """Identificadores a los que se puede enlazar dentro de un capítulo."""
    encontradas: set[str] = set()
    en_codigo = False
    profundidad_div = 0

    for linea in fichero.read_text(encoding="utf-8").splitlines():
        if FENCE.match(linea):
            en_codigo = not en_codigo
            continue
        if en_codigo:
            continue

        if linea.startswith(":::"):
            resto = linea.lstrip(":").strip()
            if resto:  # apertura del div
                profundidad_div += 1
                explicito = EXPLICIT_ID.search(resto)
                if explicito:
                    encontradas.add(explicito.group(1))
            else:  # cierre
                profundidad_div = max(0, profundidad_div - 1)
            continue

        cabecera = HEADING.match(linea)
        if cabecera and profundidad_div == 0:
            titulo = cabecera.group(2)
            explicito = EXPLICIT_ID.search(titulo)
            encontradas.add(explicito.group(1) if explicito else slug(titulo))

    return encontradas


def main() -> int:
    fuentes = sorted(ROOT.glob("parts/**/*.qmd")) + sorted(ROOT.glob("*.qmd"))
    cache: dict[Path, set[str]] = {}
    problemas: list[str] = []

    for fuente in fuentes:
        for numero, linea in enumerate(fuente.read_text(encoding="utf-8").splitlines(), 1):
            for destino_rel, ancla in LINK.findall(linea):
                destino = (fuente.parent / destino_rel).resolve()
                origen = fuente.relative_to(ROOT)

                if not destino.is_file():
                    problemas.append(f"{origen}:{numero}: no existe {destino_rel}")
                    continue

                if not ancla:
                    continue

                if destino not in cache:
                    cache[destino] = anclas(destino)

                if ancla not in cache[destino]:
                    problemas.append(
                        f"{origen}:{numero}: {destino_rel} no tiene el ancla #{ancla}"
                    )

            for ancla in LINK_LOCAL.findall(linea):
                if fuente not in cache:
                    cache[fuente] = anclas(fuente)
                if ancla not in cache[fuente]:
                    problemas.append(
                        f"{fuente.relative_to(ROOT)}:{numero}: "
                        f"este capítulo no tiene el ancla #{ancla}"
                    )

    if problemas:
        print("Enlaces internos rotos:\n", file=sys.stderr)
        for problema in problemas:
            print(f"  {problema}", file=sys.stderr)
        print(
            f"\n{len(problemas)} enlace(s) que arreglar. Recordad que los títulos de "
            "callout no generan ancla: usad ::: {#un-id .callout-note}.",
            file=sys.stderr,
        )
        return 1

    print(f"Enlaces internos correctos ({len(fuentes)} capítulos revisados).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
