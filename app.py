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
# INICIALIZAR ESTADO DE SESIÓN
# =====================================================
if 'datos_cargados' not in st.session_state:
    st.session_state.datos_cargados = False
if 'df' not in st.session_state:
    st.session_state.df = None
if 'ciudades_lista' not in st.session_state:
    st.session_state.ciudades_lista = []
if 'mostrar_resultados' not in st.session_state:
    st.session_state.mostrar_resultados = False
if 'ciudad_actual' not in st.session_state:
    st.session_state.ciudad_actual = None
if 'df_ciudad_actual' not in st.session_state:
    st.session_state.df_ciudad_actual = None
if 'api_key_validada' not in st.session_state:
    st.session_state.api_key_validada = False
if 'umbral_calor' not in st.session_state:
    st.session_state.umbral_calor = 30

# =====================================================
# MAPEO MANUAL DE PROVINCIAS/REGIONES
# =====================================================
REGIONES_MAPEO = {
    'CANARIAS': ['TENERIFE', 'GRAN CANARIA', 'LANZAROTE', 'FUERTEVENTURA', 'LA PALMA', 'EL HIERRO', 'LA GOMERA'],
    'ANDALUCÍA': ['SEVILLA', 'MÁLAGA', 'CÁDIZ', 'GRANADA', 'ALMERÍA', 'CÓRDOBA', 'JAÉN', 'HUELVA'],
    'COMUNIDAD VALENCIANA': ['VALENCIA', 'ALICANTE', 'CASTELLÓN'],
    'CATALUÑA': ['BARCELONA', 'TARRAGONA', 'GIRONA', 'LLEIDA'],
    'MADRID': ['MADRID'],
    'PAÍS VASCO': ['BILBAO', 'SAN SEBASTIÁN', 'VITORIA'],
    'GALICIA': ['A CORUÑA', 'LUGO', 'OURENSE', 'PONTEVEDRA'],
    'CASTILLA Y LEÓN': ['VALLADOLID', 'LEÓN', 'SALAMANCA', 'BURGOS', 'SEGOVIA'],
    'CASTILLA-LA MANCHA': ['TOLEDO', 'CIUDAD REAL', 'CUENCA', 'GUADALAJARA', 'ALBACETE'],
    'ARAGÓN': ['ZARAGOZA', 'HUESCA', 'TERUEL'],
    'MURCIA': ['MURCIA'],
    'BALEARES': ['PALMA', 'MALLORCA', 'MENORCA', 'IBIZA'],
    'NAVARRA': ['PAMPLONA'],
    'EXTREMADURA': ['BADAJOZ', 'CÁCERES'],
    'CANTABRIA': ['SANTANDER'],
    'ASTURIAS': ['OVIEDO'],
    'LA RIOJA': ['LOGROÑO'],
    'CEUTA': ['CEUTA'],
    'MELILLA': ['MELILLA']
}

def asignar_region(ciudad):
    ciudad_upper = ciudad.upper()
    for region, keywords in REGIONES_MAPEO.items():
        for keyword in keywords:
            if keyword in ciudad_upper:
                return region
    return "OTRAS"

# =====================================================
# FUNCIONES
# =====================================================
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

def hacer_prediccion_ciudad(df_ciudad, nombre_ciudad):
    if df_ciudad is None or len(df_ciudad) < 1:
        return None
    
    temp_actual = df_ciudad['temp'].iloc[0]
    
    if temp_actual > 30:
        prediccion = temp_actual + 1.5
        tendencia = "📈 EN AUMENTO"
        consejo = "¡Mucho calor! Mantente hidratado y evita el sol."
        icono = "🔥"
    elif temp_actual > 20:
        prediccion = temp_actual + 0.5
        tendencia = "📈 LEVE ASCENSO"
        consejo = "Temperatura agradable, ideal para actividades al aire libre."
        icono = "☀️"
    elif temp_actual > 10:
        prediccion = temp_actual - 0.5
        tendencia = "📉 LEVE DESCENSO"
        consejo = "Puede refrescar hacia la noche. Lleva una chaqueta."
        icono = "🍂"
    else:
        prediccion = temp_actual - 1.0
        tendencia = "📉 EN DESCENSO"
        consejo = "¡Hace frío! Abrígate bien."
        icono = "❄️"
    
    return {
        'ciudad': nombre_ciudad,
        'temp_actual': temp_actual,
        'prediccion': prediccion,
        'tendencia': tendencia,
        'consejo': consejo,
        'icono': icono
    }

