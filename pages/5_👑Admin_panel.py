import streamlit as st
from sqlalchemy import text
from db import engine

# 🔐 Validar sesión
if not st.session_state.get("logged_in"):
    st.error("❌ Debes iniciar sesión")
    st.stop()

# 🔐 Validar rol admin
if st.session_state.get("rol") != "admin":
    st.error("⛔ Acceso solo para administradores")
    st.stop()

st.title("Panel de Administrador")

st.caption(f"Usuario: {st.session_state.get('usuario')} | Rol: {st.session_state.get('rol')}")

st.sidebar.title("Administración")

seccion = st.sidebar.radio(
    "Gestionar:",
    [
        "👨‍🏫 Profesores",
        "👤 Alumnos",
        "📅 Asistencias",
        "📝 Evaluaciones"
    ]
)
# ======================
# MENSAJES
# ======================
if st.session_state.get("alumno_actualizado"):
    st.success("✅ Alumno actualizado")
    del st.session_state["alumno_actualizado"]

if st.session_state.get("alumno_eliminado"):
    st.success("🗑️ Alumno desactivado")
    del st.session_state["alumno_eliminado"]

if st.session_state.get("asistencia_actualizada"):
    st.success("✅ Asistencia actualizada")
    del st.session_state["asistencia_actualizada"]

if st.session_state.get("asistencia_eliminada"):
    st.success("🗑️ Asistencia eliminada")
    del st.session_state["asistencia_eliminada"]

if seccion == "👨‍🏫 Profesores":
    st.subheader("Gestión de Profesores")
    st.info("Crear, editar o desactivar profesores")

    if st.session_state.get("profesor_creado"):
        st.success("✅ Profesor creado correctamente")
        del st.session_state["profesor_creado"]

    if st.session_state.get("profesor_actualizado"):
        st.success("💾 Cambios guardados correctamente")
        del st.session_state["profesor_actualizado"]

    if st.session_state.get("profesor_eliminado"):
        st.success("🗑️ Profesor eliminado correctamente")
        del st.session_state["profesor_eliminado"]

#=======================
# PROFESORES
#=======================
    query_profesores = text("""
    SELECT id_profesor, usuario, rol, activo
    FROM profesores
    ORDER BY usuario
    """)

    with engine.begin() as conn:
        profesores = conn.execute(query_profesores).fetchall()

    for p in profesores:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])

        with col1:
            st.write(p.usuario)

        with col2:
            rol_nuevo = st.selectbox(
                "Rol",
                ["profesor", "admin"],
                index=0 if p.rol == "profesor" else 1,
                key=f"rol_{p.id_profesor}"
            )

        with col3:
            activo_nuevo = st.checkbox(
                "Activo",
                value=p.activo,
                key=f"activo_{p.id_profesor}"
            )

        with col4:
            if st.button("💾 Guardar", key=f"save_prof_{p.id_profesor}"):

                query_update = text("""
                UPDATE profesores
                SET rol = :rol, activo = :activo
                WHERE id_profesor = :id
                """)

                with engine.begin() as conn:
                    conn.execute(
                        query_update,
                        {
                            "rol": rol_nuevo,
                            "activo": activo_nuevo,
                            "id": p.id_profesor
                        }
                    )

                st.session_state["profesor_actualizado"] = True
                st.rerun()

        with col5:
            if st.button("🗑️", key=f"del_prof_{p.id_profesor}"):

                query_delete = text("""
                DELETE FROM profesores
                WHERE id_profesor = :id
                """)

                with engine.begin() as conn:
                    conn.execute(query_delete, {"id": p.id_profesor})

                st.session_state["profesor_eliminado"] = True
                st.rerun()

# Nuevo profesor
    st.subheader("Nuevo profesor")

    with st.form("form_nuevo_profesor", clear_on_submit=True):
        nuevo_usuario = st.text_input("Usuario")
        nueva_password = st.text_input("Contraseña", type="password")
        nuevo_rol = st.selectbox("Rol", ["profesor", "admin"])
        activo = st.checkbox("Activo", value=True)

        guardar = st.form_submit_button("Crear profesor")

        if guardar:
            if not nuevo_usuario or not nueva_password:
                st.warning("Completa usuario y contraseña")
            else:
                query_insert = text("""
                INSERT INTO profesores (usuario, password, rol, activo)
                VALUES (:usuario, :password, :rol, :activo)
                """)

                with engine.begin() as conn:
                    conn.execute(
                        query_insert,
                        {
                            "usuario": nuevo_usuario,
                            "password": nueva_password,
                            "rol": nuevo_rol,
                            "activo": activo
                        }
                    )

                st.session_state["profesor_creado"] = True
                st.rerun()

