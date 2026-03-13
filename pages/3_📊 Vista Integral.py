import streamlit as st
import plotly.graph_objects as go
from sqlalchemy import text
from db import engine
from datetime import date
from datetime import timedelta, date, datetime
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px

st.title("Seguimiento Tecnico del Tenista")

# ============================
# 1️⃣ FILTROS
# ============================

# Estado para colapsar filtros
if "filtros_listos" not in st.session_state:
    st.session_state.filtros_listos = False
    
    # Login
if not st.session_state.get("logged_in"):
    st.switch_page("app.py")

# ============================
# 👤 ALUMNOS
# ============================
query_alumnos = text("""
SELECT id_alumno, nombre
FROM alumno
ORDER BY nombre
""")

with engine.begin() as conn:
    alumnos = conn.execute(query_alumnos).fetchall()

alumnos_dict = {a.nombre: a.id_alumno for a in alumnos}

# ============================
# 🎛️ EXPANDER DE FILTROS
# ============================
with st.expander("🎛️ Filtros", expanded=not st.session_state.filtros_listos):

    # 👤 Alumno
    alumno_nombre = st.selectbox(
        "👤 Alumno",
        ["-- Selecciona alumno --"] + list(alumnos_dict.keys())
    )

    if alumno_nombre.startswith("--"):
        st.stop()

    id_alumno = alumnos_dict[alumno_nombre]

    # ============================
    # 📅 Año
    # ============================
    query_anios = text("""
    SELECT DISTINCT anio
    FROM evaluaciones
    WHERE id_alumno = :id
    ORDER BY anio DESC
    """)

    with engine.begin() as conn:
        anios = [r.anio for r in conn.execute(query_anios, {"id": id_alumno})]

    if not anios:
        st.info("Este alumno no tiene evaluaciones registradas")
        st.stop()

    anio = st.selectbox("📅 Año", anios)

    # ============================
    # 📘 Periodo
    # ============================
    periodo = st.selectbox(
        "📘 Periodo de evaluación",
        ["1er", "2do", "3er"]
    )

    # ============================
    # 🧪 Tipo de evaluación
    # ============================
    st.markdown("**Tipo de evaluación**")

    tipo_eval = None
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🧪 Diagnóstico"):
            tipo_eval = "Diagnóstico"

    with col2:
        if st.button("🏆 Principal"):
            tipo_eval = "Principal"

    with col3:
        if st.button("🔁 Seguimiento"):
            tipo_eval = "Seguimiento"

    if not tipo_eval:
        st.stop()

# ============================
# ✅ MARCAR FILTROS COMO LISTOS
# ============================
st.session_state.filtros_listos = True

#TRAER EVALUACION
query_eval = text("""
SELECT *
FROM evaluaciones
WHERE id_alumno = :id
  AND anio = :anio
  AND periodo = :periodo
  AND tipo_evaluacion = :tipo
ORDER BY fecha_evaluacion DESC
LIMIT 1
""") 

with engine.begin() as conn:
    evaluacion = conn.execute(
        query_eval,
        {
            "id": id_alumno,
            "anio": anio,
            "periodo": periodo,
            "tipo": tipo_eval
        }
    ).fetchone()

if not evaluacion:
    st.warning("No existe esa evaluación")
    st.stop()

st.markdown(f"""
<div style="
    background:#f8fafc;
    border-radius:12px;
    padding:10px 14px;
    font-size:14px;
    margin-bottom:12px;
">
👤 <strong>{alumno_nombre}</strong> · 📅 {anio} · 📘 {periodo} · 🧪 {tipo_eval}
</div>
""", unsafe_allow_html=True)

# ============================
# 🧾 TARJETA DEL ALUMNO
# ============================

query_alumno = text("""
SELECT foto, fecha_nacimiento, accion, grupo, torneos
FROM alumno
WHERE id_alumno = :id
""")

with engine.begin() as conn:
    alumno = conn.execute(query_alumno, {"id": id_alumno}).fetchone()

# 🧮 Edad al momento de la evaluación
fecha_eval = evaluacion.fecha_evaluacion
fecha_nac = alumno.fecha_nacimiento

