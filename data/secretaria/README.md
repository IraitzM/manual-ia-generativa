# El dominio de la secretaría académica

Este directorio contiene el caso que recorre el manual de principio a fin: el asistente de la secretaría de una universidad ficticia. Todos los cuadernos y todos los ejemplos de código a partir de la parte de contexto tiran de aquí.

Es el mismo dominio que usa el otro libro, [`ingenieria-datos`](https://github.com/IraitzM/ingenieria-datos), y eso no es casualidad. Allí se construye el almacén, aquí se consulta. Quien haya hecho los dos reconoce `dim_alumno`, `dim_asignatura` y `fct_matriculas` con los mismos nombres y las mismas columnas.

La diferencia es que aquí el almacén se **genera en local con datos sintéticos** en lugar de leerse del otro repositorio. Así el manual se ejecuta sin haber tocado el otro libro, y la continuidad se mantiene donde importa, que es el modelo de datos.

## Qué hay

```
data/secretaria/
├── generar.py       Genera el almacén DuckDB desde una semilla fija
├── secretaria.py    Arranque común de los cuadernos
└── corpus/          Los documentos que el RAG recupera
```

El fichero `secretaria.duckdb` no se versiona: sale de `generar.py` y ocupa 4 MB.

## Cómo se usa

Desde un cuaderno, en local o en Colab:

```python
from secretaria import preparar

ctx = preparar()
con = ctx.conectar()
docs = ctx.documentos()
```

`preparar()` clona el repositorio si hace falta, genera el almacén si no existe y devuelve las rutas. Desde la línea de comandos, para regenerarlo a mano:

```bash
uv run python data/secretaria/generar.py
```

La semilla está fija, así que dos ejecuciones dan el mismo fichero. Importa porque el arnés de evaluación compara contra respuestas escritas a mano.

## El esquema

Seis tablas, 711 filas. Las tres primeras vienen del almacén hermano; las tres últimas se añaden aquí porque son lo que el agente necesita y allí no existe.

| Tabla | Filas | Qué es |
|---|---|---|
| `dim_alumno` | 60 | Alumnado, con el correo institucional o personal |
| `dim_asignatura` | 22 | Plan de estudios, cuatro cursos |
| `fct_matriculas` | 300 | Matrículas del curso 2026-27 |
| `dim_plazo` | 14 | Plazos de cada trámite |
| `fct_calificaciones` | 279 | Expediente, con ordinaria y extraordinaria |
| `fct_solicitudes` | 36 | Trámites abiertos. La única tabla que el agente escribe |

Tres detalles que están puestos a propósito porque dan juego más adelante:

* **El 15 % del alumnado usa correo personal.** Es lo que da sentido a las columnas `tipo_correo` y `dominio_email`, y la excusa para hablar de datos personales en la parte de seguridad.
* **Quien suspende en ordinaria reaparece en extraordinaria.** Así la pregunta "¿cuántas convocatorias me quedan?" tiene una respuesta que hay que calcular, no leer.
* **El 30 % de las matrículas no tiene nota todavía.** El agente tiene que saber decir "aún no está publicada" en lugar de inventarse un número.

## El corpus

Cinco documentos en markdown, unos 22.000 caracteres en total. Están escritos a mano y en registro administrativo, que es distinto del registro en el que pregunta un alumno. Esa distancia entre cómo se pregunta y cómo está escrita la respuesta es justo lo que hace interesante el ejercicio de recuperación.

| Documento | Qué contiene |
|---|---|
| `normativa-matricula.md` | 22 artículos: plazos, convocatorias, permanencia, reconocimiento, becas |
| `calendario-academico.md` | Las mismas fechas en forma de tabla |
| `guia-docente-INF401.md` | IA generativa |
| `guia-docente-INF302.md` | Ingeniería de datos |
| `guia-docente-TFG401.md` | Trabajo de fin de grado |

Que la normativa y el calendario digan lo mismo de dos maneras distintas es deliberado. Un buen sistema de recuperación tiene que devolver el fragmento útil para la pregunta, y a veces el útil es la tabla y a veces el artículo.

Hay además tres sitios donde el corpus está escrito para provocar el error típico:

* **El TFG** distingue entre matricular, trabajar y defender con asignaturas pendientes. Es fácil que un modelo responda que no se puede matricular.
* **La beca general** se solicita en la sede del Ministerio, no en la de la universidad, y la normativa dice expresamente que la Secretaría no puede anticipar si se concederá. Es el caso que la parte de normativa usa para hablar de clasificación de riesgo.
* **El artículo 21** prohíbe que ningún canal, incluidos los automatizados, revele el expediente de una persona a otra. Es el requisito que la parte de seguridad tiene que hacer cumplir.

## Extenderlo

El corpus se queda corto para algunos ejercicios de troceado, así que crecerá. Basta con añadir un `.md` con frontmatter a `corpus/`: `ctx.documentos()` lo recoge solo.

Para el almacén, las listas de `generar.py` (`ASIGNATURAS`, `PLAZOS`, `TIPOS_SOLICITUD`) están al principio del fichero justo para que se puedan tocar sin leer el resto.
