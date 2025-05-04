"""
Componente para visualización del mapa electoral.
Muestra el mapa electoral principal de departamentos.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
from app.components.functional.map_generator import create_department_choropleth
from settings.settings import PATHS
from domain.transformers import normalize_for_comparison

def display_map_dashboard(election_data):
    """
    Muestra un mapa interactivo con los departamentos de Uruguay y sus resultados electorales.
    
    Args:
        election_data (dict): Datos electorales por departamento
    """
    # Detectar departamento seleccionado de la sesión
    selected_department = None
    if 'selected_department' in st.session_state and st.session_state.selected_department:
        # Buscar el departamento real por su nombre normalizado
        dept_norm = normalize_for_comparison(st.session_state.selected_department)
        for dept in election_data.keys():
            if normalize_for_comparison(dept) == dept_norm:
                selected_department = dept
                break
    
    # CSS para maximizar el espacio del mapa - aplicado solo al iframe de Folium
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
    .stCustomComponentV1 {
        height: 200px !important;
        min-height: 200px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    try:
        # Crear mapa de departamentos
        m = create_department_choropleth(
            PATHS["departments_geojson"],
            election_data,
            field="Partido ganador",
            show_labels=False,
            show_legend=False,
            highlight_department=selected_department,
            width='100%',
            height='800px',
            zoom_start=6.5,  # Mejor enfoque inicial
            min_zoom=7       # Limitar el zoom out
        )
        
        # Renderizar directamente el mapa ocupando todo el ancho
        folium_output = st_folium(
            m,
            width=1200,
            height=800,
            returned_objects=["last_object_clicked"],
            key="national_map"
        )
        
        # Procesar clic en departamento si existe
        if folium_output and folium_output.get('last_object_clicked'):
            clicked_obj = folium_output['last_object_clicked']
            if clicked_obj and 'properties' in clicked_obj:
                properties = clicked_obj['properties']
                clicked_department = properties.get('display_name') or properties.get('name')
                
                if clicked_department and clicked_department != st.session_state.get('selected_department'):
                    # Actualizar el estado de sesión con el departamento seleccionado
                    st.session_state['selected_department'] = clicked_department
                    # Forzar recarga para mostrar el dashboard del departamento
                    st.rerun()
        
    except Exception as e:
        st.error(f"Error al generar el mapa: {e}")
        with st.expander("Ver detalles del error"):
            import traceback
            st.code(traceback.format_exc(), language="python") 