edad = fecha_eval.year - fecha_nac.year
if (fecha_eval.month, fecha_eval.day) < (fecha_nac.month, fecha_nac.day):
    edad -= 1

# ============================
# 🧱 CONTENEDOR VISUAL
# ============================
st.markdown("""
<div style="
    border: 1px solid #e0e0e0;
    padding: 20px;
    border-radius: 14px;
    background-color: #ffffff;
    margin-bottom: 25px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
">
""", unsafe_allow_html=True)

col_img, col_info, col_extra = st.columns([2.5, 2.4, 2.3])

# 📸 Foto
with col_img:
    if alumno.foto:
        st.image(bytes(alumno.foto), width=260)
    else:
        st.info("📷 Sin foto")

# 🧾 Info principal
with col_info:
    st.markdown(f"""
        <h3 style="margin-bottom:6px;">{alumno_nombre}</h3>
        <p style="margin:2px 0;">Edad: <strong>{edad} años</strong></p>
        <p style="font-size:16px; margin-top:0;">
            Profesor: <strong>{evaluacion.profesor}</strong>
        </p>
        <p style="margin:6px 0;">
            📘 <strong>{evaluacion.periodo} periodo {evaluacion.anio}</strong>
        </p>
    """, unsafe_allow_html=True)

# 📋 Info secundaria
with col_extra:
    if alumno.grupo:
        st.markdown(f"👥 Grupo: <strong>{alumno.grupo}</strong>", unsafe_allow_html=True)

    if alumno.torneos:
        st.markdown(f"🏆 Torneos: <strong>{alumno.torneos}</strong>", unsafe_allow_html=True)

    st.markdown(
        f"📅 Evaluación: <strong>{fecha_eval.strftime('%d/%m/%Y')}</strong>",
        unsafe_allow_html=True
    )

    st.markdown(
        f"🧪 Tipo: <strong>{evaluacion.tipo_evaluacion}</strong>",
        unsafe_allow_html=True
    )

st.markdown("</div>", unsafe_allow_html=True)


# ============================
# 🧮 CÁLCULOS DE KPIs
# ============================
# Disciplina
disciplina_vals = [
    evaluacion.conducta,
    evaluacion.atencion,
    evaluacion.esfuerzo
]
prom_disciplina = round(sum(disciplina_vals) / len(disciplina_vals), 1)

# Habilidad atlética
habilidad_vals = [
    evaluacion.balance,
    evaluacion.movilidad,
    evaluacion.fuerza,
    evaluacion.coordinacion,
    evaluacion.velocidad
]
prom_habilidad = round(sum(habilidad_vals) / len(habilidad_vals), 1)

# Técnica (desde evaluacion_tecnica)
query_tecnica = text("""
SELECT preparacion, contacto, terminacion
FROM evaluacion_tecnica
WHERE id_evaluacion = :id
""")

with engine.begin() as conn:
    tecnica_rows = conn.execute(
        query_tecnica, {"id": evaluacion.id_evaluacion}
    ).fetchall()

tecnica_vals = []
for t in tecnica_rows:
    tecnica_vals.extend([t.preparacion, t.contacto, t.terminacion])

prom_tecnica = round(sum(tecnica_vals) / len(tecnica_vals), 1) if tecnica_vals else 0

# TOTAL GLOBAL
total_eval = round(
    (prom_disciplina + prom_habilidad + prom_tecnica) / 3, 1
)

# GUGE 
st.markdown("## Resultados de la Evaluación")

col_gauge, col_kpis, col_nivel = st.columns([2.8, 2.5, 1.5])

