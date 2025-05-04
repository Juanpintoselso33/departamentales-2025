"""
Componentes de gráficos para la interfaz de usuario.
Proporciona elementos visuales para representación de datos.
"""

import streamlit as st
import pandas as pd
from settings.theme import PARTY_COLORS
from streamlit_echarts import st_echarts

def create_vote_distribution_chart(vote_data, title="Distribución de votos", show_percentages=False):
    """
    Crea opciones para un gráfico de barras horizontal en ECharts.
    
    Args:
        vote_data (dict): Diccionario con partidos como clave y valores como valores
        title (str): Título del gráfico
        show_percentages (bool): Si True, muestra valores en porcentaje
    """
    # Verificar si hay datos
    if not vote_data:
        return {"title": {"text": "No hay datos disponibles"}}
    
    partes = list(vote_data.keys())
    valores = list(vote_data.values())
    
    # Mapear color por partido
    bar_data = []
    for partido, valor in vote_data.items():
        bar_data.append({
            "value": valor,
            "itemStyle": {"color": PARTY_COLORS.get(partido, "#888888")},
            "name": partido  # Añadir nombre para tooltip
        })

    # Determinar el valor máximo para ajustar la escala
    max_value = max(valores) if valores else 0
    axis_max = max(max_value * 1.2, 1)  # 20% extra para evitar overflow
    
    # Determinar etiqueta del eje según lo que mostramos
    axis_label = "Cantidad" if not show_percentages else "Porcentaje"
    
    # Configurar etiquetas para las barras
    label_config = {
        "show": True, 
        "position": "right",
        "formatter": "{c}" if not show_percentages else "{c}%",
        "color": "#ffffff",
        "fontSize": 10,  # Reducir tamaño de fuente
        "textBorderWidth": 2,
        "textBorderColor": "rgba(0,0,0,0.3)",
        "textShadowColor": "rgba(0,0,0,0.5)",
        "textShadowBlur": 3
    }
    
    # Crear las opciones del gráfico
    options = {
        "backgroundColor": "transparent",
        "textStyle": {"color": "#fff"},
        "tooltip": {
            "trigger": "axis", 
            "axisPointer": {
                "type": "shadow",
                "shadowStyle": {
                    "color": "rgba(150,150,150,0.1)"
                }
            }, 
            "backgroundColor": "rgba(50,50,50,0.9)", 
            "borderColor": "#333",
            "borderWidth": 1,
            "textStyle": {"color": "#fff"},
            "formatter": "{b}: {c}" if not show_percentages else "{b}: {c}%"
        },
        "legend": {
            "show": True,
            "type": "scroll",
            "orient": "horizontal",
            "bottom": 0,
            "left": "center",
            "data": partes,
            "textStyle": {"color": "#fff", "fontSize": 10},
            "pageTextStyle": {"color": "#fff"},
            "pageIconColor": "#fff",
            "pageIconInactiveColor": "#888",
            "itemWidth": 12,
            "itemHeight": 8,
            "itemGap": 4,
            "padding": [2, 2, 2, 2]
        },
        "grid": {
            "left": "5%", 
            "right": "5%", 
            "top": "2%",
            "bottom": "15%",
            "containLabel": True, 
            "backgroundColor": "rgba(40,50,70,0.4)",
            "borderColor": "rgba(160,160,160,0.2)",
            "borderWidth": 1,
            "shadowColor": "rgba(0,0,0,0.5)",
            "shadowBlur": 5
        },
        "xAxis": {
            "type": "value", 
            "name": "",  # Eliminar la etiqueta de eje X
            "nameTextStyle": {
                "color": "#fff",
                "fontSize": 12,
                "padding": [0, 0, 0, 5]
            }, 
            "axisLine": {"lineStyle": {"color": "#ccc"}}, 
            "axisLabel": {"color": "#eee"},
            "max": axis_max,  # Establecer máximo con espacio extra
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "rgba(120,120,120,0.2)"
                }
            }
        },
        "yAxis": {
            "type": "category", 
            "data": partes, 
            "inverse": True, 
            "axisLine": {"lineStyle": {"color": "#ccc"}}, 
            "axisLabel": {
                "color": "#eee",
                "fontWeight": "bold",
                "fontSize": 12
            },
            "axisTick": {"alignWithLabel": True}
        },
        "series": [{
            "type": "bar", 
            "data": bar_data,
            "label": label_config,
            "barMaxWidth": "50%",  # Limitar ancho máximo de las barras
            "itemStyle": {
                "borderRadius": [0, 4, 4, 0],
                "shadowColor": "rgba(0,0,0,0.3)",
                "shadowBlur": 5
            },
            "emphasis": {
                "itemStyle": {
                    "shadowColor": "rgba(0,0,0,0.5)",
                    "shadowBlur": 10
                }
            },
            "animationDuration": 1200,
            "animationEasing": "elasticOut"
        }]
    }
    return options

