# Manual de IA Generativa

Manual de referencia en español sobre IA generativa, escrito en [Quarto](https://quarto.org/). Cubre desde cómo funciona un modelo por dentro hasta lo que hace falta para que un agente viva en una empresa sin causar un disgusto.

Publicado en [iraitzm.github.io/manual-ia-generativa](https://iraitzm.github.io/manual-ia-generativa/).

## Qué hay aquí

| Componente | Qué es | Por dónde empezar |
|---|---|---|
| **El manual** | El libro en sí, cinco partes y tres apéndices | [`index.qmd`](index.qmd) o el [sitio publicado](https://iraitzm.github.io/manual-ia-generativa/) |
| **Los cuadernos** | Material de formación ejecutable en Colab | [`notebooks/`](notebooks/) y el [apéndice que los describe](parts/apendices/cuadernos.qmd) |

El contenido vive en [`parts/`](parts/) y el índice de capítulos está en [`_quarto.yaml`](_quarto.yaml):

| Parte | Directorio | De qué va |
|---|---|---|
| Modelos generativos | [`parts/modelos/`](parts/modelos/) | Qué es un modelo generativo, transformers, inferencia y panorama de modelos |
| Contexto | [`parts/contexto/`](parts/contexto/) | Ingeniería de contexto, prompting y recuperación |
| Agentes | [`parts/agentes/`](parts/agentes/) | Bucle de agente, herramientas y MCP, orquestación y frameworks |
| Producción | [`parts/produccion/`](parts/produccion/) | Ecosistema, gateways, evaluación y observabilidad |
| Normativa y seguridad | [`parts/seguridad/`](parts/seguridad/), [`parts/normativa/`](parts/normativa/) | Inyección de prompt, defensas y AI Act |
| Apéndices | [`parts/apendices/`](parts/apendices/) | Cuadernos, copilotos y método, glosario |

## Convenciones

Dos cosas que conviene respetar al escribir un capítulo nuevo:

**El código de color de los diagramas.** Todos los `mermaid` usan el mismo `classDef`, explicado en [la introducción](parts/intro.qmd#cómo-leer-los-diagramas): violeta para el modelo, azul para el contexto, ámbar para las herramientas, verde para el control, gris para lo que no controlamos y rojo para el riesgo. Se copia y se pega tal cual del capítulo más cercano.

**Las citas van al `.bib`.** Los trabajos citados están en [`parts/references.bib`](parts/references.bib) y se referencian con `[@clave]`. Los estándares y marcos que cambian de versión (OWASP, MCP, AI Act) se enlazan a su documentación, no se citan.

## Renderizarlo en local

```bash
uv sync
quarto preview
```

El resultado se deja en `_book/`, que no se versiona. Los capítulos no ejecutan código por ahora, así que el render es rápido y no necesita intérprete de Python configurado.

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
