import streamlit as st
import requests
import datetime
from typing import Dict, Any, Optional, List

# Eliminar el decorador de caché para que siempre se haga la solicitud a la API
# @st.cache_data(ttl=600)
def load_election_data_from_api(api_url: str) -> Optional[List[Dict[str, Any]]]:
    """
    Carga los datos electorales crudos desde la API especificada, SIN UTILIZAR CACHÉ.
    Esta función siempre hará una nueva solicitud para obtener datos actualizados.

    Args:
        api_url (str): La URL completa de la API REST que devuelve el JSON.

    Returns:
        Lista de diccionarios con los datos crudos o None si hay error.
    """
    try:
        response = requests.get(api_url, timeout=30) # Timeout de 30 segundos
        response.raise_for_status() # Lanza HTTPError para respuestas 4xx/5xx
        try:
            data = response.json()
            if data:
                return data
            return None
        except Exception:
            return None
    except Exception:
        return None # Silenciosamente retornar None en caso de cualquier error 