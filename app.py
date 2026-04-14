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
            'pais': 'País', 'ISO': 'ISO', 'autores_tot': 'Total Autores',
            'nombre_completo': 'Institución', 'abrev': 'Abrev'
        }
        df = df.rename(columns=columnas_a_renombrar)
        return df
    except Exception as e:
        st.error(f"Error al cargar la pestaña '{nombre_pestana}': {e}")
        return pd.DataFrame()

# --- TÍTULO PRINCIPAL ---
st.title("○ Plataforma de Datos Laboratorio Natural Subantártico")

menu = st.sidebar.selectbox("Seleccionar Módulo", 
                            ["◒ Dashboard de Publicaciones", "⚲ Mapa de Capacidades", "💬 Chat de Consultas"])

if "Dashboard" in menu:
    df_articulos = cargar_datos("autoresLNS")
    df_redes = cargar_datos("pais_autores")
    df_inst = cargar_datos("inst_autores")
    
    if not df_articulos.empty and not df_redes.empty:
        # Estandarización de ambientes
        for df in [df_articulos, df_redes, df_inst]:
            if not df.empty:
                df["Ambiente"] = df["Ambiente"].astype(str).str.upper().str.strip()

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

        # --- INDICADORES ---
        st.divider()
        with st.container(border=True):
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Publicaciones", int(df_art_f["N° Publicaciones"].sum()))
            m_col2.metric("Países colaboradores", df_red_f["País"].nunique())
            m_col3.metric("Autores(as)", int(df_red_f["Total Autores"].sum()))
            m_col4.metric("Instituciones", df_inst_f["Institución"].nunique() if not df_inst_f.empty else 0)
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
            
            # NORMALIZACIÓN
            otros_paises_inst = df_pais_inst[df_pais_inst['País'] != 'Chile']
            v_max_inst = otros_paises_inst['Institución'].max() if not otros_paises_inst.empty else df_pais_inst['Institución'].max()
            df_pais_inst['Color_Plot'] = df_pais_inst['Institución'].clip(upper=v_max_inst)

            i_col1, i_col2 = st.columns([1, 1])
            with i_col1:
                fig_inst_map = px.choropleth(df_pais_inst, locations="ISO", color="Color_Plot", hover_name="País",
                                             hover_data={"Institución": True, "Color_Plot": False},
                                             color_continuous_scale="Blues", title="")
                fig_inst_map.update_layout(coloraxis_colorbar=dict(title="N° instituciones", orientation="h", y=-0.2), margin=dict(l=0,r=0,t=40,b=100))
                st.plotly_chart(fig_inst_map, use_container_width=True)
            with i_col2:
                # Ranking Países (Monocolor)
                fig_pais_bar = px.bar(df_pais_inst.sort_values(by="Institución", ascending=True).tail(10), 
                                      y="País", x="Institución", orientation='h', 
                                      text="Institución", title="Ranking: Países con más instituciones colaboradoras")
                fig_pais_bar.update_traces(marker_color='#22A7E0', textposition='outside')
                st.plotly_chart(fig_pais_bar, use_container_width=True)
            
            # Ranking Instituciones (Discriminado por Ambiente)
            df_inst_ranking = df_inst_f.groupby(["Abrev", "Institución", "Ambiente"]).agg({"Total Autores": "sum"}).reset_index()
            orden_inst = df_inst_f.groupby('Abrev')['Total Autores'].sum().sort_values().tail(15).index
            df_inst_ranking = df_inst_ranking[df_inst_ranking['Abrev'].isin(orden_inst)]

            fig_inst_bar = px.bar(df_inst_ranking, y="Abrev", x="Total Autores", orientation='h',
                                  color="Ambiente", color_discrete_map=PALETA_LNS,
                                  title="Ranking: Instituciones con mayor número de colaboradores(as)",
                                  hover_data={"Institución": True},
                                  category_orders={"Abrev": list(orden_inst)})
            st.plotly_chart(fig_inst_bar, use_container_width=True)

        # --- 3. BLOQUE COLABORACIÓN (REDES NORMALIZADO) ---
        st.divider()
        st.subheader("III. Redes de colaboración internacional")
        st.caption(f"Ambiente: {filter_amb}")
        
        df_red_mapa = df_red_f.dropna(subset=['ISO'])
        df_mapa = df_red_mapa.groupby(['País', 'ISO'])['Total Autores'].sum().reset_index()
        
        if not df_mapa.empty:
            # NORMALIZACIÓN: Escala basada en el máximo fuera de Chile
            otros_paises_red = df_mapa[df_mapa['País'] != 'Chile']
            v_max_red = otros_paises_red['Total Autores'].max() if not otros_paises_red.empty else df_mapa['Total Autores'].max()
            df_mapa['Color_Plot'] = df_mapa['Total Autores'].clip(upper=v_max_red)

            m1, m2 = st.columns([1.2, 1]) 
            with m1:
                fig_world = px.choropleth(df_mapa, locations="ISO", color="Color_Plot", hover_name="País",
                                          hover_data={"Total Autores": True, "Color_Plot": False},
                                          color_continuous_scale="Reds", title="")
                fig_world.update_layout(coloraxis_colorbar=dict(title="N° autores(as)", orientation="h", y=-0.2), margin=dict(l=0,r=0,t=40,b=100))
                st.plotly_chart(fig_world, use_container_width=True)
            with m2:
                fig_p = px.bar(df_mapa.sort_values(by="Total Autores", ascending=True).tail(10), 
                               y="País", x="Total Autores", orientation='h', text="Total Autores", title="Ranking: Países con mayor colaboración (autores/as)")
                fig_p.update_traces(marker_color='#ee750a')
                st.plotly_chart(fig_p, use_container_width=True)

        # --- 4. BLOQUE TABLAS ---
        st.divider()
        st.subheader("IV. Tablas de datos detallados")
        st.caption(leyenda_dinamica)
        t1, t2, t3 = st.tabs(["📄 Publicaciones", "🏢 Instituciones", "🌍 Colaboración internacional"])
        with t1: st.dataframe(df_art_f, use_container_width=True, hide_index=True)
        with t2: st.dataframe(df_inst_f, use_container_width=True, hide_index=True)
        with t3: st.dataframe(df_red_f, use_container_width=True, hide_index=True)