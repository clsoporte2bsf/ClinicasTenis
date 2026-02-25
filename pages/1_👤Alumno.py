import streamlit as st
from sqlalchemy import text
from db import engine
import datetime

# Login
if not st.session_state.get("logged_in"):
    st.switch_page("app.py")

st.title("Registro de Alumno")
st.write("Completa la información del alumno.")

# Variables persistentes
if "reset" not in st.session_state:
    st.session_state.reset = False

if "mensaje_ok" not in st.session_state:
    st.session_state.mensaje_ok = ""

# Mostrar mensaje después del reset
if st.session_state.mensaje_ok:
    st.success(st.session_state.mensaje_ok)
    st.session_state.mensaje_ok = ""   # limpiar para la siguiente vuelta

# FORMULARIO
with st.form("form_usuario"):

    # Cambiar el key para forzar reinicio del file_uploader
    uploader_key = "foto_uploader" if not st.session_state.reset else "foto_uploader_reset"

    nombre = st.text_input("Nombre", value="" if st.session_state.reset else None)
    accion = st.text_input("Numero de Acción", value="" if st.session_state.reset else None)

    fecha_nac = st.date_input(
        "Fecha de nacimiento",
        value=datetime.date.today() if st.session_state.reset else datetime.date(2010, 1, 1),
        min_value=datetime.date(1950, 1, 1),
        max_value=datetime.date.today()
    )

    grupo = st.selectbox(
        "Grupo",
        ["Mini Tenis", "Principiantes - Intermedio", "Avanzados", "Equipo de competencia",],
        index=0 if st.session_state.reset else None
    )

    torneos = st.selectbox(
        "Torneos (Si/No)",
        ["Si", "No"],
        index=0 if st.session_state.reset else None
    )

    # ⬅️ AQUÍ está la solución
    foto = st.file_uploader(
        "Subir foto (opcional)",
        type=["jpg", "png"],
        key=uploader_key
    )

    submit = st.form_submit_button("Guardar")


# PROCESAR ENVÍO
if submit:
    st.session_state.reset = False  # evita reset accidental

    if not nombre:
        st.error("El nombre es obligatorio.")
    else:
        try:
            foto_bytes = foto.read() if foto else None

            query = text("""
                INSERT INTO alumno (nombre, accion, fecha_nacimiento, grupo, torneos, foto)
                VALUES (:nombre, :accion, :fecha_nacimiento, :grupo, :torneos, :foto)
            """)

            with engine.begin() as conn:
                conn.execute(
                    query,
                    {
                        "nombre": nombre,
                        "accion": accion,
                        "fecha_nacimiento": fecha_nac,
                        "grupo": grupo,
                        "torneos": torneos,
                        "foto": foto_bytes
                    }
                )

            # Guardar mensaje
            st.session_state.mensaje_ok = "✅ Alumno guardado correctamente."

            # Activar reset
            st.session_state.reset = True
            st.rerun()

        except Exception as e:
            st.error("Ocurrió un error al guardar.")
            st.write(e)