def create_party_pie_chart(data, show_percentages=True):
    """
    Crea opciones para un gráfico de torta en ECharts.
    
    Args:
        data (dict): Diccionario con partidos como clave y votos/porcentajes como valores
        show_percentages (bool): Si True, muestra valores en porcentajes
    
    Returns:
        dict: Opciones para ECharts
    """
    # Verificar si hay datos
    if not data:
        return {"title": {"text": "No hay datos disponibles"}}
    
    # Extraer partidos y valores
    partidos = list(data.keys())
    valores = list(data.values())
    
    # Mapear color por partido
    pie_data = []
    for partido, valor in data.items():
        pie_data.append({
            "name": partido,
            "value": valor,
            "itemStyle": {"color": PARTY_COLORS.get(partido, "#888888")}
        })

    # Calcular total para porcentajes, si es necesario
    total = sum(valores)
    formatter = "{b}: {c}" if not show_percentages else "{b}: {c} ({d}%)"

    options = {
        "backgroundColor": "transparent",
        "textStyle": {"color": "#fff"},
        "tooltip": {
            "trigger": "item", 
            "backgroundColor": "rgba(50,50,50,0.9)",
            "borderColor": "#333",
            "borderWidth": 1,
            "textStyle": {"color": "#fff"},
            "formatter": formatter
        },
        "legend": {
            "show": False,  # Ocultamos la leyenda por defecto
            "type": "scroll",
            "orient": "horizontal",
            "bottom": 0,
            "data": partidos,
            "textStyle": {"color": "#fff"},
            "pageTextStyle": {"color": "#fff"},
            "pageIconColor": "#fff",
            "pageIconInactiveColor": "#888"
        },
        "series": [{
            "type": "pie",
            "radius": ["40%", "70%"],  # Tipo donut
            "center": ["50%", "40%"],  # Centrar en la parte superior
            "avoidLabelOverlap": True,
            "itemStyle": {
                "borderRadius": 4,
                "borderColor": "rgba(20,20,20,0.2)",
                "borderWidth": 1,
                "shadowColor": "rgba(0,0,0,0.3)",
                "shadowBlur": 5
            },
            "label": {
                "show": True,
                "formatter": "{b}: {d}%",
                "color": "#fff",
                "fontWeight": "bold",
                "fontSize": 12,
                "textBorderWidth": 2,
                "textBorderColor": "rgba(0,0,0,0.3)",
                "textShadowColor": "rgba(0,0,0,0.5)",
                "textShadowBlur": 3
            },
            "labelLine": {
                "show": True,
                "lineStyle": {
                    "color": "rgba(255,255,255,0.5)"
                },
                "smooth": 0.2,
                "length": 10,
                "length2": 15
            },
            "data": pie_data,
            "emphasis": {
                "itemStyle": {
                    "shadowBlur": 10,
                    "shadowOffsetX": 0,
                    "shadowColor": "rgba(0, 0, 0, 0.5)"
                },
                "label": {
                    "fontSize": 14
                }
            },
            "animationType": "scale",
            "animationEasing": "elasticOut",
            "animationDuration": 1200
        }]
    }
    return options

