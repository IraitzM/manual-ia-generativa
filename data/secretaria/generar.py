"""Genera el almacén sintético de la secretaría académica.

Es el dominio que recorre el manual de principio a fin. El esquema respeta el
que produce el otro libro (`ingenieria-datos`) en su proyecto dbt de academia,
de modo que quien haya hecho los dos reconozca las mismas tablas, y lo extiende
con las tres cosas que el agente necesita y allí no existen: calificaciones,
plazos y solicitudes.

Todo sale de una semilla fija: dos ejecuciones producen el mismo fichero. Eso
importa porque los cuadernos comparan resultados y el arnés de evaluación tiene
respuestas esperadas escritas a mano.

    uv run python data/secretaria/generar.py
"""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import duckdb

SEMILLA = 20260826
CURSO = "2026-27"
DOMINIO_INSTITUCIONAL = "alumnos.uni-ficticia.es"

NOMBRES = [
    "Aitor", "Amaia", "Ane", "Asier", "Beñat", "Carla", "Diego", "Elena",
    "Gorka", "Haizea", "Ibai", "Iratxe", "Jon", "Julen", "Laia", "Leire",
    "Lucía", "Manex", "Marta", "Mikel", "Naia", "Nerea", "Oihana", "Pablo",
    "Paula", "Sergio", "Uxue", "Xabier", "Yeray", "Zuriñe",
]

APELLIDOS = [
    "Agirre", "Alonso", "Arrieta", "Bilbao", "Castro", "Etxebarria",
    "Fernández", "Gallego", "Garmendia", "Ibarra", "Iglesias", "Larrañaga",
    "López", "Mendoza", "Moreno", "Olabarria", "Ortega", "Ruiz", "Salazar",
    "Sánchez", "Urrutia", "Vidal", "Zabala", "Zubizarreta",
]

# (código, nombre, créditos, curso, semestre)
ASIGNATURAS = [
    ("MAT101", "Álgebra lineal", 6, 1, 1),
    ("MAT102", "Cálculo", 6, 1, 1),
    ("INF101", "Fundamentos de programación", 9, 1, 1),
    ("INF102", "Estructuras de datos", 6, 1, 2),
    ("FIS101", "Física para la computación", 6, 1, 2),
    ("MAT201", "Estadística", 6, 2, 1),
    ("INF201", "Bases de datos", 6, 2, 1),
    ("INF202", "Sistemas operativos", 6, 2, 1),
    ("INF203", "Redes de computadores", 6, 2, 2),
    ("INF204", "Ingeniería del software", 9, 2, 2),
    ("MAT301", "Optimización", 6, 3, 1),
    ("INF301", "Aprendizaje automático", 6, 3, 1),
    ("INF302", "Ingeniería de datos", 6, 3, 1),
    ("INF303", "Sistemas distribuidos", 6, 3, 2),
    ("INF304", "Procesamiento del lenguaje natural", 6, 3, 2),
    ("INF305", "Seguridad informática", 6, 3, 2),
    ("INF401", "Inteligencia artificial generativa", 6, 4, 1),
    ("INF402", "Arquitecturas de despliegue", 6, 4, 1),
    ("DER401", "Derecho digital y protección de datos", 3, 4, 1),
    ("INF403", "Ética y gobernanza de la IA", 3, 4, 2),
    ("EMP401", "Gestión de proyectos", 6, 4, 2),
    ("TFG401", "Trabajo de fin de grado", 12, 4, 2),
]

