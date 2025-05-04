"""
Transformador de datos geográficos.
Prepara los datos geográficos para su uso en la aplicación.
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import streamlit as st

from settings.settings import DEPARTMENT_NAME_MAPPING
from domain.transformers.text_normalizer import normalize_department_name as normalize_name
from domain.transformers.text_normalizer import normalize_for_comparison, find_matching_name

def transform_department_geodata(gdf: gpd.GeoDataFrame, election_data: Dict[str, Any]) -> gpd.GeoDataFrame:
    """
    Transforma un GeoDataFrame de departamentos incorporando datos electorales.
    
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame original con geometrías de departamentos
        election_data (Dict[str, Any]): Datos electorales procesados
        
    Returns:
        gpd.GeoDataFrame: GeoDataFrame transformado con datos electorales
    """
    if gdf is None or gdf.empty:
        return None
    
    # Crear copia para no modificar el original
    transformed_gdf = gdf.copy()
    
    # Determinar qué columna contiene los nombres de departamentos
    name_column = _identify_department_name_column(transformed_gdf)
    
    # Si no se encontró una columna de nombres, retornar el original
    if name_column is None:
        return transformed_gdf
    
    # Normalizar nombres de departamentos según el mapeo
    transformed_gdf[name_column] = transformed_gdf[name_column].apply(normalize_name)
    
    # Depurar nombres para ver qué pasa - estos son los nombres ya normalizados del shapefile
    shapefile_departments = set(transformed_gdf[name_column].tolist())
    
    # Nombres en los datos electorales
    election_data_departments = set(election_data.keys())
    
    # Registrar nombres para depuración (sin mostrar mensaje)
    departments_not_found = election_data_departments - shapefile_departments
    
    # Incorporar datos electorales en las filas correspondientes
    match_count = 0
    for dept_name, dept_data in election_data.items():
        # Buscar coincidencias exactas
        mask = transformed_gdf[name_column] == dept_name
        
        # Si no hay coincidencias exactas, intentar con normalización
        if not mask.any():
            # Crear una lista de nombres de departamentos en el GeoDataFrame
            shapefile_names = transformed_gdf[name_column].tolist()
            
            # Buscar un nombre que coincida tras normalización
            matching_name = find_matching_name(dept_name, shapefile_names)
            
            if matching_name:
                mask = transformed_gdf[name_column] == matching_name
        
        if mask.any():
            match_count += 1
            # Añadir información electoral
            transformed_gdf.loc[mask, 'winning_party'] = dept_data.get('winning_party', 'No disponible')
            
            # Obtener el porcentaje del partido ganador
            vote_percentages = dept_data.get('vote_percentages', {})
            if vote_percentages and dept_data.get('winning_party') in vote_percentages:
                transformed_gdf.loc[mask, 'vote_percentage'] = vote_percentages[dept_data['winning_party']]
            else:
                transformed_gdf.loc[mask, 'vote_percentage'] = 0
    
    # Guardar el nombre de la columna para uso en visualización
    transformed_gdf.attrs['name_column'] = name_column
    
    # Asegurar que todos los valores sean serializables a JSON
    transformed_gdf = _ensure_json_serializable(transformed_gdf)
    
    return transformed_gdf

# Conservar la función por compatibilidad, pero delegando a la implementación centralizada
def normalize_department_name(name: str) -> str:
    """
    Función wrapper que delega a la implementación centralizada.
    
    Args:
        name (str): Nombre del departamento a normalizar
        
    Returns:
        str: Nombre normalizado usando el mapeo oficial
    """
    return normalize_name(name)

def transform_municipality_geodata(
    muni_gdf: gpd.GeoDataFrame, 
    dept_gdf: gpd.GeoDataFrame, 
    election_data: Dict[str, Any],
    department_name: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Transforma un GeoDataFrame de municipios incorporando datos electorales.
    Opcionalmente filtra por departamento.
    
    Args:
        muni_gdf (gpd.GeoDataFrame): GeoDataFrame original con geometrías de municipios
        dept_gdf (gpd.GeoDataFrame): GeoDataFrame con geometrías de departamentos
        election_data (Dict[str, Any]): Datos electorales procesados
        department_name (Optional[str]): Nombre del departamento a filtrar
        
    Returns:
        gpd.GeoDataFrame: GeoDataFrame transformado con datos electorales
    """
    if muni_gdf is None or muni_gdf.empty or dept_gdf is None or dept_gdf.empty:
        return None
    
    # Crear copia para no modificar el original
    transformed_muni_gdf = muni_gdf.copy()
    
    # Determinar columnas de nombres
    dept_name_column = dept_gdf.attrs.get('name_column')
    if dept_name_column is None:
        dept_name_column = _identify_department_name_column(dept_gdf)
    
    muni_name_column = _identify_municipality_name_column(transformed_muni_gdf)
    
    # Si no se encontraron columnas necesarias, retornar el original
    if dept_name_column is None or muni_name_column is None:
        return transformed_muni_gdf
    
    # Filtrar por departamento si se especifica
    if department_name:
        # Normalizar nombre del departamento
        department_name = DEPARTMENT_NAME_MAPPING.get(department_name, department_name)
        
        # Buscar la geometría del departamento
        dept_mask = dept_gdf[dept_name_column] == department_name
        if dept_mask.any():
            # Obtener geometría del departamento
            dept_geometry = dept_gdf.loc[dept_mask].geometry.iloc[0]
            
            # Filtrar municipios que intersectan con el departamento
            transformed_muni_gdf = transformed_muni_gdf[
                transformed_muni_gdf.intersects(dept_geometry)
            ]
    
    # Si después del filtro no quedan municipios, retornar None
    if transformed_muni_gdf.empty:
        return None
    
    # Incorporar datos electorales de municipios
    for dept_name, dept_data in election_data.items():
        # Verificar si hay datos de municipios
        if 'municipalities' not in dept_data:
            continue
        
        # Procesar cada municipio
        for muni_name, muni_data in dept_data['municipalities'].items():
            # Buscar coincidencias aproximadas en nombres
            mask = transformed_muni_gdf[muni_name_column].str.contains(
                muni_name, case=False, na=False
            )
            if mask.any():
                # Añadir datos electorales
                transformed_muni_gdf.loc[mask, 'mayor'] = muni_data.get('mayor', 'No disponible')
                transformed_muni_gdf.loc[mask, 'party'] = muni_data.get('party', 'No disponible')
    
    # Guardar los nombres de columnas para uso en visualización
    transformed_muni_gdf.attrs['name_column'] = muni_name_column
    
    # Asegurar que todos los valores sean serializables a JSON
    transformed_muni_gdf = _ensure_json_serializable(transformed_muni_gdf)
    
    return transformed_muni_gdf

