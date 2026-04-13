# utils/data_processor.py
"""
Módulo para procesamiento de datos climáticos
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def procesar_datos_clima(datos_clima):
    """
    Convierte los datos crudos de AEMET en un DataFrame limpio
    """
    df = pd.DataFrame(datos_clima)
    
    # Buscar columna de temperatura (AEMET usa 'ta')
    if 'ta' in df.columns:
        df['temp'] = pd.to_numeric(df['ta'], errors='coerce')
    elif 'temp' in df.columns:
        df['temp'] = pd.to_numeric(df['temp'], errors='coerce')
    else:
        return None
    
    # Limpiar datos nulos
    df = df.dropna(subset=['temp'])
    
    # Convertir coordenadas a numéricas si existen
    for col in ['lat', 'lon']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def calcular_estadisticas(df):
    """
    Calcula estadísticas básicas de temperatura
    Retorna: dict con métricas
    """
    if df is None or len(df) == 0:
        return None
    
    stats = {
        'temp_max': df['temp'].max(),
        'temp_min': df['temp'].min(),
        'temp_media': df['temp'].mean(),
        'total_estaciones': len(df)
    }
    
    # Buscar nombres de ciudades si existen
    col_ubi = None
    for col in ['ubi', 'nombre', 'municipio']:
        if col in df.columns:
            col_ubi = col
            break
    
    if col_ubi:
        stats['ciudad_max'] = df[df['temp'] == stats['temp_max']][col_ubi].values[0]
        stats['ciudad_min'] = df[df['temp'] == stats['temp_min']][col_ubi].values[0]
    else:
        stats['ciudad_max'] = "Desconocida"
        stats['ciudad_min'] = "Desconocida"
    
    return stats


def obtener_alerta_ciudades(df, umbral):
    """
    Encuentra ciudades que superan el umbral de temperatura
    """
    if df is None or 'temp' not in df.columns:
        return []
    
    col_ubi = 'ubi' if 'ubi' in df.columns else None
    
    if col_ubi:
        alertas = df[df['temp'] >= umbral].drop_duplicates(subset=[col_ubi])
        return alertas[[col_ubi, 'temp']].to_dict('records')
    
    return []


def hacer_prediccion(df):
    """
    Realiza una predicción simple usando regresión lineal
    Retorna: dict con tendencia y predicción
    """
    if df is None or len(df) < 5:
        return None
    
    # Ordenar por temperatura
    df_ordenado = df.sort_values('temp').reset_index(drop=True)
    
    # Tomar los primeros 10 registros para la tendencia
    n_puntos = min(10, len(df_ordenado))
    X = np.array(range(n_puntos)).reshape(-1, 1)
    y = df_ordenado['temp'].head(n_puntos).values
    
    modelo = LinearRegression()
    modelo.fit(X, y)
    
    pendiente = modelo.coef_[0]
    siguiente = modelo.predict([[n_puntos]])[0]
    
    # Determinar consejo según la tendencia
    if pendiente > 0.5:
        consejo = "🔥 ¡Las temperaturas altas dominan! Cuídate del calor."
    elif pendiente > 0:
        consejo = "☀️ Clima cálido pero controlado. Disfruta el día."
    elif pendiente < -0.5:
        consejo = "🧊 ¡Predominan temperaturas frías! Abrígate bien."
    else:
        consejo = "☁️ Clima variado. Temperaturas repartidas."
    
    return {
        'tendencia': pendiente,
        'prediccion': max(0, siguiente),
        'consejo': consejo,
        'puntos_usados': n_puntos
    }
