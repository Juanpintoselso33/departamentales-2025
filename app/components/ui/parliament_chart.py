"""
Componente para generar gráficos de parlamento (hemiciclo) usando plotly.
"""

import plotly.graph_objects as go
import numpy as np
import streamlit as st
from settings.theme import get_party_color
from typing import List, Dict, Any # Importar tipos

def create_parliament_chart(list_data: List[Dict[str, Any]], height=500):
    """
    Crea un gráfico de parlamento (hemiciclo) usando plotly.
    Los colores se obtienen automáticamente del sistema de temas.
    La información para tooltips (Nº Lista, Candidato) viene de list_data.

    Args:
        list_data (List[Dict[str, Any]]): Lista de diccionarios, cada uno representando
                                           una lista electoral con claves como 'Partido',
                                           'NumeroLista', 'Candidatos', 'Ediles'.
        height (int): Altura del gráfico en píxeles

    Returns:
        go.Figure or None: Figura de plotly o None si no hay datos.
    """
    # Crear lista de todas las bancas individuales, cada una con sus datos detallados
    all_seats_details = []
    aggregated_seats_by_party = {} # Para la leyenda
    for lista in list_data:
        party = lista.get("Partido", "N/A")
        seats = lista.get("Ediles", 0)
        list_num = lista.get("NumeroLista", "N/A")
        # Usar el primer candidato para el tooltip
        candidate = lista.get("Candidatos", ["N/A"])[0] if isinstance(lista.get("Candidatos"), list) and lista.get("Candidatos") else "N/A"

        if seats > 0:
            for _ in range(seats):
                all_seats_details.append({
                    "party": party,
                    "list_num": list_num,
                    "candidate": candidate
                })
            # Agregar al agregado para la leyenda
            aggregated_seats_by_party[party] = aggregated_seats_by_party.get(party, 0) + seats

    total_seats = len(all_seats_details)
    if total_seats == 0:
        return None

    # Ordenar partidos para la leyenda por cantidad de bancas (desc)
    sorted_parties = sorted(aggregated_seats_by_party.items(), key=lambda item: item[1], reverse=True)

    # Configurar número de filas (ajustar si es necesario para total_seats)
    # Esta distribución es fija para 31 ediles, podría necesitar ajuste dinámico
    # si el número total de ediles varía mucho entre departamentos.
    # Por ahora, mantenemos la fija de 31.
    rows = [11, 10, 10] 
    n_rows = len(rows)

    fig = go.Figure()
    seat_index = 0
    parties_in_legend = set() # Para controlar qué se añade a la leyenda

    # Para cada fila
    for row_idx, seats_in_row in enumerate(rows):
        r = 1 + (row_idx * 0.4)
        phi = np.linspace(0.1 * np.pi, 0.9 * np.pi, seats_in_row)
        x = r * np.cos(phi)
        y = r * np.sin(phi)

        # Agregar cada asiento en esta fila
        for i in range(seats_in_row):
            if seat_index < total_seats:
                seat_details = all_seats_details[seat_index]
                party = seat_details["party"]
                list_num = seat_details["list_num"]
                candidate = seat_details["candidate"]
                color = get_party_color(party)

                # Determinar si mostrar en leyenda (solo la primera vez para cada partido)
                show_legend_for_this_seat = False
                if party not in parties_in_legend:
                    show_legend_for_this_seat = True
                    parties_in_legend.add(party)

                # MODIFICAR HOVERTEMPLATE Y NAME PARA LEYENDA
                fig.add_trace(go.Scatter(
                    x=[x[i]],
                    y=[y[i]],
                    mode='markers',
                    # Usar nombre con total de ediles para la leyenda
                    name=f'{party} ({aggregated_seats_by_party.get(party, 0)})',
                    legendgroup=party, # Agrupar por partido
                    marker=dict(
                        size=20,
                        color=color,
                        line=dict(color='rgba(255,255,255,0.5)', width=1),
                        symbol='circle'
                    ),
                    hovertemplate=(
                        f'<b>Partido:</b> {party}<br>' +
                        f'<b>Lista:</b> {list_num}<br>' +
                        f'<b>Candidato:</b> {candidate}' +
                        '<extra></extra>' # Ocultar info extra de plotly
                    ),
                    showlegend=show_legend_for_this_seat 
                ))

                seat_index += 1

    # Configurar el layout (igual que antes, pero ajustando leyenda si es necesario)
    fig.update_layout(
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=height,
        autosize=True, 
        margin=dict(l=0, r=0, t=0, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            traceorder="reversed"
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-2, 2],
            fixedrange=True
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.2, 2.2],
            fixedrange=True,
            scaleanchor="x",
            scaleratio=1
        )
    )

    return fig

def render_parliament_chart(list_data: List[Dict[str, Any]], height=500):
    """
    Renderiza un gráfico de parlamento en Streamlit.

    Args:
        list_data (List[Dict[str, Any]]): Lista detallada de listas con ediles.
        height (int): Altura del gráfico en píxeles
    """
    fig = create_parliament_chart(list_data, height) # Pasar list_data
    if fig:
        st.plotly_chart(fig, use_container_width=True, config={
            'responsive': True,
            'displayModeBar': False
        })
    else:
        st.info("No hay datos de bancas para mostrar.") 