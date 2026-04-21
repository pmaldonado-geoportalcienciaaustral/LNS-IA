import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# --- PALETA DE COLORES LNS ---
PALETA_LNS = {
    "ESTEPA": "#F0C042",
    "FIORDOS Y CANALES": "#22A7E0",
    "BOSQUES Y TURBERAS": "#3FA535",
    "GLACIARES": "#AFD5CA"
}

st.set_page_config(page_title="Nodo LNS - Gestión de Datos", layout="wide")

# --- BARRA LATERAL (LOGO, MENÚ Y GESTIÓN) ---
with st.sidebar:
    # Logo institucional
    st.image("https://nodosubantartico.cl/wp-content/uploads/2024/10/LOGO-COLOR5.png", use_container_width=True)
    st.divider()
    
    # Menú de navegación
    menu = st.sidebar.selectbox("Seleccionar Módulo", 
                                ["◒ Dashboard de Publicaciones", "⚲ Mapa de Capacidades", "💬 Chat de Consultas"])
    
    st.divider()
    
    # SECCIÓN DE GESTIÓN DE DATOS
    st.markdown("### 📝 Gestión de Información")
    st.caption("Utilice estos formularios para actualizar la base de datos institucional.")
    
    # Botón dinámico al formulario
    st.link_button("➕ Registrar Nueva Capacidad", "https://docs.google.com/forms/d/e/TU_ID_DE_FORMULARIO/viewform")
    
    st.info("Nota: Las actualizaciones pueden tardar unos minutos en reflejarse debido al caché del sistema.")

# --- CONEXIÓN CON GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def cargar_datos(nombre_pestana):
    try:
        df = conn.read(worksheet=nombre_pestana)
        df.columns = df.columns.str.strip()
        columnas_a_renombrar = {
            'autor': 'Autor(a)', 'ambiente': 'Ambiente',
            'publicaciones_tot': 'N° Publicaciones',
            'pais': 'País', 'ISO': 'ISO', 'autores_tot': 'Total autores(as)',
            'nombre_completo': 'Institución', 'abrev': 'Abrev'
        }
        df = df.rename(columns=columnas_a_renombrar)
        return df
    except Exception as e:
        st.error(f"Error al cargar la pestaña '{nombre_pestana}': {e}")
        return pd.DataFrame()

# --- TÍTULO PRINCIPAL ---
st.title("○ Plataforma de Datos Laboratorio Natural Subantártico")