#========================
# ALUMNOS
# =======================                

elif seccion == "👤 Alumnos":
    st.subheader("Gestión de Alumnos")
    st.info("Editar información de alumnos registrados")

    query = text("""
    SELECT id_alumno, nombre, accion, fecha_nacimiento, grupo, torneos
    FROM alumno
    ORDER BY nombre
    """)

    with engine.begin() as conn:
        alumnos = conn.execute(query).fetchall()

    busqueda = st.text_input("🔍 Buscar alumno")

    if busqueda:
        alumnos = [a for a in alumnos if busqueda.lower() in a.nombre.lower()]

    with st.container(height=500):
        for a in alumnos:
            col1, col2, col3, col4, col5, col6 = st.columns([2.8, 1, 2, 2.5, 1.5, 1])

            with col1:
                nombre = st.text_input("Nombre", a.nombre, key=f"nom_{a.id_alumno}")

            with col2:
                accion = st.text_input("Acción", a.accion, key=f"acc_{a.id_alumno}")

            with col3:
                fecha_nacimiento = st.date_input(
                    "Nacimiento",
                    a.fecha_nacimiento,
                    key=f"fec_{a.id_alumno}"
                )

            with col4:
                opciones_grupo = [
                    "Mini Tenis",
                    "Principiantes - Intermedio",
                    "Avanzados",
                    "Equipo de competencia"
                ]

                # índice seguro
                if a.grupo in opciones_grupo:
                    idx = opciones_grupo.index(a.grupo)
                else:
                    idx = 0   # o el que tú quieras por defecto

                grupo = st.selectbox(
                    "Grupo",
                    opciones_grupo,
                    index=idx,
                    key=f"grupo_{a.id_alumno}"
                )

            with col5:
                torneos = st.checkbox("Torneos", a.torneos, key=f"tor_{a.id_alumno}")

            with col6:
                if st.button("💾", key=f"save_al_{a.id_alumno}"):

                    query_update = text("""
                    UPDATE alumno
                    SET nombre = :nombre,
                        accion = :accion,
                        fecha_nacimiento = :fecha,
                        grupo = :grupo,
                        torneos = :torneos
                    WHERE id_alumno = :id
                    """)

                    with engine.begin() as conn:
                        conn.execute(
                            query_update,
                            {
                                "nombre": nombre,
                                "accion": accion,
                                "fecha": fecha_nacimiento,
                                "grupo": grupo,
                                "torneos": torneos,
                                "id": a.id_alumno
                            }
                        )

                    st.session_state["alumno_actualizado"] = True
                    st.rerun()

