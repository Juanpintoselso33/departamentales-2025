"""
Dashboard para la comparación de datos electorales entre departamentos o años.
"""

import streamlit as st
import pandas as pd
import numpy as np

from app.components.ui.charts import create_comparison_chart, render_chart
from app.components.ui.tables import display_comparison_table
from app.components.ui.containers import section_container, tabs_container
from domain.summary import get_department_summary

def display_comparison_dashboard(election_data):
    """
    Muestra un dashboard para comparar datos electorales.
    
    Args:
        election_data (dict): Datos electorales completos
    """
    # Configurar el tipo de comparación
    comparison_type = st.radio(
        "Tipo de comparación",
        ["Entre departamentos", "Por partido"],
        horizontal=True,
        key="comparison_type"
    )
    
    # Mostrar la comparación adecuada según tipo
    if comparison_type == "Entre departamentos":
        display_department_comparison(election_data)
    else:
        display_party_comparison(election_data)

def display_department_comparison(election_data):
    """
    Muestra comparación entre departamentos seleccionados.
    
    Args:
        election_data (dict): Datos electorales completos
    """
    # Obtener lista de departamentos
    departments = list(election_data.keys())
    
    # Crear selector de departamentos
    selected_departments = st.multiselect(
        "Seleccionar departamentos a comparar",
        options=departments,
        default=departments[:2] if len(departments) >= 2 else departments,
        key="department_multiselect"
    )
    
    # Verificar que hay departamentos seleccionados
    if not selected_departments:
        st.warning("Seleccione al menos un departamento para comparar")
        return
    
    # Crear selector de métrica a comparar
    comparison_metric = st.selectbox(
        "Métrica a comparar",
        options=["Distribución de votos", "Composición de la Junta Departamental", "Participación electoral"],
        key="comparison_metric"
    )
    
    # Mostrar la comparación según métrica seleccionada
    if comparison_metric == "Distribución de votos":
        display_vote_distribution_comparison(election_data, selected_departments)
    elif comparison_metric == "Composición de la Junta Departamental":
        display_council_composition_comparison(election_data, selected_departments)
    else:
        st.info("Comparación de participación electoral no disponible en esta versión")

def display_vote_distribution_comparison(election_data, departments):
    """
    Muestra comparación de distribución de votos entre departamentos.
    
    Args:
        election_data (dict): Datos electorales completos
        departments (list): Lista de departamentos a comparar
    """
    # Obtener datos de cada departamento
    dept_data_list = []
    for dept in departments:
        dept_summary = get_department_summary(election_data, dept)
        if dept_summary and 'vote_percentages' in dept_summary:
            dept_data_list.append(dept_summary)
    
    # Verificar que hay datos
    if not dept_data_list:
        st.warning("No hay datos disponibles para los departamentos seleccionados")
        return
    
    # Mostrar comparación en pestañas
    tab_items = [
        {
            'title': "Gráfico de Comparación",
            'content_callable': lambda: display_vote_comparison_chart(dept_data_list, departments)
        },
        {
            'title': "Tabla Comparativa",
            'content_callable': lambda: display_vote_comparison_table(dept_data_list, departments)
        }
    ]
    
    tabs_container(tab_items)

def display_vote_comparison_chart(dept_data_list, dept_labels):
    """
    Muestra gráfico comparativo de votos entre departamentos.
    
    Args:
        dept_data_list (list): Lista de datos departamentales
        dept_labels (list): Lista de nombres de departamentos
    """
    # Preparar datos para el gráfico
    data_list = []
    
    for dept_data in dept_data_list:
        if 'vote_percentages' in dept_data:
            data_list.append(dept_data['vote_percentages'])
    
    # Verificar que hay datos
    if not data_list:
        st.warning("No hay datos disponibles para mostrar")
        return
    
    # Crear gráfico de comparación
    chart = create_comparison_chart(data_list, dept_labels, "Comparación de distribución de votos")
    render_chart(chart)

def display_vote_comparison_table(dept_data_list, dept_labels):
    """
    Muestra tabla comparativa de votos entre departamentos.
    
    Args:
        dept_data_list (list): Lista de datos departamentales
        dept_labels (list): Lista de nombres de departamentos
    """
    # Preparar datos para la tabla
    vote_percentages_list = []
    
    for dept_data in dept_data_list:
        if 'vote_percentages' in dept_data:
            vote_percentages_list.append(dept_data['vote_percentages'])
    
    # Verificar que hay datos
    if not vote_percentages_list:
        st.warning("No hay datos disponibles para mostrar")
        return
    
    # Mostrar tabla comparativa
    display_comparison_table(vote_percentages_list, dept_labels, "Comparación de Porcentajes por Departamento")