# (trámite, inicio, fin, descripción). Las fechas son las que el agente tiene
# que saber citar, así que aquí es donde hay que mirar si una prueba falla.
PLAZOS = [
    ("matricula_ordinaria", date(2026, 7, 15), date(2026, 7, 31),
     "Matrícula ordinaria para estudiantes con el curso anterior superado."),
    ("matricula_extraordinaria", date(2026, 9, 1), date(2026, 9, 10),
     "Matrícula extraordinaria, con recargo del 10 % sobre las tasas."),
    ("modificacion_matricula", date(2026, 10, 1), date(2026, 10, 15),
     "Alta y baja de asignaturas sin coste."),
    ("solicitud_beca_general", date(2026, 8, 1), date(2026, 10, 15),
     "Beca general del Ministerio. Se resuelve antes de marzo."),
    ("solicitud_beca_movilidad", date(2026, 9, 1), date(2026, 11, 30),
     "Ayuda de movilidad para estancias en otras universidades."),
    ("reconocimiento_creditos", date(2026, 9, 1), date(2026, 9, 30),
     "Reconocimiento de créditos cursados en otros estudios."),
    ("cambio_grupo", date(2026, 9, 15), date(2026, 9, 25),
     "Cambio de grupo de mañana a tarde o al revés."),
    ("convocatoria_ordinaria_s1", date(2027, 1, 12), date(2027, 1, 30),
     "Exámenes de la convocatoria ordinaria del primer semestre."),
    ("convocatoria_extraordinaria_s1", date(2027, 2, 9), date(2027, 2, 20),
     "Exámenes de la convocatoria extraordinaria del primer semestre."),
    ("convocatoria_ordinaria_s2", date(2027, 5, 25), date(2027, 6, 12),
     "Exámenes de la convocatoria ordinaria del segundo semestre."),
    ("convocatoria_extraordinaria_s2", date(2027, 6, 28), date(2027, 7, 10),
     "Exámenes de la convocatoria extraordinaria del segundo semestre."),
    ("defensa_tfg", date(2027, 6, 15), date(2027, 6, 30),
     "Defensa del trabajo de fin de grado ante tribunal."),
    ("revision_calificaciones", date(2027, 2, 1), date(2027, 2, 6),
     "Revisión de calificaciones. El plazo es de cinco días hábiles desde la publicación del acta."),
    ("anulacion_convocatoria", date(2026, 11, 1), date(2026, 12, 15),
     "Anulación de convocatoria, hasta dos por asignatura y titulación."),
]

TIPOS_SOLICITUD = [
    "reconocimiento_creditos",
    "cambio_grupo",
    "anulacion_convocatoria",
    "revision_calificacion",
    "certificado_academico",
]

ESTADOS_SOLICITUD = ["registrada", "en_tramite", "resuelta_favorable", "resuelta_desfavorable"]


def _sin_acentos(texto: str) -> str:
    tabla = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return texto.translate(tabla)


def _alumnos(rnd: random.Random, cuantos: int) -> list[dict]:
    """Un alumno por combinación única de nombre y dos apellidos.

    Una minoría usa correo personal en lugar del institucional. No es un
    detalle decorativo: es lo que da sentido a las columnas `dominio_email` y
    `tipo_correo` que hereda del almacén hermano, y da juego al hablar de
    datos personales en la parte de seguridad.
    """
    vistos: set[tuple[str, str, str]] = set()
    alumnos = []
    alta_base = date(2023, 9, 1)

    while len(alumnos) < cuantos:
        clave = (rnd.choice(NOMBRES), rnd.choice(APELLIDOS), rnd.choice(APELLIDOS))
        if clave in vistos or clave[1] == clave[2]:
            continue
        vistos.add(clave)

        nombre, ap1, ap2 = clave
        completo = f"{nombre} {ap1} {ap2}"
        usuario = _sin_acentos(f"{nombre}.{ap1}".lower())

        if rnd.random() < 0.15:
            dominio = rnd.choice(["gmail.com", "protonmail.com", "outlook.es"])
            tipo = "personal"
        else:
            dominio = DOMINIO_INSTITUCIONAL
            tipo = "institucional"

        idx = len(alumnos)
        alta = alta_base + timedelta(days=rnd.randint(0, 1000))
        alumnos.append(
            {
                "alumno_id": f"A{2023000 + idx:07d}",
                "nombre_completo": completo,
                "email": f"{usuario}{idx}@{dominio}",
                "dominio_email": dominio,
                "tipo_correo": tipo,
                "curso_actual": rnd.choices([1, 2, 3, 4], weights=[30, 28, 24, 18])[0],
                "alta_en_almacen": alta,
                "ultima_modificacion": alta + timedelta(days=rnd.randint(1, 400)),
            }
        )
    return alumnos


