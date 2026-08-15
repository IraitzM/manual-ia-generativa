#!/usr/bin/env python3
"""Corrector ortográfico en español para los capítulos del manual.

Limpia la sintaxis propia de Quarto antes de pasar el texto por aspell o
hunspell, porque sin ese paso los diagramas `mermaid`, las citas y los
bloques de código generan cientos de falsos positivos.

Se salta por su cuenta lo que no tiene sentido corregir con un diccionario
español: siglas en mayúsculas (RAG, MCP), nombres en CamelCase (GraphRAG,
OpenTelemetry) y cualquier token con dígitos. Los términos técnicos que sí
son palabras corrientes en minúscula (prompt, token, gateway) se declaran
en `[tool.spellcheck]` dentro de `pyproject.toml`.

Uso:
    python3 scripts/spellcheck.py              # corrige
    python3 scripts/spellcheck.py --dump       # lista las palabras candidatas
    python3 scripts/spellcheck.py --strict     # falla si no hay diccionario
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"

FENCE = re.compile(r"^\s*(?:`{3,}|~{3,})")
PALABRA = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*", re.UNICODE)

# Limpieza línea a línea, en este orden.
LIMPIEZA = [
    (re.compile(r"`[^`]*`"), " "),                     # código en línea
    (re.compile(r"\$\$?[^$]*\$\$?"), " "),             # fórmulas
    (re.compile(r"\[@[^\]]*\]"), " "),                 # citas [@clave]
    (re.compile(r"(?<!\w)@[\w:.#$%&+?<>~/-]+"), " "),  # citas en línea @clave
    (re.compile(r"\[\^[^\]]*\]"), " "),                # notas al pie
    (re.compile(r"!?\[([^\]]*)\]\([^)]*\)"), r"\1"),   # enlaces: conserva el texto
    (re.compile(r"https?://\S+"), " "),                # urls sueltas
    (re.compile(r"<[^>]+>"), " "),                     # etiquetas html
    (re.compile(r"\{[^}]*\}"), " "),                   # atributos {#id .clase}
    (re.compile(r"^\s*\|[\s|:-]+\|\s*$"), " "),        # separadores de tabla
]


def texto_util(fichero: Path) -> list[tuple[int, str]]:
    """Devuelve las líneas de prosa del capítulo, ya limpias."""
    lineas: list[tuple[int, str]] = []
    en_codigo = False
    en_portada = False

    crudas = fichero.read_text(encoding="utf-8").splitlines()
    for numero, linea in enumerate(crudas, 1):
        # Cabecera YAML al principio del fichero
        if numero == 1 and linea.strip() == "---":
            en_portada = True
            continue
        if en_portada:
            if linea.strip() == "---":
                en_portada = False
            continue

        if FENCE.match(linea):
            en_codigo = not en_codigo
            continue
        if en_codigo or linea.startswith(":::"):
            continue

        for patron, reemplazo in LIMPIEZA:
            linea = patron.sub(reemplazo, linea)

        if linea.strip():
            lineas.append((numero, linea))

    return lineas


def es_candidata(palabra: str) -> bool:
    """Descarta lo que no procede corregir con un diccionario español."""
    if len(palabra) < 3:
        return False
    if palabra.isupper():  # siglas: RAG, MCP, GPAI
        return False
    if any(c.isupper() for c in palabra[1:]):  # CamelCase: GraphRAG, LangGraph
        return False
    return True


def hay_aspell() -> list[str] | None:
    try:
        dicts = subprocess.run(
            ["aspell", "dump", "dicts"], capture_output=True, text=True, check=True
        ).stdout.split()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    if any(d == "es" or d.startswith("es_") for d in dicts):
        return ["aspell", "--lang=es", "--encoding=utf-8", "list"]
    return None


def hay_hunspell() -> list[str] | None:
    try:
        salida = subprocess.run(["hunspell", "-D"], capture_output=True, text=True, input="")
    except FileNotFoundError:
        return None
    if re.search(r"\bes[_-][A-Z]{2}\b", salida.stdout + salida.stderr):
        return ["hunspell", "-d", "es_ES", "-l"]
    return None


def diccionarios_disponibles(preferido: str) -> list[tuple[str, list[str]]]:
    """Correctores con diccionario español instalados.

    `preferido` sale de [tool.spellcheck].backend y admite "todos", "aspell"
    o "hunspell".

    Con "todos" una palabra solo se señala si **ningún** diccionario la
    reconoce, y esa es la opción recomendada. Ninguno de los dos es bueno
    por separado y sus lagunas son distintas: aspell rechaza "tutorial",
    "chat", "metadatos" o "resiliencia", y la grafía "guion" que la RAE
    fijó en 2010; hunspell rechaza "heurística", "muestrear",
    "milisegundos" o "estadísticamente". Cruzarlos quita del medio esos
    falsos positivos y deja una lista de excepciones bastante más corta.
    """
    buscadores = {"aspell": hay_aspell, "hunspell": hay_hunspell}

    if preferido in buscadores:
        orden = buscadores[preferido]()
        return [(preferido, orden)] if orden else []

    return [(nombre, orden) for nombre, buscar in buscadores.items() if (orden := buscar())]


def configuracion() -> dict:
    """Lee [tool.spellcheck] de pyproject.toml."""
    with PYPROJECT.open("rb") as fichero:
        datos = tomllib.load(fichero)
    return datos.get("tool", {}).get("spellcheck", {})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", action="store_true", help="lista las palabras candidatas y sale")
    parser.add_argument("--strict", action="store_true", help="falla si no hay diccionario español")
    args = parser.parse_args()

    config = configuracion()
    conocidas = {palabra.lower() for palabra in config.get("words", [])}
    patrones = config.get("sources", ["index.qmd", "parts/**/*.qmd"])

    apariciones: dict[str, list[str]] = defaultdict(list)
    fuentes = sorted({f for patron in patrones for f in ROOT.glob(patron)})

    for fuente in fuentes:
        origen = fuente.relative_to(ROOT)
        for numero, linea in texto_util(fuente):
            for palabra in PALABRA.findall(linea):
                # Se conserva la caja original: en minúscula, el corrector
                # rechaza los nombres propios (España, Francia, Europa).
                if es_candidata(palabra) and palabra.lower() not in conocidas:
                    apariciones[palabra].append(f"{origen}:{numero}")

    if args.dump:
        for palabra in sorted(apariciones):
            print(palabra)
        return 0

    correctores = diccionarios_disponibles(config.get("backend", "todos"))
    if not correctores:
        mensaje = (
            "No hay diccionario español instalado, se omite la corrección.\n"
            "  Instaladlos con:  sudo apt install aspell-es hunspell hunspell-es\n"
            "  (con los dos a la vez hay menos falsos positivos)"
        )
        print(mensaje, file=sys.stderr)
        return 1 if args.strict else 0

    entrada = "\n".join(sorted(apariciones))
    desconocidas = set(apariciones)
    for _, orden in correctores:
        resultado = subprocess.run(orden, input=entrada, capture_output=True, text=True)
        rechazadas = {p.strip() for p in resultado.stdout.split() if p.strip()}
        # Solo sobrevive lo que ningún diccionario reconoce.
        desconocidas &= rechazadas

    usados = " y ".join(nombre for nombre, _ in correctores)

    if not desconocidas:
        print(f"Ortografía correcta ({len(apariciones)} palabras revisadas con {usados}).")
        return 0

    print(f"Palabras que no reconoce {usados}:\n", file=sys.stderr)
    for palabra in sorted(desconocidas, key=lambda p: (-len(apariciones[p]), p)):
        sitios = apariciones[palabra]
        muestra = ", ".join(sitios[:3])
        resto = f" (+{len(sitios) - 3})" if len(sitios) > 3 else ""
        print(f"  {palabra:<24} {muestra}{resto}", file=sys.stderr)
    print(
        f"\n{len(desconocidas)} palabra(s). Si alguna es correcta y propia del dominio, "
        "añadidla a [tool.spellcheck].words en pyproject.toml.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
