import streamlit as st
from sqlalchemy import text
from db import engine
from datetime import time
from datetime import date

if not st.session_state.get("logged_in"):
    st.switch_page("app.py")

id_profesor = st.session_state["id_profesor"]


st.title("Evaluación del Alumno")

# ===============================
# INICIALIZACIÓN DE SESSION STATE
# ===============================
if "reset" not in st.session_state:
    st.session_state.reset = False

if "success_msg" not in st.session_state:
    st.session_state.success_msg = ""

# ================
# CARGAR ALUMNOS
# ================
with engine.connect() as conn:
    alumnos = conn.execute(text("SELECT id_alumno, nombre FROM alumno ORDER BY nombre")).fetchall()

lista_alumnos = {a.nombre: a.id_alumno for a in alumnos}

alumno_seleccionado = st.selectbox(
    "Selecciona un alumno:",
    list(lista_alumnos.keys()),
    key="alumno_select"
)

id_alumno = lista_alumnos[alumno_seleccionado] if alumno_seleccionado else None

# =====================
# MOSTRAR MENSAJE FINAL
# =====================
if st.session_state.success_msg:
    st.success(st.session_state.success_msg)
    st.session_state.success_msg = ""   # limpiar después de mostrar

if "reset_form" not in st.session_state:
    st.session_state.reset_form = False

# =====================
# FORMULARIO PRINCIPAL
# =====================
with st.form("form_eval", clear_on_submit=st.session_state.reset):

    st.subheader("Disciplina y habilidad atlética")

    col1, col2, col3 = st.columns(3)

    # --------------------
    # COLUMNA 1
    # --------------------

    with col1:
        fecha_evaluacion = st.date_input(
            "📆 Fecha de evaluación",
            value=date.today()
        )
        conducta = st.number_input("Conducta", 7, 13, step=1, key="conducta")
        balance = st.number_input("Balance", 7, 13, step=1, key="balance")
        movilidad = st.number_input("Movilidad", 7, 13, step=1, key="movilidad")

    # --------------------
    # COLUMNA 2
    # --------------------
    with col2:
        tipo_evaluacion = st.selectbox(
            "Tipo de evaluación",
        ["Diagnóstico", "Principal", "Seguimiento"]
        )
        atencion = st.number_input("Atención", 7, 13, step=1, key="atencion")
        fuerza = st.number_input("Fuerza", 7, 13, step=1, key="fuerza")
        coordinacion = st.number_input("Coordinación", 7, 13, step=1, key="coordinacion")

    # --------------------
    # COLUMNA 3
    # --------------------
    with col3:
        profesor = st.selectbox(
            "Profesor",
            ["Rene Moreno", "Uriel Parra", "Salvador Morales", "Ricardo Rosas", "Julio Rendon"],
            key="profesor"
        )
        esfuerzo = st.number_input("Esfuerzo", 7, 13, step=1, key="esfuerzo")
        velocidad = st.number_input("Velocidad", 7, 13, step=1, key="velocidad")
        periodo = st.selectbox(
            "Periodo",
            ["1er", "2do", "3er"],
            key="periodo_select"
        )

    # =====================
    # TÉCNICA
    # =====================
    st.subheader("Técnica")

    golpes_catalogo = [
        "Derecha", "Reves", "Volea derecha",
        "Volea revés", "Remate", "Servicio"
    ]

    golpes_data = {}

    for golpe in golpes_catalogo:
        st.markdown(f"##### {golpe}")

        c1, c2, c3 = st.columns(3)

        with c1:
            prep = st.number_input(f"{golpe} - Preparación", 7, 13, step=1, key=f"{golpe}_prep")
        with c2:
            cont = st.number_input(f"{golpe} - Contacto", 7, 13, step=1, key=f"{golpe}_cont")
        with c3:
            term = st.number_input(f"{golpe} - Terminación", 7, 13, step=1, key=f"{golpe}_term")

        golpes_data[golpe] = (prep, cont, term)

    recomendaciones = st.text_area("Recomendaciones (opcional)", key="recomendaciones")

    submit = st.form_submit_button("Guardar Evaluación")
    
