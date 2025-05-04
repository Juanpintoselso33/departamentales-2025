import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import hashlib
import json

def add_percentages(df: pd.DataFrame, group_by: str = "departamento", value_col: str = "votos") -> pd.DataFrame:
    """
    Añade columna de porcentajes a un DataFrame agrupando por el campo indicado.
    
    Args:
        df: DataFrame con datos electorales
        group_by: Columna por la que agrupar para calcular porcentajes
        value_col: Columna que contiene los valores a sumar
        
    Returns:
        DataFrame con la columna 'pct' añadida
    """
    # Clonar para no modificar el original
    result_df = df.copy()
    
    # Calcular totales por grupo
    totals = result_df.groupby(group_by)[value_col].transform("sum")
    
    # Calcular porcentajes
    result_df["pct"] = (result_df[value_col] / totals * 100).round(2)
    
    return result_df

def add_ranking(df: pd.DataFrame, group_by: str = "departamento", value_col: str = "votos") -> pd.DataFrame:
    """
    Añade ranking de posición dentro de cada grupo.
    
    Args:
        df: DataFrame con datos electorales
        group_by: Columna por la que agrupar para calcular ranking
        value_col: Columna que se usa para el ranking
        
    Returns:
        DataFrame con la columna 'ranking' añadida
    """
    # Clonar para no modificar el original
    result_df = df.copy()
    
    # Calcular ranking dentro de cada grupo
    result_df["ranking"] = result_df.groupby(group_by)[value_col].rank(ascending=False, method="min").astype(int)
    
    return result_df

def calculate_winning_parties(df: pd.DataFrame, group_by: str = "departamento") -> Dict[str, str]:
    """
    Calcula el partido ganador en cada departamento.
    
    Args:
        df: DataFrame con datos electorales (debe incluir partido y votos)
        group_by: Columna a usar como clave para los resultados
        
    Returns:
        Diccionario con departamento -> partido ganador
    """
    # Necesitamos tener los votos por cada partido y departamento
    if "pct" not in df.columns:
        df = add_percentages(df, group_by=group_by)
    
    # Obtener el partido con más votos por departamento
    winning_parties = {}
    
    for name, group in df.groupby(group_by):
        winner = group.loc[group["votos"].idxmax()]
        winning_parties[name] = winner["partido"]
    
    return winning_parties

def add_file_metadata(df: pd.DataFrame, filepath: str) -> pd.DataFrame:
    """
    Añade metadatos sobre el archivo de origen para trazabilidad.
    
    Args:
        df: DataFrame con datos
        filepath: Ruta al archivo de origen
        
    Returns:
        DataFrame con metadatos añadidos
    """
    result_df = df.copy()
    
    # Añadir columnas con información del origen
    try:
        with open(filepath, 'rb') as f:
            file_bytes = f.read()
            file_hash = hashlib.md5(file_bytes).hexdigest()
            file_size = len(file_bytes)
            
        result_df["_source_file"] = filepath
        result_df["_source_hash"] = file_hash
        result_df["_source_size"] = file_size
    except Exception as e:
        # Si falla la lectura, añadir información básica
        result_df["_source_file"] = filepath
        result_df["_source_error"] = str(e)
    
    return result_df

def enriched_election_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica todas las transformaciones de enriquecimiento al DataFrame electoral.
    
    Args:
        df: DataFrame con datos electorales limpios
        
    Returns:
        DataFrame enriquecido con métricas derivadas
    """
    # Aplicar todas las transformaciones en secuencia
    result = df.copy()
    result = add_percentages(result)
    result = add_ranking(result)
    
    return result 