def _identify_department_name_column(gdf: gpd.GeoDataFrame) -> Optional[str]:
    """
    Identifica la columna que contiene nombres de departamentos.
    
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame a analizar
        
    Returns:
        Optional[str]: Nombre de la columna o None si no se encuentra
    """
    candidates = [
        'NOMBRE', 'nombre', 'NAME', 'name', 'DN', 'DEPTO', 
        'depto', 'DEPARTAMENTO', 'departamento'
    ]
    
    for col in candidates:
        if col in gdf.columns:
            return col
    
    return None

def _identify_municipality_name_column(gdf: gpd.GeoDataFrame) -> Optional[str]:
    """
    Identifica la columna que contiene nombres de municipios.
    
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame a analizar
        
    Returns:
        Optional[str]: Nombre de la columna o None si no se encuentra
    """
    candidates = [
        'NOM_LOC', 'NOMBRE', 'nombre', 'NAME', 'name', 
        'MUNICIPIO', 'municipio', 'LOCALIDAD', 'localidad'
    ]
    
    for col in candidates:
        if col in gdf.columns:
            return col
    
    return None

def _ensure_json_serializable(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Convierte todos los valores no serializables a JSON en formatos compatibles.
    
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame a procesar
        
    Returns:
        gpd.GeoDataFrame: GeoDataFrame con valores serializables
    """
    # Convertir timestamps a cadenas ISO
    for col in gdf.select_dtypes(include=['datetime64']).columns:
        gdf[col] = gdf[col].astype(str)
    
    # Convertir objetos Timedelta a cadenas
    for col in gdf.select_dtypes(include=['timedelta64']).columns:
        gdf[col] = gdf[col].astype(str)
    
    # Convertir números complejos a cadenas
    for col in gdf.select_dtypes(include=['complex128', 'complex64']).columns:
        gdf[col] = gdf[col].astype(str)
    
    # Convertir valores NaN a None (null en JSON)
    for col in gdf.columns:
        if pd.api.types.is_numeric_dtype(gdf[col]):
            gdf[col] = gdf[col].replace({np.nan: None})
    
    return gdf 