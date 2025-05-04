"""
Estilos CSS para la aplicación de monitoreo electoral.
Se centraliza para mantener consistencia y modularidad.
"""

import streamlit as st

def apply_base_styles():
    """
    Aplica los estilos CSS básicos a la aplicación.
    """
    st.markdown("""
    <style>
    /* Estilo general para la aplicación */
    .main {
        background-color: #0E1117;
        color: #FAFAFA;
        padding: 0;
    }
    
    /* Contenedor principal con margen adecuado */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 1400px !important;
    }
    
    /* Espaciado entre elementos principales */
    div.stVerticalBlock {
        gap: 0.75rem !important;
    }
    
    /* Espaciado adecuado para los contenedores */
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    
    /* Títulos con espaciado adecuado */
    h1 {
        font-size: 2rem !important;
        margin: 0.5rem 0 !important;
        padding: 0 !important;
    }
    
    h2 {
        font-size: 1.5rem !important;
        margin: 1rem 0 0.5rem 0 !important;
        padding: 0 !important;
    }
    
    h3, h4, h5, h6 {
        margin: 0.5rem 0 !important;
        padding: 0 !important;
    }
    
    /* Estilos para tarjetas y contenedores */
    .dashboard-card {
        background-color: #1E293B;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        height: 100%;
        margin-bottom: 0.5rem;
    }
    
    /* Estilos para títulos dentro de tarjetas */
    .card-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 0.5rem;
    }
    
    /* Eliminar márgenes extra en tabs */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 0.5rem;
    }
    
    /* Estilizar barras de pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        padding: 0 16px;
        border-radius: 4px;
        font-weight: 500;
    }
    
    /* Estilo para tarjetas de estadísticas */
    .metric-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    /* Estilos para el mapa Folium */
    .folium-map {
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
        border-radius: 0.5rem !important;
        overflow: hidden !important;
    }
    
    /* Quitar bordes del iframe */
    iframe {
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
        display: block !important;
        width: 100% !important;
    }
    
    /* Contenedor del iframe */
    .element-container:has(iframe) {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Ajustar elementos dentro del iframe */
    .stMarkdown:has(iframe) {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Eliminar espacio adicional en las filas que contienen mapas */
    [data-testid="stVerticalBlock"]:has(iframe) {
        gap: 0 !important;
    }
    
    /* Ajustar leyenda para mejor visibilidad */
    .leaflet-control-attribution {
        background-color: rgba(255, 255, 255, 0.7) !important;
        padding: 2px 5px !important;
        border-radius: 3px !important;
        font-size: 10px !important;
    }
    
    /* Estilos para la leyenda del mapa Folium */
    iframe .leaflet-control.leaflet-control-layers {
        background-color: rgba(45, 55, 72, 0.9) !important;
        box-shadow: 0 1px 5px rgba(0, 0, 0, 0.4) !important;
        border-radius: 4px !important;
        color: #f8f9fa !important;
    }
    
    /* Asegurar que los textos en la leyenda sean legibles */
    iframe body .leaflet-control-layers-overlays span,
    iframe body .leaflet-control-layers-overlays label {
        color: #f8f9fa !important;
        text-shadow: 0 0 2px #000 !important;
    }
    
    /* Corregir colores de la leyenda */
    iframe body .leaflet-control-layers {
        background-color: #1a202c !important;
        color: #f8f9fa !important;
        border: 1px solid #4a5568 !important;
    }
    
    /* Estilos para estilizar elementos dentro del iframe */
    iframe body .info.legend {
        background-color: rgba(26, 32, 44, 0.8) !important;
        color: #f8f9fa !important;
        padding: 8px !important;
        border-radius: 4px !important;
        box-shadow: 0 1px 5px rgba(0, 0, 0, 0.4) !important;
    }
    
    iframe body .info.legend i {
        opacity: 1 !important;
    }
    
    /* Estilo para etiquetas en el mapa */
    iframe body .leaflet-tooltip {
        background-color: rgba(26, 32, 44, 0.8) !important;
        color: #f8f9fa !important;
        border: 1px solid #4a5568 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
    }
    
    /* Espaciado para controles de radio y checks */
    .stRadio > div {
        margin-bottom: 0.25rem !important;
    }
    
    /* Estilo para el sidebar */
    [data-testid="stSidebar"] {
        padding-top: 2rem !important;
        background-color: #111827 !important;
    }
    
    /* Ocultar footer */
    footer {
        visibility: hidden !important;
    }

    /* NUEVOS ESTILOS PARA LA APLICACIÓN - OPTIMIZADOS */
    
    /* Títulos de secciones */
    h2 {
        margin-bottom: 0.5rem !important;
        font-weight: 600;
    }
    
    /* Optimizar espacio en párrafos */
    p {
        margin: 0.25rem 0 !important;
    }
    
    /* Estilos para iframe de los mapas */
    iframe[data-testid="stHorizontalBlock"] {
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
    }
    
    /* Estilos para las métricas - igualar alturas */
    [data-testid="metric-container"] {
        background-color: rgba(30, 41, 59, 0.7) !important;
        border-radius: 8px !important;
        padding: 1.25rem !important;
        height: 140px !important;
        min-height: 140px !important;
        max-height: 140px !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        gap: 5px !important;
        overflow: hidden !important;
    }
    
    /* Forzar alineación de contenedores de métricas dentro de columnas */
    [data-testid="column"]:has([data-testid="metric-container"]) {
        display: flex !important;
        align-items: stretch !important;
    }
    
    /* Hacer que las métricas ocupen todo el espacio disponible */
    [data-testid="column"] > div:has([data-testid="metric-container"]) {
        height: 100% !important;
        flex-grow: 1 !important;
    }
    
    /* Asegurar que todas las métricas dentro de una fila tengan la misma altura */
    [data-testid="stHorizontalBlock"]:has([data-testid="metric-container"]) {
        align-items: stretch !important;
        display: flex !important;
    }
    
    /* Ajustar tamaño del título de métricas */
    [data-testid="metric-container"] label {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    /* Ajustar tamaño del valor principal */
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        padding: 0.25rem 0 !important;
    }
    
    /* Forzar ancho completo para el contenedor de métricas */
    .element-container:has([data-testid="metric-container"]) {
        width: 100% !important;
    }
    
    /* Estilos específicos para el dashboard nacional */
    [data-testid="tabs-header"] {
        gap: 0.5rem !important;
    }
    
    [data-testid="tabs-header-container"] {
        margin-bottom: 0.5rem !important;
    }
    
    [data-testid="tabs-header"] button {
        padding: 0.5rem 1rem !important;
    }
    
    /* Ajustar estilos para las gráficas */
    .chart-container {
        background-color: rgba(30, 41, 59, 0.5);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.75rem !important;
    }
    
    /* Reducir espaciado entre componentes en el dashboard */
    [data-testid="stHorizontalBlock"] {
        margin-bottom: 0.75rem !important;
        gap: 0.75rem !important;
    }
    
    /* Espacio específico para las secciones de gráficos */
    div.stSubheader {
        margin-top: 0.75rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Reducir espacio adicional entre tablas y gráficos */
    .element-container + .element-container:has(div.stDataFrame) {
        margin-top: 0.75rem !important;
    }
    
    /* Reducir espaciado después de los gráficos */
    [data-testid="block-container"] > div > [data-testid="stVerticalBlock"] > div:has(.chart-container) {
        margin-bottom: 0.75rem !important;
    }
    
    /* Quitar separadores en pestañas */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 0.25rem !important;
    }
    
    /* Evitar espacios excesivos en dataframes */
    [data-testid="stDataFrame"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Ajustar espacio después de los encabezados de sección */
    h3 {
        margin-top: 0.75rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Optimizar separadores horizontales */
    hr {
        margin: 0.75rem 0 !important;
        border: 0;
        height: 1px;
        background-color: #2d3748;
    }
    
    /* Estilos para los selectores en la interfaz */
    [data-testid="stSelectbox"] {
        margin-bottom: 0.5rem !important;
    }
    
    /* Optimizar espacio para radio buttons */
    [data-testid="stHorizontalRadio"] {
        margin-bottom: 0.5rem !important;
    }
    
    /* Optimizar checkbox */
    [data-testid="stCheckbox"] {
        margin-bottom: 0.25rem !important;
    }
    
    /* Optimizar columnas */
    [data-testid="column"] {
        padding: 0.25rem !important;
    }
    
    /* Optimizar contenedores de widgets */
    .stWidgetLabel {
        margin-bottom: 0 !important;
    }

    /* Ajustar espacios en el dashboard nacional */
    div [data-testid="stVerticalBlock"] div [data-testid="stVerticalBlock"] {
        padding: 0.25rem !important;
        gap: 0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Aplicar CSS adicional directamente para manejar la leyenda del mapa
    st.markdown("""
    <style>
    /* Asegurar que el iframe del mapa tenga el tamaño correcto sin espacio extra */
    .element-container iframe {
        min-height: 600px !important;
        height: 100% !important;
        margin-bottom: 0 !important;
    }
    
    /* Estilos específicos para el mapa nacional */
    [data-testid="stFormSubmitter"] iframe {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Asegurar que el mapa nacional tenga el layout correcto */
    [key="national_map"] iframe,
    iframe[key="national_map"] {
        min-height: 700px !important;
    }
    
    /* Eliminar espacios adicionales en el contenedor del mapa */
    div.stHorizontalBlock {
        gap: 0 !important;
    }
    
    /* Ajustar margen inferior para los elementos que contienen mapas */
    .element-container:has(iframe) + .element-container {
        margin-top: 0.5rem !important;
    }
    </style>
    <script>
    // Función para inyectar estilos en el iframe después de que cargue
    const fixMapLegend = () => {
        // Obtener todos los iframes
        const iframes = document.querySelectorAll('iframe');
        
        // Para cada iframe, intentar acceder a su contenido y modificar los estilos
        iframes.forEach(iframe => {
            try {
                // Esperar a que el iframe cargue
                iframe.onload = function() {
                    try {
                        // Crear una hoja de estilo para insertar en el iframe
                        const style = document.createElement('style');
                        style.textContent = `
                            .leaflet-control-layers {
                                background-color: #1a202c !important;
                                color: #f8f9fa !important;
                                border: 1px solid #4a5568 !important;
                            }
                            .leaflet-control-layers-overlays span,
                            .leaflet-control-layers-overlays label {
                                color: #f8f9fa !important;
                                text-shadow: 0 0 2px #000 !important;
                            }
                            .info.legend {
                                background-color: rgba(26, 32, 44, 0.8) !important;
                                color: #f8f9fa !important;
                                padding: 8px !important;
                                border-radius: 4px !important;
                                box-shadow: 0 1px 5px rgba(0, 0, 0, 0.4) !important;
                            }
                        `;
                        
                        // Insertar la hoja de estilo en el iframe
                        iframe.contentDocument.head.appendChild(style);
                    } catch (e) {
                        console.error('Error al aplicar estilos a iframe:', e);
                    }
                };
            } catch (e) {
                console.error('Error al acceder al iframe:', e);
            }
        });
    };
    
    // Ejecutar la función cuando la página esté cargada
    window.addEventListener('load', fixMapLegend);
    // También ejecutar periódicamente para capturar iframes añadidos dinámicamente
    setInterval(fixMapLegend, 2000);
    </script>
    """, unsafe_allow_html=True)

def get_container_style(style_type="default"):
    """
    Devuelve las propiedades CSS para un tipo específico de contenedor.
    
    Args:
        style_type (str): Tipo de estilo ('default', 'info', 'chart', 'map', etc.)
        
    Returns:
        str: CSS styles para usar con stylable_container
    """
    styles = {
        "default": """
            {
                background-color: rgba(30, 41, 59, 0.5);
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 10px;
            }
        """,
        "info": """
            {
                background-color: rgba(59, 130, 246, 0.1);
                border-left: 5px solid #3B82F6;
                padding: 10px;
                border-radius: 3px;
                margin: 10px 0px;
            }
        """,
        "chart": """
            {
                background-color: rgba(30, 41, 59, 0.5);
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 10px;
            }
        """,
        "map_controls": """
            {
                background-color: rgba(30, 41, 59, 0.5);
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 10px;
            }
        """,
        "map_container": """
            {
                background-color: rgba(30, 41, 59, 0.5);
                border-radius: 10px;
                padding: 0px;
                margin-bottom: 10px;
                overflow: hidden;
            }
        """,
        "info_panel": """
            {
                background-color: rgba(30, 41, 59, 0.7);
                border-radius: 10px;
                padding: 10px;
                border-left: 5px solid #3B82F6;
                margin-bottom: 10px;
            }
        """,
        "footer": """
            {
                background-color: rgba(30, 41, 59, 0.3);
                border-radius: 5px;
                padding: 10px;
                text-align: center;
                margin-top: 20px;
            }
        """,
        "filter_container": """
            {
                background-color: rgba(59, 130, 246, 0.05);
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 10px;
            }
        """
    }
    
    return styles.get(style_type, styles["default"])

def create_card_container(title=None):
    """
    Genera el HTML para abrir un contenedor tipo tarjeta con título opcional
    
    Args:
        title (str): Título opcional para la tarjeta
    
    Returns:
        str: HTML para el inicio de un contenedor de tarjeta
    """
    html = '<div class="dashboard-card">'
    if title:
        html += f'<p class="card-title">{title}</p>'
    return html

def close_container():
    """
    Devuelve el HTML para cerrar un contenedor
    
    Returns:
        str: HTML para cerrar un div
    """
    return '</div>'

def create_metric_card(title, value, delta=None):
    """
    Genera el HTML para una tarjeta de métrica
    
    Args:
        title (str): Título de la métrica
        value (str): Valor principal de la métrica
        delta (str, opcional): Valor de cambio (positivo/negativo)
        
    Returns:
        str: HTML para la tarjeta de métrica
    """
    html = '<div class="metric-container">'
    html += f'<div class="metric-title">{title}</div>'
    html += f'<div class="metric-value">{value}</div>'
    
    if delta:
        # Determinar si es positivo o negativo para el color
        delta_class = "positive" if delta.startswith("+") else "negative" if delta.startswith("-") else "neutral"
        html += f'<div class="metric-delta {delta_class}">{delta}</div>'
    
    html += '</div>'
    return html 