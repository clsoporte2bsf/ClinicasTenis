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
    st.session_state.mensaje_ok = ""

# Fecha máxima permitida (3 años mínimo)
hoy = datetime.date.today()
try:
    max_fecha_nac = hoy.replace(year=hoy.year - 3)
except ValueError:
    max_fecha_nac = hoy.replace(year=hoy.year - 3, day=28)

# FORMULARIO
with st.form("form_usuario"):

    uploader_key = "foto_uploader" if not st.session_state.reset else "foto_uploader_reset"

    nombre = st.text_input("Nombre", value="" if st.session_state.reset else "")
    accion = st.text_input("Numero de Acción", value="" if st.session_state.reset else "")

    fecha_nac = st.date_input(
        "Fecha de nacimiento",
        value=max_fecha_nac if st.session_state.reset else datetime.date(2010, 1, 1),
        min_value=datetime.date(1950, 1, 1),
        max_value=max_fecha_nac
    )

    grupo = st.selectbox(
        "Grupo",
        ["Mini Tenis", "Principiantes - Intermedio", "Avanzados", "Equipo de competencia"],
        index=0
    )

    torneos = st.selectbox(
        "Torneos (Si/No)",
        ["Si", "No"],
        index=0
    )

    foto = st.file_uploader(
        "Subir foto (opcional)",
        type=["jpg", "png"],
        key=uploader_key
    )

    submit = st.form_submit_button("Guardar")


# PROCESAR ENVÍO
if submit:
    try:
        nombre_limpio = nombre.strip() if nombre else ""
        accion_limpia = accion.strip() if accion else ""
        foto_bytes = foto.read() if foto else None

        # VALIDACIONES
        if not nombre_limpio:
            st.error("El nombre es obligatorio.")

        elif not accion_limpia:
            st.error("Completa todos los campos.")

        elif fecha_nac > max_fecha_nac:
            st.error("La fecha de nacimiento debe ser al menos 3 años menor que hoy.")

        else:
            with engine.connect() as conn:

                # Validar duplicado nombre + accion
                existe = conn.execute(
                    text("""
                        SELECT 1
                        FROM public.alumno
                        WHERE UPPER(TRIM(nombre)) = UPPER(TRIM(:nombre))
                        AND TRIM(accion) = TRIM(:accion)
                        LIMIT 1
                    """),
                    {
                        "nombre": nombre_limpio,
                        "accion": accion_limpia
                    }
                ).fetchone()

                if existe:
                    st.error("Ya existe un alumno con ese nombre y número de acción.")

                else:
                    conn.execute(
                        text("""
                            INSERT INTO public.alumno
                            (nombre, accion, fecha_nacimiento, grupo, torneos, foto)
                            VALUES
                            (:nombre, :accion, :fecha_nacimiento, :grupo, :torneos, :foto)
                        """),
                        {
                            "nombre": nombre_limpio,
                            "accion": accion_limpia,
                            "fecha_nacimiento": fecha_nac,
                            "grupo": grupo,
                            "torneos": torneos,
                            "foto": foto_bytes
                        }
                    )

                    conn.commit()

                    # mensaje
                    st.session_state.mensaje_ok = "✅ Alumno guardado correctamente."

                    # activar reset
                    st.session_state.reset = True

                    st.rerun()

    except Exception as e:
        st.error("Ocurrió un error al guardar.")
        st.exception(e)