#=================
# ASISTENCIAS
#=================
elif seccion == "📅 Asistencias":
    st.subheader("📅 Gestión de Asistencias")
    st.info("Corregir o modificar asistencias")

    # Obtener lista de alumnos para el filtro
    with engine.begin() as conn:
        alumnos_query = text("SELECT id_alumno, nombre FROM alumno ORDER BY nombre")
        alumnos_lista = conn.execute(alumnos_query).fetchall()
    
    # FILTROS
    with st.expander("🔍 Filtros de búsqueda", expanded=True):
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        
        with col_f1:
            # Filtro de alumnos como select normal (uno a la vez)
            opciones_alumnos = {"Todos los alumnos": None}
            opciones_alumnos.update({al.nombre: al.id_alumno for al in alumnos_lista})
            
            alumno_seleccionado = st.selectbox(
                "Alumno",
                options=list(opciones_alumnos.keys()),
                index=0,  # "Todos los alumnos" por defecto
                key="filtro_alumno"
            )
        
        with col_f2:
            # Filtro de mes
            meses = ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            mes_seleccionado = st.selectbox("Mes", meses, index=0, key="filtro_mes")
        
        with col_f3:
            # Filtro de estado
            estados_filtro = ["Todos", "Asistió", "Retardo", "Falta"]
            estado_seleccionado = st.selectbox("Estado", estados_filtro, index=0, key="filtro_estado")

    # Convertir mes a número
    meses_map = {
        "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6,
        "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
    }

    # Construir consulta con filtros
    query_base = """
    SELECT a.id_asistencia,
           al.nombre,
           a.fecha,
           a.estado,
           a.observaciones
    FROM asistencias a
    JOIN alumno al ON al.id_alumno = a.id_alumno
    WHERE 1=1
    """
    
    params = {}
    
    # Aplicar filtro de alumno (solo si no es "Todos")
    if alumno_seleccionado != "Todos los alumnos":
        query_base += " AND al.nombre = :alumno_nombre"
        params["alumno_nombre"] = alumno_seleccionado
    
    # Aplicar filtro de mes
    if mes_seleccionado != "Todos":
        query_base += " AND EXTRACT(MONTH FROM a.fecha) = :mes"
        params["mes"] = meses_map[mes_seleccionado]
    
    # Aplicar filtro de estado
    if estado_seleccionado != "Todos":
        query_base += " AND a.estado = :estado"
        params["estado"] = estado_seleccionado
    
    query_base += " ORDER BY a.fecha DESC, al.nombre"
    
    query = text(query_base)

    with engine.begin() as conn:
        asistencias = conn.execute(query, params).fetchall()

    # Mostrar contador de resultados
    st.markdown(f"**Mostrando {len(asistencias)} registro(s)**")

    if not asistencias:
        st.warning("No se encontraron asistencias con los filtros seleccionados")
    else:
        # Tabla de asistencias - ancho original
        st.markdown("---")
        
        # Cabecera sin columna de registrado
        header_cols = st.columns([2.0, 1.5, 2.0, 2.5, 1])
        headers = ["Alumno", "Fecha", "Estado", "Observaciones", "Borrar"]
        
        for col, header in zip(header_cols, headers):
            col.markdown(f"**{header}**")
        
        # Diccionario para almacenar los cambios
        cambios = {}
        
        # Contenedor con scroll
        with st.container(height=500):
            for r in asistencias:
                cols = st.columns([2.0, 1.5, 2.0, 2.5, 1])
                
                with cols[0]:  # Nombre
                    st.write(r.nombre)
                
                with cols[1]:  # Fecha
                    fecha_nueva = st.date_input(
                        "",
                        r.fecha,
                        key=f"fec_{r.id_asistencia}",
                        label_visibility="collapsed",
                        format="DD/MM/YYYY"
                    )
                    if fecha_nueva != r.fecha:
                        if r.id_asistencia not in cambios:
                            cambios[r.id_asistencia] = {}
                        cambios[r.id_asistencia]["fecha"] = fecha_nueva
                
                with cols[2]:  # Estado
                    estados = ["Asistió", "Retardo", "Falta"]
                    estado_nuevo = st.selectbox(
                        "",
                        estados,
                        index=estados.index(r.estado) if r.estado in estados else 0,
                        key=f"est_{r.id_asistencia}",
                        label_visibility="collapsed"
                    )
                    if estado_nuevo != r.estado:
                        if r.id_asistencia not in cambios:
                            cambios[r.id_asistencia] = {}
                        cambios[r.id_asistencia]["estado"] = estado_nuevo
                
                with cols[3]:  # Observaciones
                    obs_nueva = st.text_input(
                        "",
                        r.observaciones or "",
                        key=f"obs_{r.id_asistencia}",
                        label_visibility="collapsed",
                        placeholder="Observaciones"
                    )
                    if obs_nueva != (r.observaciones or ""):
                        if r.id_asistencia not in cambios:
                            cambios[r.id_asistencia] = {}
                        cambios[r.id_asistencia]["observaciones"] = obs_nueva
                
                with cols[4]:  # Botón de borrar
                    if st.button("🗑️", key=f"del_{r.id_asistencia}", help="Eliminar este registro"):
                        try:
                            query_delete = text("DELETE FROM asistencias WHERE id_asistencia = :id")
                            with engine.begin() as conn:
                                conn.execute(query_delete, {"id": r.id_asistencia})
                            st.success("✅ Eliminado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al eliminar: {e}")
                
                st.markdown("---")
        
        # Botón de guardar todo al final
        if cambios:
            st.markdown("---")
            col_save = st.columns([1, 2, 1])
            with col_save[1]:
                if st.button("💾 GUARDAR CAMBIOS", type="primary", use_container_width=True):
                    try:
                        with engine.begin() as conn:
                            for id_asistencia, campos in cambios.items():
                                set_clause = []
                                params_update = {"id": id_asistencia}
                                
                                if "fecha" in campos:
                                    set_clause.append("fecha = :fecha")
                                    params_update["fecha"] = campos["fecha"]
                                
                                if "estado" in campos:
                                    set_clause.append("estado = :estado")
                                    params_update["estado"] = campos["estado"]
                                
                                if "observaciones" in campos:
                                    set_clause.append("observaciones = :obs")
                                    params_update["obs"] = campos["observaciones"]
                                
                                if set_clause:
                                    query_update = text(f"""
                                    UPDATE asistencias 
                                    SET {', '.join(set_clause)}
                                    WHERE id_asistencia = :id
                                    """)
                                    conn.execute(query_update, params_update)
                        
                        st.success("✅ Cambios guardados exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar cambios: {e}")
        else:
            st.info("✏️ Realiza cambios en los registros para guardar")

