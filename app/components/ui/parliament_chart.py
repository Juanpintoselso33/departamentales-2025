"""
Componente para generar gráficos de parlamento (hemiciclo) usando plotly.
"""

import plotly.graph_objects as go
import numpy as np
import streamlit as st
from settings.theme import get_party_color

def create_parliament_chart(seats_by_party, height=500):
    """
    Crea un gráfico de parlamento (hemiciclo) usando plotly.
    Los colores se obtienen automáticamente del sistema de temas.
    
    Args:
        seats_by_party (dict): Diccionario con {partido: número_de_bancas}
        height (int): Altura del gráfico en píxeles
        
    Returns:
        go.Figure: Figura de plotly con el gráfico de parlamento
    """
    # Filtrar partidos sin bancas y ordenar de mayor a menor
    seats_by_party = {k: v for k, v in seats_by_party.items() if v > 0}
    
    # Calcular el total de bancas
    total_seats = sum(seats_by_party.values())
    
    if total_seats == 0:
        return None

    # Configurar número de filas y asientos por fila para simular anfiteatro
    rows = [11, 10, 10]  # 31 ediles en total, distribuidos en 3 filas
    n_rows = len(rows)
    
    # Crear el gráfico base
    fig = go.Figure()
    
    # Crear lista de todos los ediles con su partido
    all_seats = []
    for party, seats in seats_by_party.items():
        all_seats.extend([party] * seats)
    
    # Posición actual en la lista de ediles
    seat_index = 0
    
    # Para cada fila
    for row_idx, seats_in_row in enumerate(rows):
        # Radio para esta fila (las filas de atrás están más lejos)
        r = 1 + (row_idx * 0.4)  # Incremento del radio para cada fila
        
        # Calcular ángulos para distribuir los asientos en esta fila
        phi = np.linspace(0.1 * np.pi, 0.9 * np.pi, seats_in_row)
        
        # Coordenadas para esta fila
        x = r * np.cos(phi)
        y = r * np.sin(phi)
        
        # Agregar cada asiento en esta fila
        for i in range(seats_in_row):
            if seat_index < len(all_seats):
                party = all_seats[seat_index]
                color = get_party_color(party)
                
                fig.add_trace(go.Scatter(
                    x=[x[i]],
                    y=[y[i]],
                    mode='markers',
                    name=party,
                    marker=dict(
                        size=25,  # Puntos más grandes
                        color=color,
                        line=dict(color='rgba(255,255,255,0.5)', width=1),
                        symbol='circle'
                    ),
                    hovertemplate=(
                        f'<b>{party}</b><br>' +
                        f'Banca {seat_index + 1}' +
                        '<extra></extra>'
                    ),
                    showlegend=seat_index < len(seats_by_party)  # Mostrar en leyenda solo una vez por partido
                ))
                
                seat_index += 1
    
    # Configurar el layout
    fig.update_layout(
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=height,
        autosize=True,  # Permitir autoajuste
        margin=dict(l=0, r=0, t=0, b=50),  # Márgenes mínimos
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-2, 2],  # Rango más amplio para mejor distribución
            fixedrange=True
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.2, 2.2],  # Rango ajustado para la altura
            fixedrange=True,
            scaleanchor="x",
            scaleratio=1
        )
    )
    
    return fig

def render_parliament_chart(seats_by_party, height=500):
    """
    Renderiza un gráfico de parlamento en Streamlit.
    
    Args:
        seats_by_party (dict): Diccionario con {partido: número_de_bancas}
        height (int): Altura del gráfico en píxeles
    """
    fig = create_parliament_chart(seats_by_party, height)
    if fig:
        # Usar config para habilitar modo responsive
        st.plotly_chart(fig, use_container_width=True, config={
            'responsive': True,
            'displayModeBar': False  # Ocultar barra de herramientas
        })
    else:
        st.info("No hay datos de bancas para mostrar.") 