"""
Traduce el JSON oficial de 2020 (estructura Corte Electoral)
al modelo canónico definido en domain.models.

El archivo original es un array de departamentos.
"""

from __future__ import annotations
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Set, Callable

from pydantic import ValidationError
from domain.models import Departamento, ElectionSummary

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG") == "1" else logging.INFO,
    format="%(levelname)s | %(message)s"
)
log = logging.getLogger("loader2020")

# ---------- tablas de renombre de claves ---------- #
# (solo las que difieren; las demás se copian tal cual)

_RENAME_MUNI = {
    "VB": "TA",
    "VA": "TO",
    "TOT": "TH",
}

_RENAME_DEPTO = {
    "VB": "TA",
    "VA": "TO",
    "TOT": "TH",
}

# ---------- claves permitidas en el modelo canónico ---------- #
_ALLOWED_MUNI = {
    "MI", "MD", "CE", "CT", "CP", "CFCO", "TEB", "TEBP", "TA", "TO", "TNO",
    "TE", "TH", "TOR", "CCO", "Eleccion"
}

_ALLOWED_DEPTO = {
    "DI", "DN", "CE", "CT", "CP", "CFCO", "TEB", "TEBP", "TA", "TO", "TNO",
    "TE", "TH", "TOR", "CCO", "Municipales", "Departamentales"
}

def _rename_keys(obj: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
    """Devuelve un dict nuevo con las claves renombradas según 'mapping'."""
    return {mapping.get(k, k): v for k, v in obj.items()}

def _safe_get(obj: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Obtiene un valor de un diccionario de forma segura."""
    return obj.get(key, default)

def _filter(obj: Dict[str, Any], allowed_keys: Set[str]) -> Dict[str, Any]:
    """Filtra un diccionario para que solo contenga las claves permitidas."""
    return {k: v for k, v in obj.items() if k in allowed_keys}

def _map_municipio(m: Dict[str, Any]) -> Dict[str, Any]:
    """Traduce un municipio del formato oficial al canónico."""
    base = _rename_keys(m, _RENAME_MUNI)
    base["Eleccion"] = _safe_get(m, "Eleccion", [])
    # Filtrar al final
    return _filter(base, _ALLOWED_MUNI)

def _map_partido_depto(p: Dict[str, Any]) -> Dict[str, Any]:
    """Traduce un partido del formato oficial al canónico."""
    return p

def _map_departamento(d: Dict[str, Any]) -> Dict[str, Any]:
    """Traduce un departamento del formato oficial al canónico."""
    base = _rename_keys(d, _RENAME_DEPTO)
    base["Municipales"] = [_map_municipio(m) for m in _safe_get(d, "Municipales", [])]
    base["Departamentales"] = [_map_partido_depto(p) for p in _safe_get(d, "Departamentales", [])]
    # Filtrar al final, después de agregar todas las claves necesarias
    base = _filter(base, _ALLOWED_DEPTO)
    return base

def load(path: str) -> ElectionSummary:
    """
    Carga y traduce el JSON de 2020 al modelo canónico.
    
    Args:
        path: Ruta al archivo JSON
        
    Returns:
        ElectionSummary: Modelo canónico con los datos cargados
    """
    try:
        log.info(f"Cargando datos de elecciones 2020 desde: {path}")
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        
        departamentos = []
        log.info(f"Total de departamentos encontrados en el JSON: {len(data)}")
        
        # Procesar cada departamento del JSON
        for idx, depto_data in enumerate(data):
            try:
                # Obtener el nombre del departamento para logging
                depto_nombre = depto_data.get("DN", f"índice {idx}")
                log.info(f"Procesando departamento: {depto_nombre}")
                
                # Mapear y filtrar el departamento
                mapped_depto = _map_departamento(depto_data)
                
                # Crear el departamento a partir de los datos mapeados
                depto = Departamento(**mapped_depto)
                
                departamentos.append(depto)
                log.info(f"✅ Departamento {depto_nombre} procesado correctamente")
                
            except Exception as e:
                log.error(f"Error procesando departamento {depto_data.get('DN', idx)}: {e}")
                if os.getenv("DEBUG") == "1":
                    import traceback
                    log.debug(traceback.format_exc())
        
        log.info(f"Carga completada: {len(departamentos)} departamentos procesados")
        if len(departamentos) == 0:
            log.warning("No se pudo cargar ningún departamento correctamente")
        elif len(departamentos) < len(data):
            log.warning(f"Solo se cargaron {len(departamentos)} de {len(data)} departamentos")
            
        # Crear el ElectionSummary con los departamentos procesados
        return ElectionSummary(year=2020, departamentos=departamentos)
        
    except Exception as e:
        log.error(f"Error general al cargar el archivo {path}: {str(e)}")
        if os.getenv("DEBUG") == "1":
            import traceback
            log.debug(traceback.format_exc())
        # Devolver un ElectionSummary vacío
        return ElectionSummary(year=2020, departamentos=[]) 