# =================
# EVALUACIONES
# =================
elif seccion == "📝 Evaluaciones":

    # ALUMNOS

    with engine.connect() as conn:
        alumnos = conn.execute(text("""
            SELECT id_alumno, nombre
            FROM alumno
            ORDER BY nombre
        """)).fetchall()

    alumno_map = {a.nombre:a.id_alumno for a in alumnos}

    alumno_nombre = st.selectbox("Alumno", list(alumno_map.keys()))
    id_alumno = alumno_map[alumno_nombre]


    # CARGAR EVALUACIONES
    
    with engine.connect() as conn:
        evaluaciones = conn.execute(text("""
            SELECT id_evaluacion,
                   fecha_evaluacion,
                   tipo_evaluacion
            FROM evaluaciones
            WHERE id_alumno=:id
            ORDER BY fecha_evaluacion DESC
        """),{"id":id_alumno}).fetchall()

    if not evaluaciones:
        st.info("No hay evaluaciones")
        st.stop()

    
    # FILTROS
  
    tipos = sorted({e.tipo_evaluacion for e in evaluaciones})
    tipo_sel = st.selectbox("Tipo", ["Todos"]+tipos)

    fecha_sel = st.date_input("Fecha (opcional)", value=None)

    lista = evaluaciones

    if tipo_sel!="Todos":
        lista=[e for e in lista if e.tipo_evaluacion==tipo_sel]

    if fecha_sel:
        lista=[e for e in lista if e.fecha_evaluacion==fecha_sel]

   
    # SELECT EVALUACION
    
    mapa = {
        f"{e.fecha_evaluacion} | {e.tipo_evaluacion}":e.id_evaluacion
        for e in lista
    }

    sel = st.selectbox("Evaluación", list(mapa.keys()))
    id_eval = mapa[sel]

    
    # CARGAR DATOS

    with engine.connect() as conn:

        datos = conn.execute(text("""
            SELECT *
            FROM evaluaciones
            WHERE id_evaluacion=:id
        """),{"id":id_eval}).fetchone()

        tecnica = conn.execute(text("""
            SELECT id_golpe, preparacion, contacto, terminacion
            FROM evaluacion_tecnica
            WHERE id_evaluacion=:id
            ORDER BY id_golpe 
        """),{"id":id_eval}).fetchall()

    tec_dict = {
        t.id_golpe:{
            "prep":t.preparacion,
            "cont":t.contacto,
            "term":t.terminacion
        } for t in tecnica
    }

    
    # FORMULARIO
    mensaje = st.empty()
    with st.form("edit_eval"):

        st.markdown("## Disciplina y habilidad atlética")

        c1,c2,c3=st.columns(3)

        with c1:
            st.write("Fecha:",datos.fecha_evaluacion)

        with c2:
            tipo = st.selectbox(
                "Tipo",
                ["Diagnóstico","Principal","Seguimiento"],
                index=["Diagnóstico","Principal","Seguimiento"].index(datos.tipo_evaluacion)
            )

        with c3:
            periodo = st.selectbox(
                "Periodo",
                ["1er","2do","3er","Final"],
                index=["1er","2do","3er","Final"].index(datos.periodo)
                if datos.periodo in ["1er","2do","3er","Final"] else 0
            )

        # FISICA 

        puntajes=list(range(7,14))

        etiquetas={
            "conducta":"Conducta",
            "atencion":"Atención",
            "esfuerzo":"Esfuerzo",
            "balance":"Balance",
            "movilidad":"Movilidad",
            "fuerza":"Fuerza",
            "coordinacion":"Coordinación",
            "velocidad":"Velocidad"
        }

        valores={}

        campos=list(etiquetas.items())

        for i in range(0,len(campos),3):

            cols=st.columns(3)

            for col,(campo,txt) in zip(cols,campos[i:i+3]):

                with col:

                    val=getattr(datos,campo) or 7

                    valores[campo]=st.number_input(
                        txt,
                        7,13,
                        value=int(val),
                        key=f"{campo}_{id_eval}"
                    )

        # TECNICA 

        st.markdown("## Técnica")

        golpes=[
            (1,"Derecha"),
            (2,"Reves"),
            (3,"Volea derecha"),
            (4,"Volea revés"),
            (5,"Remate"),
            (6,"Servicio")
        ]

        valores_tec={}

        for gid,nombre in golpes:

            st.markdown(f"### {nombre}")

            c1,c2,c3=st.columns(3)

            bd=tec_dict.get(gid,{"prep":7,"cont":7,"term":7})

            with c1:
                p=st.number_input(
                    "Preparación",
                    7,13,value=int(bd["prep"]),
                    key=f"p_{id_eval}_{gid}"
                )

            with c2:
                c=st.number_input(
                    "Contacto",
                    7,13,value=int(bd["cont"]),
                    key=f"c_{id_eval}_{gid}"
                )

            with c3:
                t=st.number_input(
                    "Terminación",
                    7,13,value=int(bd["term"]),
                    key=f"t_{id_eval}_{gid}"
                )

            valores_tec[gid]=(p,c,t)

        # OBS

        recomendaciones=st.text_area(
            "Recomendaciones",
            value=datos.recomendaciones or ""
        )

        # BOTONES 
        mensaje = st.empty()
        guardar=st.form_submit_button("💾 Guardar cambios")
        borrar=st.form_submit_button("🗑️ Eliminar evaluación")

        if guardar:

            with engine.begin() as conn:

                conn.execute(text("""
                    UPDATE evaluaciones
                    SET tipo_evaluacion=:tipo,
                        periodo=:per,
                        recomendaciones=:rec,
                        conducta=:conducta,
                        atencion=:atencion,
                        esfuerzo=:esfuerzo,
                        balance=:balance,
                        movilidad=:movilidad,
                        fuerza=:fuerza,
                        coordinacion=:coordinacion,
                        velocidad=:velocidad
                    WHERE id_evaluacion=:id
                """),{
                    "tipo":tipo,
                    "per":periodo,
                    "rec":recomendaciones,
                    **valores,
                    "id":id_eval
                })

                for gid,(p,c,t) in valores_tec.items():

                    conn.execute(text("""
                        UPDATE evaluacion_tecnica
                        SET preparacion=:p,
                            contacto=:c,
                            terminacion=:t
                        WHERE id_evaluacion=:id
                        AND id_golpe=:g
                    """),{
                        "p":p,
                        "c":c,
                        "t":t,
                        "id":id_eval,
                        "g":gid
                    })

            st.session_state.msg="guardado"

            for k in list(st.session_state.keys()):
                if k.startswith(("Alumno","Tipo","Fecha","Evaluación","p_","c_","t_","conducta","atencion","esfuerzo","balance","movilidad","fuerza","coordinacion","velocidad")):
                    del st.session_state[k]

            st.rerun()

        if borrar:

            with engine.begin() as conn:

                conn.execute(text(
                    "DELETE FROM evaluacion_tecnica WHERE id_evaluacion=:id"
                ),{"id":id_eval})

                conn.execute(text(
                    "DELETE FROM evaluaciones WHERE id_evaluacion=:id"
                ),{"id":id_eval})

                st.session_state.msg="borrado"

            for k in list(st.session_state.keys()):
                if k.startswith(("Alumno","Tipo","Fecha","Evaluación","p_","c_","t_","conducta","atencion","esfuerzo","balance","movilidad","fuerza","coordinacion","velocidad")):
                    del st.session_state[k]

            st.rerun()
if "msg" in st.session_state:

    if st.session_state.msg=="guardado":
        mensaje.success("✅ Cambios guardados")

    if st.session_state.msg=="borrado":
        mensaje.error("🗑️ Evaluación eliminada")

    del st.session_state["msg"]

