import streamlit as st
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

# Importar configuración y servicios
from settings import settings, theme
from utils.styles import apply_base_styles

# Importar servicios de dominio
from domain.summary import get_national_summary

# Importar infraestructura
# from infrastructure.loaders import load_geo_data # Importación eliminada
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
    
    # --- INICIO: Configuración de la Barra Lateral ---
    st.sidebar.title("Panel de Control")
    st.sidebar.markdown("Utilice las opciones a continuación para filtrar los datos mostrados.")
    st.sidebar.markdown("---")
    # --- FIN: Configuración de la Barra Lateral ---
    
    # Inicializar estado si no existe
    if 'selected_department' not in st.session_state:
        st.session_state.selected_department = None
    
    # Configurar filtros laterales comunes
    filters_config = [
        {
            'type': 'selectbox',
            'key': 'election_year',
            'label': 'Año Electoral',
            'options': ['2015', '2020', '2025'],
            'default_index': 1,
            'add_separator': True
        }
    ]

    # Aplicar filtros en la barra lateral
    filter_values = sidebar_filters(filters_config)

    # Mostrar nota informativa para 2025
    if filter_values.get('election_year') == '2025':
        st.sidebar.info(
            """**Nota:** Los datos para 2025 se actualizarán en tiempo real 
            directamente desde la Corte Electoral una vez que estén disponibles."""
        )

    # --- INICIO: Guía Rápida en Sidebar ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Guía Rápida")
    st.sidebar.markdown("""
    *   **Año Electoral:** Seleccione el año de la elección.
    *   **Selector Principal:** Use el menú desplegable (bajo el mapa) para elegir:
        *   **NACIONAL:** Resumen general del país (Votos, Intendencias, Ediles, Alcaldes).
        *   **[Departamento]:** Detalle del departamento seleccionado.
    *   **Mapa:** Visualiza el partido ganador por departamento.
    
    **Tipos de Resultados:**
    *   **Vista Nacional:** Gráficos y tablas con agregados nacionales.
    *   **Vista Departamental:** Resultados para Intendencia y Junta Departamental. Incluye un selector al final para ver el detalle de un **Municipio** (Alcaldías y Concejos).
    """)
    # --- FIN: Guía Rápida en Sidebar ---

    # Decidir qué título mostrar según la vista
    view_type = "department" if st.session_state.selected_department else "national"
    selected_year = filter_values.get('election_year', 'N/A') # Obtener año seleccionado
    
    # Construir títulos dinámicos (se usará en la llamada a header más abajo)
    national_title = f"Elecciones Departamentales Uruguay {selected_year}"
    national_subtitle = "Visualización de Resultados Electorales Nacionales"
    department_title = f"{st.session_state.selected_department} - {selected_year}"
    department_subtitle = "Detalle de Resultados Electorales Departamentales"

    # Actualizar la llamada a header() con títulos dinámicos y centrado
    if view_type == "department":
        header(department_title, subtitle=department_subtitle, centered=True)
    else:
        header(national_title, subtitle=national_subtitle, centered=True)
    
    # Cargar los datos electorales (común para ambas vistas)
    try:
        # --- Carga de datos dinámica por año ---
        selected_year = filter_values.get('election_year', '2025') # Default a 2025
        
        summary_enriched = None
        stats = None
        
        # Decidir cómo cargar según el año
        if selected_year == '2025':
            source_key = 'API_URL_2025'
            source_type = 'api'
            if source_key not in settings.PATHS:
                st.error(f"Error: No se encontró la configuración '{source_key}' para el año {selected_year} en settings.py.")
                st.stop()
            source_location = settings.PATHS[source_key]
            print(f"Cargando datos para {selected_year} desde API: {source_location}")
            # Llamar con tipo 'api' y la URL
            result = load_election_data(source_type=source_type, source_location=source_location)

        elif selected_year in ['2020', '2015']:
            source_key = f"election_data_{selected_year}"
            source_type = 'json'
            if source_key not in settings.PATHS:
                st.error(f"Error: No se encontró la configuración '{source_key}' para el año {selected_year} en settings.py.")
                st.stop()
            source_location = settings.PATHS[source_key]
            print(f"Cargando datos para {selected_year} desde JSON: {source_location}")
            # Llamar con tipo 'json' y la ruta
            result = load_election_data(source_type=source_type, source_location=source_location)
            
        else:
            st.error(f"Año electoral no soportado: {selected_year}")
            st.stop()
        
        # Desempaquetar resultado si no es None
        if result:
            summary_enriched, stats = result
        else:
             # El error ya se mostró en las funciones de carga o pipeline
             st.error(f"Fallo al cargar o procesar los datos para {selected_year}.")
             st.stop()
        # --- Fin carga dinámica ---
        
        # 1. Enriquecer con cálculo de concejales por lista D'Hondt
        # --- ELIMINADO: Este paso ahora ocurre DENTRO de load_election_data (via pipeline/enrich) ---
        # summary_enriched = enrich_municipal_concejales(summary_enriched_base)

        # 2. Transformar al formato esperado por la UI
        from infrastructure.loaders import _transform_to_frontend_format
        election_data = _transform_to_frontend_format(summary_enriched, stats)
        
        # Verificar que los datos se cargaron y transformaron correctamente
        if not election_data:
            # Mejorar mensaje de error post-transformación
            st.error("No se pudieron transformar los datos electorales al formato esperado por la UI.")
            st.info("Verifique la salida del pipeline de procesamiento y la función _transform_to_frontend_format.")
            return
        
        # 3. Obtener resumen nacional para la vista principal (después de enriquecer)
        summary = get_national_summary(election_data)
        
        # Crear opciones para el selector principal (movido más abajo)
        # department_options = ["NACIONAL"] + sorted(list(election_data.keys()))

        # 1. SECCIÓN DEL MAPA (siempre visible)
        display_map_dashboard(election_data)
        
        # Separador visual
        st.markdown('<hr>', unsafe_allow_html=True)

        # --- INICIO: Selector de vista NACIONAL/Departamento ---
        st.markdown("<br>", unsafe_allow_html=True) # Espacio adicional arriba
        st.markdown("""
        <div style='text-align: center;'>
            <strong>Seleccione 'NACIONAL' para ver el resumen del país o elija un departamento para ver el detalle:</strong>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True) # Espacio adicional abajo del texto

        # Crear opciones para el selector principal (necesario para el debug y el selector)
        department_options = ["NACIONAL"] + sorted(list(election_data.keys()))
        
        # Determinar el índice inicial basado en el estado de sesión
        current_selection_index = 0 # Default a NACIONAL
        if st.session_state.selected_department:
            try:
                current_selection_index = department_options.index(st.session_state.selected_department)
            except ValueError:
                st.session_state.selected_department = None
                current_selection_index = 0

        # Crear columnas para centrar el selector
        col1, col_selector, col3 = st.columns([1, 2, 1])

        with col_selector:
            # Selector centralizado para Nacional/Departamento
            selected_view = st.selectbox(
                "Seleccione Vista:", # Label usada como placeholder interno
                options=department_options,
                index=current_selection_index,
                key="main_view_selector",
                label_visibility="collapsed" # Ocultar label formal
            )

            # Actualizar el estado de sesión según la selección
            if selected_view == "NACIONAL":
                if st.session_state.selected_department is not None:
                    st.session_state.selected_department = None
                    st.rerun()
            else:
                if st.session_state.selected_department != selected_view:
                    st.session_state.selected_department = selected_view
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True) # Añadir espacio después del selector
        # --- FIN: Selector de vista ---

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
        
        # 2. CONTENIDO CONDICIONAL: Nacional o Departamental
        dashboard_container = st.container()
        
        with dashboard_container:
            # Mostrar el dashboard correspondiente según la vista (ahora controlado por el selectbox)
            if view_type == "department" and department_to_show:
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
        
    # --- Actualizar Footer ---
    footer_text = (
        "Proyecto diseñado en Streamlit usando como fuente datos de la Corte Electoral. "
        "Hecho por el Lic. Juan Ignacio Pintos Elso.<br>"
        "<a href='https://github.com/Juanpintoselso33/departamentales-2025/tree/main' target='_blank'>Repositorio en GitHub</a><br><br>"
        "**Disclaimer:** Los cálculos de asignación de cargos (Ediles, Concejales) son interpretaciones "
        "realizadas por esta aplicación y pueden diferir de los resultados oficiales de la Corte Electoral."
    )
    footer(footer_text)

if __name__ == "__main__":
    main() 