---
titulo: Guía docente de Ingeniería de datos
asignatura_id: INF302
creditos: 6
curso: 3
semestre: 1
idioma: castellano
---

# Ingeniería de datos (INF302)

Guía docente ficticia, escrita como corpus de ejemplo para el manual.

## Datos básicos

| Campo | Valor |
|---|---|
| Código | INF302 |
| Créditos ECTS | 6 |
| Curso | Tercero |
| Semestre | Primero |
| Carácter | Obligatoria |
| Idioma | Castellano |

## Requisitos previos

Es imprescindible haber superado Bases de datos (INF201). Quien la arrastre puede matricularse, pero la asignatura arranca dando por sabido el modelo relacional y el SQL de agregación.

## Competencias

Modelar un almacén de datos, distinguir cuándo conviene normalizar y cuándo desnormalizar, construir procesos de carga reproducibles y auditables, y razonar sobre la calidad del dato con pruebas automáticas en lugar de con inspección manual.

## Contenidos

1. Del sistema operacional al analítico. Por qué no se consulta la base de producción.
2. Modelado: formas normales, modelo en estrella y Data Vault.
3. Ingesta y capa de preparación.
4. Transformación declarativa y linaje.
5. Calidad del dato y pruebas.
6. Explotación: cuadros de mando y consumo por sistemas automáticos.

## Metodología

La asignatura se construye sobre un caso único que se arrastra de la primera sesión a la última: el almacén de la secretaría académica de esta misma universidad, con sus alumnos, sus asignaturas y sus matrículas.

El caso se elige a propósito por ser conocido para el estudiantado, que así puede juzgar si el modelo representa bien la realidad que vive.

## Evaluación

| Instrumento | Peso | Convocatoria |
|---|---|---|
| Entregas del caso | 50 % | Continua, cuatro entregas |
| Prueba práctica | 30 % | Ordinaria y extraordinaria |
| Prueba escrita | 20 % | Ordinaria y extraordinaria |

Las entregas del caso son recuperables en convocatoria extraordinaria mediante una entrega única que agrupa las cuatro.

## Relación con otras asignaturas

El almacén que se construye aquí es el que consume Inteligencia artificial generativa (INF401) en su bloque de agentes. Quien curse las dos verá las mismas tablas desde los dos lados: aquí se construyen, allí se consultan.