def cargar_datos(api_key):
    """Carga los datos y los guarda en session_state"""
    with st.spinner("🔍 Validando API Key..."):
        es_valida = validar_api_key(api_key)
    
    if not es_valida:
        st.error("❌ API Key inválida. Verifica tu clave.")
        return False
    
    with st.spinner("📡 Descargando datos de AEMET..."):
        datos_clima = obtener_datos(api_key)
    
    if datos_clima is None:
        st.error("❌ Error al obtener los datos")
        return False
    
    df = pd.DataFrame(datos_clima)
    
    if 'ta' in df.columns:
        df['temp'] = pd.to_numeric(df['ta'], errors='coerce')
    else:
        st.error("No se encontró columna de temperatura")
        return False
    
    for col in ['lat', 'lon']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=['temp'])
    
    if 'ubi' in df.columns:
        ciudades = df['ubi'].dropna().unique()
        ciudades = [c for c in ciudades if isinstance(c, str)]
        st.session_state.ciudades_lista = sorted(ciudades)
        df['region'] = df['ubi'].apply(asignar_region)
    
    st.session_state.df = df
    st.session_state.datos_cargados = True
    st.success(f"✅ Datos cargados: {len(df)} estaciones con datos válidos")
    return True

# =====================================================
# PANTALLA DE INICIO (API Key)
# =====================================================
def pantalla_inicio():
    st.title("🤖 ROBOT VIGILANTE CLIMÁTICO")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("🔑 Acceso al sistema")
        
        st.markdown("""
        ### 🌤️ ¿Qué obtendrás al conectar?
        
        Al introducir tu API Key de AEMET podrás:
        
        - 📊 **Datos climáticos en tiempo real** de toda España
        - 🗺️ **Mapa interactivo** con colores según temperatura
        - 🔮 **Predicciones por IA** con tendencias y consejos
        - 🏆 **Ranking de ciudades** más cálidas y frías
        - 📍 **Búsqueda por ciudad o región**
        - 📊 **Comparativa entre ciudades**
        - ⚠️ **Alertas personalizables** por calor
        - 💾 **Exportación a CSV** para análisis externo
        
        ---
        
        ### 🔑 ¿Cómo obtener tu API Key?
        
        1. Ve a [opendata.aemet.es](https://opendata.aemet.es)
        2. Solicita tu clave gratuita (solo necesitas email)
        3. Copia la clave que recibirás por correo
        4. Pégala en el campo de abajo
        """)
        
        api_key = st.text_input(
            "🔑 Introduce tu API Key de AEMET",
            type="password",
            placeholder="Ej: eyJhbGciOiJIUzI1NiJ9.eyJzdWI...",
            help="La clave es gratuita y la obtienes en opendata.aemet.es"
        )
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            conectar = st.button("🚀 CONECTAR CON AEMET", type="primary", use_container_width=True)
        
        if conectar:
            if not api_key:
                st.error("❌ Por favor, introduce tu API Key")
            else:
                if cargar_datos(api_key):
                    st.session_state.api_key_validada = True
                    st.rerun()