def _matriculas(rnd: random.Random, alumnos: list[dict]) -> list[dict]:
    """Cada alumno se matricula de lo suyo y arrastra algo pendiente de antes."""
    por_curso: dict[int, list[tuple]] = {}
    for asig in ASIGNATURAS:
        por_curso.setdefault(asig[3], []).append(asig)

    matriculas = []
    for alumno in alumnos:
        curso = alumno["curso_actual"]
        candidatas = list(por_curso.get(curso, []))

        # Casi todo el mundo arrastra alguna asignatura del curso anterior.
        if curso > 1 and rnd.random() < 0.55:
            candidatas += rnd.sample(por_curso[curso - 1], k=rnd.randint(1, 2))

        # El TFG solo se matricula si de verdad estás en cuarto.
        if curso < 4:
            candidatas = [a for a in candidatas if a[0] != "TFG401"]

        elegidas = rnd.sample(candidatas, k=min(len(candidatas), rnd.randint(4, 7)))
        for asig in elegidas:
            fecha = date(2026, 7, 15) + timedelta(days=rnd.randint(0, 16))
            if rnd.random() < 0.12:  # los rezagados van a la extraordinaria
                fecha = date(2026, 9, 1) + timedelta(days=rnd.randint(0, 9))
            matriculas.append(
                {
                    "matricula_id": f"M{len(matriculas) + 1:06d}",
                    "alumno_id": alumno["alumno_id"],
                    "asignatura_id": asig[0],
                    "curso_academico": CURSO,
                    "fecha_matricula": fecha,
                    "origen": "sede_electronica" if rnd.random() < 0.85 else "presencial",
                }
            )
    return matriculas


def _calificaciones(rnd: random.Random, matriculas: list[dict]) -> list[dict]:
    """El expediente. Solo el 70 % tiene nota: el resto está aún en curso.

    Quien suspende en ordinaria reaparece en extraordinaria, que es lo que hace
    que la pregunta "¿cuántas convocatorias me quedan?" tenga respuesta.
    """
    calificaciones = []
    for matricula in matriculas:
        if rnd.random() > 0.70:
            continue

        nota = round(min(10.0, max(0.0, rnd.gauss(6.1, 2.2))), 1)
        calificaciones.append(
            {
                "calificacion_id": f"C{len(calificaciones) + 1:06d}",
                "matricula_id": matricula["matricula_id"],
                "convocatoria": "ordinaria",
                "nota": nota,
                "fecha_acta": date(2027, 2, 3),
            }
        )

        if nota < 5.0:
            recuperada = round(min(10.0, max(0.0, rnd.gauss(5.4, 1.8))), 1)
            calificaciones.append(
                {
                    "calificacion_id": f"C{len(calificaciones) + 1:06d}",
                    "matricula_id": matricula["matricula_id"],
                    "convocatoria": "extraordinaria",
                    "nota": recuperada,
                    "fecha_acta": date(2027, 2, 24),
                }
            )
    return calificaciones


def _solicitudes(rnd: random.Random, alumnos: list[dict]) -> list[dict]:
    """Trámites ya abiertos. La tabla es la única que el agente escribe."""
    solicitudes = []
    for alumno in alumnos:
        for _ in range(rnd.choices([0, 1, 2], weights=[55, 33, 12])[0]):
            creacion = date(2026, 9, 1) + timedelta(days=rnd.randint(0, 120))
            solicitudes.append(
                {
                    "solicitud_id": f"S{len(solicitudes) + 1:06d}",
                    "alumno_id": alumno["alumno_id"],
                    "tipo": rnd.choice(TIPOS_SOLICITUD),
                    "estado": rnd.choices(ESTADOS_SOLICITUD, weights=[20, 30, 40, 10])[0],
                    "fecha_creacion": creacion,
                    "comentario": None,
                }
            )
    return solicitudes


