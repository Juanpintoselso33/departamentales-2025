"""
Componente generador de mapas electorales.
Crea mapas interactivos o estáticos con datos electorales.
"""

import streamlit as st
import leafmap.foliumap as leafmap
import geopandas as gpd
from typing import Dict, Any, Optional, Callable
import folium
import pandas as pd
import numpy as np
import json
import matplotlib as mpl
import matplotlib.pyplot as plt

from settings.theme import PARTY_COLORS, get_party_color, get_percentage_color
from settings.settings import DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM, PERCENTAGE_COLORMAP, DEPARTMENT_NAME_MAPPING, MAP_BOUNDS
from domain.transformers import get_display_department_name, normalize_department_name, find_matching_name, normalize_for_comparison

def clean_dataframe_for_json(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Limpia el DataFrame para asegurar que todos los datos sean serializables a JSON.
    
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame original
        
    Returns:
        gpd.GeoDataFrame: GeoDataFrame limpio
    """
    def convert_to_serializable(val):
        """Convierte valores a tipos serializables."""
        if isinstance(val, (np.integer, np.floating)):
            return val.item()
        elif isinstance(val, np.ndarray):
            return val.tolist()
        elif pd.isna(val):
            return None
        return val
    
    # Crear una copia para no modificar el original
    clean_gdf = gdf.copy()
    
    # Convertir timestamps a strings y otros tipos a serializables
    for col in clean_gdf.columns:
        if pd.api.types.is_datetime64_any_dtype(clean_gdf[col]):
            clean_gdf[col] = clean_gdf[col].astype(str)
        elif clean_gdf[col].dtype == 'object':
            # Convertir cualquier timestamp que pueda estar como objeto
            try:
                clean_gdf[col] = pd.to_datetime(clean_gdf[col]).astype(str)
            except:
                # Si no es timestamp, intentar convertir valores numpy
                clean_gdf[col] = clean_gdf[col].map(convert_to_serializable)
        else:
            # Convertir otros tipos de numpy
            clean_gdf[col] = clean_gdf[col].map(convert_to_serializable)
    
    # Mantener solo las columnas necesarias
    essential_columns = ['depto', 'geometry']
    optional_columns = ['winning_party', 'vote_percentage', 'color']
    
    # Filtrar columnas
    columns_to_keep = essential_columns + [col for col in optional_columns if col in clean_gdf.columns]
    clean_gdf = clean_gdf[columns_to_keep]
    
    return clean_gdf

def normalize_department_names(gdf: gpd.GeoDataFrame, name_column: str) -> gpd.GeoDataFrame:
    """
    Normaliza los nombres de departamentos en el GeoDataFrame.
    
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame con datos departamentales
        name_column (str): Nombre de la columna que contiene los nombres
        
    Returns:
        gpd.GeoDataFrame: GeoDataFrame con nombres normalizados
    """
    # Crear copia para no modificar el original
    normalized_gdf = gdf.copy()
    
    # Normalizar nombres usando el mapeo
    normalized_gdf[name_column] = normalized_gdf[name_column].map(
        lambda x: DEPARTMENT_NAME_MAPPING.get(x.upper(), x.title())
    )
    
    return normalized_gdf

def load_geojson(path: str) -> dict:
    """
    Carga un archivo GeoJSON y lo devuelve como diccionario.
    Corrige problemas de codificación en las propiedades del GeoJSON.
    """
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
        # Corregir nombres de departamentos en propiedades
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            if "name" in props:
                # Obtener el nombre original
                original_name = props["name"]
                
                # Obtener el nombre para visualización usando la función centralizada
                display_name = get_display_department_name(original_name)
                
                # Actualizar propiedades
                props["name"] = display_name
                props["display_name"] = display_name
        
        return data

def get_winning_party_style(feature: dict, election_data: Dict[str, Any]) -> dict:
    """Función de estilo para partido ganador (para Folium)."""
    name = feature['properties'].get('name', 'Desconocido') # Usar .get()
    party_data = election_data.get(name, {})
    if not party_data:
        matching_name = find_matching_name(name, list(election_data.keys()))
        if matching_name:
            party_data = election_data.get(matching_name, {})
    party = party_data.get('winning_party', 'No disponible')
    color = get_party_color(party)
    return {'fillColor': color, 'weight': 0.5, 'opacity': 1, 'color': 'white', 'fillOpacity': 0.7}

def get_percentage_style(feature: dict, election_data: Dict[str, Any]) -> dict:
    """Función de estilo para porcentaje de votos."""
    name = feature['properties']['name'].title()
    percentage = election_data.get(name, {}).get('vote_percentage', 0)
    return {
        'fillColor': get_percentage_color(percentage),
        'weight': 1,
        'opacity': 1,
        'color': 'white',
        'fillOpacity': 0.7
    }

def create_department_choropleth(
    geojson_path: str,
    election_data: Dict[str, Any],
    field: str = "winning_party", # No usado realmente, pero mantenido
    highlight_department: str = None,
    width='100%',
    height='100%',
    zoom_start=6.5, # Se usará si fit_bounds falla
    min_zoom=7, # Mantenido por si acaso
    **kwargs
) -> folium.Map:
    """
    Crea un mapa ESTÁTICO de coropletas (sin fondo ni zoom/pan) usando Folium.
    Intenta ajustar la vista con fit_bounds.
    Crea un mapa de coropletas departamental usando Folium, permitiendo zoom y desplazamiento.
    Intenta ajustar la vista inicial con fit_bounds.
    """
    print("[MAPGEN DEBUG] Usando versión Folium de create_department_choropleth.")
    try:
        geojson_data = load_geojson(str(geojson_path))

        m = folium.Map(
            location=[-32.8, -56.0], # Ubicación inicial por si fit_bounds falla
            zoom_start=zoom_start,
            # tiles=None, # Quitado para usar capa base
            # bgcolor='white', # Quitado para usar capa base
            width=width,
            height=height,
            control_scale=True, # Habilitado para contexto
            min_zoom=min_zoom,
            zoom_control=True, # Habilitado
            scrollWheelZoom=True, # Habilitado
            dragging=True, # Habilitado
            doubleClickZoom=True, # Habilitado
            attribution_control=True # Habilitado
        )

        # Añadir capa base de mosaicos
        folium.TileLayer("CartoDB positron", name="Mapa Base", control=False).add_to(m)

        def style_function(feature):
            base_style = get_winning_party_style(feature, election_data)
            # Asegurarse que feature['properties'] existe
            props = feature.get('properties', {})
            name = props.get('name', '') # Acceso seguro
            if highlight_department and name == highlight_department:
                 base_style['fillOpacity'] = 0.9
                 base_style['weight'] = 2
                 base_style['color'] = '#000000' # Borde negro para resaltar
            return base_style

        geojson_layer = folium.GeoJson(
            geojson_data,
            style_function=style_function,
            name='Departamentos'
        ).add_to(m)

        # Ajustar la vista a los límites de la capa GeoJSON añadida
        try:
             print("[MAPGEN DEBUG] Intentando fit_bounds...")
             m.fit_bounds(geojson_layer.get_bounds())
             print("[MAPGEN DEBUG] fit_bounds completado.")
        except Exception as e_bounds:
             print(f"[MAPGEN WARNING] fit_bounds falló: {e_bounds}. Usando location/zoom inicial.")
             # Si fit_bounds falla, confiaremos en location/zoom_start

        return m

    except Exception as e:
        print(f"[MAPGEN ERROR] Error FATAL generando mapa Folium: {e}")
        st.error(f"Error al generar mapa Folium: {e}")
        # Devolver un mapa vacío o de error si falla críticamente
        m = folium.Map(location=[-32.8, -56.0], zoom_start=6, tiles=None, bgcolor='lightgrey')
        folium.Marker(
            location=[-32.8, -56.0],
            popup=f"Error al generar mapa: {e}"
        ).add_to(m)
        return m

def get_municipality_style(feature: dict, muni_data: Dict[str, Any]) -> dict:
    """Función de estilo para municipios."""
    name = feature['properties']['name']
    party = muni_data.get(name, {}).get('party', 'No disponible')
    return {
        'fillColor': get_party_color(party),
        'weight': 1,
        'opacity': 1,
        'color': 'white',
        'fillOpacity': 0.7
    }

def get_department_border_style(feature: dict, department_name: str) -> dict:
    """Función de estilo para borde departamental."""
    name = feature['properties']['name']
    return {
        'fillColor': 'none',
        'color': 'black' if name == department_name else 'none',
        'weight': 2 if name == department_name else 0,
        'fillOpacity': 0
    }

def create_municipality_map(
    muni_geojson: str,
    dept_geojson: str,
    election_data: Dict[str, Any],
    department_name: str,
    show_labels: bool = True,
    show_legend: bool = True
) -> leafmap.Map:
    """
    Crea un mapa de municipios usando Leafmap.
    
    Args:
        muni_geojson (str): Ruta al archivo GeoJSON de municipios
        dept_geojson (str): Ruta al archivo GeoJSON de departamentos
        election_data (dict): Datos electorales
        department_name (str): Nombre del departamento a mostrar
        show_labels (bool): Si True, muestra etiquetas
        show_legend (bool): Si True, muestra leyenda
        
    Returns:
        leafmap.Map: Mapa de Leafmap con municipios
    """
    # Cargar GeoJSON
    muni_geojson_data = load_geojson(str(muni_geojson))
    dept_geojson_data = load_geojson(str(dept_geojson))
    
    # Crear mapa base con opciones restringidas
    m = folium.Map(
        center=DEFAULT_MAP_CENTER,
        zoom=DEFAULT_MAP_ZOOM,
        draw_control=False,
        measure_control=False,
        fullscreen_control=True,
        attribution_control=True,
        scale_control=False,
        max_zoom=9,      # Limitar el zoom máximo
        min_zoom=6.5,    # Limitar el zoom mínimo (más restrictivo, no se puede alejar tanto)
        zoom_control=True,
        locate_control=False,
        search_control=False
    )
    
    # Configurar estilo base del mapa
    folium.TileLayer("CartoDB positron", name="CartoDB.Positron", control=False).add_to(m)
    
    # Establecer límites de navegación para no salirse de Uruguay
    m.fit_bounds(MAP_BOUNDS)
    
    # Leer datos del departamento
    dept_data = election_data.get(department_name, {})
    muni_data = dept_data.get('municipalities', {})
    
    # Función para tooltip personalizado de municipios
    tooltip = folium.GeoJsonTooltip(
        fields=["display_name"],
        aliases=[""],
        style=("background-color: rgba(50,50,50,0.8); color: white; font-family: Arial, sans-serif; "
               "font-size: 12px; padding: 5px; border-radius: 3px; box-shadow: 0 0 5px rgba(0,0,0,0.5);")
    )
    
    # Añadir capa de municipios
    folium_muni_layer = folium.GeoJson(
        data=muni_geojson_data,
        style_function=lambda x: get_municipality_style(x, muni_data),
        highlight_function=lambda x: {"fillOpacity": 0.9},
        tooltip=tooltip
    )
    m.add_layer(folium_muni_layer)
    
    # Añadir contorno del departamento
    folium_dept_layer = folium.GeoJson(
        data=dept_geojson_data,
        style_function=lambda x: get_department_border_style(x, department_name)
    )
    m.add_layer(folium_dept_layer)
    
    # Añadir leyenda si se solicita
    if show_legend:
        # Recopilar partidos únicos
        unique_parties = set()
        for data in muni_data.values():
            party = data.get('party', 'No disponible')
            if party:
                unique_parties.add(party)
        
        # Ordenar partidos para mostrarlos en orden consistente
        sorted_parties = sorted(list(unique_parties))
        
        # Crear diccionario de leyenda con colores correctos
        legend_dict = {}
        for party in sorted_parties:
            color = get_party_color(party)
            legend_dict[party] = color
        
        # Agregar leyenda
        m.add_legend(title="Partidos Políticos", legend_dict=legend_dict)
    
    # Añadir etiquetas si se solicita
    if show_labels:
        gdf = gpd.read_file(str(muni_geojson))
        gdf = gdf[gdf['department'] == department_name]
        for idx, row in gdf.iterrows():
            centroid = row.geometry.centroid
            m.add_text(
                text=row['name'],
                xy=(centroid.x, centroid.y),
                font_size="10pt",
                font_family="Arial",
                font_weight="bold"
            )
    
    return m 

def create_tooltip_html(feature):
    """
    Crea un tooltip HTML personalizado para los departamentos.
    
    Args:
        feature (dict): Feature del GeoJSON
        
    Returns:
        str: HTML para mostrar en el tooltip
    """
    properties = feature.get("properties", {})
    name = properties.get("display_name", properties.get("name", ""))
    
    html = f"""
    <div style="font-family: Arial, sans-serif; font-size: 12px; padding: 5px; 
               background-color: rgba(50,50,50,0.8); color: white; 
               border-radius: 3px; box-shadow: 0 0 5px rgba(0,0,0,0.5);">
        <strong>{name}</strong>
    </div>
    """
    return html 