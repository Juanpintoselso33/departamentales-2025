import streamlit as st
import pandas as pd
import json
from typing import Dict, Any
import os

# Importar transformers
from domain.transformers.cleaning import clean_election_df, normalize_election_data
from domain.transformers.enrichment import add_percentages, add_ranking, enriched_election_df, add_file_metadata
from domain.transformers.adapters import create_department_table_options, create_progress_bar_renderer, prepare_summary_data
from st_aggrid import AgGrid

@st.cache_data(ttl=300)
def load_election_data(file_path: str) -> Dict[str, Any]:
    """
    Carga datos electorales de un archivo JSON y los procesa con transformers.
    
    Args:
        file_path: Ruta al archivo JSON con datos electorales
    
    Returns:
        Diccionario con datos normalizados y enriquecidos
    """
    try:
        # Cargar datos crudos
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Aplicar transformers
        normalized_data = normalize_election_data(raw_data)
        
        # Generar resumen
        summary = prepare_summary_data(normalized_data)
        
        return {
            "election_data": normalized_data,
            "summary": summary
        }
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return {"election_data": {}, "summary": {}}

@st.cache_data(ttl=300)
def load_and_transform_votes(file_path: str) -> pd.DataFrame:
    """
    Carga datos de votos brutos y aplica transformaciones.
    
    Args:
        file_path: Ruta al archivo CSV con datos de votos
    
    Returns:
        DataFrame limpio y enriquecido
    """
    try:
        # Cargar datos (simulamos datos de ejemplo)
        raw_data = [
            {"departamento": "montevideo", "partido": "FA", "votos": 350000},
            {"departamento": "montevideo", "partido": "PN", "votos": 150000},
            {"departamento": "canelones", "partido": "FA", "votos": 180000},
            {"departamento": "canelones", "partido": "PN", "votos": 120000},
            # Más datos...
        ]
        
        # 1. Limpiar y validar
        clean_df = clean_election_df(raw_data)
        
        # 2. Enriquecer con métricas
        enriched_df = enriched_election_df(clean_df)
        
        # 3. Añadir metadatos (opcional)
        if os.path.exists(file_path):
            final_df = add_file_metadata(enriched_df, file_path)
        else:
            final_df = enriched_df
            
        return final_df
    except Exception as e:
        st.error(f"Error al procesar datos: {str(e)}")
        return pd.DataFrame()

def display_demo():
    """Demostración de uso de transformers"""
    st.title("Demostración de Transformers")
    
    # Simulamos carga de datos usando transformers
    votes_df = load_and_transform_votes("data/votes.csv")
    
    if not votes_df.empty:
        st.subheader("Datos de votos procesados")
        
        # Usar adapter para configurar tabla
        gb_options = create_department_table_options(votes_df)
        
        # Mostrar tabla usando las opciones generadas
        AgGrid(
            votes_df,
            gridOptions=gb_options,
            height=400,
            theme="streamlit",
            fit_columns_on_grid_load=True,
            key="votes_table"
        )
        
        # Mostrar más información
        st.subheader("Metadatos generados")
        metadata_cols = [col for col in votes_df.columns if col.startswith('_source')]
        if metadata_cols:
            st.dataframe(votes_df[metadata_cols].drop_duplicates())

if __name__ == "__main__":
    display_demo() 