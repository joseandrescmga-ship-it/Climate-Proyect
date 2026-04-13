# =====================================================
# 🌤️ ROBOT VIGILANTE CLIMÁTICO - APP WEB
# =====================================================
# Versión CORREGIDA que mantiene los resultados en pantalla
# =====================================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Importar módulos propios
from utils.aemet_api import validar_api_key, obtener_datos_clima
from utils.data_processor import (
    procesar_datos_clima, 
    calcular_estadisticas, 
    obtener_alerta_ciudades,
    hacer_prediccion
)
from utils.maps import mostrar_mapa_interactivo, mostrar_resumen_mapa

# =====================================================
# CONFIGURACIÓN DE LA PÁGINA
# =====================================================
st.set_page_config(
    page_title="Robot Climático AEMET",
    page_icon="🌤️",
    layout="wide"
)

# =====================================================
# INICIALIZAR ESTADO DE SESIÓN
# =====================================================
if 'datos_cargados' not in st.session_state:
    st.session_state.datos_cargados = False
if 'df' not in st.session_state:
    st.session_state.df = None
if 'stats' not in st.session_state:
    st.session_state.stats = None
if 'ultima_ejecucion' not in st.session_state:
    st.session_state.ultima_ejecucion = None

# =====================================================
# TÍTULO
# =====================================================
st.title("🤖 ROBOT VIGILANTE CLIMÁTICO")
st.markdown("**Conecta con AEMET, analiza el clima y explora el mapa interactivo**")
st.markdown("---")

