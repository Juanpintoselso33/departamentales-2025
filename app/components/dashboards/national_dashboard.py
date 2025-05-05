"""
Dashboard para la visualización de datos electorales a nivel nacional.
"""

import streamlit as st
import pandas as pd

from app.components.ui.cards import stat_card, info_card, party_card
from app.components.ui.metrics import render_metrics_cards
from app.components.ui.charts import create_vote_distribution_chart, create_party_pie_chart, render_chart, create_party_legend
from app.components.ui.tables import display_results_table, display_party_color_table

def display_national_dashboard(election_data, summary):
    """
    Muestra un dashboard completo con información electoral a nivel nacional.
    
    Args:
        election_data (dict): Datos electorales por departamento
        summary (dict): Resumen nacional con estadísticas consolidadas
    """
    # Verificar si tenemos datos
    if not election_data or not summary:
        st.error("No hay datos disponibles para mostrar")
        return
    
    # Mostrar el contenido directamente (sin pestañas)
    display_party_results(summary, election_data)
    
    # Comentado: Mostrar métricas clave después del contenido principal
    # display_key_metrics(summary)

"""
Función comentada temporalmente porque muestra datos falsos.
Se puede descomentar cuando se tengan datos reales de métricas.

def display_key_metrics(summary):
    # Muestra métricas clave como participación, escrutinio, etc.
    # Args:
    #     summary (dict): Resumen nacional con estadísticas
    
    # Mostrar las métricas en cards
    if "metrics_data" in summary:
        render_metrics_cards(summary["metrics_data"])
    else:
        st.warning("No hay datos de métricas disponibles")
"""

