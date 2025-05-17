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

from domain.summary import get_department_summary, get_all_candidates_by_party
from settings.settings import PATHS
from settings.theme import PARTY_COLORS, get_party_color
from app.components.functional.map_generator import create_municipality_map
# Importar el nuevo dashboard municipal
from app.components.dashboards.municipal_dashboard import display_municipal_dashboard

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
    # y intentar mejorar responsividad del parlamento
    st.markdown("""
    <style>
    /* Forzar altura de los iframes para componentes ECharts y otros */
    iframe.stCustomComponentV1 {
        height: 300px !important;
        min-height: 300px !important;
        max-height: 300px !important;
    }

    /* Forzar ANCHO MÍNIMO específico para el gráfico parlamento (Plotly) */
    /* Asumiendo que Plotly también usa stCustomComponentV1, pero podemos ser más específicos */
    iframe[title*="plotly"] { 
        min-width: 300px !important; /* Evita que se comprima demasiado */
        /* Ya no forzamos la altura aquí, se aplica la regla general de arriba */
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
    
    # --- INICIO: Procesamiento de datos para Gráfico y Tabla (antes estaba separado) ---
    # Obtener la lista detallada de la junta departamental
    listas_junta_data = dept_summary.get("junta_departamental_lists", [])
    
    df_display = None # Inicializar df_display
    chart_data_list = [] # Inicializar lista para el gráfico

    if listas_junta_data:
        # Crear DataFrame directamente desde la lista original
        df_listas = pd.DataFrame(listas_junta_data)

        # --- Preparación de datos para el GRÁFICO ---
        # El gráfico necesita 'Partido', 'Ediles', 'NumeroLista', 'Candidatos'
        # Asegurarnos de que esas claves existen (o mapear si es necesario)
        # En este caso, los nombres originales de listas_junta_data ya coinciden
        # Convertimos el DataFrame (o la lista original) a formato lista de diccionarios
        chart_data_list = df_listas.to_dict('records') # Usamos df_listas aquí
        
        # --- Preparación de datos para la TABLA ---
        # Formatear columna de candidatos (mostrar solo el primero o los 3 primeros)
        def format_candidates(cands):
            if isinstance(cands, list):
                if len(cands) > 0:
                    return cands[0] 
                else:
                    return "N/A"
            return "N/A"
        
        # Aplicar formato AHORA para tener la columna 'Primer Candidato' en df_listas
        df_listas['Primer Candidato'] = df_listas['Candidatos'].apply(format_candidates)

        # Seleccionar y renombrar columnas para la tabla df_display
        df_display = df_listas[[
            'Partido', 'NumeroLista', 'Sublema', 'Primer Candidato', 'Votos', 'Ediles', 'Resto', 'VotosParaEdilResto'
        ]].rename(columns={
            'NumeroLista': 'Nº Lista',
            'Sublema': 'Sublema',
            'Primer Candidato': 'Primer Candidato', # Usar la columna ya formateada
            'Votos': 'Votos Lista',
            'Ediles': 'Ediles Asignados',
            'Resto': 'Resto D\'Hondt',
            'VotosParaEdilResto': 'Votos Prox. Edil'
        })

        # Ordenar la tabla
        df_display = df_display.sort_values(by=['Ediles Asignados', 'Votos Lista'], ascending=[False, False])

    # --- FIN: Procesamiento de datos ---

    # Gráfico de parlamento (ahora usa chart_data_list)
    if chart_data_list:
        render_parliament_chart(chart_data_list, height=400) # Pasar la lista de diccionarios
        # Calcular total ediles desde la lista para el caption (podría hacerse desde df_display también)
        total_ediles = sum(lista.get("Ediles", 0) for lista in chart_data_list) 
        st.caption(f"Total de Ediles: {total_ediles}")
    else:
        # Mantener mensaje si no hay datos en origen
        if not listas_junta_data:
             st.info("No hay datos de ediles para este departamento.")
        # Si hubo listas pero 0 ediles, el gráfico no se muestra, pero la tabla sí podría
    
    # TERCERA FILA: Tablas de resultados
    st.header("Resultados Detallados")
    
    # --- INICIO: Tabla de Candidatos (antes en tab2) --- 
    # Acceder a los datos "crudos" del departamento
    dept_data_raw = election_data.get(department_name, {})
    
    st.subheader("Candidatos a Intendente")
    
    # Obtener datos directamente
    candidates_raw = dept_data_raw.get("party_candidates", {})
    votes_raw = dept_data_raw.get("votes", {})
    
    if candidates_raw:
        data = []
        total_votos_departamento = sum(votes_raw.values()) if votes_raw else 0
        
        for partido, candidatos in candidates_raw.items():
            votos_partido = votes_raw.get(partido, 0) # Obtener votos totales del partido
            # Calcular porcentaje del partido en el departamento
            porcentaje_partido_depto = (votos_partido / total_votos_departamento * 100) if total_votos_departamento > 0 else 0
            
            if isinstance(candidatos, list):
                for candidato in candidatos:
                    votos_totales_cand = candidato.get("votos", 0)
                    votos_hojas_cand = candidato.get("votos_hojas", 0)
                    
                    porcentaje_partido_cand = (votos_totales_cand / votos_partido * 100) if votos_partido > 0 else 0 # Renombrado para claridad
                    porcentaje_total_cand = (votos_totales_cand / total_votos_departamento * 100) if total_votos_departamento > 0 else 0 # Renombrado para claridad
                    
                    data.append({
                        "Partido": partido,
                        "Candidato": candidato.get("nombre", "N/A"),
                        "Votos Partido": votos_partido,
                        "% Partido/Depto": porcentaje_partido_depto, 
                        "Votos Candidato": votos_totales_cand,
                        "% Cand/Partido": porcentaje_partido_cand,
                        "% Cand/Depto": porcentaje_total_cand
                    })
            elif isinstance(candidatos, str):
                 porcentaje_total = (votos_partido / total_votos_departamento * 100) if total_votos_departamento > 0 else 0
                 data.append({
                    "Partido": partido, 
                    "Candidato": candidatos,
                    "Votos Partido": votos_partido, 
                    "% Partido/Depto": porcentaje_partido_depto,
                    "Votos Candidato": votos_partido,
                    "% Cand/Partido": 100.0, 
                    "% Cand/Depto": porcentaje_total
                })

        df = pd.DataFrame(data)
        df = df.sort_values(by="Votos Candidato", ascending=False)
        
        # Formatear porcentajes
        df["% Partido/Depto"] = df["% Partido/Depto"].apply(lambda x: f"{x:.1f}%")
        df["% Cand/Partido"] = df["% Cand/Partido"].apply(lambda x: f"{x:.1f}%")
        df["% Cand/Depto"] = df["% Cand/Depto"].apply(lambda x: f"{x:.1f}%")
        
        # Actualizar lista de columnas a mostrar con nuevo orden lógico
        column_order = ["Partido", "Candidato", "Votos Partido", "% Partido/Depto", "Votos Candidato", "% Cand/Partido", "% Cand/Depto"]
        
        st.dataframe(
            df[column_order],
            column_config={
                "Partido": st.column_config.TextColumn("Partido", width="medium"),
                "Candidato": st.column_config.TextColumn("Candidato", width="large"),
                "Votos Partido": st.column_config.NumberColumn("Votos Partido", format="%d", help="Total de votos obtenidos por el partido"), 
                "% Partido/Depto": st.column_config.TextColumn("% Partido en Depto", width="small", help="Porcentaje del partido sobre el total del departamento"), 
                "Votos Candidato": st.column_config.NumberColumn("Votos Candidato", format="%d", help="Total de votos obtenidos por el candidato"),
                "% Cand/Partido": st.column_config.TextColumn("% en Partido", width="small", help="Porcentaje del candidato dentro de su propio partido"),
                "% Cand/Depto": st.column_config.TextColumn("% en Depto", width="small", help="Porcentaje del candidato sobre el total del departamento")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No hay información detallada de candidatos disponible")
    # --- FIN: Tabla de Candidatos ---
    
    # SECCIÓN MOVIDA: Listas y Ediles (ahora solo muestra la tabla df_display)
    st.subheader("Distribución de Ediles por Lista (Junta Departamental)") 
    
    # Mostrar la tabla df_display (ya creada y ordenada arriba)
    if df_display is not None and not df_display.empty:
        st.dataframe(
            df_display,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Votos Lista": st.column_config.NumberColumn(format="%d"),
                "Ediles Asignados": st.column_config.NumberColumn(format="%d"),
                "Resto D'Hondt": st.column_config.NumberColumn(format="%.4f"),
                "Votos Prox. Edil": st.column_config.NumberColumn(format="%d", help="Votos que faltaron para obtener el siguiente edil por resto (N/A si no aplica)")
            }
        )
        # Añadir nota explicativa sobre la columna Nº Lista (NUEVO)
        st.caption(
            "Nota: La columna 'Nº Lista' intenta mostrar el número de hoja de votación (HN). "
            "Debido a la estructura de los datos fuente, especialmente cuando existen votos directos al sublema o lema "
            "que afectan a una lista, la vinculación directa mediante los votos de la hoja ('VH') puede no encontrarse, "
            "resultando en el indicador 'N/A'."
        )

        # --- INICIO ANOTACIONES Y DISCLAIMER ---
        st.caption("""
        **Notas sobre la tabla:**
        *   **Ediles Asignados:** Cantidad de ediles obtenidos por cada lista según el Art. 272 de la Constitución (mayoría automática al lema ganador y método D'Hondt para el resto).
        *   **Resto D'Hondt:** Valor residual utilizado en la segunda fase de asignación (mayores restos).
        *   **Votos Prox. Edil:** Estimación de cuántos votos adicionales necesitaba una lista para obtener el siguiente edil por la vía de los restos.
            *   `0`: Indica que la lista obtuvo un edil por resto.
            *   `N/A` (o vacío): Indica que el cálculo no aplica (p. ej., no hubo reparto por resto o la lista ya obtuvo todos sus ediles por cociente).

        **Disclaimer:** El cálculo de la asignación de ediles por lista y los votos para el próximo edil es una interpretación realizada por esta aplicación y **no representa un dato oficial de la Corte Electoral**.
        """)
        # --- FIN ANOTACIONES Y DISCLAIMER ---
        
    else:
        # Mostrar info solo si originalmente no había datos
        if not listas_junta_data: 
            st.info("No hay datos detallados de listas a la Junta Departamental disponibles.")

    # --- INICIO: SECCIÓN MUNICIPAL ---
    st.markdown("<hr>", unsafe_allow_html=True)
    st.header(f"Detalle Municipal en {department_name}")

    # Obtener la lista de municipios del departamento actual
    dept_data = election_data.get(department_name, {})
    municipalities = dept_data.get("municipalities", {})
    municipality_names = sorted(list(municipalities.keys()))

    if not municipality_names:
        st.info(f"No hay datos municipales disponibles para {department_name}.")
    else:
        # Crear selector de municipios
        options = ["Seleccione un Municipio..."] + municipality_names
        
        # Usar una clave única para el selector basada en el departamento
        selector_key = f"municipality_selector_{department_name.replace(' ', '_')}"

        # Leer el estado actual ANTES de crear el selectbox
        current_selection = st.session_state.get(selector_key, options[0])

        selected_municipality = st.selectbox(
            "Ver detalle del Municipio:",
            options=options,
            index=options.index(current_selection) if current_selection in options else 0, # Usar estado guardado si existe
            key=selector_key # Clave única por departamento
        )

        # Limpiar la selección si se vuelve a "Seleccione..."
        if selected_municipality == options[0]:
            # No es necesario hacer nada explícito aquí si solo mostramos debajo
            pass 
        
        # Si se selecciona un municipio válido, mostrar su dashboard
        if selected_municipality != options[0]:
            st.markdown("<hr style='border-top: 2px solid #444;'>", unsafe_allow_html=True) # Separador más grueso
            # Llamar al dashboard municipal
            display_municipal_dashboard(election_data, department_name, selected_municipality)

    # --- FIN: SECCIÓN MUNICIPAL ---

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