# =====================================================
# BARRA LATERAL
# =====================================================
with st.sidebar:
    st.header("⚙️ Configuración")
    
    api_key = st.text_input(
        "🔑 API Key de AEMET",
        type="password",
        value=st.session_state.get('api_key', ''),
        help="Obtén tu clave gratis en https://opendata.aemet.es"
    )
    
    umbral_calor = st.slider(
        "🌡️ Umbral de alerta por calor (°C)",
        min_value=20,
        max_value=45,
        value=st.session_state.get('umbral', 30),
        step=1
    )
    
    ejecutar = st.button("🚀 EJECUTAR ROBOT", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # Botón para limpiar resultados
    if st.button("🗑️ Limpiar resultados", use_container_width=True):
        st.session_state.datos_cargados = False
        st.session_state.df = None
        st.session_state.stats = None
        st.rerun()
    
    st.caption("Datos proporcionados por AEMET")
    st.caption("📍 Los colores en el mapa indican la temperatura")

# =====================================================
# FUNCIÓN PARA CARGAR DATOS
# =====================================================
def cargar_datos(api_key, umbral):
    """Carga los datos y los guarda en session_state"""
    with st.spinner("🔍 Validando API Key..."):
        es_valida, mensaje = validar_api_key(api_key)
    
    if not es_valida:
        st.error(f"❌ {mensaje}")
        return False
    
    st.success("✅ API Key validada correctamente")
    
    with st.spinner("📡 Descargando datos de AEMET..."):
        datos_clima = obtener_datos_clima(api_key)
    
    if datos_clima is None:
        st.error("❌ Error al obtener los datos de AEMET")
        return False
    
    st.success(f"✅ Descargados {len(datos_clima)} registros")
    
    with st.spinner("📊 Procesando datos..."):
        df = procesar_datos_clima(datos_clima)
    
    if df is None or len(df) == 0:
        st.error("❌ No se pudieron procesar los datos")
        return False
    
    st.success(f"✅ Procesadas {len(df)} estaciones con datos válidos")
    
    # Guardar en session_state
    stats = calcular_estadisticas(df)
    
    st.session_state.df = df
    st.session_state.stats = stats
    st.session_state.datos_cargados = True
    st.session_state.umbral = umbral
    st.session_state.api_key = api_key
    st.session_state.ultima_ejecucion = datetime.now()
    
    return True

# =====================================================
# EJECUCIÓN PRINCIPAL
# =====================================================

if ejecutar:
    if not api_key:
        st.error("❌ Por favor, introduce tu API Key de AEMET")
    else:
        exito = cargar_datos(api_key, umbral_calor)
        if exito:
            st.rerun()  # Forzar recarga para mostrar los resultados

# =====================================================
# MOSTRAR RESULTADOS SI EXISTEN
# =====================================================

if st.session_state.datos_cargados and st.session_state.df is not None:
    df = st.session_state.df
    stats = st.session_state.stats
    umbral_actual = st.session_state.get('umbral', 30)
    
    # Mostrar hora de última actualización
    if st.session_state.ultima_ejecucion:
        st.caption(f"🕐 Última actualización: {st.session_state.ultima_ejecucion.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # =========================================
    # ESTADÍSTICAS
    # =========================================
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🌡️ Temp. Media", f"{stats['temp_media']:.1f}°C")
    with col2:
        st.metric("🔥 Máxima", f"{stats['temp_max']}°C", delta=stats.get('ciudad_max', '')[:20])
    with col3:
        st.metric("❄️ Mínima", f"{stats['temp_min']}°C", delta=stats.get('ciudad_min', '')[:20])
    with col4:
        st.metric("📊 Estaciones", stats['total_estaciones'])
    
    st.markdown("---")
    
    # =========================================
    # 🗺️ MAPA INTERACTIVO
    # =========================================
    st.subheader("🗺️ Mapa de Temperaturas")
    st.markdown("**Haz clic en cualquier marcador para ver los detalles de esa estación**")
    
    mostrar_resumen_mapa(df)
    mapa_datos = mostrar_mapa_interactivo(df, key_sufijo="principal")
    
    st.caption("📍 **Leyenda:** Rojo (>30°) | Naranja (20-30°) | Verde (10-20°) | Azul (0-10°) | Morado (<0°)")
    
    # =========================================
    # TABLA DE DATOS
    # =========================================
    with st.expander("📋 Ver tabla de datos completa"):
        if 'ubi' in df.columns:
            columnas_mostrar = ['ubi', 'temp', 'fint', 'hr']
        else:
            columnas_mostrar = df.columns[:4]
        st.dataframe(df[columnas_mostrar].head(50), use_container_width=True)
    
    # =========================================
    # GRÁFICOS
    # =========================================
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("🔥 Top 15 más cálidas")
        if 'ubi' in df.columns:
            top15 = df.nlargest(15, 'temp')[['ubi', 'temp']]
            fig1, ax1 = plt.subplots(figsize=(10, 5))
            colores = plt.cm.RdYlGn_r(np.linspace(0, 0.7, len(top15)))
            ax1.bar(range(len(top15)), top15['temp'], color=colores)
            ax1.set_xticks(range(len(top15)))
            ax1.set_xticklabels(top15['ubi'], rotation=45, ha='right', fontsize=8)
            ax1.set_ylabel('Temperatura (°C)')
            ax1.set_title('Temperaturas más altas')
            plt.tight_layout()
            st.pyplot(fig1)
    
    with col_graf2:
        st.subheader("❄️ Top 15 más frías")
        if 'ubi' in df.columns:
            bottom15 = df.nsmallest(15, 'temp')[['ubi', 'temp']]
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            ax2.bar(range(len(bottom15)), bottom15['temp'], color='skyblue')
            ax2.set_xticks(range(len(bottom15)))
            ax2.set_xticklabels(bottom15['ubi'], rotation=45, ha='right', fontsize=8)
            ax2.set_ylabel('Temperatura (°C)')
            ax2.set_title('Temperaturas más bajas')
            plt.tight_layout()
            st.pyplot(fig2)
    
    # =========================================
    # ALERTAS
    # =========================================
    st.subheader("⚠️ Sistema de Alertas")
    
    alertas = obtener_alerta_ciudades(df, umbral_actual)
    
    if alertas:
        st.error(f"🔴 ¡ATENCIÓN! {len(alertas)} ciudades superan {umbral_actual}°C")
        for alerta in alertas:
            st.warning(f"🔥 {alerta.get('ubi', 'Desconocida')}: {alerta['temp']}°C")
    else:
        st.success(f"✅ Todo bajo control. Máxima: {stats['temp_max']}°C")
    
    # =========================================
    # PREDICCIÓN
    # =========================================
    st.subheader("🔮 Predicción con IA")
    
    prediccion = hacer_prediccion(df)
    
    if prediccion:
        col_pred1, col_pred2 = st.columns(2)
        with col_pred1:
            st.metric("📈 Tendencia", f"{prediccion['tendencia']:.2f}°C por posición")
        with col_pred2:
            st.metric("🔮 Predicción", f"{prediccion['prediccion']:.1f}°C")
        st.info(f"🤖 **Consejo:** {prediccion['consejo']}")
    else:
        st.warning("⚠️ No hay suficientes datos para la predicción")
    
    # =========================================
    # EXPORTAR
    # =========================================
    st.subheader("💾 Exportar Datos")
    
    fecha_hoy = datetime.now().strftime("%Y-%m-%d_%H-%M")
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar datos (CSV)",
        data=csv_data,
        file_name=f"clima_{fecha_hoy}.csv",
        mime="text/csv"
    )

else:
    # Mostrar mensaje inicial
    st.info("👈 **Configura tu API Key en la barra lateral y presiona 'EJECUTAR ROBOT'**")
    
    with st.expander("🌟 ¿Qué hace este robot?"):
        st.markdown("""
        - **Conecta** con AEMET usando tu API Key
        - **Descarga** datos climáticos de toda España  
        - **🗺️ Mapa interactivo** con colores según temperatura
        - **Analiza** temperaturas máximas, mínimas y medias
        - **Visualiza** gráficos interactivos
        - **Alerta** cuando se superan umbrales de calor
        - **Predice** tendencias usando Inteligencia Artificial
        """)
