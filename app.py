import streamlit as st
from db import engine
from sqlalchemy import text

st.set_page_config(page_title="Login", layout="centered")

st.title("Sistema de evaluación del Tenista")

st.image("tennis_cancha.jpg")

# Si ya está logeado, redirigir
if st.session_state.get("logged_in"):
    st.switch_page("pages/4_📅_Asistencias.py")

st.subheader("🔐 Iniciar sesión")

usuario = st.text_input("Usuario")
password = st.text_input("Contraseña", type="password")

if st.button("Ingresar"):
    query = text("""
        SELECT id_profesor, usuario, rol
        FROM profesores
        WHERE usuario = :usuario
          AND password = :password
          AND activo = TRUE
    """)

    with engine.begin() as conn:
        user = conn.execute(
            query,
            {"usuario": usuario, "password": password}
        ).fetchone()

    if user:
        st.session_state["logged_in"] = True
        st.session_state["id_profesor"] = user.id_profesor
        st.session_state["usuario"] = user.usuario
        st.session_state["rol"] = user.rol
        

        st.success("✅ Bienvenido")
        st.switch_page("pages/4_📅_Asistencias.py")
    else:
        st.error("❌ Usuario o contraseña incorrectos")

st.markdown(
    '''
    <a href="https://prod-useast-a.online.tableau.com/#/site/cgbsf/views/ControlindicadoresISO/Vista?:iid=1" target="_blank">
        <button style="padding:10px 16px; border-radius:8px;">
            🌐 Tableau
        </button>
    </a>
    ''',
    unsafe_allow_html=True
)

