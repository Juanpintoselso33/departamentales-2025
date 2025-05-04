"""
Componentes de tablas para la interfaz de usuario.
Proporciona elementos visuales para mostrar datos tabulares.
"""

import streamlit as st
import pandas as pd
from settings.theme import PARTY_COLORS

def display_dataframe(df, title=None, hide_index=True, column_config=None, use_container_width=True):
    """
    Muestra un DataFrame con opciones personalizadas
    
    Args:
        df (pd.DataFrame): DataFrame a mostrar
        title (str, opcional): Título para la tabla
        hide_index (bool): Si True, oculta la columna de índice
        column_config (dict): Configuración para las columnas (formateo, estilo, etc.)
        use_container_width (bool): Si True, usa el ancho completo del contenedor
    """
    # Mostrar título si se proporciona
    if title:
        st.subheader(title)
    
    # Mostrar el DataFrame con las opciones especificadas
    st.dataframe(
        df,
        hide_index=hide_index,
        column_config=column_config,
        use_container_width=use_container_width
    )

def display_results_table(data, title="Resultados Electorales", include_percentage=True, include_votes=True):
    """
    Muestra una tabla formateada con resultados electorales
    
    Args:
        data (dict): Diccionario con datos electorales
        title (str): Título para la tabla
        include_percentage (bool): Si True, incluye columna de porcentajes
        include_votes (bool): Si True, incluye columna de votos totales
    """
    # Verificar que tenemos datos
    if not data:
        st.warning("No hay datos disponibles para mostrar.")
        return
    
    # Preparar datos para la tabla
    votes_data = data.get('votes', {})
    percentages_data = data.get('vote_percentages', {})
    seats_data = data.get('council_seats', {})
    
    # Crear DataFrame
    table_data = []
    
    for party, votes in votes_data.items():
        row = {
            'Partido': party,
        }
        
        if include_votes:
            row['Votos'] = votes
            
        if include_percentage:
            row['Porcentaje'] = f"{percentages_data.get(party, 0):.1f}%"
            
        if seats_data:
            row['Bancas'] = seats_data.get(party, 0)
            
        table_data.append(row)
    
    # Convertir a DataFrame
    df = pd.DataFrame(table_data)
    
    # Ordenar por votos descendentes
    if include_votes and not df.empty:
        df = df.sort_values('Votos', ascending=False)
    elif include_percentage and not df.empty:
        df = df.sort_values('Porcentaje', ascending=False)
    
    # Mostrar la tabla
    st.subheader(title)
    
    # Configurar columnas para formato
    column_config = {
        'Partido': st.column_config.TextColumn(
            "Partido Político",
            width="medium"
        )
    }
    
    if include_votes:
        column_config['Votos'] = st.column_config.NumberColumn(
            "Votos Totales",
            format="%d",
            width="small"
        )
        
    if include_percentage:
        column_config['Porcentaje'] = st.column_config.TextColumn(
            "% Votos",
            width="small"
        )
        
    if 'Bancas' in df.columns:
        column_config['Bancas'] = st.column_config.NumberColumn(
            "Bancas",
            format="%d",
            width="small"
        )
    
    # Mostrar el DataFrame
    st.dataframe(df, column_config=column_config, hide_index=True, use_container_width=True)

def display_comparison_table(data_list, labels=None, title="Comparación de Resultados"):
    """
    Muestra una tabla comparativa de resultados entre diferentes elecciones
    
    Args:
        data_list (list): Lista de diccionarios con datos electorales
        labels (list): Lista de etiquetas para cada conjunto de datos
        title (str): Título para la tabla
    """
    # Verificar que hay datos para comparar
    if not data_list:
        st.warning("No hay datos disponibles para comparar.")
        return
    
    # Crear etiquetas por defecto si no se proporcionan
    if labels is None:
        labels = [f"Conjunto {i+1}" for i in range(len(data_list))]
    
    # Asegurar que tenemos suficientes etiquetas
    while len(labels) < len(data_list):
        labels.append(f"Conjunto {len(labels)+1}")
    
    # Crear DataFrame para comparación
    comparison_data = {}
    all_parties = set()
    
    # Recopilar todos los partidos primero
    for data in data_list:
        if isinstance(data, dict) and 'vote_percentages' in data:
            all_parties.update(data['vote_percentages'].keys())
    
    # Preparar datos para cada partido en cada elección
    for party in all_parties:
        comparison_data[party] = []
        
        for i, data in enumerate(data_list):
            if isinstance(data, dict) and 'vote_percentages' in data:
                percentage = data['vote_percentages'].get(party, 0)
                comparison_data[party].append(f"{percentage:.1f}%")
            else:
                comparison_data[party].append("N/D")
    
    # Convertir a formato tabular
    table_data = []
    
    for party, percentages in comparison_data.items():
        row = {'Partido': party}
        for i, label in enumerate(labels):
            if i < len(percentages):
                row[label] = percentages[i]
        table_data.append(row)
    
    # Crear DataFrame
    df = pd.DataFrame(table_data)
    
    # Mostrar tabla
    st.subheader(title)
    st.dataframe(df, hide_index=True, use_container_width=True)

def display_party_color_table(parties, title="Partidos Políticos"):
    """
    Muestra una tabla con los partidos y sus colores representativos
    
    Args:
        parties (list): Lista de nombres de partidos
        title (str): Título para la tabla
    """
    # Crear DataFrame
    data = []
    
    for party in parties:
        color = PARTY_COLORS.get(party, "#CCCCCC")
        data.append({
            'Partido': party,
            'Color': color
        })
    
    df = pd.DataFrame(data)
    
    # Configurar columnas sin usar ColorColumn que no está disponible
    column_config = {
        'Partido': st.column_config.TextColumn("Partido Político"),
        # Usar TextColumn en lugar de ColorColumn
        'Color': st.column_config.TextColumn("Color Representativo")
    }
    
    # Mostrar tabla
    st.subheader(title)
    st.dataframe(df, column_config=column_config, hide_index=True)
    
    # Mostrar una visualización adicional de los colores
    st.markdown("### Referencia de colores")
    colors_html = "<div style='display: flex; flex-wrap: wrap; gap: 10px;'>"
    
    for party, color in PARTY_COLORS.items():
        if party in parties:
            colors_html += f"""
            <div style='display: flex; align-items: center; margin-bottom: 5px;'>
                <div style='width: 20px; height: 20px; background-color: {color}; margin-right: 8px; border: 1px solid #ddd;'></div>
                <span>{party}</span>
            </div>
            """
    
    colors_html += "</div>"
    st.markdown(colors_html, unsafe_allow_html=True) 