if "Dashboard" in menu:
    df_articulos = cargar_datos("autoresLNS")
    df_redes = cargar_datos("pais_autores")
    df_inst = cargar_datos("inst_autores")
    
    if not df_articulos.empty and not df_redes.empty:
        # Estandarización de ambientes
        for df in [df_articulos, df_redes, df_inst]:
            if not df.empty:
                df["Ambiente"] = df["Ambiente"].astype(str).str.upper().str.strip()

        # --- SECCIÓN METODOLÓGICA (CERRADA POR DEFECTO) ---
        with st.expander("ℹ️ Metodología", expanded=False):
            st.markdown("""
            Los datos contenidos en este visualizador son parte del **estudio bibliométrico** desarrollado por el Dr. Ronald Cancino, Dr. José Coloma y Matías Navarrete 
            para el **análisis de capacidades CTCI** del proyecto Laboratorio Natural Subantártico. 
            """)                

        # --- FILTROS ---
        st.subheader("Filtros")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            search_autor = st.text_input("🔍 Buscar por autor(a):", "")
        with f_col2:
            opciones = ["Todos"] + sorted(df_articulos["Ambiente"].unique().tolist())
            filter_amb = st.selectbox("🌍 Filtrar por ambiente:", opciones)

        # Copias filtradas
        df_art_f = df_articulos.copy()
        df_red_f = df_redes.copy()
        df_inst_f = df_inst.copy()

        if search_autor:
            df_art_f = df_art_f[df_art_f["Autor(a)"].str.contains(search_autor, case=False, na=False)]
        if filter_amb != "Todos":
            df_art_f = df_art_f[df_art_f["Ambiente"] == filter_amb]
            df_red_f = df_red_f[df_red_f["Ambiente"] == filter_amb]
            df_inst_f = df_inst_f[df_inst_f["Ambiente"] == filter_amb]

        # Texto dinámico
        filtros_activos = []
        if filter_amb != "Todos": filtros_activos.append(f"Ambiente: {filter_amb}")
        if search_autor: filtros_activos.append(f"Autor: {search_autor}")
        leyenda_dinamica = f"Filtrado por: {' | '.join(filtros_activos)}" if filtros_activos else "Todos los datos."

        # --- INDICADORES (REORDENADOS) ---
        st.divider()
        with st.container(border=True):
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Publicaciones", int(df_art_f["N° Publicaciones"].sum()))
            m_col2.metric("Autores(as)", int(df_red_f["Total autores(as)"].sum()))
            m_col3.metric("Instituciones", df_inst_f["Institución"].nunique() if not df_inst_f.empty else 0)
            m_col4.metric("Países colaboradores", df_red_f["País"].nunique())
        st.divider()

        # --- 1. BLOQUE PUBLICACIONES ---
        st.subheader("I. Investigación científica en temática subantártica")
        st.caption(leyenda_dinamica)
        
        c1, c2 = st.columns([1, 1])
        with c1:
            df_pie = df_art_f.groupby("Ambiente")["N° Publicaciones"].sum().reset_index()
            fig_pie = px.pie(df_pie, values="N° Publicaciones", names="Ambiente", hole=0.5,
                             color="Ambiente", color_discrete_map=PALETA_LNS, title="Publicaciones por ambiente")
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            df_top = df_art_f.sort_values(by="N° Publicaciones", ascending=True).tail(15)
            fig_top = px.bar(df_top, y="Autor(a)", x="N° Publicaciones", orientation='h', color="Ambiente",
                             color_discrete_map=PALETA_LNS, text="N° Publicaciones", title="Ranking: Autores(as) con mayor número de publicaciones")
            st.plotly_chart(fig_top, use_container_width=True)

        # --- 2. BLOQUE INSTITUCIONES ---
        st.divider()
        st.subheader("II. Redes de colaboración inter-institucional")
        st.caption(leyenda_dinamica)
        
        if not df_inst_f.empty:
            df_pais_inst = df_inst_f.groupby(['País', 'ISO']).agg({'Institución': 'nunique'}).reset_index()
            
            otros_paises_inst = df_pais_inst[df_pais_inst['País'] != 'Chile']
            v_max_inst = otros_paises_inst['Institución'].max() if not otros_paises_inst.empty else df_pais_inst['Institución'].max()
            df_pais_inst['Color_Plot'] = df_pais_inst['Institución'].clip(upper=v_max_inst)

            i_col1, i_col2 = st.columns([1, 1])
            with i_col1:
                fig_inst_map = px.choropleth(df_pais_inst, locations="ISO", color="Color_Plot", hover_name="País",
                                             hover_data={"Institución": True, "Color_Plot": False},
                                             color_continuous_scale="Blues")
                fig_inst_map.update_layout(coloraxis_colorbar=dict(title="N° instituciones", orientation="h", y=-0.2), margin=dict(l=0,r=0,t=40,b=100))
                st.plotly_chart(fig_inst_map, use_container_width=True)
            with i_col2:
                fig_pais_bar = px.bar(df_pais_inst.sort_values(by="Institución", ascending=True).tail(10), 
                                      y="País", x="Institución", orientation='h', 
                                      text="Institución", title="Ranking: Países con más instituciones colaboradoras")
                fig_pais_bar.update_traces(marker_color='#22A7E0', textposition='outside')
                st.plotly_chart(fig_pais_bar, use_container_width=True)
            
            df_inst_ranking = df_inst_f.groupby(["Abrev", "Institución", "Ambiente"]).agg({"Total autores(as)": "sum"}).reset_index()
            orden_inst = df_inst_f.groupby('Abrev')['Total autores(as)'].sum().sort_values().tail(15).index
            df_inst_ranking = df_inst_ranking[df_inst_ranking['Abrev'].isin(orden_inst)]

            fig_inst_bar = px.bar(df_inst_ranking, y="Abrev", x="Total autores(as)", orientation='h',
                                  color="Ambiente", color_discrete_map=PALETA_LNS,
                                  title="Ranking: Instituciones con mayor número de colaboradores(as)",
                                  hover_data={"Institución": True},
                                  category_orders={"Abrev": list(orden_inst)})
            st.plotly_chart(fig_inst_bar, use_container_width=True)

        # --- 3. BLOQUE COLABORACIÓN (REDES) ---
        st.divider()
        st.subheader("III. Redes de colaboración internacional")
        st.caption(f"Ambiente: {filter_amb}")
        
        df_red_mapa = df_red_f.dropna(subset=['ISO'])
        df_mapa = df_red_mapa.groupby(['País', 'ISO'])['Total autores(as)'].sum().reset_index()
        
        if not df_mapa.empty:
            otros_paises_red = df_mapa[df_mapa['País'] != 'Chile']
            v_max_red = otros_paises_red['Total autores(as)'].max() if not otros_paises_red.empty else df_mapa['Total autores(as)'].max()
            df_mapa['Color_Plot'] = df_mapa['Total autores(as)'].clip(upper=v_max_red)

            m1, m2 = st.columns([1.2, 1]) 
            with m1:
                fig_world = px.choropleth(df_mapa, locations="ISO", color="Color_Plot", hover_name="País",
                                          hover_data={"Total autores(as)": True, "Color_Plot": False},
                                          color_continuous_scale="Reds")
                fig_world.update_layout(coloraxis_colorbar=dict(title="N° autores(as)", orientation="h", y=-0.2), margin=dict(l=0,r=0,t=40,b=100))
                st.plotly_chart(fig_world, use_container_width=True)
            with m2:
                fig_p = px.bar(df_mapa.sort_values(by="Total autores(as)", ascending=True).tail(10), 
                               y="País", x="Total autores(as)", orientation='h', text="Total autores(as)", 
                               title="Ranking: Países con mayor colaboración (autores/as)")
                fig_p.update_traces(marker_color='#ee750a')
                st.plotly_chart(fig_p, use_container_width=True)

