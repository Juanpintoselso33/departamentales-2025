"""
Sistema de caché para evitar recargar y reprocesar datos electorales.
Proporciona funciones para cargar datos con caché.
"""

from functools import lru_cache
from typing import Union, Dict, Any, Tuple
from pathlib import Path

from domain.enrichers import ElectionSummaryEnriquecido

# Tamaño máximo de caché (ajustable según necesidades)
_CACHE_SIZE = 4

@lru_cache(maxsize=_CACHE_SIZE)
def get_summary(path: Union[str, Path]) -> Tuple[ElectionSummaryEnriquecido, Dict[str, Any]]:
    """
    Carga, mapea, normaliza y enriquece datos electorales, cacheando el resultado.
    
    Args:
        path: Ruta al archivo JSON
        
    Returns:
        Tuple con:
        - ElectionSummaryEnriquecido: Modelo canónico enriquecido
        - Dict: Estadísticas nacionales agregadas
    """
    from domain.pipeline import build_dataset
    
    # Utilizar el pipeline completo para procesar los datos
    return build_dataset(path)


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