"""
Componentes de layout para la interfaz de usuario.
Proporciona elementos para estructura y organización de la UI.
"""

import streamlit as st

def header(title, subtitle=None, logo=None, hide_menu=False, centered=False):
    """
    Muestra un encabezado personalizado con título, subtítulo y/o logo
    
    Args:
        title (str): Título principal
        subtitle (str, opcional): Subtítulo o descripción
        logo (str, opcional): Ruta a archivo de imagen para logo
        hide_menu (bool): Si True, oculta el menú de hamburguesa
        centered (bool): Si True, centra el título y subtítulo y añade margen superior.
    """
    # Estilos CSS para centrado y margen
    css_styles = """
        <style>
        .header-container {
            margin-top: 2rem; /* Añadir margen superior */
            text-align: center; /* Centrar texto */
        }
        .header-container hr {
            margin-top: 1.5rem; /* Ajustar margen de la línea divisora */
        }
        </style>
    """ if centered else ""
    st.markdown(css_styles, unsafe_allow_html=True)

    # Contenedor principal para aplicar estilos si está centrado
    container_class = "header-container" if centered else ""
    st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)

    # Ocultar menú de hamburguesa si se solicita
    if hide_menu:
        st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """, unsafe_allow_html=True)
    
    # Crear layout con/sin logo
    if logo:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(logo, width=80)
        with col2:
            st.title(title)
            if subtitle:
                st.caption(subtitle)
    else:
        st.title(title)
        if subtitle:
            st.caption(subtitle)
    
    # Añadir línea divisora
    st.markdown("<hr>", unsafe_allow_html=True)

    # Cerrar el contenedor principal si se usó
    if centered:
        st.markdown("</div>", unsafe_allow_html=True)

def footer(text=None, hide_streamlit_footer=True):
    """
    Muestra un pie de página personalizado
    
    Args:
        text (str, opcional): Texto a mostrar en el footer
        hide_streamlit_footer (bool): Si True, oculta el footer predeterminado de Streamlit
    """
    # Ocultar footer de Streamlit si se solicita
    if hide_streamlit_footer:
        st.markdown("""
        <style>
        footer {visibility: hidden;}
        </style>
        """, unsafe_allow_html=True)
    
    # Mostrar footer personalizado si se proporciona texto
    if text:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='text-align: center; color: #888; padding: 10px; font-size: 0.8em;'>
            {text}
        </div>
        """, unsafe_allow_html=True)

def sidebar_filters(filters_config):
    """
    Muestra filtros en la barra lateral según una configuración
    
    Args:
        filters_config (list): Lista de diccionarios con configuración de filtros
            Cada filtro debe tener: type, key, label, options (opcional), etc.
    
    Returns:
        dict: Valores seleccionados de los filtros
    """
    # Inicializar diccionario de resultados
    filter_values = {}
    
    # Procesar cada filtro
    for filter_item in filters_config:
        filter_type = filter_item.get('type', 'selectbox')
        filter_key = filter_item.get('key')
        filter_label = filter_item.get('label', 'Filtro')
        
        # Verificar que tenemos al menos tipo y clave
        if not filter_key:
            continue
            
        # Mostrar el filtro según su tipo
        if filter_type == 'selectbox':
            options = filter_item.get('options', [])
            default_index = filter_item.get('default_index', 0)
            value = st.sidebar.selectbox(
                filter_label,
                options=options,
                index=min(default_index, len(options)-1) if options else 0,
                key=f"sidebar_{filter_key}"
            )
            filter_values[filter_key] = value
            
        elif filter_type == 'radio':
            options = filter_item.get('options', [])
            default_index = filter_item.get('default_index', 0)
            value = st.sidebar.radio(
                filter_label,
                options=options,
                index=min(default_index, len(options)-1) if options else 0,
                key=f"sidebar_{filter_key}"
            )
            filter_values[filter_key] = value
            
        elif filter_type == 'multiselect':
            options = filter_item.get('options', [])
            default = filter_item.get('default', [])
            value = st.sidebar.multiselect(
                filter_label,
                options=options,
                default=default,
                key=f"sidebar_{filter_key}"
            )
            filter_values[filter_key] = value
            
        elif filter_type == 'slider':
            min_value = filter_item.get('min_value', 0)
            max_value = filter_item.get('max_value', 100)
            default_value = filter_item.get('default_value', min_value)
            step = filter_item.get('step', 1)
            value = st.sidebar.slider(
                filter_label,
                min_value=min_value,
                max_value=max_value,
                value=default_value,
                step=step,
                key=f"sidebar_{filter_key}"
            )
            filter_values[filter_key] = value
            
        elif filter_type == 'checkbox':
            default = filter_item.get('default', False)
            value = st.sidebar.checkbox(
                filter_label,
                value=default,
                key=f"sidebar_{filter_key}"
            )
            filter_values[filter_key] = value
            
        # Añadir separador si se solicita
        if filter_item.get('add_separator', False):
            st.sidebar.markdown("---")
    
    return filter_values

def two_column_layout(left_content, right_content, left_width=1, right_width=1):
    """
    Crea un layout de dos columnas con contenido personalizado
    
    Args:
        left_content (callable): Función que renderiza el contenido de la columna izquierda
        right_content (callable): Función que renderiza el contenido de la columna derecha
        left_width (int): Ancho relativo de la columna izquierda
        right_width (int): Ancho relativo de la columna derecha
    """
    col1, col2 = st.columns([left_width, right_width])
    
    with col1:
        left_content()
        
    with col2:
        right_content()

def conditional_display(condition, content_callable):
    """
    Muestra contenido condicionalmente
    
    Args:
        condition (bool): Condición que determina si se muestra el contenido
        content_callable (callable): Función que renderiza el contenido
    """
    if condition and callable(content_callable):
        content_callable() 