ESQUEMA = """
drop table if exists fct_solicitudes;
drop table if exists fct_calificaciones;
drop table if exists fct_matriculas;
drop table if exists dim_plazo;
drop table if exists dim_asignatura;
drop table if exists dim_alumno;

-- Heredadas del almacén de `ingenieria-datos`, con los mismos nombres.
create table dim_alumno (
    alumno_id           varchar primary key,
    nombre_completo     varchar not null,
    email               varchar not null,
    dominio_email       varchar not null,
    tipo_correo         varchar not null,  -- institucional | personal
    curso_actual        integer not null,
    alta_en_almacen     date    not null,
    ultima_modificacion date    not null
);

create table dim_asignatura (
    asignatura_id varchar primary key,
    asignatura    varchar not null,
    creditos      integer not null,
    curso         integer not null,
    semestre      integer not null
);

create table fct_matriculas (
    matricula_id    varchar primary key,
    alumno_id       varchar not null references dim_alumno(alumno_id),
    asignatura_id   varchar not null references dim_asignatura(asignatura_id),
    curso_academico varchar not null,
    fecha_matricula date    not null,
    origen          varchar not null
);

-- Añadidas aquí: son lo que el agente necesita y el almacén hermano no tiene.
create table dim_plazo (
    plazo_id        varchar primary key,
    tramite         varchar not null,
    curso_academico varchar not null,
    fecha_inicio    date    not null,
    fecha_fin       date    not null,
    descripcion     varchar not null
);

create table fct_calificaciones (
    calificacion_id varchar primary key,
    matricula_id    varchar not null references fct_matriculas(matricula_id),
    convocatoria    varchar not null,  -- ordinaria | extraordinaria
    nota            double  not null,
    fecha_acta      date    not null
);

create table fct_solicitudes (
    solicitud_id   varchar primary key,
    alumno_id      varchar not null references dim_alumno(alumno_id),
    tipo           varchar not null,
    estado         varchar not null,
    fecha_creacion date    not null,
    comentario     varchar
);
"""


def generar(destino: Path, alumnos: int = 60) -> Path:
    rnd = random.Random(SEMILLA)

    filas_alumnos = _alumnos(rnd, alumnos)
    filas_matriculas = _matriculas(rnd, filas_alumnos)
    filas_calificaciones = _calificaciones(rnd, filas_matriculas)
    filas_solicitudes = _solicitudes(rnd, filas_alumnos)

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.unlink(missing_ok=True)

    con = duckdb.connect(str(destino))
    try:
        con.execute(ESQUEMA)

        con.executemany(
            "insert into dim_alumno values (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    a["alumno_id"], a["nombre_completo"], a["email"],
                    a["dominio_email"], a["tipo_correo"], a["curso_actual"],
                    a["alta_en_almacen"], a["ultima_modificacion"],
                )
                for a in filas_alumnos
            ],
        )
        con.executemany("insert into dim_asignatura values (?, ?, ?, ?, ?)", ASIGNATURAS)
        con.executemany(
            "insert into dim_plazo values (?, ?, ?, ?, ?, ?)",
            [
                (f"P{i + 1:03d}", tramite, CURSO, inicio, fin, desc)
                for i, (tramite, inicio, fin, desc) in enumerate(PLAZOS)
            ],
        )
        con.executemany(
            "insert into fct_matriculas values (?, ?, ?, ?, ?, ?)",
            [
                (
                    m["matricula_id"], m["alumno_id"], m["asignatura_id"],
                    m["curso_academico"], m["fecha_matricula"], m["origen"],
                )
                for m in filas_matriculas
            ],
        )
        con.executemany(
            "insert into fct_calificaciones values (?, ?, ?, ?, ?)",
            [
                (
                    c["calificacion_id"], c["matricula_id"], c["convocatoria"],
                    c["nota"], c["fecha_acta"],
                )
                for c in filas_calificaciones
            ],
        )
        con.executemany(
            "insert into fct_solicitudes values (?, ?, ?, ?, ?, ?)",
            [
                (
                    s["solicitud_id"], s["alumno_id"], s["tipo"], s["estado"],
                    s["fecha_creacion"], s["comentario"],
                )
                for s in filas_solicitudes
            ],
        )
    finally:
        con.close()

    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        type=Path,
        default=Path(__file__).parent / "secretaria.duckdb",
        help="Ruta del fichero DuckDB a generar.",
    )
    parser.add_argument("--alumnos", type=int, default=60)
    args = parser.parse_args()

    ruta = generar(args.destino, args.alumnos)

    con = duckdb.connect(str(ruta), read_only=True)
    tablas = [t[0] for t in con.execute("show tables").fetchall()]
    print(f"Almacén generado en {ruta}")
    for tabla in tablas:
        n = con.execute(f"select count(*) from {tabla}").fetchone()[0]
        print(f"  {tabla:20s} {n:6d} filas")
    con.close()


if __name__ == "__main__":
    main()