# --- 4. BLOQUE TABLAS ---
        st.divider()
        st.subheader("IV. Tablas de datos")
        st.caption(leyenda_dinamica)
        t1, t2, t3 = st.tabs(["📄 Publicaciones", "🏢 Instituciones", "🌍 Colaboración internacional"])
        
        with t1: 
            st.dataframe(df_art_f, use_container_width=True, hide_index=True)
        
        with t2: 
            # Aquí ocultamos la columna 'Institución' (nombre completo) dejando solo 'Abrev' y las demás
            st.dataframe(
                df_inst_f, 
                use_container_width=True, 
                hide_index=True,
                column_config={"nombre": None} # Esto oculta la columna
            )
        
        with t3: 
            st.dataframe(df_red_f, use_container_width=True, hide_index=True)

# --- MÓDULO MAPA DE CAPACIDADES ---

elif "Mapa" in menu:
    st.subheader("⚲ Directorio georreferenciado de capacidades CTCI")
    st.caption("Visualización de infraestructura y equipamiento científico en el territorio austral de Chile.")
    
    # 1. Cargar datos
    df_cap = cargar_datos("capacidades")

    if not df_cap.empty:
        # --- LIMPIEZA Y NORMALIZACIÓN DE DATOS ---
        df_cap.columns = df_cap.columns.str.strip()
        
        # Normalización robusta de coordenadas (maneja comas y formatos de texto)
        df_cap['lat'] = df_cap['lat'].astype(str).str.replace(',', '.')
        df_cap['lon'] = df_cap['lon'].astype(str).str.replace(',', '.')
        
        # Extraer solo los números y signos para evitar caracteres extraños
        df_cap['lat'] = df_cap['lat'].str.extract(r'([-+]?\d*\.?\d+)')
        df_cap['lon'] = df_cap['lon'].str.extract(r'([-+]?\d*\.?\d+)')
        
        # Convertir a numérico y eliminar filas sin coordenadas válidas
        df_cap['lat'] = pd.to_numeric(df_cap['lat'], errors='coerce')
        df_cap['lon'] = pd.to_numeric(df_cap['lon'], errors='coerce')
        df_cap = df_cap.dropna(subset=['lat', 'lon'])
        
        # --- LÓGICA DE FILTROS DINÁMICOS ---
        st.markdown("### 🔍 Explorar instalaciones y equipamiento")
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            # 1. Filtro de Región
            opciones_reg = ["Todas"] + sorted(df_cap["region"].unique().tolist()) if "region" in df_cap.columns else ["Todas"]
            f_region = st.selectbox("Filtrar por región:", opciones_reg)

        # DataFrame temporal para alimentar el filtro de instituciones según la región
        df_temp = df_cap.copy()
        if f_region != "Todas":
            df_temp = df_temp[df_temp["region"] == f_region]

        with f_col2:
            # 2. Filtro de Institución (Dinámico)
            opciones_inst = ["Todas"] + sorted(df_temp["institucion_princ"].unique().tolist()) if "institucion_princ" in df_temp.columns else ["Todas"]
            f_inst_p = st.selectbox("Filtrar por institución:", opciones_inst)

        with f_col3:
            # 3. Búsqueda por texto libre
            search_cap = st.text_input("Buscar equipamiento:", "")

        # --- APLICAR FILTROS FINALES ---
        df_cap_f = df_temp.copy()
        
        if f_inst_p != "Todas":
            df_cap_f = df_cap_f[df_cap_f["institucion_princ"] == f_inst_p]
            
        if search_cap:
            # Búsqueda en columnas clave
            cols_busqueda = ['nombre', 'equipamiento', 'info']
            cols_presentes = [c for c in cols_busqueda if c in df_cap_f.columns]
            if cols_presentes:
                mask = df_cap_f[cols_presentes].apply(
                    lambda x: x.str.contains(search_cap, case=False, na=False)
                ).any(axis=1)
                df_cap_f = df_cap_f[mask]

        # --- VISUALIZACIÓN DE MAPA ---
        st.divider()
        if not df_cap_f.empty:
            st.markdown(f"**Ubicación de las {len(df_cap_f)} instalaciones seleccionadas:**")
            st.map(df_cap_f, latitude="lat", longitude="lon", color="#22A7E0", size=40)
            
            # >>> AQUÍ EMPIEZA LA INTEGRACIÓN DEL NUEVO CÓDIGO <<<
            
            # --- DETALLE DE LAS INSTALACIONES ---
        st.divider()
        st.subheader("Listado de instituciones e instalaciones CTCI")

        # 1. Configuración básica
        items_por_pagina = 10
        total_items = len(df_cap_f)
        total_paginas = (total_items + items_por_pagina - 1) // items_por_pagina

        # 2. Inicializar y resetear estado si cambian los filtros
        if 'pagina_actual' not in st.session_state:
            st.session_state.pagina_actual = 1
            
        if 'last_total' not in st.session_state or st.session_state.last_total != total_items:
            st.session_state.pagina_actual = 1
            st.session_state.last_total = total_items

        # 3. Calcular índices
        inicio = (st.session_state.pagina_actual - 1) * items_por_pagina
        fin = inicio + items_por_pagina

        # 4. MOSTRAR EL LISTADO 
        for index, row in df_cap_f.iloc[inicio:fin].iterrows():
            nombre_inst = row.get('nombre', 'Sin nombre')
            abrev_inst = row.get('Abrev', 'S/A') 
            comuna_inst = row.get('comuna', 'Sin comuna')
            
            with st.expander(f"📍 {nombre_inst} ({abrev_inst}) - {comuna_inst}"):
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.markdown(f"**Institución principal:** {row.get('institucion_princ', 'N/A')}")
                    st.markdown(f"**Dirección:** {row.get('direccion', 'N/A')}")
                    st.markdown(f"**Equipamiento destacado:** {row.get('equipamiento', 'N/A')}")
                    st.markdown(f"**Información adicional:** {row.get('info', 'N/A')}")
                
                    
                    # 4. Construcción de la URL de pre-llenado

                    with col_b:
                        st.markdown("**Contacto:**")
                        st.write(f"👤 {row.get('encargado', 'N/A')}")
                        st.write(f"📧 {row.get('contacto', 'N/A')}")
    
                        # 1. Botón de Sitio Web
                        web = str(row.get('sitio_web', ''))
                        if web != '' and web != 'nan':
                            st.link_button("🌐 Ir al Sitio Web", web, use_container_width=True)
    
                        # 2. CONFIGURACIÓN DEL REPORTE DE ERROR
                        # Extraemos el nombre de la fila actual para el pre-llenado
                        nombre_inst = row.get('nombre', 'Sin nombre')
    
                        # Codificamos el nombre para que la URL sea segura (maneja espacios y tildes)
                        import urllib.parse
                        nombre_codificado = urllib.parse.quote(nombre_inst)
    
                        # Tu ID de formulario y el ID de pregunta que obtuvimos
                        id_form = "1FAIpQLSe8C_rBX8OWSRsedEWbSajnWhIn0cWdgg1jlb26cG5lNp-D-g/viewform?usp=pp_url&entry.431876949"
                        id_pregunta = "431876949"
    
                        # Construcción de la URL final
                        url_reporte = f"https://docs.google.com/forms/d/e/{id_form}/viewform?usp=pp_url&entry.{id_pregunta}={nombre_codificado}"
    
                        # Botón Reportar Error
                        st.link_button(
                            "⚠️ Reportar error", 
                            url_reporte, 
                            use_container_width=True, 
                            help=f"Notificar un error en los datos de {nombre_inst}"
                        )                   

        # 5. CONTROL DE NAVEGACIÓN SIMÉTRICO Y CENTRADO DEFINITIVO
        if total_paginas > 1:
            st.write("") # Espacio superior
            
            # Usamos 7 columnas para un control total del aire lateral
            # Las columnas 1, 2 y 6, 7 funcionan como márgenes elásticos
            _, _, col_prev, col_txt, col_next, _, _ = st.columns([2, 1, 0.5, 2, 0.5, 1, 2])
            
            with col_prev:
                # Botón de flecha izquierda
                if st.button("⬅️", key="btn_prev") and st.session_state.pagina_actual > 1:
                    st.session_state.pagina_actual -= 1
                    st.rerun()
            
            with col_txt:
                # Texto centrado con CSS para alineación vertical perfecta con el botón
                st.markdown(
                    f"""
                    <div style='text-align: center; font-size: 16px; margin-top: 5px;'>
                        Página <b>{st.session_state.pagina_actual}</b> de {total_paginas}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            
            with col_next:
                # Botón de flecha derecha
                if st.button("➡️", key="btn_next") and st.session_state.pagina_actual < total_paginas:
                    st.session_state.pagina_actual += 1
                    st.rerun()

            st.write("") # Espacio inferior

        else:
            st.warning("No hay instalaciones que coincidan con los filtros seleccionados.")
        
# --- MÓDULO CHAT DE CONSULTAS ---

elif "Chat" in menu:
    st.write("¿Clave detectada?:", "GOOGLE_API_KEY" in st.secrets)
    st.subheader("💬 Asistente Virtual de Capacidades CTCI")
    st.caption("Consulta información sobre infraestructura, equipamiento y autores usando lenguaje natural.")

    # 1. Preparar el contexto de la base de datos
    # Cargamos todas las pestañas relevantes para que la IA tenga "memoria"
    with st.status("Preparando base de conocimientos...", expanded=False) as status:
        df_cap = cargar_datos("capacidades")
        df_aut = cargar_datos("autoresLNS")
        
        # Convertimos los DataFrames a una cadena de texto que la IA pueda entender
        contexto_text = "BASE DE DATOS DE CAPACIDADES:\n" + df_cap.to_csv(index=False)
        contexto_text += "\n\nBASE DE DATOS DE AUTORES Y PUBLICACIONES:\n" + df_aut.to_csv(index=False)
        status.update(label="Base de conocimientos lista", state="complete", expanded=False)

    # 2. Configurar el historial del chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostrar mensajes previos
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 3. Lógica del Chat
    if prompt := st.chat_input("Ej: ¿Qué instituciones tienen microscopio electrónico en Magallanes?"):
        # Mostrar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generar respuesta de la IA
        with st.chat_message("assistant"):
            try:
                import google.generativeai as genai
                
                # Acceso directo a la clave (ahora que está fuera del bloque de gsheets)
                api_key = st.secrets["GOOGLE_API_KEY"]
                
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

                # Instrucciones del sistema para "entrenar" a la IA sobre su rol
                sistema_prompt = f"""
                Eres un asistente experto en el ecosistema científico (CTCI) del territorio austral de Chile. 
                Tu objetivo es responder preguntas basadas EXCLUSIVAMENTE en el contexto proporcionado abajo.
                Si la información no está en los datos, responde amablemente que no cuentas con ese detalle.
                
                CONTEXTO DE LA BASE DE DATOS:
                {contexto_text}
                """

                # Llamada al modelo
                response = model.generate_content([sistema_prompt, prompt])
                full_response = response.text
                
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                st.error(f"Hubo un error con el motor de IA: {e}")
                st.info("Asegúrate de tener configurada la GOOGLE_API_KEY en los Secrets.")


# --- PIE DE PÁGINA CON FONDO ---
st.write("") 
st.markdown("""
    <style>
    .footer {
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f0f2f6;
        color: #31333F;
        text-align: left;
        padding: 20px;
        border-radius: 10px;
        line-height: 1.6;
    }
    .footer a {
        color: #22A7E0;
        text-decoration: none;
    }
    </style>
    <div class="footer">
        <div style="display: flex; justify-content: space-between;">
            <div style="flex: 1.5;">
                <p><strong>Desarrollado por:</strong><br>
                Pamela Maldonado Venegas<br>
                <span style="font-size: 0.8em; color: #555;">Nodo Laboratorio Natural Subantártico</span></p>
            </div>
            <div style="flex: 1;">
                <p><strong>Contacto:</strong><br>
                📧 <a href="mailto:pamela.maldonado@umag.cl">pamela.maldonado@umag.cl</a><br>
                📧 <a href="mailto:nodosubantartico@umag.cl">nodosubantartico@umag.cl</a></p>
            </div>
            <div style="flex: 1;">
                <p><strong>Redes Nodo LNS:</strong><br>
                🌐 <a href="https://nodosubantartico.cl" target="_blank">nodosubantartico.cl</a><br>
                📸 <a href="https://www.instagram.com/nodosubantartico/" target="_blank">Instagram</a></p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)