def create_party_legend(parties=None):
    """
    Crea una leyenda centralizada para partidos políticos usando ECharts.
    
    Args:
        parties (list): Lista de partidos a mostrar. Si es None, muestra todos los partidos definidos.
        
    Returns:
        dict: Configuración de ECharts para la leyenda
    """
    if parties is None:
        # Usar todos los partidos con colores definidos
        parties = list(PARTY_COLORS.keys())
    
    # Crear datos ficticios para el gráfico (no se mostrará)
    fake_data = []
    for party in parties:
        fake_data.append({
            "name": party, 
            "value": 1,
            "itemStyle": {"color": PARTY_COLORS.get(party, "#888888")}
        })
    
    # Configuración de la leyenda centralizada - optimizada para mejor distribución
    options = {
        "backgroundColor": "transparent",
        "series": [{
            "type": "pie",
            "radius": 0,  # Radio 0 para que no se muestre el gráfico
            "center": ["50%", "-50%"],  # Fuera de la vista
            "data": fake_data,
            "label": {"show": False},
            "silent": True  # No interactivo
        }],
        "legend": {
            "type": "plain",  # Usar plain en lugar de scroll para mostrar todo
            "orient": "horizontal",
            "top": "center",
            "left": "center", 
            "data": parties,
            "textStyle": {"color": "#fff"},
            "itemWidth": 15,
            "itemHeight": 15,
            "itemGap": 15,  # Más espacio entre elementos
            "selectedMode": False,  # Evitar que items se desactiven al hacer clic
            "padding": [10, 5, 10, 5],  # Padding para dar más espacio
            "align": "auto",
            "width": "90%",
            "wrap": True,  # Permitir múltiples filas
            "pageButtonGap": 10,
            "selectorLabel": {
                "show": False
            }
        }
    }
    
    return options

def create_bar_chart(data, x_field, y_field, title='', color_field=None, horizontal=False):
    """Alias de create_vote_distribution_chart para uniformidad."""
    vote_data = {row[x_field]: row[y_field] for _, row in data.iterrows()} if hasattr(data, 'iterrows') else data
    return create_vote_distribution_chart(vote_data, title)

def create_comparison_chart(data_list, labels=None, title="Comparación", stacked=False):
    """Crea opciones para gráfico de comparación apilado o agrupado en ECharts."""
    series = []
    for i, data in enumerate(data_list):
        values = list(data.values())
        series.append({"name": (labels or [])[i] if labels else f"Conjunto {i+1}", "type": "bar", "data": values})
    options = {
        "title": {"text": title, "left": "center"},
        "legend": {"bottom": 0},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": list(data_list[0].keys()) if data_list else []},
        "yAxis": {"type": "value"},
        "series": series,
        "seriesLayoutBy": stacked and "row" or "column",
        "dataset": stacked and {"dimensions": []} or None
    }
    return options

def render_chart(chart, use_container_width=True, height="180px"):
    """
    Renderiza un gráfico en Streamlit con opciones comunes.
    
    Args:
        chart: El objeto gráfico (altair, plotly, etc.)
        use_container_width (bool): Si es True, usa el ancho completo del contenedor
        height (str): Altura del gráfico en formato CSS (ej: "180px")
    """
    if isinstance(chart, dict):
        # Renderizar ECharts con altura personalizable
        st_echarts(
            options=chart, 
            height=height,
            width="100%" if use_container_width else None
        )
    else:
        st.error("Tipo de gráfico no soportado, solo ECharts está habilitado ahora.")

# -------------------------------------
# ECharts: gráfico de distribución de votos
def create_vote_distribution_echarts(vote_data, title="Distribución de votos"):
    """
    Crea la configuración de un gráfico de barras horizontal en ECharts.
    """
    partes = list(vote_data.keys())
    valores = list(vote_data.values())
    options = {
        "title": {"text": title, "left": "center"},
        "color": list(PARTY_COLORS.values()),
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "xAxis": {"type": "value", "name": "Porcentaje de votos"},
        "yAxis": {"type": "category", "data": partes, "inverse": True},
        "series": [{"type": "bar", "data": valores}]
    }
    return options

def render_echarts(options, height="400px", width="100%"):
    """
    Renderiza un gráfico de ECharts en Streamlit.
    """
    st_echarts(options, height=height, width=width) 