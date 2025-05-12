"""
Pipeline principal para procesamiento de datos electorales.
Coordina la carga, limpieza y enriquecimiento de los datos.

METODOLOGÍA OFICIAL DE CÁLCULO DE VOTOS VÁLIDOS:
-------------------------------------------------------------------------------
Según la metodología de la Corte Electoral de Uruguay:

1. Votos válidos: Son exclusivamente la suma de votos asignados a partidos.
   - Se calculan como la suma de los valores 'Tot' de cada partido en 'Departamentales'.
   - NO se incluyen votos en blanco, anulados u observados en el cálculo.

2. Porcentajes: Se calculan dividiendo los votos de cada partido por el total de votos válidos.
   - Esto asegura que la suma de porcentajes siempre dé 100%.

3. Advertencias sobre datos preliminares:
   - Se muestra una advertencia explícita cuando el porcentaje escrutado es menor al 10%.
   - Esto evita confusiones con resultados muy preliminares.

4. Campos involucrados en los datos crudos:
   - TO: Votos anulados
   - TNO: Votos no observados
   - TE: Sobres en urna
   - TH: Votos válidos totales del departamento
-------------------------------------------------------------------------------
"""

from pathlib import Path
from typing import Union, Dict, Any, Tuple, Optional, List

from domain.models import ElectionSummary
from domain.transformers.cleaning import clean
from domain.enrichers.enrich import enrich, aggregate, ElectionSummaryEnriquecido

# Importar directamente el detector real en lugar de mantener un stub
from infrastructure.loaders import detect_load

def build_dataset(path: Optional[Union[str, Path]] = None, raw_data: Optional[List[Dict[str, Any]]] = None) -> Tuple[ElectionSummaryEnriquecido, Dict[str, Any]]:
    """
    Construye un conjunto de datos electoral completo y validado.
    Puede recibir la ruta a un archivo o los datos crudos pre-cargados.
    
    Args:
        path (Optional[Union[str, Path]]): Ruta al archivo de datos electorales. Requerido si raw_data no se proporciona.
        raw_data (Optional[List[Dict[str, Any]]]): Lista de diccionarios con los datos crudos. Requerido si path no se proporciona.
        
    Returns:
        Tuple con:
        - ElectionSummaryEnriquecido: Modelo canónico enriquecido con ganadores y ediles
        - Dict: Estadísticas nacionales agregadas
        
    Raises:
        ValueError: Si no se proporciona ni path ni raw_data, o si se proporcionan ambos.
    """
    
    # Validar argumentos
    if raw_data is not None and path is not None:
        raise ValueError("Proporcione 'path' o 'raw_data', pero no ambos.")
    if raw_data is None and path is None:
        raise ValueError("Debe proporcionar 'path' o 'raw_data'.")

    # Paso 1: Obtener datos crudos (desde archivo o argumento)
    loaded_raw_data = None # Renombrar para claridad
    if raw_data is not None:
        print("Pipeline: Usando datos crudos proporcionados.")
        # Asumimos que los datos crudos ya están en el formato base esperado (lista de dicts)
        loaded_raw_data = raw_data # Usar los datos directamente
    elif path is not None:
        print(f"Pipeline: Cargando datos desde path: {path}")
        # Cargar datos según el formato específico usando detect_load
        loaded_raw_data = detect_load(path)
    else:
        # Este caso está cubierto por la validación inicial, pero por seguridad:
        raise ValueError("Error lógico: No hay fuente de datos definida.")
    
    # Verificar si la carga falló
    if not loaded_raw_data:
         print("Error: La carga de datos inicial resultó en datos vacíos o nulos.")
         raise ValueError("Fallo al obtener los datos crudos iniciales.")

    # Crear instancia de ElectionSummary ANTES de pasar a clean
    # Asumiendo que ElectionSummary tiene un campo 'departamentos' que acepta List[Dict]
    try:
        # Si loaded_raw_data es el objeto que devolvía detect_load (con .departamentos)
        if hasattr(loaded_raw_data, 'departamentos'):
             print("Pipeline: Datos cargados desde archivo, usando atributo 'departamentos'.")
             summary_obj = ElectionSummary(departamentos=loaded_raw_data.departamentos)
        # Si loaded_raw_data es la lista directa de la API
        elif isinstance(loaded_raw_data, list):
             print("Pipeline: Datos cargados desde API (lista), creando ElectionSummary.")
             summary_obj = ElectionSummary(departamentos=loaded_raw_data)
        else:
             # Manejar caso inesperado
             raise TypeError(f"Tipo de datos cargados inesperado: {type(loaded_raw_data)}")
             
    except Exception as e:
        # Capturar errores durante la instanciación de ElectionSummary (p.ej. validación Pydantic inicial)
        print(f"Error al crear instancia de ElectionSummary con los datos cargados: {e}")
        raise ValueError(f"Los datos cargados no son válidos para el modelo ElectionSummary: {e}")

    # Paso 2: Limpieza y normalización (clean)
    print("Pipeline: Ejecutando limpieza...")
    # Ahora pasamos el objeto ElectionSummary a clean
    normalized_summary = clean(summary_obj)
    
    # Paso 3: Enriquecimiento con ganadores y distribución de ediles (enrich)
    print("Pipeline: Ejecutando enriquecimiento...")
    enriched_summary = enrich(normalized_summary)
    
    # Paso 3+: Agregación de métricas nacionales (aggregate)
    print("Pipeline: Ejecutando agregación...")
    stats = aggregate(enriched_summary)
    
    print("Pipeline: Procesamiento completado.")
    return enriched_summary, stats 