import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Nodo LNS - Gestión de Datos", layout="wide")

# --- CONEXIÓN CON GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para cargar datos (ajusta los nombres de las pestañas según tu Excel)
def cargar_datos(nombre_pestana):
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    return conn.read(spreadsheet=url, worksheet=nombre_pestana)

st.title("📊 Plataforma de Datos Laboratorio Natural Subantártico")

# --- MENÚ LATERAL ---
menu = st.sidebar.selectbox("Seleccionar Módulo", 
                            ["Dashboard de Publicaciones", "Mapa de Capacidades", "Editor y Limpieza"])

if menu == "Dashboard de Publicaciones":
    st.header("Análisis Científico")
    df = cargar_datos("publicaciones") # Nombre de tu pestaña en Sheets
    
    col1, col2 = st.columns(2)
    with col1:
        # Gráfico por Institución
        fig = px.bar(df, x="Institucion", y="Total", color="Subcategoria", title="Publicaciones por Institución")
        st.plotly_chart(fig)
    
    with col2:
        # Aquí puedes agregar un resumen ejecutivo generado con lógica de Python
        total_pub = df['Total'].sum()
        st.metric("Total de Publicaciones registradas", total_pub)
        st.write("El área con mayor actividad es:", df.groupby('Subcategoria')['Total'].sum().idxmax())

elif menu == "Mapa de Capacidades":
    st.header("📍 Georreferenciación de Capacidades CTCI")
    df_cap = cargar_datos("capacidades")
    
    # Streamlit reconoce automáticamente columnas 'lat' y 'lon' o 'LATITUD' y 'LONGITUD'
    st.map(df_cap)
    st.dataframe(df_cap)
