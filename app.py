import streamlit as st
from st_pages import Page, Section, add_page_title
from streamlit_autorefresh import st_autorefresh

# Configuración de la página - debe ser lo primero que se ejecuta
st.set_page_config(
    page_title="Elecciones Departamentales Uruguay 2020",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar CSS global para la aplicación
st.markdown("""
<style>
/* Estilos globales para maximizar espacio */
.main .block-container {
    max-width: 100% !important;
    padding-top: 1rem !important;
    padding-right: 1rem !important;
    padding-left: 1rem !important;
    padding-bottom: 1rem !important;
}

/* Eliminar restricciones de ancho para todos los contenedores */
div[data-testid="stVerticalBlock"] {
    width: 100% !important;
    max-width: 100% !important;
}

/* Estilos de separadores */
hr {
    margin-top: 1rem;
    margin-bottom: 1rem;
    border-top: 1px solid rgba(128, 128, 128, 0.2);
}

/* Ajustes para dashboards */
div[data-testid="stHorizontalBlock"] {
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# Configurar las páginas de la aplicación
pages = [
    Page("app.py", "🏠 Resumen Nacional", icon="🏠"),
    # Nota: La página de departamentos ahora está integrada en la página principal
    Page("app/pages/comparison.py", "📊 Comparación", icon="📊"),
]

# Importar configuración y servicios
from settings.settings import PATHS
from utils.styles import apply_base_styles

# Importar servicios de dominio
from domain.summary import get_national_summary

# Importar infraestructura
from infrastructure.loaders import load_geo_data
from infrastructure.loaders.cache import get_summary as load_election_data

# Importar componentes UI
from app.components.ui.layout import header, footer, sidebar_filters

# Importar dashboards y componentes funcionales
from app.components.dashboards import display_national_dashboard
from app.components.dashboards import display_map_dashboard
from app.components.dashboards import display_department_dashboard

def main():
    """Función principal que estructura la aplicación"""
    # Aplicar estilos desde el módulo centralizado
    apply_base_styles()
    
    # Inicializar estado si no existe
    if 'selected_department' not in st.session_state:
        st.session_state.selected_department = None
    
    # Función para volver a la vista nacional
    def back_to_national():
        st.session_state.selected_department = None
        st.rerun()
    
    # Configurar filtros laterales comunes
    filters_config = [
        {
            'type': 'selectbox',
            'key': 'election_year',
            'label': 'Año Electoral',
            'options': ['2020'],
            'default_index': 0,
            'add_separator': True
        }
    ]
    
    # Decidir qué título mostrar según la vista
    view_type = "department" if st.session_state.selected_department else "national"
    
    if view_type == "department":
        header("Detalle Departamental", subtitle="Elecciones Departamentales 2020")
    else:
        header("Resumen Nacional", subtitle="Elecciones Departamentales 2020")
    
    # Cargar los datos electorales (común para ambas vistas)
    try:
        # Cargar datos electorales utilizando el módulo de infraestructura
        summary_enriched, stats = load_election_data(PATHS["election_data_2020"])
        
        # Transformar al formato esperado por la UI
        from infrastructure.loaders import _transform_to_frontend_format
        election_data = _transform_to_frontend_format(summary_enriched, stats)
        
        # Verificar que los datos se cargaron correctamente
        if not election_data:
            st.error("No se pudieron cargar los datos electorales. El archivo existe pero no contiene datos en el formato esperado.")
            st.info("Verifique que el archivo JSON contiene la estructura correcta con lista de departamentos o una clave 'Departamentos' con la lista.")
            return
        
        # Obtener resumen nacional para la vista principal
        summary = get_national_summary(election_data)
        
        # Configurar auto-refresh (activado solo en modo elecciones)
        if st.sidebar.checkbox("Habilitar refresco automático", value=False, key="enable_autorefresh"):
            refresh_interval = st.sidebar.slider(
                "Intervalo de refresco (segundos)", 
                min_value=30, 
                max_value=300, 
                value=60, 
                step=30,
                key="refresh_interval"
            )
            st_autorefresh(interval=refresh_interval * 1000, key="data_autorefresh")
        
        # Aplicar filtros en la barra lateral
        filter_values = sidebar_filters(filters_config)
        
        # Si hay un departamento seleccionado, encontrar el objeto de departamento correspondiente
        department_to_show = None
        
        if st.session_state.selected_department:
            from domain.transformers import normalize_for_comparison
            dept_norm = normalize_for_comparison(st.session_state.selected_department)
            
            # Buscar el departamento que coincida
            for dept in election_data.keys():
                if normalize_for_comparison(dept) == dept_norm:
                    department_to_show = dept
                    break
            
            # Si no se encontró el departamento, volver a la vista nacional
            if not department_to_show:
                st.warning(f"No se encontró información para el departamento '{st.session_state.selected_department}'")
                st.session_state.selected_department = None
                st.rerun()
        
        # 1. SECCIÓN DEL MAPA (siempre visible)
        display_map_dashboard(election_data)
        
        # Separador visual
        st.markdown('<hr>', unsafe_allow_html=True)
        
        # 2. CONTENIDO CONDICIONAL: Nacional o Departamental
        dashboard_container = st.container()
        
        with dashboard_container:
            # Mostrar el dashboard correspondiente según la vista
            if view_type == "department" and department_to_show:
                # Mostrar botón para volver a la vista nacional
                if st.button("← Volver a Resumen Nacional", on_click=back_to_national):
                    pass
                
                # Mostrar dashboard departamental
                display_department_dashboard(election_data, department_to_show)
            elif view_type == "national":
                # Mostrar el dashboard nacional
                try:
                    display_national_dashboard(election_data, summary)
                except Exception as e:
                    st.error(f"Error al mostrar el dashboard nacional: {e}")
                    import traceback
                    st.code(traceback.format_exc(), language="python")
        
    except FileNotFoundError as e:
        st.error(f"Error: {e}")
        st.warning("Verifique que los archivos de datos existan en la ubicación correcta.")
    except Exception as e:
        st.error(f"Error inesperado: {e}")
        st.error(f"Tipo de error: {type(e)}")
        import traceback
        st.code(traceback.format_exc(), language="python")
        st.warning("Verifique los datos y la configuración para resolver el problema.")
        
    # Mostrar footer
    footer("Visualizador de Elecciones Departamentales de Uruguay • 2025")

if __name__ == "__main__":
    main() 