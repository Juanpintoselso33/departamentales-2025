"""
Componentes de métricas para la interfaz de usuario.
Proporciona elementos visuales para mostrar métricas clave.
"""

import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards

def render_metrics_cards(metrics_data):
    """
    Renderiza tarjetas con métricas clave de la elección usando st.metric nativo
    
    Args:
        metrics_data (list): Lista de diccionarios con datos de métricas
            Cada diccionario debe tener keys: title, value, delta(opcional), is_positive(opcional)
    """
    # Primero, establecer CSS para forzar altura exacta en todas las métricas
    st.markdown("""
    <style>
    /* Estilos para forzar altura igual en métricas */
    [data-testid="metric-container"] {
        background-color: #1E293B !important;
        height: 130px !important;
        min-height: 130px !important;
        max-height: 130px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        padding: 1rem !important;
        border-left: 4px solid #0EA5E9 !important;
        border-radius: 5px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Alinear contenedor horizontal de métricas */
    [data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
        display: flex !important;
    }
    
    /* Hacer que las columnas ocupen el mismo espacio */
    [data-testid="column"] {
        flex: 1 !important;
        display: flex !important;
    }
    
    /* Hacer que cada contenedor métrica ocupe todo el espacio disponible */
    [data-testid="column"] > div:has([data-testid="metric-container"]) {
        width: 100% !important;
        flex-grow: 1 !important;
    }
    
    /* Estilos para el valor principal */
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Crear columnas para las tarjetas
    cols = st.columns(len(metrics_data))
    
    # Renderizar cada métrica
    for i, metric in enumerate(metrics_data):
        with cols[i]:
            # Usar el componente nativo de Streamlit
            delta_value = metric.get('delta', None)
            
            # Determinar si el delta es positivo o negativo (si tiene un valor)
            delta_color = "off"  # Default value to ensure it's never None
            if delta_value and metric.get('is_positive') is not None:
                delta_color = "normal" if metric.get('is_positive', False) else "inverse"
            
            st.metric(
                label=metric['title'],
                value=metric['value'],
                delta=delta_value,
                delta_color=delta_color
            )
    
    # No es necesario aplicar style_metric_cards ya que estamos forzando nuestros propios estilos
    # style_metric_cards(
    #    background_color="#1E293B",  # Fondo oscuro
    #    border_left_color="#0EA5E9",  # Borde izquierdo azul
    #    border_color="#334155",  # Borde general gris oscuro
    #    box_shadow=True,  # Sombra para profundidad
    #    border_size_px=1,  # Borde delgado
    #    border_radius_px=5  # Bordes redondeados
    # )

def metric_row(title, value, description=None, delta=None, delta_text=None, is_positive=None):
    """
    Muestra una métrica individual con descripción opcional
    
    Args:
        title (str): Título de la métrica
        value (str): Valor a mostrar
        description (str, opcional): Texto descriptivo adicional
        delta (str, opcional): Valor de cambio
        delta_text (str, opcional): Texto explicativo del cambio
        is_positive (bool, opcional): Si el cambio es positivo
    """
    # Determinar si el delta es positivo o negativo
    delta_color = "off"
    if delta and is_positive is not None:
        delta_color = "normal" if is_positive else "inverse"
    
    # Mostrar la métrica
    st.metric(
        label=title,
        value=value,
        delta=delta,
        delta_color=delta_color
    )
    
    # Mostrar descripción o texto de delta si existe
    if description:
        st.caption(description)
    elif delta_text:
        st.caption(delta_text) 