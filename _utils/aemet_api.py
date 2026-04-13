# utils/aemet_api.py
"""
Módulo para la conexión con la API de AEMET
Siguiendo el principio de responsabilidad única (SRP)
"""

import requests
import streamlit as st

def validar_api_key(api_key):
    """
    Verifica si la API Key es correcta
    Retorna: (bool, str) - (es_valida, mensaje)
    """
    url = "https://opendata.aemet.es/opendata/api/observacion/convencional/todas"
    headers = {'api_key': api_key}
    
    try:
        respuesta = requests.get(url, headers=headers, timeout=10)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            if datos.get('estado') == 200:
                return True, "API Key válida"
            else:
                return False, f"Error de AEMET: {datos.get('descripcion', 'Desconocido')}"
        elif respuesta.status_code == 401:
            return False, "API Key incorrecta o no autorizada"
        else:
            return False, f"Error de conexión (código: {respuesta.status_code})"
    except requests.exceptions.Timeout:
        return False, "Tiempo de espera agotado"
    except requests.exceptions.RequestException as e:
        return False, f"Error de red: {str(e)[:50]}"


def obtener_datos_clima(api_key):
    """
    Descarga los datos climáticos actuales de AEMET
    Retorna: list o None
    """
    url_base = "https://opendata.aemet.es/opendata/api/observacion/convencional/todas"
    headers = {'api_key': api_key}
    
    try:
        respuesta = requests.get(url_base, headers=headers, timeout=15)
        
        if respuesta.status_code != 200:
            return None
        
        datos = respuesta.json()
        
        if datos.get('estado') != 200:
            return None
        
        url_datos = datos['datos']
        respuesta_final = requests.get(url_datos, timeout=15)
        
        return respuesta_final.json()
    
    except Exception as e:
        st.error(f"Error obteniendo datos: {e}")
        return None


def obtener_estaciones(api_key):
    """
    Obtiene el inventario de estaciones con coordenadas
    Retorna: DataFrame o None
    """
    url_estaciones = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"
    headers = {'api_key': api_key}
    
    try:
        respuesta = requests.get(url_estaciones, headers=headers, timeout=15)
        
        if respuesta.status_code != 200:
            return None
        
        datos = respuesta.json()
        
        if datos.get('estado') != 200:
            return None
        
        url_datos = datos['datos']
        respuesta_final = requests.get(url_datos, timeout=15)
        
        import pandas as pd
        df = pd.DataFrame(respuesta_final.json())
        
        return df
    
    except Exception as e:
        st.error(f"Error obteniendo estaciones: {e}")
        return None
