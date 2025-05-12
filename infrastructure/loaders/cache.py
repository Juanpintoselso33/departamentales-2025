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
    cacheando el resultado usando LRU cache EXCEPTO para datos de API 2025.
    
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
    
    # MODIFICACIÓN: Forzar una nueva ejecución del lru_cache para API 2025
    # Esto hará que siempre se obtengan datos frescos
    if source_type == 'api' and '2025' in str(source_location):
        # Invalidar el lru_cache para siempre obtener datos frescos de 2025
        get_summary.cache_clear()
        print(f"Cache invalidado para API 2025: {source_location}")
    
    raw_data: Optional[List[Dict[str, Any]]] = None
    
    if source_type == 'api':
        print(f"Cargando datos en tiempo real para API: {source_location}")
        # Carga desde API (ya no usa su propia caché st.cache_data)
        raw_data = load_election_data_from_api(str(source_location))
        if raw_data:
            # --- GUARDAR BACKUP LOCAL SI ES 2025 ---
            import json
            import os
            from datetime import datetime
            # Detectar si es 2025 por la URL o por la variable
            if '2025' in str(source_location):
                backup_path = Path(__file__).parent.parent.parent / 'data' / 'election_data' / '2025' / 'results_2025.json'
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        json.dump(raw_data, f, ensure_ascii=False, indent=2)
                    print(f"Backup de datos 2025 guardado en {backup_path}")
                except Exception as e:
                    print(f"Error al guardar backup local de datos 2025: {e}")
        else:
            print(f"Fallo al cargar datos desde API: {source_location}")
            # --- FALLBACK: Intentar cargar desde backup local si es 2025 ---
            if '2025' in str(source_location):
                backup_path = Path(__file__).parent.parent.parent / 'data' / 'election_data' / '2025' / 'results_2025.json'
                if backup_path.exists():
                    print(f"Cargando datos de backup local: {backup_path}")
                    import json
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        raw_data = json.load(f)
                else:
                    print(f"No se encontró backup local de datos 2025 en {backup_path}")
                    return None
            
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
def get_streamlit_cached_summary(source_type: str, source_location: Union[str, Path]) -> Optional[Tuple[ElectionSummaryEnriquecido, Dict[str, Any]]]:
    """
    Versión específica para Streamlit que utiliza st.cache_data, excepto para datos de API 2025
    que siempre se cargan frescos sin usar caché.
    
    Args:
        source_type (str): Tipo de fuente ('json' o 'api')
        source_location (Union[str, Path]): Ruta al archivo JSON o URL de la API
        
    Returns:
        Tuple con summary enriquecido y estadísticas, o None si hay error
    """
    try:
        import streamlit as st
        
        # CORREGIR: Modificando para evitar caché en datos 2025
        # Si es la API 2025, no usar caché
        if source_type == 'api' and (isinstance(source_location, str) and '2025' in str(source_location)):
            # Cargar directamente sin caché
            print("Cargando datos 2025 sin caché de Streamlit")
            from domain.pipeline import build_dataset
            # Llamar a la función sin caché del api_loader
            from .api_loader import load_election_data_from_api
            raw_data = load_election_data_from_api(str(source_location))
            if raw_data:
                return build_dataset(raw_data=raw_data)
            else:
                return None
                
        # Para el resto, usar caché normal
        @st.cache_data(ttl=5*60)  # 5 minutos de TTL
        def _cached_load(source_t, source_loc):
            from domain.pipeline import build_dataset
            if source_t == 'json':
                return build_dataset(path=source_loc)
            elif source_t == 'api':
                from .api_loader import load_election_data_from_api
                raw_data = load_election_data_from_api(str(source_loc))
                if raw_data:
                    return build_dataset(raw_data=raw_data)
                return None
            
        return _cached_load(source_type, source_location)
        
    except ImportError:
        # Si Streamlit no está disponible, usar la versión con lru_cache
        return get_summary(source_type, source_location)
    except Exception as e:
        # Capturar otros errores
        print(f"Error en get_streamlit_cached_summary: {e}")
        return None 