# =====================================================
# PANTALLA PRINCIPAL (Datos y análisis)
# =====================================================
def pantalla_principal():
    df = st.session_state.df
    
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        umbral = st.slider("🌡️ Umbral de alerta por calor (°C)", 20, 45, st.session_state.umbral_calor, 1)
        st.session_state.umbral_calor = umbral
        
        st.markdown("---")
        
        if st.button("🗑️ Limpiar y volver al inicio", use_container_width=True):
            st.session_state.datos_cargados = False
            st.session_state.df = None
            st.session_state.mostrar_resultados = False
            st.session_state.api_key_validada = False
            st.session_state.ciudad_actual = None
            st.session_state.df_ciudad_actual = None
            st.rerun()
        
        st.caption("Datos proporcionados por AEMET")
        st.caption("📍 Los colores en el mapa indican la temperatura")
    
    st.title("🤖 ROBOT VIGILANTE CLIMÁTICO")
    st.markdown("**Datos en tiempo real de AEMET**")
    st.markdown("---")
    
    # =========================================
    # ESTADÍSTICAS GENERALES
    # =========================================
    temp_max = df['temp'].max()
    temp_min = df['temp'].min()
    temp_media = df['temp'].mean()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🌡️ Temperatura Media España", f"{temp_media:.1f}°C")
    col2.metric("🔥 Máxima España", f"{temp_max}°C")
    col3.metric("❄️ Mínima España", f"{temp_min}°C")
    
    st.markdown("---")
    
    # =========================================
    # SELECTOR DE UBICACIÓN
    # =========================================
    st.subheader("📍 Selecciona una ubicación")
    
    tipo_busqueda = st.radio(
        "Tipo de búsqueda:",
        ["🔍 Por ciudad", "🗺️ Por provincia/región", "📊 Comparar ciudades"],
        horizontal=True
    )
    
    if tipo_busqueda == "🔍 Por ciudad":
        ciudad_seleccionada = st.selectbox(
            "Elige una ciudad:",
            ["-- Selecciona una ciudad --"] + st.session_state.ciudades_lista
        )
        
        if ciudad_seleccionada and ciudad_seleccionada != "-- Selecciona una ciudad --":
            if st.button("🗺️ Ver datos y predicción", key="btn_ciudad"):
                df_ciudad = df[df['ubi'] == ciudad_seleccionada]
                if len(df_ciudad) > 0:
                    st.session_state.df_ciudad_actual = df_ciudad
                    st.session_state.ciudad_actual = ciudad_seleccionada
                    st.session_state.mostrar_resultados = True
                    st.rerun()
    
    elif tipo_busqueda == "🗺️ Por provincia/región":
        regiones_disponibles = sorted(df['region'].dropna().unique())
        provincia_seleccionada = st.selectbox(
            "Elige una provincia/región:",
            ["-- Selecciona una región --"] + regiones_disponibles
        )
        
        if provincia_seleccionada and provincia_seleccionada != "-- Selecciona una región --":
            if st.button("🗺️ Ver datos de la región", key="btn_region"):
                df_region = df[df['region'] == provincia_seleccionada]
                if len(df_region) > 0:
                    st.session_state.df_ciudad_actual = df_region
                    st.session_state.ciudad_actual = provincia_seleccionada
                    st.session_state.mostrar_resultados = True
                    st.rerun()
    
    elif tipo_busqueda == "📊 Comparar ciudades":
        ciudades_comparar = st.multiselect(
            "Selecciona hasta 5 ciudades para comparar:",
            st.session_state.ciudades_lista,
            max_selections=5
        )
        
        if ciudades_comparar and st.button("📊 Generar comparativa", key="btn_comparar"):
            df_comparar = df[df['ubi'].isin(ciudades_comparar)]
            if len(df_comparar) > 0:
                st.session_state.df_ciudad_actual = df_comparar
                st.session_state.ciudad_actual = "Comparativa"
                st.session_state.mostrar_resultados = True
                st.rerun()
    
    st.markdown("---")
    
    # =========================================
    # RESULTADOS DETALLADOS
    # =========================================
    if st.session_state.mostrar_resultados and st.session_state.df_ciudad_actual is not None:
        df_actual = st.session_state.df_ciudad_actual
        nombre_actual = st.session_state.ciudad_actual
        
        st.subheader(f"📊 Resultados para: {nombre_actual}")
        
        # Predicción
        st.subheader("🔮 PREDICCIÓN DEL TIEMPO")
        
        if nombre_actual != "Comparativa" and len(df_actual) == 1:
            prediccion = hacer_prediccion_ciudad(df_actual, nombre_actual)
            if prediccion:
                col_p1, col_p2, col_p3 = st.columns(3)
                with col_p1:
                    st.metric("🌡️ Temperatura actual", f"{prediccion['temp_actual']:.1f}°C")
                with col_p2:
                    st.metric("🔮 Predicción próxima", f"{prediccion['prediccion']:.1f}°C")
                with col_p3:
                    st.metric("📈 Tendencia", prediccion['tendencia'])
                st.info(f"{prediccion['icono']} **Consejo:** {prediccion['consejo']}")
        else:
            st.info(f"📊 Mostrando datos de {len(df_actual)} estaciones en {nombre_actual}")
            st.metric("🌡️ Temperatura media", f"{df_actual['temp'].mean():.1f}°C")
        
        # Mapa
        st.subheader("🗺️ Ubicación en el mapa")
        
        if nombre_actual != "Comparativa" and len(df_actual) == 1 and 'lat' in df_actual.columns:
            try:
                import folium
                from streamlit_folium import st_folium
                
                lat = float(df_actual['lat'].iloc[0])
                lon = float(df_actual['lon'].iloc[0])
                temp = df_actual['temp'].iloc[0]
                
                mapa_ciudad = folium.Map(location=[lat, lon], zoom_start=12)
                color = 'red' if temp > 30 else 'orange' if temp > 20 else 'green'
                folium.Marker([lat, lon], popup=f"{nombre_actual}: {temp}°C", icon=folium.Icon(color=color)).add_to(mapa_ciudad)
                st_folium(mapa_ciudad, width=700, height=400)
            except:
                st.warning("No se pudo cargar el mapa")
        
        # Visualización de datos
        st.subheader("📊 Visualización de datos")
        
        if 'ubi' in df_actual.columns:
            # Agrupar por nombre de estación para evitar duplicados
            df_agrupado_local = df_actual.groupby('ubi')['temp'].max().reset_index()
            df_agrupado_local = df_agrupado_local.sort_values('temp', ascending=False)
            top_local = df_agrupado_local.head(10)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            barras = ax.bar(range(len(top_local)), top_local['temp'], color='skyblue', edgecolor='navy', linewidth=1)
            ax.set_xticks(range(len(top_local)))
            ax.set_xticklabels(top_local['ubi'], rotation=45, ha='right', fontsize=9)
            ax.set_ylabel('Temperatura (°C)')
            ax.set_title(f'Temperaturas en {nombre_actual}', fontsize=14, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            
            for barra, temp in zip(barras, top_local['temp']):
                ax.text(barra.get_x() + barra.get_width()/2, barra.get_height() + 0.3,
                       f"{temp:.1f}°C", ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            st.pyplot(fig)
        
        if st.button("🗑️ Limpiar esta vista"):
            st.session_state.mostrar_resultados = False
            st.session_state.df_ciudad_actual = None
            st.rerun()
    
    # =========================================
    # TOP 10 ESTACIONES MÁS CÁLIDAS (AGRUPADO POR NOMBRE EXACTO)
    # =========================================
    st.subheader("🏆 Top 10 estaciones más cálidas de España")
    
    if 'ubi' in df.columns:
        # Agrupar por nombre de estación (evitar duplicados por múltiples mediciones)
        # Usamos max() para mostrar la temperatura más alta registrada en esa estación
        df_agrupado = df.groupby('ubi')['temp'].max().reset_index()
        df_agrupado = df_agrupado.sort_values('temp', ascending=False)
        
        # Mostrar información de cuántas estaciones únicas hay
        st.caption(f"📊 Total de estaciones únicas: {len(df_agrupado)} | Mostrando las 10 más cálidas")
        
        top10 = df_agrupado.head(10)
        
        fig, ax = plt.subplots(figsize=(14, 6))
        colores = plt.cm.RdYlGn_r(np.linspace(0, 0.7, len(top10)))
        barras = ax.bar(range(len(top10)), top10['temp'], color=colores, edgecolor='darkred', linewidth=1.5)
        
        ax.set_xticks(range(len(top10)))
        ax.set_xticklabels(top10['ubi'], rotation=45, ha='right', fontsize=10)
        ax.set_ylabel('Temperatura (°C)', fontsize=12)
        ax.set_title('Top 10 estaciones más cálidas de España', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        for barra, temp in zip(barras, top10['temp']):
            ax.text(barra.get_x() + barra.get_width()/2, barra.get_height() + 0.5,
                   f"{temp:.1f}°C", ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # =========================================
        # TOP 10 ESTACIONES MÁS FRÍAS
        # =========================================
        st.subheader("❄️ Top 10 estaciones más frías de España")
        
        df_agrupado_min = df.groupby('ubi')['temp'].min().reset_index()
        df_agrupado_min = df_agrupado_min.sort_values('temp', ascending=True)
        top10_frias = df_agrupado_min.head(10)
        
        fig2, ax2 = plt.subplots(figsize=(14, 6))
        barras2 = ax2.bar(range(len(top10_frias)), top10_frias['temp'], color='skyblue', edgecolor='navy', linewidth=1.5)
        
        ax2.set_xticks(range(len(top10_frias)))
        ax2.set_xticklabels(top10_frias['ubi'], rotation=45, ha='right', fontsize=10)
        ax2.set_ylabel('Temperatura (°C)', fontsize=12)
        ax2.set_title('Top 10 estaciones más frías de España', fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        
        for barra, temp in zip(barras2, top10_frias['temp']):
            ax2.text(barra.get_x() + barra.get_width()/2, barra.get_height() + 0.5,
                   f"{temp:.1f}°C", ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        st.pyplot(fig2)
    
    # =========================================
    # ALERTAS
    # =========================================
    st.subheader("⚠️ Sistema de Alertas Nacional")
    
    alertas = df[df['temp'] >= st.session_state.umbral_calor]
    if len(alertas) > 0:
        st.error(f"🔴 ¡ATENCIÓN! {len(alertas)} estaciones superan {st.session_state.umbral_calor}°C")
        if 'ubi' in df.columns:
            alertas_mostrar = alertas.drop_duplicates(subset=['ubi'])[['ubi', 'temp']].head(10)
            st.dataframe(alertas_mostrar, use_container_width=True)
    else:
        st.success(f"✅ Todo bajo control a nivel nacional. Máxima: {temp_max}°C")
    
    # =========================================
    # EXPORTAR
    # =========================================
    st.subheader("💾 Exportar Datos")
    fecha_hoy = datetime.now().strftime("%Y-%m-%d_%H-%M")
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar CSV", csv_data, f"clima_{fecha_hoy}.csv")

# =====================================================
# CONTROL DE FLUJO DE PANTALLAS
# =====================================================
if not st.session_state.api_key_validada:
    pantalla_inicio()
else:
    pantalla_principal()
