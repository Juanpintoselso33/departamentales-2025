"""
Utilidades para crear y configurar tablas con st-aggrid.
"""
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode, JsCode
from domain.transformers.adapters import create_progress_bar_renderer as transformer_create_progress_bar_renderer

def create_aggrid_table(df, selection_mode=None, pagination=True, use_checkbox=False, 
                       theme="streamlit", height=400, custom_css=None, columns_auto_size_mode='FIT_CONTENTS',
                       key=None):
    """
    Crea una tabla interactiva con st-aggrid.
    
    Args:
        df (pd.DataFrame): DataFrame con los datos a mostrar
        selection_mode (str, optional): Modo de selección ("single" o "multiple")
        pagination (bool): Si se debe paginar la tabla
        use_checkbox (bool): Si se debe usar checkboxes para selección
        theme (str): Tema a usar (streamlit, alpine, balham, material)
        height (int): Altura de la tabla en píxeles
        custom_css (dict, optional): CSS personalizado para la tabla
        columns_auto_size_mode (str): Modo de ajuste automático de columnas
        key (str, optional): Clave única para el componente
        
    Returns:
        dict: Resultado de la tabla AgGrid, con datos seleccionados si aplica
    """
    # Configurar opciones de la tabla
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configurar opciones básicas
    gb.configure_default_column(
        filterable=True,
        sortable=True,
        editable=False,
        groupable=True,
        resizable=True,
        autoHeight=True
    )
    
    # Configurar selección si se requiere
    if selection_mode:
        if selection_mode == "single":
            gb.configure_selection(selection_mode="single", use_checkbox=use_checkbox)
        elif selection_mode == "multiple":
            gb.configure_selection(selection_mode="multiple", use_checkbox=use_checkbox)
            
    # Habilitar paginación si se requiere
    if pagination:
        gb.configure_pagination(
            paginationAutoPageSize=False,
            paginationPageSize=10
        )
    
    # Construir opciones
    grid_options = gb.build()
    
    # Ajustar el tamaño de las columnas
    grid_options['columnDefs'] = [
        {**col, 'autoSize': True} for col in grid_options['columnDefs']
    ]
    
    # Agregar CSS personalizado si se proporciona
    if custom_css:
        grid_options['css'] = custom_css
    
    # Crear y mostrar la tabla
    return AgGrid(
        df,
        gridOptions=grid_options,
        enable_enterprise_modules=False,
        height=height,
        fit_columns_on_grid_load=True,
        key=key,
        reload_data=False,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        columns_auto_size_mode=columns_auto_size_mode,
        theme=theme
    )

def create_progress_bar_renderer():
    """
    Crea un renderizador personalizado para mostrar barras de progreso en la tabla.
    
    Returns:
        str: Código JavaScript para el renderizador
    """
    # Usar la versión del transformer para evitar código duplicado y garantizar serialización
    return transformer_create_progress_bar_renderer() 