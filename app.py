# =====================================================
# 🌤️ ROBOT VIGILANTE CLIMÁTICO - APP WEB
# =====================================================
# Web interactiva con Streamlit
# =====================================================

import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression

# =====================================================
# CONFIGURACIÓN DE LA PÁGINA
# =====================================================
st.set_page_config(
    page_title="Robot Climático AEMET",
    page_icon="🌤️",
    layout="wide"
)

# =====================================================
# TÍTULO Y DESCRIPCIÓN
# =====================================================
st.title("🤖 ROBOT VIGILANTE CLIMÁTICO")
st.markdown("**Conecta con AEMET, analiza el clima y obtén predicciones**")
st.markdown("---")

# =====================================================
# BARRA LATERAL (Configuración)
# =====================================================
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Input para API Key (oculta)
    api_key = st.text_input(
        "🔑 API Key de AEMET",
        type="password",
        help="Obtén tu clave gratis en https://opendata.aemet.es"
    )
    
    # Slider para umbral de alerta
    umbral_calor = st.slider(
        "🌡️ Umbral de alerta por calor (°C)",
        min_value=20,
        max_value=45,
        value=30,
        step=1
    )
    
    # Botón para ejecutar
    ejecutar = st.button("🚀 EJECUTAR ROBOT", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.caption("Datos proporcionados por AEMET")

# =====================================================
# FUNCIONES DEL ROBOT
# =====================================================

def validar_api_key(key):
    """Verifica si la API Key es correcta"""
    url = "https://opendata.aemet.es/opendata/api/observacion/convencional/todas"
    headers = {'api_key': key}
    
    try:
        respuesta = requests.get(url, headers=headers, timeout=10)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            return datos.get('estado') == 200
        return False
    except:
        return False

def obtener_datos(key):
    """Descarga los datos climáticos de AEMET"""
    url_base = "https://opendata.aemet.es/opendata/api/observacion/convencional/todas"
    headers = {'api_key': key}
    
    respuesta = requests.get(url_base, headers=headers)
    datos = respuesta.json()
    
    if datos.get('estado') != 200:
        return None
    
    url_datos = datos['datos']
    respuesta_final = requests.get(url_datos)
    return respuesta_final.json()

def procesar_datos(datos_clima):
    """Convierte los datos en DataFrame y calcula temperaturas"""
    df = pd.DataFrame(datos_clima)
    
    # Usar 'ta' como temperatura del aire
    if 'ta' in df.columns:
        df['temp'] = pd.to_numeric(df['ta'], errors='coerce')
    elif 'temp' in df.columns:
        df['temp'] = pd.to_numeric(df['temp'], errors='coerce')
    else:
        return None
    
    df = df.dropna(subset=['temp'])
    return df

# =====================================================
# EJECUCIÓN PRINCIPAL
# =====================================================

if ejecutar:
    if not api_key:
        st.error("❌ Por favor, introduce tu API Key de AEMET")
    else:
        # Validar API Key
        with st.spinner("🔍 Validando API Key..."):
            es_valida = validar_api_key(api_key)
        
        if not es_valida:
            st.error("❌ API Key inválida. Verifica tu clave e inténtalo de nuevo.")
        else:
            st.success("✅ API Key validada correctamente")
            
            # Descargar datos
            with st.spinner("📡 Descargando datos de AEMET..."):
                datos_clima = obtener_datos(api_key)
            
            if datos_clima is None:
                st.error("❌ Error al obtener los datos de AEMET")
            else:
                st.success(f"✅ Descargados {len(datos_clima)} registros")
                
                # Procesar datos
                df = procesar_datos(datos_clima)
                
                if df is None or len(df) == 0:
                    st.error("❌ No se pudieron procesar los datos de temperatura")
                else:
                    st.success(f"✅ Procesadas {len(df)} estaciones con datos válidos")
                    
                    # =============================================
                    # SECCIÓN 1: ESTADÍSTICAS
                    # =============================================
                    st.subheader("📈 Estadísticas Generales")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    temp_max = df['temp'].max()
                    temp_min = df['temp'].min()
                    temp_media = df['temp'].mean()
                    
                    ciudad_max = df[df['temp'] == temp_max]['ubi'].values[0] if 'ubi' in df.columns else "Desconocida"
                    ciudad_min = df[df['temp'] == temp_min]['ubi'].values[0] if 'ubi' in df.columns else "Desconocida"
                    
                    col1.metric("🌡️ Temperatura Media", f"{temp_media:.1f}°C")
                    col2.metric("🔥 Máxima", f"{temp_max}°C", delta=f"en {ciudad_max[:20]}")
                    col3.metric("❄️ Mínima", f"{temp_min}°C", delta=f"en {ciudad_min[:20]}")
                    col4.metric("📊 Estaciones", len(df))
                    
                    # =============================================
                    # SECCIÓN 2: TABLA DE DATOS
                    # =============================================
                    st.subheader("📋 Tabla de Datos")
                    
                    if 'ubi' in df.columns and 'fint' in df.columns:
                        columnas_mostrar = ['ubi', 'temp']
                        if 'hr' in df.columns:
                            columnas_mostrar.append('hr')
                        if 'fint' in df.columns:
                            columnas_mostrar.append('fint')
                        
                        df_mostrar = df[columnas_mostrar].head(20)
                        st.dataframe(df_mostrar, use_container_width=True)
                    else:
                        st.dataframe(df.head(20), use_container_width=True)
                    
                    # =============================================
                    # SECCIÓN 3: GRÁFICOS
                    # =============================================
                    col_graf1, col_graf2 = st.columns(2)
                    
                    # Gráfico de las más cálidas
                    with col_graf1:
                        st.subheader("🔥 Top 15 más cálidas")
                        top15 = df.nlargest(15, 'temp')[['ubi', 'temp']].copy() if 'ubi' in df.columns else df.nlargest(15, 'temp')
                        
                        fig1, ax1 = plt.subplots(figsize=(10, 6))
                        colores = plt.cm.RdYlGn_r(np.linspace(0, 0.7, len(top15)))
                        barras = ax1.bar(range(len(top15)), top15['temp'], color=colores)
                        
                        if 'ubi' in df.columns:
                            ax1.set_xticks(range(len(top15)))
                            ax1.set_xticklabels(top15['ubi'], rotation=45, ha='right', fontsize=8)
                        
                        ax1.set_title('Temperaturas más altas', fontsize=12)
                        ax1.set_ylabel('Temperatura (°C)')
                        
                        for barra, temp in zip(barras, top15['temp']):
                            ax1.text(barra.get_x() + barra.get_width()/2, barra.get_height() + 0.3,
                                    f"{temp:.1f}°C", ha='center', va='bottom', fontsize=8)
                        
                        plt.tight_layout()
                        st.pyplot(fig1)
                    
                    # Gráfico de las más frías
                    with col_graf2:
                        st.subheader("❄️ Top 15 más frías")
                        bottom15 = df.nsmallest(15, 'temp')[['ubi', 'temp']].copy() if 'ubi' in df.columns else df.nsmallest(15, 'temp')
                        
                        fig2, ax2 = plt.subplots(figsize=(10, 6))
                        barras = ax2.bar(range(len(bottom15)), bottom15['temp'], color='skyblue')
                        
                        if 'ubi' in df.columns:
                            ax2.set_xticks(range(len(bottom15)))
                            ax2.set_xticklabels(bottom15['ubi'], rotation=45, ha='right', fontsize=8)
                        
                        ax2.set_title('Temperaturas más bajas', fontsize=12)
                        ax2.set_ylabel('Temperatura (°C)')
                        
                        for barra, temp in zip(barras, bottom15['temp']):
                            ax2.text(barra.get_x() + barra.get_width()/2, barra.get_height() + 0.3,
                                    f"{temp:.1f}°C", ha='center', va='bottom', fontsize=8)
                        
                        plt.tight_layout()
                        st.pyplot(fig2)
                    
                    # =============================================
                    # SECCIÓN 4: ALERTAS
                    # =============================================
                    st.subheader("⚠️ Sistema de Alertas")
                    
                    alertas = df[df['temp'] >= umbral_calor]
                    
                    if len(alertas) > 0:
                        st.error(f"🔴 ¡ATENCIÓN! {len(alertas)} mediciones superan {umbral_calor}°C")
                        if 'ubi' in df.columns:
                            alertas_unicas = alertas.drop_duplicates(subset=['ubi'])
                            for _, fila in alertas_unicas.iterrows():
                                temp_ciudad = alertas[alertas['ubi'] == fila['ubi']]['temp'].max()
                                st.warning(f"🔥 {fila['ubi']}: {temp_ciudad}°C")
                    else:
                        st.success(f"✅ Todo bajo control. Máxima registrada: {temp_max}°C")
                    
                    # =============================================
                    # SECCIÓN 5: PREDICCIÓN IA
                    # =============================================
                    st.subheader("🔮 Predicción con IA")
                    
                    if len(df) >= 10:
                        df_ordenado = df.sort_values('temp').reset_index(drop=True)
                        X = np.array(range(10)).reshape(-1, 1)
                        y = df_ordenado['temp'].head(10).values
                        
                        modelo = LinearRegression()
                        modelo.fit(X, y)
                        
                        pendiente = modelo.coef_[0]
                        siguiente = modelo.predict([[10]])[0]
                        
                        col_pred1, col_pred2 = st.columns(2)
                        col_pred1.metric("📈 Tendencia", f"{pendiente:.2f}°C por posición")
                        col_pred2.metric("🔮 Predicción siguiente", f"{max(0, siguiente):.1f}°C")
                        
                        # Consejo del robot
                        if pendiente > 0.5:
                            st.info("🔥 **Consejo:** Las temperaturas altas dominan. ¡Cuídate del calor y mantente hidratado!")
                        elif pendiente > 0:
                            st.info("☀️ **Consejo:** Clima cálido pero controlado. Disfruta el día con precaución.")
                        elif pendiente < -0.5:
                            st.info("🧊 **Consejo:** Predominan temperaturas frías. ¡Abrígate bien antes de salir!")
                        else:
                            st.info("☁️ **Consejo:** Clima variado. Temperaturas repartidas entre frío y calor.")
                    else:
                        st.warning(f"⚠️ No hay suficientes datos para predicción (solo {len(df)} registros)")
                    
                    # =============================================
                    # SECCIÓN 6: DESCARGA DE DATOS
                    # =============================================
                    st.subheader("💾 Exportar Datos")
                    
                    fecha_hoy = datetime.now().strftime("%Y-%m-%d_%H-%M")
                    nombre_csv = f"clima_{fecha_hoy}.csv"
                    
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Descargar datos (CSV)",
                        data=csv_data,
                        file_name=nombre_csv,
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                    st.caption(f"📊 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
else:
    # Mensaje cuando no se ha ejecutado
    st.info("👈 **Configura tu API Key en la barra lateral y presiona 'EJECUTAR ROBOT'**")
    st.markdown("""
    ### 🌟 ¿Qué hace este robot?
    
    - **Conecta** con AEMET usando tu API Key
    - **Descarga** datos climáticos de toda España
    - **Analiza** temperaturas máximas, mínimas y medias
    - **Visualiza** gráficos interactivos
    - **Alerta** cuando se superan umbrales de calor
    - **Predice** tendencias usando Inteligencia Artificial
    
    ### 🔑 ¿No tienes API Key?
    1. Ve a https://opendata.aemet.es
    2. Solicita tu clave gratuita (solo necesitas email)
    3. ¡Vuelve aquí y pégala en la barra lateral!
    """)