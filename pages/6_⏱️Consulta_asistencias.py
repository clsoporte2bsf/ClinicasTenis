import streamlit as st
import pandas as pd
from sqlalchemy import text
import plotly.express as px
from db import engine

# Login
if not st.session_state.get("logged_in"):
    st.switch_page("app.py")


st.title("Consulta de asistencias")

# =============================
# FILTROS
# =============================

col1,col2,col3 = st.columns(3)

with col1:
    tipo_consulta = st.selectbox(
        "Tipo de consulta",
        ["Alumno","Grupo","General"]
    )

with col2:
    fecha_inicio = st.date_input("Fecha inicio")

with col3:
    fecha_fin = st.date_input("Fecha fin")


# =============================
# FILTRO ALUMNO
# =============================

id_alumno = None
id_grupo = None

if tipo_consulta == "Alumno":

    alumnos = pd.read_sql(
        "SELECT id_alumno, nombre FROM alumno ORDER BY nombre",
        engine
    )

    alumno_nombre = st.selectbox(
        "Alumno",
        alumnos["nombre"]
    )

    id_alumno = int(alumnos.loc[
        alumnos["nombre"] == alumno_nombre,
        "id_alumno"
    ].values[0])


# =============================
# FILTRO GRUPO
# =============================

if tipo_consulta == "Grupo":

    grupos = pd.read_sql(
        "SELECT grupo FROM alumno ORDER BY grupo",
        engine
    )

    grupo_nombre = st.selectbox(
        "Grupo",
        grupos["grupo"]
    )

# =============================
# BOTON CONSULTAR
# =============================

if st.button("Consultar"):

    params = {}   # ← IMPORTANTE

    # -----------------------------
    # CONSULTA BASE
    # -----------------------------

    if tipo_consulta == "Alumno":

        query = """
        SELECT a.fecha, a.estado, al.nombre
        FROM asistencias a
        JOIN alumno al ON al.id_alumno = a.id_alumno
        WHERE a.id_alumno = :id
        AND a.fecha BETWEEN :fi AND :ff
        ORDER BY a.fecha
        """

        params = {
            "id": id_alumno,
            "fi": fecha_inicio,
            "ff": fecha_fin
        }


    elif tipo_consulta == "Grupo":

        query = """
        SELECT a.fecha, a.estado, al.nombre, al.grupo
        FROM asistencias a
        JOIN alumno al ON al.id_alumno = a.id_alumno
        WHERE al.grupo = :grupo
        AND a.fecha BETWEEN :fi AND :ff
        ORDER BY al.nombre, a.fecha
        """

        params = {
            "grupo": grupo_nombre,
            "fi": fecha_inicio,
            "ff": fecha_fin
        }


    else:

        query = """
        SELECT a.fecha, a.estado, al.nombre
        FROM asistencias a
        JOIN alumno al ON al.id_alumno = a.id_alumno
        WHERE a.fecha BETWEEN :fi AND :ff
        ORDER BY a.fecha
        """

        params = {
            "fi": fecha_inicio,
            "ff": fecha_fin
        }


    df = pd.read_sql(text(query), engine, params=params)


    # =============================
    # RESULTADOS
    # =============================

    if df.empty:

        st.warning("No hay registros en ese periodo")

    else:

        total = len(df)

        asistencias = (df["estado"] == "Asistió").sum()
        faltas = (df["estado"] == "Falta").sum()
        retardos = (df["estado"] == "Retardo").sum()

        porcentaje = round((asistencias/total)*100,1)


        col1,col2,col3,col4 = st.columns(4)

        col1.metric("Total clases", total)
        col2.metric("Asistencias", asistencias)
        col3.metric("Faltas", faltas)
        col4.metric("Retardos", retardos)

        st.metric("Porcentaje asistencia", f"{porcentaje}%")


        # =============================
        # GRAFICA
        # =============================

        graf = pd.DataFrame({
            "Estado":["Asistió","Falta","Retardo"],
            "Cantidad":[asistencias,faltas,retardos]
        })

        fig = px.pie(
            graf,
            names="Estado",
            values="Cantidad",
            hole=0.5
        )

        st.plotly_chart(fig)


        # =============================
        # TABLA DETALLADA
        # =============================

        st.subheader("Detalle")

        df = df.sort_values("fecha")

        st.dataframe(
            df,
            use_container_width=True
        )