import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Nodo LNS - Gestión de Datos", layout="wide")

# --- CONEXIÓN CON GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def cargar_datos(nombre_pestana):
    try:
        df = conn.read(worksheet=nombre_pestana)
        
        # --- RENOMBRAR CAMPOS ESPECÍFICOS ---
        # Mapeamos 'Nombre Original': 'Nombre Nuevo'
        columnas_a_renombrar = {
            'autor': 'Autor(a)',
            'ambiente': 'Ambiente',
            'publicaciones_tot': 'N° Publicaciones'
        }
        
        # Solo renombramos si las columnas existen en la pestaña actual
        df = df.rename(columns=columnas_a_renombrar)
        return df
    except Exception as e:
        st.error(f"Error al cargar la pestaña '{nombre_pestana}': {e}")
        return pd.DataFrame()

st.title("📊 Plataforma de Datos Laboratorio Natural Subantártico")

# --- MENÚ LATERAL ---
menu = st.sidebar.selectbox("Seleccionar Módulo", 
                            ["Dashboard de Publicaciones", "Mapa de Capacidades", "Editor y Limpieza"])

if menu == "Dashboard de Publicaciones":
    st.header("Análisis Científico")
    
    df = cargar_datos("autoresLNS") 
    
    if not df.empty:
        # Definimos los nuevos nombres para la lógica del dashboard
        col_autor = "Autor(a)"
        col_ambiente = "Ambiente"
        col_total = "N° Publicaciones"

        col1, col2 = st.columns([2, 1]) # Ajustamos ancho de columnas
        
        with col1:
            # Verificamos que las columnas ya renombradas existan
            if col_autor in df.columns and col_total in df.columns:
                # Gráfico: Publicaciones por Autor(a) coloreado por Ambiente
                fig = px.bar(df, 
                             x=col_autor, 
                             y=col_total, 
                             color=col_ambiente if col_ambiente in df.columns else None,
                             title="Total de Publicaciones por Autor(a)",
                             labels={col_total: "Cantidad de Publicaciones"})
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"No se encontraron las columnas esperadas. Verifica que en el Excel se llamen: autor, ambiente, publicaciones_tot")
        
        with col2:
            if col_total in df.columns:
                total_pub = df[col_total].sum()
                st.metric("Total de Publicaciones", int(total_pub))
                
                if col_ambiente in df.columns:
                    # Área con más publicaciones
                    top_area = df.groupby(col_ambiente)[col_total].sum().idxmax()
                    st.info(f"El ambiente con mayor impacto es: **{top_area}**")
            
        st.subheader("Vista Detallada de Datos")
        st.dataframe(df, use_container_width=True)

elif menu == "Mapa de Capacidades":
    st.header("📍 Georreferenciación de Capacidades CTCI")
    df_cap = cargar_datos("capacidades")
    
    if not df_cap.empty:
        if "LATITUD" in df_cap.columns and "LONGITUD" in df_cap.columns:
            df_cap = df_cap.rename(columns={"LATITUD": "lat", "LONGITUD": "lon"})
        
        if "lat" in df_cap.columns and "lon" in df_cap.columns:
            st.map(df_cap)
        else:
            st.warning("No se encontraron columnas de ubicación (lat, lon).")
            
        st.dataframe(df_cap)