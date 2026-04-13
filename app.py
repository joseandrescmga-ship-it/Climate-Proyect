import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Robot Climático AEMET", page_icon="🌤️", layout="wide")

st.title("🤖 ROBOT VIGILANTE CLIMÁTICO")
st.markdown("**Conecta con AEMET, analiza el clima**")
st.markdown("---")

# Inicializar estado
if 'datos_cargados' not in st.session_state:
    st.session_state.datos_cargados = False
if 'df' not in st.session_state:
    st.session_state.df = None

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("🔑 API Key de AEMET", type="password")
    umbral_calor = st.slider("🌡️ Umbral de alerta (°C)", 20, 45, 30, 1)
    ejecutar = st.button("🚀 EJECUTAR ROBOT", type="primary", use_container_width=True)

# Funciones
def validar_api_key(key):
    try:
        url = "https://opendata.aemet.es/opendata/api/observacion/convencional/todas"
        headers = {'api_key': key}
        respuesta = requests.get(url, headers=headers, timeout=10)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            return datos.get('estado') == 200
        return False
    except:
        return False

def obtener_datos(key):
    url_base = "https://opendata.aemet.es/opendata/api/observacion/convencional/todas"
    headers = {'api_key': key}
    respuesta = requests.get(url_base, headers=headers)
    datos = respuesta.json()
    if datos.get('estado') != 200:
        return None
    url_datos = datos['datos']
    respuesta_final = requests.get(url_datos)
    return respuesta_final.json()

# Ejecución
if ejecutar:
    if not api_key:
        st.error("❌ Introduce tu API Key")
    else:
        with st.spinner("Validando API Key..."):
            if not validar_api_key(api_key):
                st.error("❌ API Key inválida")
            else:
                with st.spinner("Descargando datos..."):
                    datos_clima = obtener_datos(api_key)
                
                if datos_clima is None:
                    st.error("❌ Error al obtener datos")
                else:
                    df = pd.DataFrame(datos_clima)
                    if 'ta' in df.columns:
                        df['temp'] = pd.to_numeric(df['ta'], errors='coerce')
                    else:
                        st.error("No se encontró columna de temperatura")
                        st.stop()
                    
                    df = df.dropna(subset=['temp'])
                    st.session_state.df = df
                    st.session_state.datos_cargados = True
                    st.success(f"✅ Datos cargados: {len(df)} estaciones")
                    # ⚠️ ELIMINÉ st.rerun() - ESO CAUSABA EL ERROR

# Mostrar resultados (esto se ejecuta automáticamente después de cargar)
if st.session_state.datos_cargados and st.session_state.df is not None:
    df = st.session_state.df
    
    temp_max = df['temp'].max()
    temp_min = df['temp'].min()
    temp_media = df['temp'].mean()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🌡️ Temp. Media", f"{temp_media:.1f}°C")
    col2.metric("🔥 Máxima", f"{temp_max}°C")
    col3.metric("❄️ Mínima", f"{temp_min}°C")
    
    st.markdown("---")
    
    st.subheader("📋 Datos")
    if 'ubi' in df.columns:
        st.dataframe(df[['ubi', 'temp']].head(20), use_container_width=True)
    else:
        st.dataframe(df[['temp']].head(20), use_container_width=True)
    
    st.subheader("📊 Top 10 más cálidas")
    if 'ubi' in df.columns:
        top10 = df.nlargest(10, 'temp')[['ubi', 'temp']]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(range(len(top10)), top10['temp'], color='orange')
        ax.set_xticks(range(len(top10)))
        ax.set_xticklabels(top10['ubi'], rotation=45, ha='right', fontsize=8)
        ax.set_ylabel('Temperatura (°C)')
        st.pyplot(fig)
    
    st.subheader("⚠️ Alertas")
    alertas = df[df['temp'] >= umbral_calor]
    if len(alertas) > 0:
        st.error(f"🔴 {len(alertas)} ciudades superan {umbral_calor}°C")
    else:
        st.success(f"✅ Todo bien. Máxima: {temp_max}°C")
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar CSV", csv, f"clima_{datetime.now().strftime('%Y-%m-%d')}.csv")
