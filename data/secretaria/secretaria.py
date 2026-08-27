"""Arranque común de los cuadernos del hilo conductor.

Todos los cuadernos del manual que usan el dominio de la secretaría empiezan
con la misma celda:

    from secretaria import preparar
    ctx = preparar()

`preparar()` se encarga de lo aburrido: en Colab clona el repositorio, genera
el almacén DuckDB si no existe y localiza el corpus. En local no hace casi
nada porque ya está todo. Devuelve un contexto con la conexión, las rutas y el
nombre del modelo por defecto.

El modelo por defecto es `Qwen/Qwen3-0.6B` cargado con `transformers` en el
propio proceso. Es pequeño a propósito: cabe en la memoria gratuita de Colab y
no exige clave de ninguna API. Sus respuestas son mediocres y eso forma parte
del ejercicio, que trata de ver el mecanismo y no de obtener la mejor
respuesta. Para cambiarlo basta con pasar `modelo=` a `preparar()`.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = "https://github.com/IraitzM/manual-ia-generativa.git"
MODELO_POR_DEFECTO = "Qwen/Qwen3-0.6B"
EMBEDDINGS_POR_DEFECTO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@dataclass
class Contexto:
    """Lo que un cuaderno necesita para empezar a trabajar."""

    raiz: Path
    almacen: Path
    corpus: Path
    modelo: str = MODELO_POR_DEFECTO
    embeddings: str = EMBEDDINGS_POR_DEFECTO
    _conexion: object = field(default=None, repr=False)
    _solo_lectura: bool = field(default=True, repr=False)

    def conectar(self, solo_lectura: bool = True):
        """Conexión DuckDB al almacén, reutilizada entre llamadas.

        Por defecto en solo lectura. El cuaderno de agentes que crea
        solicitudes es el único que necesita escribir, y conviene que tenga
        que pedirlo de forma explícita.

        Si ya hay una conexión abierta en solo lectura y ahora se pide poder
        escribir, se cierra y se vuelve a abrir. Sin esto, `preparar()` dejaría
        cacheada una conexión de solo lectura y el parámetro no serviría de
        nada, que es justo lo que pasaba antes.
        """
        import duckdb

        if self._conexion is not None and self._solo_lectura and not solo_lectura:
            self._conexion.close()
            self._conexion = None

        if self._conexion is None:
            self._conexion = duckdb.connect(str(self.almacen), read_only=solo_lectura)
            self._solo_lectura = solo_lectura

        return self._conexion

    def documentos(self) -> list[dict]:
        """El corpus como lista de documentos con su texto y sus metadatos.

        Sin trocear: el troceado es justo lo que se estudia en el cuaderno de
        recuperación, así que no conviene dárselo hecho.
        """
        docs = []
        for ruta in sorted(self.corpus.glob("*.md")):
            texto = ruta.read_text(encoding="utf-8")
            docs.append(
                {
                    "id": ruta.stem,
                    "ruta": str(ruta),
                    "texto": texto,
                    "metadatos": _frontmatter(texto),
                }
            )
        return docs

    def tablas(self) -> dict[str, int]:
        """Nombre y número de filas de cada tabla. Útil como comprobación."""
        con = self.conectar()
        return {
            nombre: con.execute(f"select count(*) from {nombre}").fetchone()[0]
            for (nombre,) in con.execute("show tables").fetchall()
        }


def _frontmatter(texto: str) -> dict[str, str]:
    """Lee el frontmatter YAML sin depender de un parser de YAML.

    Los ficheros del corpus tienen un frontmatter plano de clave y valor, así
    que partir por el primer `:` basta y ahorra una dependencia.
    """
    if not texto.startswith("---"):
        return {}
    _, _, resto = texto.partition("---\n")
    bloque, _, _ = resto.partition("\n---")
    metadatos = {}
    for linea in bloque.splitlines():
        clave, sep, valor = linea.partition(":")
        if sep:
            metadatos[clave.strip()] = valor.strip()
    return metadatos


def _en_colab() -> bool:
    return "google.colab" in sys.modules or os.path.isdir("/content")


def _localizar_raiz() -> Path:
    """Busca la raíz del repositorio subiendo desde este fichero.

    En Colab el repositorio puede no estar todavía, y entonces se clona.
    """
    aqui = Path(__file__).resolve()
    for candidata in [aqui.parent, *aqui.parents]:
        if (candidata / "_quarto.yaml").exists():
            return candidata

    if _en_colab():
        destino = Path("/content/manual-ia-generativa")
        if not destino.exists():
            print("Clonando el repositorio del manual...")
            subprocess.run(
                ["git", "clone", "--depth", "1", "--quiet", REPO, str(destino)],
                check=True,
            )
        return destino

    raise RuntimeError(
        "No encuentro la raíz del repositorio. Ejecuta el cuaderno desde dentro "
        "del proyecto o clona https://github.com/IraitzM/manual-ia-generativa."
    )


def preparar(modelo: str | None = None, regenerar: bool = False) -> Contexto:
    """Deja el entorno listo y devuelve el contexto del dominio."""
    raiz = _localizar_raiz()
    base = raiz / "data" / "secretaria"
    almacen = base / "secretaria.duckdb"

    if regenerar or not almacen.exists():
        sys.path.insert(0, str(base))
        from generar import generar  # noqa: PLC0415

        print("Generando el almacén de la secretaría...")
        generar(almacen)

    ctx = Contexto(
        raiz=raiz,
        almacen=almacen,
        corpus=base / "corpus",
        modelo=modelo or MODELO_POR_DEFECTO,
    )

    filas = ctx.tablas()
    print(f"Almacén listo: {sum(filas.values())} filas en {len(filas)} tablas.")
    print(f"Corpus: {len(list(ctx.corpus.glob('*.md')))} documentos.")
    print(f"Modelo por defecto: {ctx.modelo}")
    return ctx
