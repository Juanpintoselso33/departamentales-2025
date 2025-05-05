"""
Pipeline principal para procesamiento de datos electorales.
Coordina la carga, limpieza y enriquecimiento de los datos.
"""

from pathlib import Path
from typing import Union, Dict, Any, Tuple

from domain.models import ElectionSummary
from domain.transformers.cleaning import clean
from domain.enrichers.enrich import enrich
from domain.enrichers.aggregate import aggregate
from domain.enrichers import ElectionSummaryEnriquecido

# Importar directamente el detector real en lugar de mantener un stub
from infrastructure.loaders import detect_load

def build_dataset(path: Union[str, Path]) -> Tuple[ElectionSummaryEnriquecido, Dict[str, Any]]:
    """
    Construye un conjunto de datos electoral completo y validado.
    
    Args:
        path: Ruta al archivo de datos electorales
        
    Returns:
        Tuple con:
        - ElectionSummaryEnriquecido: Modelo canónico enriquecido con ganadores y ediles
        - Dict: Estadísticas nacionales agregadas
    """
    # Paso 1: Cargar datos según el formato específico (detect_load)
    raw_summary = detect_load(path)
    
    # Paso 2: Limpieza y normalización (clean)
    normalized_summary = clean(raw_summary)
    
    # Paso 3: Enriquecimiento con ganadores y distribución de ediles (enrich)
    enriched_summary = enrich(normalized_summary)
    
    # Paso 3+: Agregación de métricas nacionales (aggregate)
    stats = aggregate(enriched_summary)
    
    return enriched_summary, stats 