col_gauge, col_kpis = st.columns([4, 3])
with col_gauge:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(total_eval, 2),
        number={"font": {"size": 38}},
        title={"text": "Calificación Final", "font": {"size": 20}},
        gauge={
            "axis": {"range": [7, 13]},
            "bar": {"color": "#2563eb"},
            "steps": [
                {"range": [7, 9], "color": "#eff6ff"},
                {"range": [9, 11], "color": "#bfdbfe"},
                {"range": [11, 13], "color": "#60a5fa"},
            ],
            "threshold": {
                "line": {"color": "black", "width": 4},
                "thickness": 0.75,
                "value": total_eval
            }
        }
    ))
    fig_gauge.update_layout(
        height=300,
        margin=dict(t=40, b=10, l=10, r=10)
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

# KPI'S
with col_kpis:
    st.metric(
        label="🧠 Disciplina",
        value=round(prom_disciplina, 2)
    )

    st.metric(
        label="🏃 Habilidad Atlética",
        value=round(prom_habilidad, 2)
    )

    st.metric(
        label="🎾 Técnica",
        value=round(prom_tecnica, 2)
    )

# MOSTRAR NIVEL
# CONSULTA DE NIVEL 
query_nivel = text("""
SELECT nivel
FROM niveles
WHERE :valor BETWEEN valor_min AND valor_max
LIMIT 1
""")

with engine.begin() as conn:
    nivel_eval = conn.execute(
        query_nivel, {"valor": total_eval}
    ).scalar()

# # MOSTRAR NIVEL
with col_nivel:
    st.markdown(f"""
        <div style="
            margin-top:01px;
        ">
            <div style="
                padding:25px 20px;
                border-radius:30px;
                background-color:#f0f4f8;
                font-size:17px;
                text-align:center;
                min-width:180px;
            ">
                <strong>Nivel:</strong> {nivel_eval}
            </div>
        </div>
    """, unsafe_allow_html=True)

#-------------------------------------
# TABLA HABILIDAD TECNICA Y ASISTENCIA
#-------------------------------------
col_tabla, col_asist = st.columns([1.2, 1.8])

with col_tabla:
    tabla_html = f"""
<div style="
    background:#ffffff;
    border-radius:20px;
    padding:16px;
    box-shadow:0 4px 12px rgba(0,0,0,0.05);
">
<table style="width:100%; border-collapse:collapse; font-size:15px;">

<tr>
    <th colspan="2" style="padding:10px; background:#f5f7fa;">
        🧠 Disciplina
    </th>
</tr>
<tr>
    <td style="padding:8px;">Conducta</td>
    <td style="padding:8px; text-align:center;"><strong>{evaluacion.conducta}</strong></td>
</tr>
<tr>
    <td style="padding:8px;">Atención</td>
    <td style="padding:8px; text-align:center;"><strong>{evaluacion.atencion}</strong></td>
</tr>
<tr>
    <td style="padding:8px;">Esfuerzo</td>
    <td style="padding:8px; text-align:center;"><strong>{evaluacion.esfuerzo}</strong></td>
</tr>

<tr>
    <th colspan="2" style="padding:10px; background:#f5f7fa;">
        🏃‍♂️ Habilidad Atlética
    </th>
</tr>
<tr>
    <td style="padding:8px;">Balance</td>
    <td style="padding:8px; text-align:center;"><strong>{evaluacion.balance}</strong></td>
</tr>
<tr>
    <td style="padding:8px;">Movilidad</td>
    <td style="padding:8px; text-align:center;"><strong>{evaluacion.movilidad}</strong></td>
</tr>
<tr>
    <td style="padding:8px;">Fuerza</td>
    <td style="padding:8px; text-align:center;"><strong>{evaluacion.fuerza}</strong></td>
</tr>
<tr>
    <td style="padding:8px;">Coordinación</td>
    <td style="padding:8px; text-align:center;"><strong>{evaluacion.coordinacion}</strong></td>
</tr>
<tr>
    <td style="padding:8px;">Velocidad</td>
    <td style="padding:8px; text-align:center;"><strong>{evaluacion.velocidad}</strong></td>
</tr>

</table>
</div>
"""
    st.markdown(tabla_html, unsafe_allow_html=True)

# ============================
# DEFINIR RANGO POR EVALUACIÓN (NO ACUMULADO)
# ============================

# FIN: siempre la evaluación actual
fecha_fin = evaluacion.fecha_evaluacion

# Buscar la evaluación anterior del alumno (cualquier tipo)
query_eval_anterior = text("""
SELECT fecha_evaluacion
FROM evaluaciones
WHERE id_alumno = :id
  AND fecha_evaluacion < :fecha_actual
ORDER BY fecha_evaluacion DESC
LIMIT 1
""")

with engine.begin() as conn:
    fecha_eval_anterior = conn.execute(
        query_eval_anterior,
        {
            "id": id_alumno,
            "fecha_actual": fecha_fin
        }
    ).scalar()

if fecha_eval_anterior:
    if isinstance(fecha_eval_anterior, str):
        fecha_eval_anterior = date.fromisoformat(fecha_eval_anterior[:10])
    elif isinstance(fecha_eval_anterior, datetime):
        fecha_eval_anterior = fecha_eval_anterior.date()

    # empezar un día después para no duplicar
    fecha_inicio = fecha_eval_anterior + timedelta(days=1)
else:
    # si es la primera evaluación, usar la primera asistencia
    query_primera_asistencia = text("""
    SELECT MIN(fecha)
    FROM asistencias
    WHERE id_alumno = :id
    """)
    with engine.begin() as conn:
        fecha_inicio = conn.execute(
            query_primera_asistencia,
            {"id": id_alumno}
        ).scalar()

if fecha_inicio is None:
    fecha_inicio = fecha_fin

# ============================
# 4️⃣ CONSULTAR ASISTENCIAS
# ============================
with col_asist:
    query_asistencias = text("""
    SELECT LOWER(TRIM(estado)) AS estado, COUNT(*) AS total
    FROM asistencias
    WHERE id_alumno = :id
    AND fecha BETWEEN :inicio AND :fin
    GROUP BY LOWER(TRIM(estado))
    """)

    with engine.begin() as conn:
        asistencias = conn.execute(
            query_asistencias,
            {
                "id": id_alumno,
                "inicio": fecha_inicio,
                "fin": fecha_fin
            }
        ).fetchall()

    # ============================
    # 5️⃣ PROCESAR DATOS
    # ============================
    labels = []
    values = []

    total_asistencias = 0
    total_retardos = 0
    total_faltas = 0

    for a in asistencias:
        estado = a.estado.lower()
        labels.append(a.estado.capitalize())
        values.append(a.total)


        if estado == "asistió":
            total_asistencias = a.total
        elif estado == "retardo":
            total_retardos = a.total
        elif estado == "falta":
            total_faltas = a.total

    # ============================
    # 6️⃣ MOSTRAR DONUT
    # ============================
    if values:
        color_map = {
            "Asistió": "#1f4ed8",
            "Retardo": "#93c5fd",
            "Falta": "#F97316"
        }
        colors = [color_map[label] for label in labels]

        fig_donut = go.Figure(
                    data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.6,
                    textinfo="label+percent",
                    textposition="outside",
                    insidetextorientation="radial",
                    marker=dict(
                        colors=colors,
                        line=dict(color="#ffffff", width=2)
                    )
                )
            ]
        )

        fig_donut.update_layout(
            height=260,
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=False
        )
        
        st.markdown("""
        <div style="margin:8px 0 4px 0;">
            <strong style="font-size:16px;">Asistencias</strong>
        </div>
        """, unsafe_allow_html=True)

        st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info("ℹ️ No hay asistencias registradas.")
        
    # --- TABLA ASISTENCIAS ---
    mini_tabla_html = f"""
    <div style="
        background:#ffffff;
        border-radius:16px;
        padding:14px;
        box-shadow:0 4px 12px rgba(0,0,0,0.05);
        font-size:14px;
    ">
        <table style="width:100%; border-collapse:collapse;">
            <tr>
                <td>Asistencias</td>
                <td style="text-align:center;"><strong>{total_asistencias}</strong></td>
            </tr>
            <tr>
                <td>Retardos</td>
                <td style="text-align:center;"><strong>{total_retardos}</strong></td>
            </tr>
            <tr>
                <td>Faltas</td>
                <td style="text-align:center;"><strong>{total_faltas}</strong></td>
            </tr>
        </table>
    </div>
    """
    st.markdown(mini_tabla_html, unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ============================
# RADAR (Alumno vs Promedio de Grupo)
# ============================

import plotly.graph_objects as go
from sqlalchemy import text
import streamlit as st

id_evaluacion = evaluacion.id_evaluacion

# 1) Traer golpes de esa evaluación (alumno)
query_tecnica = text("""
SELECT g.id_golpe, g.nombre_golpe, et.preparacion, et.contacto, et.terminacion
FROM evaluacion_tecnica et
JOIN golpes g ON g.id_golpe = et.id_golpe
WHERE et.id_evaluacion = :id;
""")

with engine.begin() as conn:
    golpes = conn.execute(query_tecnica, {"id": id_evaluacion}).fetchall()

if not golpes:
    st.info("ℹ️ No hay datos técnicos para esta evaluación")
    st.stop()

# 2) Obtener el grupo del alumno (a partir de la evaluación actual)
query_grupo = text("""
SELECT a.grupo
FROM evaluaciones e
JOIN alumno a ON a.id_alumno = e.id_alumno
WHERE e.id_evaluacion = :id_evaluacion
LIMIT 1;
""")

with engine.begin() as conn:
    grupo_alumno = conn.execute(query_grupo, {"id_evaluacion": id_evaluacion}).scalar()

# 3) Promedios del grupo por golpe (prep/cont/term)
query_promedio_grupo = text("""
SELECT
  g.id_golpe,
  g.nombre_golpe,
  AVG(et.preparacion) AS avg_preparacion,
  AVG(et.contacto)    AS avg_contacto,
  AVG(et.terminacion) AS avg_terminacion
FROM evaluaciones e
JOIN alumno a              ON a.id_alumno = e.id_alumno
JOIN evaluacion_tecnica et ON et.id_evaluacion = e.id_evaluacion
JOIN golpes g              ON g.id_golpe = et.id_golpe
WHERE a.grupo = :grupo
GROUP BY g.id_golpe, g.nombre_golpe
ORDER BY g.id_golpe;
""")

with engine.begin() as conn:
    promedios = conn.execute(query_promedio_grupo, {"grupo": grupo_alumno}).fetchall()

# 4) Construir labels y valores (alumno)
labels, values = [], []

for g in golpes:
    labels += [
        f"{g.nombre_golpe} Prep",
        f"{g.nombre_golpe} Cont",
        f"{g.nombre_golpe} Term"
    ]
    values += [
        g.preparacion or 6,
        g.contacto or 6,
        g.terminacion or 6
    ]

# 5) Construir values_promedio con el mismo orden que 'golpes'
prom_map = {p.nombre_golpe: p for p in promedios}

values_promedio = []
for g in golpes:
    p = prom_map.get(g.nombre_golpe)
    values_promedio += [
        (p.avg_preparacion if p and p.avg_preparacion is not None else 6),
        (p.avg_contacto    if p and p.avg_contacto    is not None else 6),
        (p.avg_terminacion if p and p.avg_terminacion is not None else 6),
    ]

# 6) Crear RADAR con 2 series
fig_radar = go.Figure()

# Alumno (azul)
fig_radar.add_trace(go.Scatterpolar(
    r=values,
    theta=labels,
    fill="toself",
    line=dict(color="#18399e", width=2),
    fillcolor="rgba(24,57,158,0.25)",
    marker=dict(size=4),
    name="Alumno"
))

# Promedio grupo (naranja)
fig_radar.add_trace(go.Scatterpolar(
    r=values_promedio,
    theta=labels,
    fill="toself",
    line=dict(color="#d4af37", width=2),
    fillcolor="rgba(212,175,55,0.20)",
    marker=dict(size=4),
    name="Promedio grupo"
))

fig_radar.update_layout(
    height=285,
    margin=dict(l=15, r=15, t=23, b=20),
    showlegend=False,
    hoverlabel=dict(
    font_size=20
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    polar=dict(
        radialaxis=dict(
            range=[6, 13],
            showticklabels=False
        ),
        angularaxis=dict(
            tickfont=dict(size=11),
            rotation=90
        )
    )
)

# ============================
# INDICADORES UNIFICADOS
# ============================

indicadores = [
    ("Conducta", evaluacion.conducta, "Disciplina"),
    ("Atención", evaluacion.atencion, "Disciplina"),
    ("Esfuerzo", evaluacion.esfuerzo, "Disciplina"),

    ("Balance", evaluacion.balance, "Habilidad"),
    ("Movilidad", evaluacion.movilidad, "Habilidad"),
    ("Fuerza", evaluacion.fuerza, "Habilidad"),
    ("Coordinación", evaluacion.coordinacion, "Habilidad"),
    ("Velocidad", evaluacion.velocidad, "Habilidad"),
]

# Agregar técnica (golpes)
for g in golpes:
    indicadores.extend([
        (f"{g.nombre_golpe} – Preparacion", g.preparacion, "Técnica"),
        (f"{g.nombre_golpe} – Contacto", g.contacto, "Técnica"),
        (f"{g.nombre_golpe} – Terminacion", g.terminacion, "Técnica"),
    ])

# Limpiar nulos
indicadores = [i for i in indicadores if i[1] is not None]

# Ordenar por valor
indicadores_ordenados = sorted(indicadores, key=lambda x: x[1], reverse=True)

top_2 = indicadores_ordenados[:2]
bottom_2 = indicadores_ordenados[-2:]

# ============================
# FUNCIÓN TABLA FOCO
# ============================
def tabla_foco_unica(top_items, bottom_items):
    filas_top = ""
    filas_bottom = ""

    color_map = {"Disciplina": "#03040c", "Habilidad": "#03040c", "Técnica": "#03040c"}

    for nombre, valor, bloque in top_items:
        color = color_map.get(bloque, "#334155")
        filas_top += f"""
        <tr>
            <td style="padding:8px 6px;">{nombre}</td>
            <td style="padding:8px 6px; color:{color}; font-weight:500;">{bloque}</td>
            <td style="padding:8px 6px; text-align:center; font-weight:600; color:{color};">{valor}</td>
        </tr>
        """

    for nombre, valor, bloque in bottom_items:
        color = color_map.get(bloque, "#334155")
        filas_bottom += f"""
        <tr>
            <td style="padding:8px 6px;">{nombre}</td>
            <td style="padding:8px 6px; color:{color}; font-weight:500;">{bloque}</td>
            <td style="padding:8px 6px; text-align:center; font-weight:600; color:{color};">{valor}</td>
        </tr>
        """

    components.html(
    f"""
    <div style="background:#ffffff; border-radius:18px; padding:14px;
                box-shadow:0 4px 12px rgba(0,0,0,0.05); margin-bottom:6px;">
        <div style="font-weight:600; font-size:15px; margin-bottom:10px;">Fortalezas</div>
        <table style="width:100%; border-collapse:collapse; font-size:14px;">
            <thead>
                
            </thead>
            <tbody>{filas_top}</tbody>
        </table>

        <div style="font-weight:600; font-size:15px; margin:10px 0 8px 0;">Áreas de mejora</div>
        <table style="width:100%; border-collapse:collapse; font-size:14px;">
            <thead>
            
            </thead>
            <tbody>{filas_bottom}</tbody>
        </table>
    </div>
    """,
    height=240,
)

# ============================
# RADAR + FOCO (2 COLUMNAS)
# ============================
st.markdown("""
        <div style="margin:5px 0 4px 0;">
        <strong style="font-size:16px;">Tecnica (golpes)</strong>
    </div>
    """, unsafe_allow_html=True)

col_radar, col_foco = st.columns([1.2, 1])

with col_radar:
    st.plotly_chart(fig_radar, use_container_width=True, key=f"radar_{id_evaluacion}")

with col_foco:
    tabla_foco_unica(top_2, bottom_2)
    
#==============================
# GRAFICA LINEAL (con punto actual resaltado)
#==============================
query_evolucion = text("""
SELECT 
    id_evaluacion,
    fecha_evaluacion,
    tipo_evaluacion,
    periodo,
    anio,
    conducta, atencion, esfuerzo,
    balance, movilidad, fuerza, coordinacion, velocidad
FROM evaluaciones
WHERE id_alumno = :id_alumno
ORDER BY fecha_evaluacion;
""")

with engine.begin() as conn:
    rows = conn.execute(query_evolucion, {"id_alumno": id_alumno}).fetchall()

if not rows:
    st.info("ℹ️ No hay evaluaciones registradas")
    st.stop()

data = []
for r in rows:
    valores = [
        r.conducta, r.atencion, r.esfuerzo,
        r.balance, r.movilidad, r.fuerza,
        r.coordinacion, r.velocidad
    ]
    valores = [v for v in valores if v is not None]
    if not valores:
        continue

    puntaje = round(sum(valores) / len(valores), 2)

    data.append({
        "fecha": r.fecha_evaluacion,
        "evaluacion": f"{r.tipo_evaluacion} - {r.periodo} {r.anio}",
        "puntaje": puntaje
    })

df = pd.DataFrame(data)

if df.empty:
    st.info("ℹ️ No hay datos suficientes para graficar")
    st.stop()

# ✅ 1) Identificar la evaluación actual (la que estás consultando)
eval_actual_label = f"{evaluacion.tipo_evaluacion} - {evaluacion.periodo} {evaluacion.anio}"
df["es_actual"] = df["evaluacion"] == eval_actual_label
df_actual = df[df["es_actual"]]

# ✅ 2) Gráfica base
fig_evolucion = px.line(
    df,
    x="evaluacion",
    y="puntaje",
    markers=True,
    text="puntaje"
)

fig_evolucion.update_traces(textposition="top center")

# ✅ 3) Resaltar el punto actual (si existe)
if not df_actual.empty:
    fig_evolucion.add_scatter(
        x=df_actual["evaluacion"],
        y=df_actual["puntaje"],
        mode="markers",
        marker=dict(
            size=14,
            color="#ef4444",  # 🔴
            line=dict(width=2, color="white")
        ),
        showlegend=False
    )

    # (opcional) etiqueta "Actual"
    fig_evolucion.add_annotation(
        x=df_actual["evaluacion"].iloc[0],
        y=df_actual["puntaje"].iloc[0],
        text="Actual",
        showarrow=True,
        arrowhead=2,
        yshift=18,
        font=dict(size=12, color="#ef4444")
    )

# ✅ 4) Layout
fig_evolucion.update_layout(
    height=320,
    yaxis=dict(autorange=True),
    xaxis_title="Evaluaciones",
    yaxis_title="Puntaje",
    showlegend=False,
    margin=dict(t=5, b=10, l=10, r=10)
)

# Título/descripcion
st.markdown("""
<div style="margin:8px 0 4px 0;">
    <strong style="font-size:16px;">📈 Evolución del desempeño</strong><br>
    <span style="font-size:13px; color:#64748b;">
        Comparación del puntaje promedio por evaluación
    </span>
</div>
""", unsafe_allow_html=True)

st.plotly_chart(fig_evolucion, use_container_width=True, key=f"evolucion_{id_alumno}")

# RECOMENDACIONES 
query_recomendacion = text("""
SELECT recomendaciones
FROM evaluaciones
WHERE id_evaluacion = :id_eval
""")

with engine.begin() as conn:
    recomendacion = conn.execute(
        query_recomendacion,
        {"id_eval": id_evaluacion}
    ).scalar()
    st.markdown("###### 📝 Recomendaciones del profesor")

if recomendacion and recomendacion.strip():
    texto = recomendacion
    color_fondo = "#f8fafc"
else:
    texto = "El profesor no dejó recomendaciones para esta evaluación."
    color_fondo = "#f1f5f9"

st.markdown(
    f"""
    <div style="
        padding:22px 26px;
        border-radius:16px;
        background:{color_fondo};
        border:1px solid #e2e8f0;
        font-size:15px;
        color:#334155;
        line-height:1.6;
        max-width:900px;
    ">
        {texto}
    </div>
    """,
    unsafe_allow_html=True
)