# =====================
# MOSTRAR MENSAJE FINAL
# =====================
if st.session_state.success_msg:
    st.success(st.session_state.success_msg)
    st.session_state.success_msg = ""   # limpiar después de mostrar

# =====================
# PROCESAR ENVÍO
# =====================

if submit:
    try:
        # 🔹 Obtener grupo actual del alumno
        query_grupo = text("""
            SELECT grupo
            FROM alumno
            WHERE id_alumno = :id_alumno
        """)
        anio = fecha_evaluacion.year

        with engine.begin() as conn:
            grupo_alumno = conn.execute(
                query_grupo,
                {"id_alumno": id_alumno}
            ).scalar()
            insert_eval = text("""
            INSERT INTO evaluaciones (
                id_alumno, conducta, atencion, esfuerzo,
                balance, movilidad, fuerza,
                coordinacion, velocidad, profesor, periodo,
                recomendaciones, id_profesor, fecha_evaluacion, tipo_evaluacion, grupo, anio
            )
            VALUES (
                :id_alumno, :conducta, :atencion, :esfuerzo,
                :balance, :movilidad, :fuerza,
                :coordinacion, :velocidad, :profesor, :periodo,
                :recomendaciones, :id_profesor, :fecha_evaluacion, :tipo_evaluacion, :grupo, :anio
            )
            RETURNING id_evaluacion;
        """)

        with engine.begin() as conn:
            result = conn.execute(insert_eval, {
                "id_alumno": id_alumno,
                "conducta": conducta,
                "atencion": atencion,
                "esfuerzo": esfuerzo,
                "balance": balance,
                "movilidad": movilidad,
                "fuerza": fuerza,
                "coordinacion": coordinacion,
                "velocidad": velocidad,
                "profesor": profesor,
                "periodo": periodo,
                "recomendaciones": recomendaciones,
                "id_profesor": id_profesor,
                "fecha_evaluacion": fecha_evaluacion, 
                "tipo_evaluacion": tipo_evaluacion,
                "grupo": grupo_alumno,
                "anio": anio
            })

            id_evaluacion = result.fetchone()[0]

            insert_golpe = text("""
                INSERT INTO evaluacion_tecnica (
                    id_evaluacion, id_golpe, preparacion, contacto, terminacion
                )
                VALUES (
                    :id_evaluacion,
                    (SELECT id_golpe FROM golpes WHERE nombre_golpe = :nombre_golpe),
                    :prep, :cont, :term
                );
            """)

            for golpe, valores in golpes_data.items():
                prep, cont, term = valores
                conn.execute(insert_golpe, {
                    "id_evaluacion": id_evaluacion,
                    "nombre_golpe": golpe,
                    "prep": prep,
                    "cont": cont,
                    "term": term
                })

        # ======================================
        # GUARDAR MENSAJE
        # ======================================
        st.session_state.success_msg = "✅ Evaluación registrada correctamente."

        # ======================================
        # RESETEAR TODOS LOS CAMPOS DEL FORM
        # ======================================
        keys_to_reset = [
            "conducta", "balance", "movilidad",
            "atencion", "fuerza", "coordinacion", "profesor", 
            "esfuerzo", "velocidad", "periodo_select", 
            "recomendaciones", "alumno_select"
        ]

        # Agregar dinámicamente las keys de golpes
        for golpe in golpes_catalogo:
            keys_to_reset.append(f"{golpe}_prep")
            keys_to_reset.append(f"{golpe}_cont")
            keys_to_reset.append(f"{golpe}_term")

        for k in keys_to_reset:
            if k in st.session_state:
                del st.session_state[k]

        # Rerun limpio
        st.rerun()

    except Exception as e:
        st.error("❌ Ocurrió un error al guardar la evaluación.")
        st.write(e)
