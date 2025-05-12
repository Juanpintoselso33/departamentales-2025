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
        print(f"Cargando datos en tiempo real desde API: {api_url}")
        response = requests.get(api_url, timeout=30) # Timeout de 30 segundos
        response.raise_for_status() # Lanza HTTPError para respuestas 4xx/5xx
        # --- DEBUG: Loguear la respuesta cruda ---
        print("DEBUG API 2025 - status code:", response.status_code)
        print("DEBUG API 2025 - headers:", response.headers)
        print("DEBUG API 2025 - raw text:", response.text[:1000])  # Mostramos solo los primeros 1000 caracteres
        try:
            data = response.json()
        except Exception as e:
            print("DEBUG API 2025 - ERROR al parsear JSON:", e)
            data = None
        # Asumiendo que la API devuelve una lista de departamentos como el JSON de 2020
        print(f"Datos crudos cargados exitosamente desde API ({len(data) if data else 0} registros).")
        return data
    except requests.exceptions.Timeout:
        st.error(f"Error al cargar datos: Timeout en API. URL: {api_url}")
        print(f"Error: Timeout en API. URL: {api_url}")
        return None
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al cargar datos desde API: {http_err}. URL: {api_url}")
        print(f"Error HTTP: {http_err}. URL: {api_url}")
        return None
    except requests.exceptions.RequestException as req_err:
        st.error(f"Error de conexión/red al cargar datos desde API: {req_err}. URL: {api_url}")
        print(f"Error de conexión/red: {req_err}. URL: {api_url}")
        return None
    except requests.exceptions.JSONDecodeError:
        st.error(f"Error al cargar datos: Respuesta API no es JSON válido. URL: {api_url}")
        print(f"Error: Respuesta API no es JSON válido. URL: {api_url}")
        return None
    except Exception as e:
        st.error(f"Error inesperado al cargar datos desde API: {e}. URL: {api_url}")
        print(f"Error inesperado: {e}. URL: {api_url}")
        return None 