def display_council_composition_comparison(election_data, departments):
    """
    Muestra comparación de composición de la Junta Departamental.
    
    Args:
        election_data (dict): Datos electorales completos
        departments (list): Lista de departamentos a comparar
    """
    # Obtener datos de cada departamento
    dept_data_list = []
    for dept in departments:
        dept_summary = get_department_summary(election_data, dept)
        if dept_summary and 'council_seats' in dept_summary:
            dept_data_list.append(dept_summary)
    
    # Verificar que hay datos
    if not dept_data_list:
        st.warning("No hay datos disponibles para los departamentos seleccionados")
        return
    
    # Mostrar datos en columnas
    cols = st.columns(min(3, len(dept_data_list)))
    
    for i, dept_data in enumerate(dept_data_list):
        if i < len(cols):
            with cols[i % len(cols)]:
                display_council_summary(dept_data)

def display_council_summary(dept_data):
    """
    Muestra resumen de la Junta Departamental para un departamento.
    
    Args:
        dept_data (dict): Datos del departamento
    """
    # Obtener datos
    department = dept_data.get('department', 'Departamento')
    seats = dept_data.get('council_seats', {})
    
    if not seats:
        st.warning(f"No hay datos disponibles para {department}")
        return
    
    # Crear DataFrame
    df = pd.DataFrame({
        'Partido': list(seats.keys()),
        'Bancas': list(seats.values())
    })
    
    # Mostrar información
    section_container(
        department,
        lambda: st.dataframe(df, hide_index=True),
        style_type="default"
    )

def display_party_comparison(election_data):
    """
    Muestra comparación centrada en partidos políticos.
    
    Args:
        election_data (dict): Datos electorales completos
    """
    # Obtener lista de partidos únicos
    all_parties = set()
    for dept_data in election_data.values():
        if 'vote_percentages' in dept_data:
            all_parties.update(dept_data['vote_percentages'].keys())
    
    # Ordenar alfabéticamente
    all_parties = sorted(list(all_parties))
    
    # Crear selector de partidos
    selected_party = st.selectbox(
        "Seleccionar partido",
        options=all_parties,
        key="party_select"
    )
    
    # Mostrar mapa de calor o comparativa de departamentos
    display_party_performance(election_data, selected_party)

def display_party_performance(election_data, party):
    """
    Muestra el desempeño de un partido en todos los departamentos.
    
    Args:
        election_data (dict): Datos electorales completos
        party (str): Partido a analizar
    """
    # Recopilar datos del partido en cada departamento
    party_data = []
    
    for dept_name, dept_data in election_data.items():
        if 'vote_percentages' in dept_data and party in dept_data['vote_percentages']:
            percentage = dept_data['vote_percentages'][party]
            council_seats = dept_data.get('council_seats', {}).get(party, 0)
            is_winner = dept_data.get('winning_party') == party
            
            party_data.append({
                'Departamento': dept_name,
                'Porcentaje': percentage,
                'Bancas': council_seats,
                'Ganador': "Sí" if is_winner else "No"
            })
    
    # Verificar que hay datos
    if not party_data:
        st.warning(f"No hay datos disponibles para el partido {party}")
        return
    
    # Crear DataFrame
    df = pd.DataFrame(party_data)
    
    # Ordenar por porcentaje descendente
    df = df.sort_values('Porcentaje', ascending=False)
    
    # Mostrar resumen
    total_wins = df['Ganador'].value_counts().get('Sí', 0)
    avg_percentage = df['Porcentaje'].mean()
    total_seats = df['Bancas'].sum()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Intendencias ganadas", f"{total_wins}")
    
    with col2:
        st.metric("Porcentaje promedio", f"{avg_percentage:.1f}%")
    
    with col3:
        st.metric("Total de bancas", f"{total_seats}")
    
    # Mostrar tabla detallada
    st.subheader(f"Desempeño de {party} por departamento")
    
    # Configurar columnas para formato
    column_config = {
        'Departamento': st.column_config.TextColumn("Departamento"),
        'Porcentaje': st.column_config.NumberColumn("% Votos", format="%.1f%%"),
        'Bancas': st.column_config.NumberColumn("Bancas"),
        'Ganador': st.column_config.TextColumn("Intendencia")
    }
    
    st.dataframe(df, hide_index=True, column_config=column_config, use_container_width=True) 