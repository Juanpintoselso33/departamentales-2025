"""
Sistema de caché para evitar recargar y reprocesar datos electorales.
Proporciona funciones para cargar datos con caché.
"""

from functools import lru_cache
from typing import Union, Dict, Any, Tuple, Optional, List
from pathlib import Path

# Importar el nuevo cargador de API
from .api_loader import load_election_data_from_api

from domain.enrichers import ElectionSummaryEnriquecido

# Tamaño máximo de caché (ajustable según necesidades)
_CACHE_SIZE = 8 # Aumentar caché para soportar múltiples fuentes

@lru_cache(maxsize=_CACHE_SIZE)
def get_summary(source_type: str, source_location: Union[str, Path]) -> Optional[Tuple[ElectionSummaryEnriquecido, Dict[str, Any]]]:
    """
    Carga (desde archivo o API), mapea, normaliza y enriquece datos electorales,
    cacheando el resultado usando LRU cache.
    
    Args:
        source_type (str): Tipo de fuente ('json' o 'api').
        source_location (Union[str, Path]): Ruta al archivo JSON o URL de la API.
        
    Returns:
        Tuple con:
        - ElectionSummaryEnriquecido: Modelo canónico enriquecido.
        - Dict: Estadísticas nacionales agregadas.
        O None si la carga o procesamiento fallan.
    """
    from domain.pipeline import build_dataset # Asumiendo que build_dataset puede manejar datos crudos o path
    
    raw_data: Optional[List[Dict[str, Any]]] = None
    
    if source_type == 'api':
        print(f"Cache miss o TTL expirado para API: {source_location}. Llamando a api_loader.")
        # Carga desde API (usará su propia caché st.cache_data con TTL)
        raw_data = load_election_data_from_api(str(source_location))
        if not raw_data:
            print(f"Fallo al cargar datos desde API: {source_location}")
            return None # Error ya mostrado por api_loader
            
    elif source_type == 'json':
        print(f"Cache miss para JSON: {source_location}. Procediendo a cargar y procesar.")
        # Para JSON, pasamos la ruta directamente al pipeline existente
        # build_dataset maneja la carga del archivo JSON internamente.
        # Si build_dataset NECESITARA los datos crudos, aquí haríamos:
        # raw_data = _load_json_data(source_location) # Una función interna para cargar JSON
        pass # No es necesario cargar aquí si build_dataset lo hace
    
    else:
        print(f"Error: Tipo de fuente no soportado '{source_type}'")
        # Considerar lanzar un error o devolver None
        raise ValueError(f"Tipo de fuente no soportado: {source_type}")

    # --- Procesamiento con pipeline --- 
    # Asumiendo que build_dataset puede aceptar datos crudos (lista de dicts) o una ruta
    # Se necesita verificar/adaptar build_dataset si solo acepta rutas.
    # Por ahora, intentamos pasar la fuente original si es JSON, o los datos crudos si es API.
    try:
        if source_type == 'api' and raw_data is not None:
            # ASUNCIÓN: build_dataset puede recibir datos crudos
            print("Ejecutando pipeline con datos crudos de API...")
            result = build_dataset(raw_data=raw_data) 
        elif source_type == 'json':
            # build_dataset maneja la ruta directamente
            print(f"Ejecutando pipeline con ruta JSON: {source_location}...")
            result = build_dataset(path=source_location)
        else:
             # Este caso no debería ocurrir si raw_data es None tras fallo API
             print("Error inesperado: No hay datos para procesar.")
             return None
             
        print("Pipeline completado exitosamente.")
        return result
        
    except Exception as e:
        # Capturar errores durante la ejecución del pipeline
        print(f"Error durante la ejecución del pipeline para {source_location}: {e}")
        # Podrías querer usar st.error() aquí si Streamlit está disponible, 
        # pero es mejor manejar errores específicos dentro del pipeline si es posible.
        # import streamlit as st # Evitar importar st aquí si no es necesario
        # st.error(f"Error al procesar los datos: {e}")
        return None

# --- La versión de Streamlit se mantiene igual por ahora --- 
# (Podría adaptarse de forma similar si se usa en otro lugar)
# Versión específica para Streamlit
def get_streamlit_cached_summary(path: Union[str, Path]) -> Tuple[ElectionSummaryEnriquecido, Dict[str, Any]]:
    """
    Versión específica para Streamlit que utiliza st.cache_data.
    Requiere que Streamlit esté instalado.
    
    Args:
        path: Ruta al archivo JSON
        
    Returns:
        Tuple con summary enriquecido y estadísticas
    """
    try:
        import streamlit as st
        
        # NOTA: Esta caché no distingue fuente API/JSON y usa TTL fijo
        @st.cache_data(ttl=5*60)  # 5 minutos de TTL
        def _cached_load(p):
            from domain.pipeline import build_dataset
            # Esta versión sigue asumiendo que build_dataset toma solo path
            # Necesitaría adaptación similar a get_summary si se usa con API
            return build_dataset(p) 
            
        return _cached_load(path)
        
    except ImportError:
        # Si Streamlit no está disponible, usar la versión con lru_cache
        # ¡OJO! get_summary ahora necesita source_type y source_location
        # Esta llamada fallará. Se debería decidir qué hacer aquí.
        # Opción 1: Asumir JSON si Streamlit no está
        # return get_summary(source_type='json', source_location=path)
        # Opción 2: Lanzar error
        raise RuntimeError("Streamlit no está instalado y get_streamlit_cached_summary fue llamado.")
    except Exception as e:
        # Capturar otros errores
        print(f"Error en get_streamlit_cached_summary: {e}")
        # Podría devolver None o relanzar
        return None # Ser consistente con get_summary

# Versión específica para Streamlit
def get_streamlit_cached_summary(path: Union[str, Path]) -> Tuple[ElectionSummaryEnriquecido, Dict[str, Any]]:
    """
    Versión específica para Streamlit que utiliza st.cache_data.
    Requiere que Streamlit esté instalado.
    
    Args:
        path: Ruta al archivo JSON
        
    Returns:
        Tuple con summary enriquecido y estadísticas
    """
    try:
        import streamlit as st
        
        @st.cache_data(ttl=5*60)  # 5 minutos de TTL
        def _cached_load(p):
            from domain.pipeline import build_dataset
            return build_dataset(p)
            
        return _cached_load(path)
        
    except ImportError:
        # Si Streamlit no está disponible, usar la versión con lru_cache
        return get_summary(path) 