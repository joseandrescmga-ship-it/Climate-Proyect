# utils/maps.py
"""
Módulo para crear mapas interactivos con Folium
"""

import folium
from folium import plugins
import streamlit as st
from streamlit_folium import st_folium

def crear_mapa_estaciones(df, titulo="🗺️ Mapa de Temperaturas"):
    """
    Crea un mapa interactivo con marcadores de temperatura
    Retorna el objeto mapa de Folium
    """
    if df is None or len(df) == 0:
        return None
    
    # Buscar columnas de coordenadas y nombre
    tiene_coords = 'lat' in df.columns and 'lon' in df.columns
    col_ubi = 'ubi' if 'ubi' in df.columns else None
    
    if not tiene_coords:
        st.warning("No hay coordenadas disponibles para el mapa")
        return None
    
    # Centrar el mapa en España
    mapa = folium.Map(
        location=[40.4168, -3.7038],
        zoom_start=6,
        control_scale=True
    )
    
    # Añadir capa de mosaico
    folium.TileLayer('openstreetmap').add_to(mapa)
    
    # Añadir control de capas
    folium.LayerControl().add_to(mapa)
    
    # Contadores para leyenda
    conteo_colores = {'red': 0, 'orange': 0, 'green': 0, 'blue': 0, 'purple': 0}
    
    # Añadir marcadores para cada estación
    for idx, fila in df.iterrows():
        try:
            lat = float(fila['lat'])
            lon = float(fila['lon'])
            temp = fila['temp']
            nombre = fila.get(col_ubi, f"Estación {idx}") if col_ubi else f"Estación {idx}"
            
            # Determinar color según temperatura
            if temp > 30:
                color = 'red'
                icono = 'fire'
            elif temp > 20:
                color = 'orange'
                icono = 'sun'
            elif temp > 10:
                color = 'green'
                icono = 'cloud-sun'
            elif temp > 0:
                color = 'blue'
                icono = 'cloud'
            else:
                color = 'purple'
                icono = 'snowflake'
            
            conteo_colores[color] = conteo_colores.get(color, 0) + 1
            
            # Crear popup con información detallada
            popup_html = f"""
            <div style="font-family: Arial; min-width: 150px;">
                <b>📍 {nombre}</b><br>
                🌡️ <b>Temperatura:</b> {temp}°C<br>
                📅 Hora: {fila.get('fint', 'N/A')[:16]}<br>
                💧 Humedad: {fila.get('hr', 'N/A')}%
            </div>
            """
            
            # Crear marcador circular (más limpio que el marcador tradicional)
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=folium.Popup(popup_html, max_width=300),
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                weight=2
            ).add_to(mapa)
            
        except (ValueError, TypeError) as e:
            # Saltar coordenadas inválidas
            continue
    
    # Añadir leyenda personalizada
    legend_html = f'''
    <div style="position: fixed; bottom: 50px; right: 50px; z-index: 1000; background-color: white; padding: 10px; border-radius: 8px; border: 2px solid gray; font-family: Arial; font-size: 12px;">
        <b>🌡️ Temperatura</b><br>
        <span style="color:red;">●</span> > 30°C (Muy caliente)<br>
        <span style="color:orange;">●</span> 20-30°C (Cálido)<br>
        <span style="color:green;">●</span> 10-20°C (Templado)<br>
        <span style="color:blue;">●</span> 0-10°C (Fresco)<br>
        <span style="color:purple;">●</span> < 0°C (Helado)
    </div>
    '''
    
    mapa.get_root().html.add_child(folium.Element(legend_html))
    
    return mapa


def mostrar_mapa_interactivo(df, key_sufijo=""):
    """
    Muestra un mapa interactivo y captura eventos de clic
    Retorna: dict con información del clic o None
    """
    mapa = crear_mapa_estaciones(df)
    
    if mapa is None:
        return None
    
    # Mostrar el mapa y capturar interacción
    mapa_datos = st_folium(
        mapa,
        width=800,
        height=500,
        key=f"mapa_{key_sufijo}"
    )
    
    return mapa_datos


def mostrar_resumen_mapa(df):
    """
    Muestra estadísticas resumidas del mapa
    """
    if df is None:
        return
    
    # Contar estaciones con coordenadas válidas
    tiene_coords = df['lat'].notna() & df['lon'].notna()
    total_con_coords = tiene_coords.sum()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🗺️ Estaciones en mapa", total_con_coords)
    
    with col2:
        # Temperatura media en el mapa
        temp_media = df[tiene_coords]['temp'].mean() if total_con_coords > 0 else 0
        st.metric("🌡️ Temp. media", f"{temp_media:.1f}°C")
    
    with col3:
        # Rango de temperaturas
        temp_max = df['temp'].max()
        temp_min = df['temp'].min()
        st.metric("📊 Rango térmico", f"{temp_min}°C → {temp_max}°C")
