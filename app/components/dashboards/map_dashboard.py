"""
Componente para visualización del mapa electoral.
Muestra el mapa electoral principal de departamentos.
"""

import streamlit as st
import folium # Asegurar import
from streamlit_folium import st_folium # Asegurar import

from app.components.functional.map_generator import create_department_choropleth
from settings.settings import PATHS
from domain.transformers import normalize_for_comparison

def display_map_dashboard(election_data):
    """
    Muestra un mapa interactivo (pero estático) con los departamentos de Uruguay.
    """
    # Detectar departamento seleccionado para resaltar
    selected_department_name = st.session_state.get('selected_department')
    highlight_department = None
    if selected_department_name:
        dept_norm = normalize_for_comparison(selected_department_name)
        for dept in election_data.keys():
            if normalize_for_comparison(dept) == dept_norm:
                highlight_department = dept
                break
    
    # --- RESTAURAR CSS ORIGINAL --- 
    st.markdown(""" 
    <style>
    .stCustomComponentV1[title="streamlit_folium.st_folium"] {
        height: 800px !important;
        min-height: 800px !important;
        width: 100% !important;
        display: block !important;
        margin-bottom: 2rem !important;
    }
    @media (max-width: 900px) {
        .stCustomComponentV1[title="streamlit_folium.st_folium"] {
            height: 400px !important;
            min-height: 400px !important;
        }
    }
    /* Regla general que podría afectar otros componentes si existe */
    /* .stCustomComponentV1 { ... } */ 
    </style>
    """, unsafe_allow_html=True)

    try:
        # Crear mapa estático con Folium
        m = create_department_choropleth(
            geojson_path=PATHS["departments_geojson"],
            election_data=election_data,
            highlight_department=highlight_department,
            width='100%', # Pasar 100% al generador
            height='100%' # Pasar 100% al generador
            # Otros args como zoom_start son manejados internamente
        )
        
        # --- RESTAURAR LLAMADA A st_folium --- 
        st_folium(
            m,
            width='100%',
            height=800, # Usar altura base del CSS
            returned_objects=[], # Sin esperar clics ni estado
            key="national_map"
        )
        
    except Exception as e:
        st.error(f"Error al generar o mostrar el mapa Folium: {e}")
        # Considerar mostrar traceback en un expander para depuración
        # import traceback
        # with st.expander("Detalles del error"):
        #    st.code(traceback.format_exc(), language="python") 