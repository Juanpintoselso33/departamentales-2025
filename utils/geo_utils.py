"""
Utilidades para procesamiento geoespacial.
"""
import os
import geopandas as gpd
import pandas as pd
import folium
import streamlit as st

from settings.settings import PATHS, DEPARTMENT_NAME_MAPPING
from infrastructure.loaders import load_election_data
import shapely.geometry as geometry

# Start clean with only the infrastructure imports needed
import numpy as np

def clean_dataframe_for_json(gdf):
    """
    Limpia un GeoDataFrame para asegurar que sea serializable a JSON.
    
    Args:
        gdf (geopandas.GeoDataFrame): GeoDataFrame a limpiar
        
    Returns:
        geopandas.GeoDataFrame: GeoDataFrame limpio
    """
    if gdf is None:
        return None
        
    # Crear una copia para no modificar el original
    cleaned_gdf = gdf.copy()
    
    # Convertir columnas problemáticas a formatos serializables
    for col in cleaned_gdf.columns:
        # Convertir timestamps a strings
        if pd.api.types.is_datetime64_any_dtype(cleaned_gdf[col]):
            cleaned_gdf[col] = cleaned_gdf[col].astype(str)
        # Convertir valores numéricos problemáticos (NaN, inf) a valores predeterminados
        elif pd.api.types.is_numeric_dtype(cleaned_gdf[col]):
            cleaned_gdf[col] = cleaned_gdf[col].replace([np.inf, -np.inf], np.nan)
            cleaned_gdf[col] = cleaned_gdf[col].fillna(value=0)
    
    return cleaned_gdf

def normalize_department_name(name):
    """
    Normaliza un nombre de departamento para facilitar coincidencias.
    
    Args:
        name (str): Nombre de departamento a normalizar
        
    Returns:
        str: Nombre normalizado
    """
    if not name:
        return name
        
    # Convertir a uppercase para buscar en el mapeo
    upper_name = name.upper()
    
    # Correcciones especiales para departamentos con problemas
    if upper_name == "RÌO NEGRO":  # Acento incorrecto en el shapefile
        upper_name = "RIO NEGRO"
    elif upper_name == "PAYSANDÚ":
        upper_name = "PAYSANDU"
    
    # Devolver el nombre normalizado si existe en el mapeo
    if upper_name in DEPARTMENT_NAME_MAPPING:
        return DEPARTMENT_NAME_MAPPING[upper_name]
    
    # Si no está en el mapeo, intentar convertir a formato título
    # para "Nombre Compuesto" en lugar de "NOMBRE COMPUESTO"
    return name.title()

def find_department_name_column(gdf):
    """
    Busca la columna que contiene los nombres de departamentos.
    
    Args:
        gdf (geopandas.GeoDataFrame): GeoDataFrame con datos de departamentos
        
    Returns:
        str: Nombre de la columna encontrada o None
    """
    common_names = ['NOMBRE', 'DEPTO', 'DEPARTAMENTO', 'NOMBDEP', 'NOMDEP']
    
    # Primero buscar coincidencias exactas
    for col in common_names:
        if col in gdf.columns:
            return col
    
    # Luego buscar coincidencias parciales
    for col in gdf.columns:
        col_lower = col.lower()
        if 'nom' in col_lower and ('dep' in col_lower or 'dto' in col_lower):
            return col
        elif 'depto' in col_lower or 'departamento' in col_lower:
            return col
    
    return None

def find_municipality_columns(gdf):
    """
    Busca las columnas que contienen nombres de municipios y departamentos.
    
    Args:
        gdf (geopandas.GeoDataFrame): GeoDataFrame con datos de municipios
        
    Returns:
        tuple: (columna_municipio, columna_departamento) o (None, None)
    """
    # Posibles nombres para columna de municipios
    muni_candidates = ['MUNICIPIO', 'MUNI', 'NOMBMUNI', 'NOMMUNI']
    
    # Posibles nombres para columna de departamentos
    dept_candidates = ['DEPARTAMENTO', 'DEPTO', 'NOMBDEP', 'NOMDEP', 'DEP']
    
    muni_col = None
    dept_col = None
    
    # Buscar columna de municipios (coincidencia exacta primero)
    for col in muni_candidates:
        if col in gdf.columns:
            muni_col = col
            break
    
    # Si no se encuentra, buscar por coincidencia parcial
    if muni_col is None:
        for col in gdf.columns:
            col_lower = col.lower()
            if 'muni' in col_lower:
                muni_col = col
                break
    
    # Buscar columna de departamentos (coincidencia exacta primero)
    for col in dept_candidates:
        if col in gdf.columns:
            dept_col = col
            break
    
    # Si no se encuentra, buscar por coincidencia parcial
    if dept_col is None:
        for col in gdf.columns:
            col_lower = col.lower()
            if 'dep' in col_lower or 'depto' in col_lower or 'dpto' in col_lower:
                dept_col = col
                break
    
    return muni_col, dept_col

@st.cache_data(ttl=3600, show_spinner=False)
def load_departments_shapefile():
    """
    Carga el shapefile de departamentos de Uruguay.
    
    Returns:
        geopandas.GeoDataFrame: GeoDataFrame con los departamentos
    """
    shapefile_path = PATHS["departments_shapefile"]
    gdf = gpd.read_file(shapefile_path)
    
    # Buscar la columna con nombres de departamentos
    dept_col = find_department_name_column(gdf)
    
    # Si encontramos la columna y no es 'NOMBRE', renombrar
    if dept_col and dept_col != 'NOMBRE':
        gdf = gdf.rename(columns={dept_col: 'NOMBRE'})
    elif not dept_col:
        # Si no encontramos la columna, crear una basada en índices
        gdf['NOMBRE'] = [f"Departamento {i+1}" for i in range(len(gdf))]
    
    # Normalizar los nombres de departamentos (mayúsculas a formato título)
    for index, row in gdf.iterrows():
        original_name = row['NOMBRE']
        normalized_name = normalize_department_name(original_name)
        
        # Actualizar el nombre normalizado
        gdf.at[index, 'NOMBRE'] = normalized_name
    
    # Limpiar para JSON
    gdf = clean_dataframe_for_json(gdf)
    
    return gdf

@st.cache_data(ttl=3600, show_spinner=False)
def load_municipalities_shapefile():
    """
    Carga el shapefile de municipios de Uruguay.
    
    Returns:
        geopandas.GeoDataFrame: GeoDataFrame con los municipios
    """
    shapefile_path = PATHS["municipalities_shapefile"]
    gdf = gpd.read_file(shapefile_path)
    
    # Limpiar para JSON
    gdf = clean_dataframe_for_json(gdf)
    
    return gdf 