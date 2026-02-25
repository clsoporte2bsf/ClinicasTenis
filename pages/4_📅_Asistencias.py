import streamlit as st
from sqlalchemy import text
from datetime import date
from db import engine

# 🔐 Validar login
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")

st.title("📅 Registro de Asistencias")

if "id_profesor" not in st.session_state:
    st.warning("Debes iniciar sesión")
    st.stop()

id_profesor = st.session_state["id_profesor"]

# Alumnos
query_alumnos = text("""
    SELECT id_alumno, nombre
    FROM alumno
    ORDER BY nombre
""")
with engine.begin() as conn:
    alumnos = conn.execute(query_alumnos).fetchall()

alumnos_dict = {a.nombre: a.id_alumno for a in alumnos}
opciones = ["-- Selecciona alumno --"] + list(alumnos_dict.keys())

# ✅ Widgets reactivos (FUERA del form)
alumno_sel = st.selectbox("👤 Alumno", opciones)
fecha = st.date_input("📆 Fecha de la clase", value=date.today())

estado = st.radio("Estado", ["Asistió", "Falta", "Retardo"], horizontal=True)

hora_llegada = None
if estado == "Retardo":
    hora_llegada = st.time_input("⏰ Hora de llegada")

# ✅ Form solo para texto + submit (puede incluir todo lo demás si quieres,
# pero la parte reactiva debe estar fuera)
with st.form("form_asistencia", clear_on_submit=True):
    observaciones = st.text_area("📝 Observaciones (opcional)")
    guardar = st.form_submit_button("💾 Guardar asistencia")

if guardar:
    if alumno_sel.startswith("--"):
        st.warning("Selecciona un alumno")
        st.stop()

    id_alumno = alumnos_dict[alumno_sel]

    try:
        query_insert = text("""
            INSERT INTO asistencias
            (id_alumno, fecha, estado, hora_llegada, observaciones, id_profesor)
            VALUES
            (:id_alumno, :fecha, :estado, :hora_llegada, :obs, :id_profesor)
        """)
        with engine.begin() as conn:
            conn.execute(query_insert, {
                "id_alumno": id_alumno,
                "fecha": fecha,
                "estado": estado,
                "hora_llegada": hora_llegada,
                "obs": observaciones,
                "id_profesor": id_profesor
            })

        st.success("✅ Asistencia registrada correctamente")

    except Exception:
        st.error("❌ Ya existe una asistencia para este alumno en esta fecha")
