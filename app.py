import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Nodo LNS - Gestión de Datos", layout="wide")

# --- CONEXIÓN CON GOOGLE SHEETS ---
# No es necesario pasar la URL manualmente si ya está en secrets.toml
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para cargar datos optimizada
@st.cache_data(ttl=600) # Caché de 10 minutos para no saturar la conexión
def cargar_datos(nombre_pestana):
    try:
        # La librería busca automáticamente la URL en st.secrets["connections"]["gsheets"]["spreadsheet"]
        return conn.read(worksheet=nombre_pestana)
    except Exception as e:
        st.error(f"Error al cargar la pestaña '{nombre_pestana}': {e}")
        return pd.DataFrame()

st.title("📊 Plataforma de Datos Laboratorio Natural Subantártico")

# --- MENÚ LATERAL ---
menu = st.sidebar.selectbox("Seleccionar Módulo", 
                            ["Dashboard de Publicaciones", "Mapa de Capacidades", "Editor y Limpieza"])

if menu == "Dashboard de Publicaciones":
    st.header("Análisis Científico")
    
    # IMPORTANTE: Verifica que la pestaña se llame exactamente "autoresLNS" en tu Google Sheet
    df = cargar_datos("autoresLNS") 
    
    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            # Verificamos que las columnas existan antes de graficar
            columnas_necesarias = ["Institucion", "Total", "Subcategoria"]
            if all(col in df.columns for col in columnas_necesarias):
                fig = px.bar(df, x="Institucion", y="Total", color="Subcategoria", title="Publicaciones por Institución")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"La hoja debe tener las columnas: {columnas_necesarias}")
        
        with col2:
            if "Total" in df.columns:
                total_pub = df['Total'].sum()
                st.metric("Total de Publicaciones registradas", int(total_pub))
                
                if "Subcategoria" in df.columns:
                    top_area = df.groupby('Subcategoria')['Total'].sum().idxmax()
                    st.write(f"El área con mayor actividad es: **{top_area}**")
            
        st.subheader("Datos Crudos")
        st.dataframe(df)

elif menu == "Mapa de Capacidades":
    st.header("📍 Georreferenciación de Capacidades CTCI")
    
    # IMPORTANTE: Verifica que la pestaña se llame exactamente "capacidades"
    df_cap = cargar_datos("capacidades")
    
    if not df_cap.empty:
        # Streamlit necesita columnas llamadas 'lat' y 'lon' (o 'latitude'/'longitude')
        # Si tus columnas se llaman distinto (ej: 'LATITUD'), renómbralas:
        if "LATITUD" in df_cap.columns and "LONGITUD" in df_cap.columns:
            df_cap = df_cap.rename(columns={"LATITUD": "lat", "LONGITUD": "lon"})
        
        if "lat" in df_cap.columns and "lon" in df_cap.columns:
            st.map(df_cap)
        else:
            st.warning("No se encontraron columnas de ubicación (lat, lon).")
            
        st.dataframe(df_cap)