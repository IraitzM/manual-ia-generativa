# Manual de IA Generativa

Manual de referencia en español sobre IA generativa, escrito en [Quarto](https://quarto.org/). Cubre desde cómo funciona un modelo por dentro hasta lo que hace falta para que un agente viva en una empresa sin causar un disgusto.

Publicado en [iraitzm.github.io/manual-ia-generativa](https://iraitzm.github.io/manual-ia-generativa/).

## Qué hay aquí

| Componente | Qué es | Por dónde empezar |
|---|---|---|
| **El manual** | El libro en sí, seis partes y dos apéndices | [`index.qmd`](index.qmd) o el [sitio publicado](https://iraitzm.github.io/manual-ia-generativa/) |
| **Los cuadernos** | Ejecutables en Colab, uno o dos al final de cada capítulo que los tiene | [`notebooks/`](notebooks/) |
| **El dominio** | El caso que recorre el manual: la secretaría académica | [`data/secretaria/`](data/secretaria/README.md) |

El contenido vive en [`parts/`](parts/) y el índice de capítulos está en [`_quarto.yaml`](_quarto.yaml):

| Parte | Directorio | De qué va |
|---|---|---|
| Fundamentos | [`parts/fundamentos/`](parts/fundamentos/) | Del NLP clásico a los embeddings, y de la convolución a la atención |
| Modelos generativos | [`parts/modelos/`](parts/modelos/) | Qué es un modelo generativo, transformers, inferencia, panorama y ajuste fino |
| Contexto | [`parts/contexto/`](parts/contexto/) | Ingeniería de contexto, prompting y recuperación |
| Agentes | [`parts/agentes/`](parts/agentes/) | Bucle de agente, herramientas y MCP, memoria, orquestación y frameworks, interfaz |
| Producción | [`parts/produccion/`](parts/produccion/) | Ecosistema, gateways, evaluación y observabilidad |
| Normativa y seguridad | [`parts/seguridad/`](parts/seguridad/), [`parts/normativa/`](parts/normativa/) | Inyección de prompt, defensas y AI Act |
| Apéndices | [`parts/apendices/`](parts/apendices/) | Copilotos y método, glosario |

## Convenciones

Dos cosas que conviene respetar al escribir un capítulo nuevo:

**El código de color de los diagramas.** Todos los `mermaid` usan el mismo `classDef`, explicado en [la introducción](parts/intro.qmd#cómo-leer-los-diagramas): violeta para el modelo, azul para el contexto, ámbar para las herramientas, verde para el control, gris para lo que no controlamos y rojo para el riesgo. Se copia y se pega tal cual del capítulo más cercano.

**Las citas van al `.bib`.** Los trabajos citados están en [`parts/references.bib`](parts/references.bib) y se referencian con `[@clave]`. Los estándares y marcos que cambian de versión (OWASP, MCP, AI Act) se enlazan a su documentación, no se citan.

**Los cuadernos van al final de su capítulo.** Cada uno se enlaza desde una sección `## El cuaderno` al cierre del capítulo que lo usa, justo antes de la línea que lleva al siguiente. No hay un índice central: el cuaderno pertenece a su capítulo.

**Los cuadernos se versionan sin salidas.** Los `.ipynb` de [`notebooks/`](notebooks/) se confirman con las celdas sin ejecutar, para que no crezcan hasta pesar megabytes ni ensucien los diffs.

**El código de los capítulos no se ejecuta.** Los dos capítulos con código llevan `execute: enabled: false` en su cabecera y sus salidas están pegadas a mano, para que renderizar el libro no exija descargar `torch` ni modelos. Lo ejecutable vive en los cuadernos.

## Los cuadernos

La vía recomendada es **Google Colab**, y para eso está el badge al final de cada capítulo: abre el cuaderno directamente desde el repositorio, sin instalar nada. Se ejecuta la primera celda, que trae las dependencias y el dominio, y a partir de ahí va todo seguido.

Los cuadernos descargan modelos de Hugging Face, así que la primera ejecución tarda unos minutos. Ninguno exige GPU.

En local, sin tocar las dependencias del libro:

```bash
uv run --with jupyter jupyter lab
```

Al contribuir un cambio, hay que limpiar las salidas antes de confirmarlo:

```bash
uv run --with nbstripout nbstripout notebooks/**/*.ipynb
```

Los modelos que usan son pequeños a propósito, para que quepan en la memoria gratuita de Colab. Sus salidas son mediocres comparadas con las de cualquier asistente comercial, y eso es deliberado: se trata de ver el mecanismo, no de obtener la mejor respuesta.

Un aviso de mantenimiento: **los cuadernos envejecen antes que el texto**. Un capítulo que explica por qué existe la caché KV seguirá siendo válido dentro de tres años; una celda que llama a una librería con unos parámetros concretos puede romperse en tres meses. Si algo falla, mirad primero la versión de la librería y la firma de la función antes que la lógica del ejemplo.

## Renderizarlo en local

```bash
uv sync
quarto preview
```

El resultado se deja en `_book/`, que no se versiona. Los capítulos no ejecutan código, así que el render es rápido y no necesita intérprete de Python configurado. [`notebooks/`](notebooks/) queda fuera de la lista `render` de [`_quarto.yaml`](_quarto.yaml) a propósito: Quarto también sabe renderizar `.ipynb` y esos cuadernos no son capítulos del libro.

## Revisión automática

[`.pre-commit-config.yaml`](.pre-commit-config.yaml) engancha dos comprobaciones propias, además de la higiene habitual y del `uv-export`:

| Hook | Qué comprueba | Script |
|---|---|---|
| `enlaces-internos` | Que cada enlace a un `.qmd` existe y que su ancla se corresponde con una cabecera real | [`scripts/check_links.py`](scripts/check_links.py) |
| `ortografia` | La prosa de los capítulos contra un diccionario español | [`scripts/spellcheck.py`](scripts/spellcheck.py) |

```bash
uv run --with pre-commit pre-commit install   # una vez
uv run --with pre-commit pre-commit run --all-files
```

El corrector necesita diccionarios del sistema, que no se instalan con `uv`:

```bash
sudo apt install aspell-es hunspell hunspell-es
```

Si no está, el hook avisa y deja pasar el commit en lugar de bloquearlo. Su configuración (qué ficheros mira, qué corrector usa y qué términos da por buenos) vive en `[tool.spellcheck]` dentro de [`pyproject.toml`](pyproject.toml); cuando marque una palabra que sea correcta, se añade ahí. Antes de tocar nada viene bien `python3 scripts/spellcheck.py --dump`, que lista todas las palabras candidatas sin corregir.

**Se instalan los dos a propósito.** Ninguno es bueno por separado y sus lagunas son distintas: aspell rechaza `tutorial`, `chat`, `metadatos`, `resiliencia` o la grafía `guion` que la RAE fijó en 2010; hunspell rechaza `heurística`, `muestrear`, `milisegundos` o `estadísticamente`. Con `backend = "todos"` (el valor por defecto) una palabra solo se señala si **ninguno** la reconoce, lo que quita esos falsos positivos y deja la lista de excepciones en 133 entradas en lugar de 156. Se puede fijar uno concreto con `backend = "aspell"` o `"hunspell"`, pero entonces hay que alargar la lista.

El precio de cruzarlos es pequeño y conviene conocerlo. Sobre un juego de 26 erratas típicas del español, aspell en solitario detecta 23 y la política cruzada 22: lo único que se pierde es `Ademas`, porque hunspell acepta `ademas` como forma del verbo `ademar`. Las otras tres que se escapan (`mas`, `numero`, `practica`) son palabras válidas sin tilde y no las caza ningún corrector, se configure como se configure.

El script se salta por su cuenta las siglas en mayúscula (`RAG`, `MCP`) y los nombres en CamelCase (`GraphRAG`, `OpenTelemetry`), así que esos no hay que declararlos.

:warning: No se usa `codespell`: su diccionario es de erratas inglesas y sobre texto en español dispara decenas de falsos positivos (`hace`, `responde`, `ser`).

Sobre los enlaces, un detalle que el hook existe para pillar: los enlaces entre capítulos se escriben contra el fichero `.qmd` (`../modelos/inferencia.qmd#la-ventana-de-contexto`), no contra el `.html`, y **el título de un callout no genera ancla**. Para enlazar a un callout hay que darle un id explícito:

``` markdown
::: {#un-id .callout-warning}
# Título del callout
:::
```

## Publicación

[`.github/workflows/publish.yml`](.github/workflows/publish.yml) renderiza y publica en la rama `gh-pages` con cada `push` a `main`. Ojo con las dependencias: **el CI instala desde `requirements.txt`**, no desde `pyproject.toml`. Al añadir un paquete hay que actualizar los dos ficheros:

```bash
uv add <paquete>
uv export --no-hashes -o requirements.txt
```

## Contribuir

Las correcciones son bienvenidas, sobre todo las de datos que hayan caducado: el manual cita modelos, versiones y plazos legales de 2026 y esa es la parte que envejece primero.