def display_party_results(summary, election_data):
    """
    Muestra resultados detallados por partido.
    
    Args:
        summary (dict): Resumen nacional con estadísticas consolidadas
        election_data (dict): Datos electorales por departamento
    """
    # Inyectar CSS para controlar específicamente la altura de los iframes de ECharts
    # Esto es necesario como capa adicional de control para asegurar que todos los gráficos
    # tengan la misma altura, independientemente de la configuración interna del gráfico
    st.markdown("""
    <style>
    /* Forzar altura de los iframes para componentes ECharts */
    iframe.stCustomComponentV1 {
        height: 200px !important;
        min-height: 200px !important;
        max-height: 200px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Verificar si tenemos al menos algún tipo de datos para mostrar
    has_vote_data = "party_votes" in summary and summary["party_votes"]
    has_municipality_data = "alcaldes_per_party" in summary and summary["alcaldes_per_party"]
    
    if not has_vote_data and not has_municipality_data:
        st.warning("No hay datos disponibles para mostrar en los gráficos")
        return
    
    # Crear una cuadrícula 2x2 para los gráficos
    row1_col1, row1_col2 = st.columns(2, gap="small")
    row2_col1, row2_col2 = st.columns(2, gap="small")

    # Gráfico de Votos (Torta) - Fila 1, Columna 1
    with row1_col1:
        st.subheader("Distribución de Votos")
        if has_vote_data:
            display_vote_distribution(summary, show_legend=False)
        else:
            st.info("No hay datos de votos disponibles. Se muestran estadísticas basadas en alcaldes.")
            # Usar datos de alcaldes como proxy para votos si están disponibles
            if has_municipality_data:
                alcaldes_data = summary["alcaldes_per_party"]
                # Filtrar "No disponible"
                alcaldes_filtered = {k: v for k, v in alcaldes_data.items() 
                                   if k != "No disponible" and k != "Error" and v > 0}
                if alcaldes_filtered:
                    pie_chart = create_party_pie_chart(alcaldes_filtered, show_percentages=True)
                    render_chart(pie_chart, height="180px")
                else:
                    st.warning("No hay datos válidos para mostrar")

    # Gráfico de Intendencias (Barras) - Fila 1, Columna 2
    with row1_col2:
        st.subheader("Intendencias por Partido")
        display_council_distribution(summary)

    # Gráfico de Ediles (Barras) - Fila 2, Columna 1
    with row2_col1:
        st.subheader("Ediles por Partido")
        display_ediles_distribution(summary)

    # Gráfico de Alcaldes (Barras) - Fila 2, Columna 2
    with row2_col2:
        st.subheader("Alcaldes por Partido")
        display_mayors_distribution(summary)
    
    # Mostrar tabla de resultados si hay datos de votos o alcaldes
    if has_vote_data:
        st.header("Resultados Nacionales Completos")
        
        # Crear una tabla completa con todos los datos disponibles
        all_parties = set()
        
        # Obtener todos los partidos presentes en cualquiera de los conjuntos de datos
        if "party_votes" in summary:
            all_parties.update(summary["party_votes"].keys())
        if "department_winners" in summary:
            all_parties.update(summary["department_winners"].keys())
        if "ediles_per_party" in summary:
            all_parties.update(summary["ediles_per_party"].keys())
        if "alcaldes_per_party" in summary:
            all_parties.update(summary["alcaldes_per_party"].keys())
        
        # Filtrar "No disponible" o "Error"
        all_parties = [p for p in all_parties if p not in ["No disponible", "Error", None]]
        
        # Ordenar por partido con más votos
        if "party_votes" in summary and summary["party_votes"]:
            parties_sorted = sorted(
                all_parties,
                key=lambda p: summary["party_votes"].get(p, 0),
                reverse=True
            )
        else:
            # Si no hay datos de votos, ordenar por alcaldes
            parties_sorted = sorted(
                all_parties,
                key=lambda p: summary.get("alcaldes_per_party", {}).get(p, 0),
                reverse=True
            )
        
        # Construir tabla completa
        tabla_completa = []
        for partido in parties_sorted:
            row = {
                "Partido": partido,
                "Votos": summary.get("party_votes", {}).get(partido, 0),
                "Porcentaje": f"{summary.get('party_vote_percentages', {}).get(partido, 0):.1f}%",
                "Intendencias": summary.get("department_winners", {}).get(partido, 0),
                "Ediles": summary.get("ediles_per_party", {}).get(partido, 0),
                "Alcaldes": summary.get("alcaldes_per_party", {}).get(partido, 0)
            }
            tabla_completa.append(row)
        
        # Mostrar tabla completa
        df_completa = pd.DataFrame(tabla_completa)
        st.dataframe(
            df_completa, 
            hide_index=True,
            use_container_width=True
        )
        
    elif has_municipality_data:
        # Crear una tabla basada en alcaldes si no hay datos de votos
        alcaldes_data = summary["alcaldes_per_party"]
        alcaldes_filtered = {k: v for k, v in alcaldes_data.items() 
                           if k != "No disponible" and k != "Error"}
        
        if alcaldes_filtered:
            # Calcular porcentajes
            total_alcaldes = sum(alcaldes_filtered.values())
            alcaldes_percentages = {
                partido: round((cantidad / total_alcaldes) * 100, 1) 
                for partido, cantidad in alcaldes_filtered.items()
            }
            
            st.subheader("Distribución de Alcaldes por Partido")
            alcaldes_df = pd.DataFrame({
                "Partido": list(alcaldes_filtered.keys()),
                "Alcaldes": list(alcaldes_filtered.values()),
                "Porcentaje": [alcaldes_percentages.get(p, 0) for p in alcaldes_filtered.keys()]
            })
            st.dataframe(alcaldes_df.sort_values("Alcaldes", ascending=False))
            
            # Mostrar total
            st.info(f"Total de alcaldes: {total_alcaldes}")
    else:
        st.warning("No hay datos disponibles para mostrar la tabla de resultados")

    # TABLA DEPARTAMENTAL DINÁMICA POR PARTIDO
    st.header("Resultados por Departamento y Partido")
    # Detectar todos los partidos presentes en los datos departamentales
    all_parties = set()
    for dept_data in election_data.values():
        all_parties.update(dept_data.get("votes", {}).keys())
    all_parties = [p for p in all_parties if p not in ["No disponible", "Error", None]]
    all_parties = sorted(all_parties)

    rows = []
    for dept, dept_data in election_data.items():
        row = {"Departamento": dept}
        votes = dept_data.get("votes", {})
        percentages = dept_data.get("vote_percentages", {})
        for party in all_parties:
            # Asegurarse de que los votos sean int y no None
            votos = votes.get(party, 0)
            if votos is None:
                votos = 0
            row[f"{party} Votos"] = int(votos)
            row[f"{party} %"] = f"{percentages.get(party, 0):.1f}%" if party in percentages else "0.0%"
        rows.append(row)

    if rows:
        df_dept = pd.DataFrame(rows)
        # Ajustar el ancho de las columnas automáticamente
        st.dataframe(
            df_dept,
            hide_index=True,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(col) if 'Votos' in col else st.column_config.TextColumn(col) for col in df_dept.columns}
        )
    else:
        st.info("No hay datos departamentales para mostrar.")

def display_vote_distribution(summary, show_legend=False):
    """
    Muestra gráficos de distribución de votos.
    
    Args:
        summary (dict): Resumen nacional con estadísticas
        show_legend (bool): Mostrar leyenda de partidos
    """
    # Verificar que hay datos de votos disponibles
    if not summary.get("party_votes") or not summary.get("party_vote_percentages"):
        st.warning("No hay datos disponibles de votos por partido")
        return
        
    # Filtrar "No disponible" para no distorsionar el gráfico
    party_votes_filtered = {k: v for k, v in summary["party_votes"].items() 
                           if k != "No disponible" and k != "Error" and v > 0}
    
    if not party_votes_filtered:
        st.warning("No hay datos válidos para mostrar el gráfico de votos")
        return
    
    # Ordenar partidos por cantidad de votos (de mayor a menor)
    sorted_parties = sorted(
        [(party, votes) for party, votes in party_votes_filtered.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    # Asegurar que solo los 5 principales partidos se muestren individualmente
    # y el resto se agrupe como "Otros" para evitar un gráfico sobrecargado
    if len(sorted_parties) > 5:
        top_parties = sorted_parties[:5]
        other_votes = sum(votes for _, votes in sorted_parties[5:])
        
        # Recrear el diccionario con los 5 principales y "Otros"
        filtered_data = {party: votes for party, votes in top_parties}
        if other_votes > 0:
            filtered_data["Otros"] = other_votes
    else:
        filtered_data = party_votes_filtered
    
    # Crear el gráfico de torta con los datos filtrados
    pie_chart = create_party_pie_chart(filtered_data, show_percentages=True)
    render_chart(pie_chart, height="180px")
    
    # Mostrar leyenda si se solicita
    if show_legend:
        create_party_legend(list(filtered_data.keys()))

def display_council_distribution(summary):
    """
    Muestra gráficos de distribución de intendencias.
    
    Args:
        summary (dict): Resumen nacional con estadísticas
    """
    # Obtener datos de intendencias
    intendencias = {}
    
    # Probar todas las claves posibles
    for key in ['department_winners', 'intendencias']:
        if key in summary and summary[key]:
            intendencias = summary[key]
            break
    
    # Si los departamentos no tienen partidos ganadores, mostrar advertencia
    if not intendencias or all(p == "No disponible" for p in intendencias.keys()):
        st.warning("No hay datos disponibles de intendencias por partido")
        
        # Alternativa: intentar usar datos de municipios para estimar intendencias
        if "municipality_winners" in summary and summary["municipality_winners"]:
            st.info("Mostrando distribución de municipios como alternativa")
            municipios = summary["municipality_winners"]
            
            # Filtrar "No disponible" 
            municipios_filtered = {k: v for k, v in municipios.items() 
                                  if k != "No disponible" and k != "Error" and v > 0}
            
            if municipios_filtered:
                chart = create_vote_distribution_chart(
                    municipios_filtered, 
                    "Municipios por Partido", 
                    show_percentages=False
                )
                render_chart(chart, height="180px")
                st.caption("Nota: Se muestran municipios por partido debido a la falta de datos de intendencias.")
        return
    
    # Filtrar "No disponible" para que no domine el gráfico
    intendencias_filtered = {k: v for k, v in intendencias.items() 
                            if k != "No disponible" and k != "Error"}
    
    if not intendencias_filtered:
        st.warning("No hay datos válidos para mostrar el gráfico de intendencias")
        return
        
    # Crear gráfico de barras mostrando valores absolutos (no porcentajes)
    chart = create_vote_distribution_chart(intendencias_filtered, "Intendencias por Partido", show_percentages=False)
    render_chart(chart, height="180px")

# Funciones para Ediles y Alcaldes
def display_ediles_distribution(summary):
    """
    Muestra gráfico de distribución de ediles por partido.
    
    Args:
        summary (dict): Resumen nacional con estadísticas
    """
    # Obtener datos de ediles
    ediles_data = {}
    
    # Probar todas las claves posibles
    for key in ['ediles_per_party', 'ediles_totales']:
        if key in summary and summary[key]:
            ediles_data = summary[key]
            break
    
    if not ediles_data:
        st.warning("No hay datos disponibles de ediles", icon="⚠️")
        
        # Intenta generar una distribución teórica basada en municipios
        if "alcaldes_per_party" in summary and summary["alcaldes_per_party"]:
            alcaldes_data = summary["alcaldes_per_party"]
            alcaldes_filtered = {k: v for k, v in alcaldes_data.items() 
                               if k != "No disponible" and k != "Error" and v > 0}
            
            if alcaldes_filtered:
                st.info("Estimando distribución de ediles basada en municipios")
                
                # Calcular total de ediles aproximado (31 por departamento)
                total_departments = summary.get("total_departments", 19)  # Uruguay tiene 19 departamentos
                total_ediles = total_departments * 31
                ediles_mayoria = total_departments * 16
                
                # Encontrar partido con más alcaldes
                most_municipalities, _ = max(alcaldes_filtered.items(), key=lambda x: x[1])
                
                # Calcular proporción para los demás partidos
                otros_alcaldes = sum(v for k, v in alcaldes_filtered.items() if k != most_municipalities)
                ediles_restantes = total_ediles - ediles_mayoria
                
                # Crear distribución aproximada
                ediles_approx = {most_municipalities: ediles_mayoria}
                
                if otros_alcaldes > 0:
                    for partido, alcaldes in alcaldes_filtered.items():
                        if partido != most_municipalities:
                            proporcion = alcaldes / otros_alcaldes
                            ediles_approx[partido] = round(ediles_restantes * proporcion)
                
                # Mostrar gráfico aproximado
                chart = create_vote_distribution_chart(
                    ediles_approx, 
                    "Distribución Aproximada de Ediles", 
                    show_percentages=False
                )
                render_chart(chart, height="180px")
                st.caption("Nota: Esta es una aproximación basada en la distribución de alcaldes.")
        return
    
    # Filtrar "No disponible" para que no domine el gráfico
    ediles_filtered = {k: v for k, v in ediles_data.items() 
                      if k != "No disponible" and k != "Error" and v > 0}
    
    if not ediles_filtered:
        st.warning("No hay datos válidos para mostrar el gráfico de ediles")
        return
        
    # Mostrar valores absolutos (no porcentajes)
    chart = create_vote_distribution_chart(ediles_filtered, "Ediles por Partido", show_percentages=False)
    render_chart(chart, height="180px")
    
    # Añadir nota informativa sobre el cálculo
    st.caption("Nota: Los ediles se calculan según el artículo 272 de la Constitución, asignando mayoría automática al partido más votado y distribuyendo el resto proporcionalmente.")

def display_mayors_distribution(summary):
    """
    Muestra gráfico de distribución de alcaldes por partido.
    
    Args:
        summary (dict): Resumen nacional con estadísticas
    """
    # Obtener datos de alcaldes
    alcaldes_data = {}
    
    # Probar todas las claves posibles
    for key in ['alcaldes_per_party', 'municipality_winners']:
        if key in summary and summary[key]:
            alcaldes_data = summary[key]
            break
    
    if not alcaldes_data:
        st.warning("No hay datos disponibles de alcaldes", icon="⚠️")
        return
    
    # Filtrar "No disponible" para que no domine el gráfico
    alcaldes_filtered = {k: v for k, v in alcaldes_data.items() 
                        if k != "No disponible" and k != "Error" and v > 0}
    
    if not alcaldes_filtered:
        st.warning("No hay datos válidos para mostrar el gráfico de alcaldes")
        return
        
    # Mostrar valores absolutos (no porcentajes)
    chart = create_vote_distribution_chart(alcaldes_filtered, "Alcaldes por Partido", show_percentages=False)
    render_chart(chart, height="180px")
    
    # Añadir nota informativa sobre el cálculo
    st.caption("Nota: Según la Ley N° 19.272, el cargo de Alcalde corresponde al candidato de la lista más votada dentro del partido político más votado en el municipio.") 