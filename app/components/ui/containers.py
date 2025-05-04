"""
Componentes de contenedores para la interfaz de usuario.
Proporciona elementos visuales tipo contenedor para organizar la UI.
"""

import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from utils.styles import get_container_style

def section_container(title, content_callable, style_type="default", key=None):
    """
    Crea un contenedor con estilo para una sección con título
    
    Args:
        title (str): Título de la sección
        content_callable (callable): Función que renderiza el contenido
        style_type (str): Tipo de estilo a aplicar
        key (str, opcional): Clave para Streamlit
    """
    # Generar clave única si no se proporciona
    if key is None:
        key = f"section_{title}".lower().replace(" ", "_")
    
    # Crear contenedor con estilo personalizado
    with stylable_container(
        key=key,
        css_styles=get_container_style(style_type)
    ):
        # Mostrar título si existe
        if title:
            st.subheader(title)
        
        # Llamar a la función que renderiza el contenido
        content_callable()

def tabs_container(tab_items, style_type="default", key=None):
    """
    Crea un contenedor con pestañas
    
    Args:
        tab_items (list): Lista de diccionarios con 'title' y 'content_callable'
        style_type (str): Tipo de estilo a aplicar
        key (str, opcional): Clave para Streamlit
    """
    # Generar clave única si no se proporciona
    if key is None:
        key = f"tabs_container_{len(tab_items)}tabs"
    
    # Extraer títulos para las pestañas
    tab_titles = [item.get('title', f"Tab {i+1}") for i, item in enumerate(tab_items)]
    
    # Crear contenedor con estilo personalizado
    with stylable_container(
        key=key,
        css_styles=get_container_style(style_type)
    ):
        # Crear pestañas
        tabs = st.tabs(tab_titles)
        
        # Renderizar contenido en cada pestaña
        for i, tab in enumerate(tabs):
            with tab:
                # Verificar que tenemos una función a llamar
                if i < len(tab_items) and callable(tab_items[i].get('content_callable')):
                    tab_items[i]['content_callable']()

def grid_container(columns, items, key=None):
    """
    Crea un contenedor de cuadrícula con un número específico de columnas
    
    Args:
        columns (int): Número de columnas
        items (list): Lista de funciones callable para renderizar en cada celda
        key (str, opcional): Clave para Streamlit
    """
    # Generar clave única si no se proporciona
    if key is None:
        key = f"grid_{len(items)}items_{columns}cols"
    
    # Crear columnas usando st.columns
    cols = st.columns(columns)
    
    # Iterar sobre los items y asignarlos a las columnas
    for i, item_callable in enumerate(items):
        if callable(item_callable):
            with cols[i % columns]:
                item_callable()

def info_container(message, type="info", icon=None, dismissible=False):
    """
    Crea un contenedor de información, advertencia o error
    
    Args:
        message (str): Mensaje a mostrar
        type (str): Tipo de mensaje ('info', 'warning', 'error', 'success')
        icon (str, opcional): Emoji o icono para mostrar
        dismissible (bool): Si se puede cerrar el mensaje
    """
    # Mapear tipo a función streamlit
    type_map = {
        "info": st.info,
        "warning": st.warning,
        "error": st.error,
        "success": st.success
    }
    
    # Obtener la función correspondiente
    display_func = type_map.get(type.lower(), st.info)
    
    # Preparar mensaje con icono si existe
    if icon:
        message = f"{icon} {message}"
    
    # Mostrar mensaje
    display_func(message, icon=icon) 