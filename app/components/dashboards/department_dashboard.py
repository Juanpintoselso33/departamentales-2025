"""
Dashboard para la visualización de datos electorales a nivel departamental.
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import math
import plotly.graph_objects as go
from typing import Dict, Any

from app.components.ui.cards import info_card, party_card
from app.components.ui.charts import create_vote_distribution_chart, create_party_pie_chart, create_bar_chart, render_chart
from app.components.ui.tables import display_results_table
from app.components.ui.containers import section_container, tabs_container, stylable_container
from app.components.ui.parliament_chart import render_parliament_chart

from infrastructure.loaders import load_geo_data
from domain.summary import get_department_summary, get_all_candidates_by_party
from settings.settings import PATHS
from settings.theme import PARTY_COLORS, get_party_color
from app.components.functional.map_generator import create_municipality_map

def display_department_dashboard(election_data, department_name=None):
    """
    Muestra un dashboard completo con información electoral de un departamento.
    
    Args:
        election_data (dict): Datos electorales completos
        department_name (str, opcional): Nombre del departamento a mostrar
    """
    # Opción para limpiar caché
    with st.sidebar:
        if st.button("Limpiar caché y recargar datos", type="primary"):
            # Limpiar todas las cachés
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("¡Caché limpiada con éxito! Recargando datos...")
            st.rerun()
    
    # Si no se especifica un departamento, mostrar selector
    if department_name is None:
        department_name = st.selectbox(
            "Seleccionar Departamento",
            options=list(election_data.keys()),
            key="department_selector"
        )
    
    # Obtener resumen del departamento
    dept_summary = get_department_summary(election_data, department_name)
    
    # Verificar si tenemos datos
    if not dept_summary:
        st.error(f"No hay datos disponibles para el departamento {department_name}")
        return
    
    # Inyectar CSS para controlar específicamente la altura de los iframes de ECharts
    st.markdown("""
    <style>
    /* Forzar altura de los iframes para componentes ECharts */
    iframe.stCustomComponentV1 {
        height: 300px !important;
        min-height: 300px !important;
        max-height: 300px !important;
    }
    
    /* Controlar espaciado vertical */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > div:first-child {
        margin-bottom: 0px;
    }

    /* Ajustar espaciado de los separadores */
    hr {
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # PRIMERA FILA: Título, información del ganador y distribución de votos
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title(f"{department_name}")
    
    # Crear dos columnas para la primera fila
    col1, col2 = st.columns([3, 2])
    
    # Inyectar CSS para alinear las columnas
    st.markdown("""
        <style>
        [data-testid="column"] {
            padding: 0 !important;
            margin-top: 0 !important;
        }
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > div:first-child {
            margin-top: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with col1:
        votos = dept_summary.get("votes", {})
        if votos:
            pie_chart = create_party_pie_chart(votos, show_percentages=True)
            render_chart(pie_chart, height="300px")
        else:
            st.info("No hay datos de votos para este departamento.")
    
    with col2:
        # Información del ganador
        winning_party = dept_summary.get("winning_party", "No disponible")
        mayor = dept_summary.get("mayor", "No disponible")
        vote_percentage = dept_summary.get("vote_percentages", {}).get(winning_party, 0)
        total_votes = sum(votos.values()) if votos else 0
        
        # Obtener el color del partido ganador
        party_color = get_party_color(winning_party)
        
        # Usar un contenedor estilizable para toda la información
        with stylable_container(
            key="winner_info_container",
            css_styles=f"""
                {{
                    background-color: rgba(30, 41, 59, 0.5);
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    border-radius: 8px;
                    padding: 1.5rem;
                    margin: 0 0 1rem 0;
                }}
            """
        ):
            # Título principal
            st.markdown("""
                <div style='
                    font-size: 1.1rem;
                    color: rgba(255,255,255,0.7);
                    margin-bottom: 1rem;
                '>Intendente</div>
            """, unsafe_allow_html=True)
            
            # Partido ganador
            st.markdown(f"""
                <div style='
                    border-left: 4px solid {party_color};
                    padding-left: 0.75rem;
                    margin-bottom: 1.5rem;
                    background: linear-gradient(90deg, rgba({party_color[1:]}, 0.1) 0%, rgba(30, 41, 59, 0) 100%);
                '>
                    <h2 style='
                        margin: 0;
                        font-size: 1.4rem;
                        color: white;
                    '>{winning_party}</h2>
                </div>
            """, unsafe_allow_html=True)
            
            # Candidato con ícono
            st.markdown(f"""
                <div style='
                    display: flex;
                    align-items: center;
                    margin-bottom: 1.5rem;
                    padding: 0.75rem;
                    background: rgba(0,0,0,0.2);
                    border-radius: 4px;
                '>
                    <div style='
                        font-size: 1.5rem;
                        margin-right: 0.75rem;
                        color: rgba(255,255,255,0.6);
                    '>👤</div>
                    <div style='
                        color: white;
                        font-size: 1.1rem;
                    '>{mayor}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Métricas en dos columnas
            st.markdown(f"""
                <div style='
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-top: 1rem;
                '>
                    <div style='text-align: center; flex: 1;'>
                        <div style='font-size: 2rem; font-weight: bold; color: white;'>{vote_percentage:.1f}%</div>
                        <div style='color: rgba(255,255,255,0.6); font-size: 0.9rem;'>Porcentaje</div>
                    </div>
                    <div style='text-align: center; flex: 1;'>
                        <div style='font-size: 2rem; font-weight: bold; color: white;'>{total_votes:,}</div>
                        <div style='color: rgba(255,255,255,0.6); font-size: 0.9rem;'>Total Votos</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # SEGUNDA FILA: Junta Departamental
    st.header("Junta Departamental")
    
    # Gráfico de parlamento a todo el ancho
    ediles = dept_summary.get("council_seats", {})
    if ediles:
        render_parliament_chart(ediles, height=400)
        total_ediles = sum(ediles.values())
        st.caption(f"Total de Ediles: {total_ediles}")
    else:
        st.info("No hay datos de ediles para este departamento.")
    
    # TERCERA FILA: Tablas de resultados
    st.header("Resultados Detallados")
    
    # Crear pestañas para las diferentes tablas
    tab1, tab2, tab3 = st.tabs(["Resultados por Partido", "Candidatos a Intendente", "Listas y Ediles"])
    
    # Pestaña 1: Resultados por partido (tabla actual)
    with tab1:
        # Tabla de resultados por partido
        if votos:
            # Obtener candidatos por partido
            party_candidates = dept_summary.get("party_candidates", {})
            
            data = []
            for party in votos.keys():
                # Obtener el candidato más votado del partido (si hay varios)
                candidatos = party_candidates.get(party, [])
                if isinstance(candidatos, list) and candidatos:
                    candidato = candidatos[0]["nombre"]  # El primero es el más votado porque los ordenamos antes
                elif isinstance(candidatos, str):
                    candidato = candidatos
                else:
                    candidato = "No disponible"
                
                row = {
                    "Partido": party,
                    "Votos": votos.get(party, 0),
                    "Porcentaje": f"{dept_summary.get('vote_percentages', {}).get(party, 0):.1f}%",
                    "Ediles": ediles.get(party, 0) if ediles else 0,
                    "Candidato Principal": candidato
                }
                data.append(row)
            
            # Crear DataFrame y ordenar por votos (de mayor a menor)
            df = pd.DataFrame(data)
            df = df.sort_values(by="Votos", ascending=False)
            
            st.dataframe(
                df,
                column_config={
                    "Partido": st.column_config.TextColumn("Partido", width="medium"),
                    "Votos": st.column_config.NumberColumn("Votos", format="%d"),
                    "Porcentaje": st.column_config.TextColumn("Porcentaje", width="small"),
                    "Ediles": st.column_config.NumberColumn("Ediles", format="%d"),
                    "Candidato Principal": st.column_config.TextColumn("Candidato Principal", width="large")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No hay resultados detallados para mostrar.")
    
    # Pestaña 2: Candidatos a Intendente
    with tab2:
        st.write("Candidatos a Intendente")
        
        # Obtener todos los candidatos usando la clave correcta
        candidates_by_party = dept_summary.get("candidates_by_party", {})
        
        if candidates_by_party:
            # Contar candidatos totales
            total_candidatos = sum(
                len(candidatos) if isinstance(candidatos, list) else 1 
                for candidatos in candidates_by_party.values()
            )
            total_partidos = len(candidates_by_party)
            
            st.write(f"Candidatos encontrados: {total_candidatos} en {total_partidos} partidos")
            
            # Crear una única tabla con todos los candidatos
            data = []
            total_votos_departamento = sum(votos.values()) if votos else 0
            
            for partido, candidatos in candidates_by_party.items():
                votos_partido = votos.get(partido, 0)
                
                if isinstance(candidatos, list):
                    for candidato in candidatos:
                        votos_totales = candidato.get("votos", 0)
                        votos_hojas = candidato.get("votos_hojas", 0)
                        
                        # Calcular porcentajes
                        porcentaje_partido = (votos_totales / votos_partido * 100) if votos_partido > 0 else 0
                        porcentaje_total = (votos_totales / total_votos_departamento * 100) if total_votos_departamento > 0 else 0
                        
                        data.append({
                            "Partido": partido,
                            "Candidato": candidato["nombre"],
                            "Votos Totales": votos_totales,
                            "Votos Hojas": votos_hojas,
                            "% en el Partido": porcentaje_partido,
                            "% Total": porcentaje_total
                        })
                else:
                    # Este bloque else podría no ser necesario si candidates_by_party siempre es una lista, 
                    # pero lo mantenemos por seguridad por si alguna vez llega un string (aunque no debería).
                    data.append({
                        "Partido": partido,
                        "Candidato": candidatos,  # aquí candidatos es un string
                        "Votos Totales": votos_partido,
                        "Votos Hojas": votos_partido,  # asumimos todos los votos como directos
                        "% en el Partido": 100.0,  # único candidato del partido
                        "% Total": (votos_partido / total_votos_departamento * 100) if total_votos_departamento > 0 else 0
                    })
            
            # Crear DataFrame y ordenar por votos totales
            df = pd.DataFrame(data)
            df = df.sort_values(by="Votos Totales", ascending=False)
            
            # Formatear los porcentajes
            df["% en el Partido"] = df["% en el Partido"].apply(lambda x: f"{x:.1f}%")
            df["% Total"] = df["% Total"].apply(lambda x: f"{x:.1f}%")
            
            # Mostrar la tabla
            st.dataframe(
                df,
                column_config={
                    "Partido": st.column_config.TextColumn("Partido", width="medium"),
                    "Candidato": st.column_config.TextColumn("Candidato", width="large"),
                    "Votos Totales": st.column_config.NumberColumn("Votos Totales", format="%d"),
                    "Votos Hojas": st.column_config.NumberColumn("Votos Hojas", format="%d"),
                    "% en el Partido": st.column_config.TextColumn("% en el Partido", width="small"),
                    "% Total": st.column_config.TextColumn("% Total", width="small")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No hay información detallada de candidatos disponible")
    
    # Pestaña 3: Listas y Ediles
    with tab3:
        st.write("Listas y Ediles por Partido")
        
        # Obtener datos detallados de las listas (pre-procesados por el loader)
        detailed_lists = dept_summary.get("detailed_council_lists", [])
        council_seats = dept_summary.get("council_seats", {}) # Ediles por partido
        
        if detailed_lists:
            # Crear DataFrame directamente desde los datos pre-procesados
            df = pd.DataFrame(detailed_lists)
            
            # Añadir columna de Ediles totales del partido (para referencia)
            df["Ediles Partido"] = df["Partido"].apply(lambda p: council_seats.get(p, 0))
            
            # Calcular porcentajes (opcional, pero puede ser útil)
            total_votos_departamento = sum(dept_summary.get("votes", {}).values())
            df["% Total"] = df["Votos"].apply(lambda v: f"{(v / total_votos_departamento * 100):.1f}%" if total_votos_departamento > 0 else "0.0%")
            
            # Ordenar por Partido y Votos
            df = df.sort_values(by=["Partido", "Votos"], ascending=[True, False])
            
            # Seleccionar y renombrar columnas para mostrar
            df_display = df[["Partido", "Sublema", "Lista", "Votos", "% Total", "Ediles Partido"]]
            
            st.dataframe(
                df_display,
                column_config={
                    "Partido": st.column_config.TextColumn("Partido", width="medium"),
                    "Sublema": st.column_config.TextColumn("Sublema", width="large"),
                    "Lista": st.column_config.TextColumn("Lista (Descripción)", width="large"),
                    "Votos": st.column_config.NumberColumn("Votos Lista", format="%d"),
                    "% Total": st.column_config.TextColumn("% Votos Depto."),
                    "Ediles Partido": st.column_config.NumberColumn("Ediles Partido", format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Mostrar resumen por partido (opcional, similar al anterior pero usando los datos procesados)
            st.write("### Resumen por Partido")
            df_resumen = df.groupby("Partido").agg(
                Total_Ediles=("Ediles Partido", "first"),
                Total_Listas=("Lista", "count"),
                Total_Votos_Listas=("Votos", "sum")
            ).reset_index()
            
            # Añadir votos totales del partido desde dept_summary para comparar
            votos_partido_total = dept_summary.get("votes", {})
            df_resumen["Votos Partido (Total)"] = df_resumen["Partido"].apply(lambda p: votos_partido_total.get(p, 0))
            
            st.dataframe(
                df_resumen,
                column_config={
                    "Partido": st.column_config.TextColumn("Partido", width="medium"),
                    "Total_Ediles": st.column_config.NumberColumn("Total Ediles", format="%d"),
                    "Total_Listas": st.column_config.NumberColumn("Total Listas", format="%d"),
                    "Total_Votos_Listas": st.column_config.NumberColumn("Votos Suma Listas", format="%d"),
                    "Votos Partido (Total)": st.column_config.NumberColumn("Votos Total Partido", format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
            
        else:
            st.info("No hay información detallada de listas disponible.")
            
            # Mostrar información de debug si es útil
            with st.expander("Debug: Estructura de Datos (Pestaña 3)"):
                st.json({
                    "claves_disponibles": list(dept_summary.keys()),
                    "tiene_detailed_council_lists": "detailed_council_lists" in dept_summary,
                    "cantidad_listas_detalladas": len(dept_summary.get("detailed_council_lists", [])),
                    "tiene_council_seats": "council_seats" in dept_summary,
                    "total_ediles": sum(dept_summary.get("council_seats", {}).values())
                })

def display_department_header(dept_summary):
    """
    Muestra el encabezado con información básica del departamento.
    
    Args:
        dept_summary (dict): Resumen del departamento
    """
    # Obtener datos básicos
    department = dept_summary.get('department', 'Departamento')
    winning_party = dept_summary.get('winning_party', 'No disponible')
    mayor = dept_summary.get('mayor', 'No disponible')
    
    # Obtener porcentaje del partido ganador
    vote_percentages = dept_summary.get('vote_percentages', {})
    winning_pct = vote_percentages.get(winning_party, 0)
    
    # Obtener color del partido
    party_color = PARTY_COLORS.get(winning_party, "#CCCCCC")
    
    # Mostrar tarjetas con información básica
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.title(department)
        st.subheader(f"Intendente: {mayor}")
    
    with col2:
        party_card(
            winning_party, 
            winning_pct, 
            color=party_color, 
            candidate=mayor, 
            position="Intendente"
        )

def display_vote_charts(dept_summary):
    """
    Muestra gráficos de distribución de votos.
    
    Args:
        dept_summary (dict): Resumen del departamento
    """
    # Obtener datos de porcentajes
    vote_percentages = dept_summary.get('vote_percentages', {})
    
    if not vote_percentages:
        st.warning("No hay datos disponibles de votos por partido")
        return
    
    # Crear gráfico de barras horizontales
    chart = create_vote_distribution_chart(vote_percentages, "Porcentaje de Votos por Partido")
    render_chart(chart)

def display_municipality_section(dept_summary):
    """
    Muestra la sección de información de municipios.
    
    Args:
        dept_summary (dict): Resumen del departamento
    """
    # Obtener datos de municipios
    municipality_data = dept_summary.get('municipalities', {})
    
    if not municipality_data:
        st.warning("No hay datos disponibles de municipios")
        return
    
    # Mostrar información en dos columnas
    col1, col2 = st.columns(2)
    
    with col1:
        # Mostrar tabla de municipios
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        st.subheader("Lista de Municipios")
        
        # Crear DataFrame con datos de municipios
        muni_rows = []
        for muni_name, muni_data in municipality_data.items():
            muni_rows.append({
                'Municipio': muni_name,
                'Alcalde': muni_data.get('mayor', 'No disponible'),
                'Partido': muni_data.get('party', 'No disponible'),
                'Votos': sum(muni_data.get('votes', {}).values()),
                'Porc. Ganador': f"{muni_data.get('vote_percentages', {}).get(muni_data.get('party', ''), 0):.1f}%"
            })
        
        if muni_rows:
            df = pd.DataFrame(muni_rows)
            st.dataframe(
                df,
                column_config={
                    'Municipio': st.column_config.TextColumn("Municipio"),
                    'Alcalde': st.column_config.TextColumn("Alcalde", width="large"),
                    'Partido': st.column_config.TextColumn("Partido"),
                    'Votos': st.column_config.NumberColumn("Votos Totales", format="%d"),
                    'Porc. Ganador': st.column_config.TextColumn("% Ganador")
                },
                hide_index=True,
                use_container_width=True
            )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Mostrar gráfico con distribución de municipios por partido
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("Distribución por Partido")
        
        # Mostrar total de municipios
        total_municipios = len(municipality_data)
        st.metric("Total de municipios", total_municipios)
        
        # Mostrar distribución por partido
        municipalities_by_party = dept_summary.get('municipalities_by_party', {})
        if municipalities_by_party:
            df = pd.DataFrame({
                'Partido': list(municipalities_by_party.keys()),
                'Municipios': list(municipalities_by_party.values())
            })
            
            # Crear gráfico
            chart = create_bar_chart(
                df, 
                'Partido', 
                'Municipios', 
                'Distribución de Municipios por Partido', 
                'Partido'
            )
            render_chart(chart)
            
            # Mostrar tabla con porcentajes
            df['Porcentaje'] = df['Municipios'].apply(lambda x: f"{(x/total_municipios)*100:.1f}%")
            st.dataframe(
                df[['Partido', 'Municipios', 'Porcentaje']], 
                hide_index=True, 
                use_container_width=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True) 