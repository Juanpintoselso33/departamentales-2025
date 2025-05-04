"""
Componentes de tarjetas para la interfaz de usuario.
Proporciona elementos visuales de tipo tarjeta reutilizables.
"""

import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.metric_cards import style_metric_cards
from utils.styles import get_container_style, create_card_container, close_container

def stat_card(title, value, delta=None, icon=None, use_native=False):
    """
    Crea una tarjeta de estadística con un título, valor y opcional delta e icono
    
    Args:
        title (str): Título de la estadística
        value (str): Valor principal de la estadística
        delta (str, opcional): Cambio respecto al valor anterior
        icon (str, opcional): Emoji o icono para mostrar
        use_native (bool, opcional): Si True, usa componentes nativos de Streamlit
    """
    if use_native:
        st.metric(label=title, value=value, delta=delta)
        # Aplicar estilo mejorado a las métricas
        style_metric_cards()
    else:
        # Usar los estilos del módulo centralizado
        st.markdown(create_card_container(title), unsafe_allow_html=True)
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        
        # Añadir icono si se proporciona
        if icon:
            st.markdown(f"<div style='font-size: 2rem; text-align: center; margin-bottom: 0.5rem;'>{icon}</div>", unsafe_allow_html=True)
        
        # Añadir la métrica - usar título como label pero ocultarla
        st.metric(label=title, value=value, delta=delta, label_visibility="collapsed")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(close_container(), unsafe_allow_html=True)

def scrutiny_card(title, value, icon=None, use_native=False):
    """
    Crea una tarjeta específica para escrutinio electoral que evita problemas de HTML
    
    Args:
        title (str): Título de la estadística
        value (str): Porcentaje o valor de escrutinio
        icon (str, opcional): Emoji o icono para mostrar
        use_native (bool, opcional): Si True, usa componentes nativos de Streamlit
    """
    if use_native:
        with stylable_container(
            key=f"scrutiny_{title.lower().replace(' ', '_')}",
            css_styles=get_container_style("default")
        ):
            st.markdown(f"#### {title}")
            st.markdown(f"### {value}")
            if icon:
                st.markdown(f"{icon}")
    else:
        st.markdown(create_card_container(title), unsafe_allow_html=True)
        
        # Mostrar valor y opcionalmente el icono
        value_col, icon_col = st.columns([3, 1]) if icon else (st, None)
        
        with value_col:
            st.markdown(f"<p style='font-size: 1.5rem; font-weight: bold;'>{value}</p>", unsafe_allow_html=True)
        
        if icon and icon_col:
            with icon_col:
                st.markdown(f"<div style='font-size: 2rem; text-align: center;'>{icon}</div>", unsafe_allow_html=True)
        
        st.markdown(close_container(), unsafe_allow_html=True)

def info_card(title, content, footer=None, icon=None, use_native=False):
    """
    Crea una tarjeta de información con título, contenido y opcional pie de página e icono
    
    Args:
        title (str): Título de la tarjeta
        content (str): Contenido principal de la tarjeta
        footer (str, opcional): Texto pequeño al pie de la tarjeta
        icon (str, opcional): Emoji o icono para mostrar
        use_native (bool, opcional): Si True, usa componentes nativos de Streamlit
    """
    if use_native:
        with stylable_container(
            key=f"info_{title.lower().replace(' ', '_')}",
            css_styles=get_container_style("info_panel")
        ):
            st.subheader(title)
            st.markdown(f"### {content}")
            if footer:
                st.caption(footer)
            if icon:
                st.markdown(f"<div style='font-size: 2rem; text-align: right;'>{icon}</div>", unsafe_allow_html=True)
    else:
        st.markdown(create_card_container(title), unsafe_allow_html=True)
        
        # Contenido principal
        st.markdown(f"<p style='font-size: 1.2rem;'>{content}</p>", unsafe_allow_html=True)
        
        # Pie de página opcional
        if footer:
            st.caption(footer)
        
        # Icono opcional
        if icon:
            st.markdown(f"<div style='font-size: 2rem; text-align: right;'>{icon}</div>", unsafe_allow_html=True)
        
        st.markdown(close_container(), unsafe_allow_html=True)

def party_card(party_name, votes_pct, color="#3B82F6", candidate=None, position=None, use_native=False):
    """
    Crea una tarjeta para mostrar resultados de un partido político
    
    Args:
        party_name (str): Nombre del partido
        votes_pct (float): Porcentaje de votos
        color (str, opcional): Color representativo del partido
        candidate (str, opcional): Nombre del candidato
        position (str, opcional): Puesto o cargo
        use_native (bool, opcional): Si True, usa componentes nativos de Streamlit
    """
    if use_native:
        # Convertir color HEX a RGBA para fondo transparente
        hex_to_rgb = lambda h: tuple(int(h.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        bg_color = f"rgba{hex_to_rgb(color) + (0.1,)}"
        
        # Usar un contenedor estilizable para mejor control del estilo
        with stylable_container(
            key=f"party_card_{party_name.lower().replace(' ', '_')}",
            css_styles=f"""
                {{
                    background-color: {bg_color};
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    border-radius: 8px;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }}
                div:first-child {{
                    margin-top: 0;
                }}
                div:last-child {{
                    margin-bottom: 0;
                }}
            """
        ):
            # Mostrar nombre del partido con estilo
            st.markdown(f"""
                <div style='
                    border-left: 4px solid {color};
                    padding-left: 0.75rem;
                    margin-bottom: 0.5rem;
                    background: linear-gradient(90deg, {bg_color} 0%, rgba(30, 41, 59, 0) 100%);
                '>
                    <h3 style='
                        margin: 0;
                        font-size: 1.2rem;
                        color: white;
                        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
                    '>{party_name}</h3>
                </div>
            """, unsafe_allow_html=True)
            
            # Mostrar porcentaje de votos
            st.markdown(f"""
                <div style='
                    font-size: 2rem;
                    font-weight: bold;
                    color: white;
                    margin: 0.5rem 0;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
                '>{votes_pct:.1f}%</div>
            """, unsafe_allow_html=True)
            
            # Mostrar candidato si existe
            if candidate:
                st.markdown(f"""
                    <div style='
                        font-size: 1rem;
                        color: rgba(255, 255, 255, 0.9);
                        margin-bottom: 0.25rem;
                        text-shadow: 1px 1px 1px rgba(0,0,0,0.1);
                    '>{candidate}</div>
                """, unsafe_allow_html=True)
            
            # Mostrar posición si existe
            if position:
                st.markdown(f"""
                    <div style='
                        font-size: 0.9rem;
                        color: rgba(255, 255, 255, 0.7);
                        text-shadow: 1px 1px 1px rgba(0,0,0,0.1);
                    '>{position}</div>
                """, unsafe_allow_html=True)
    else:
        # Usar el contenedor básico sin título explícito
        st.markdown(create_card_container(), unsafe_allow_html=True)
        
        # Estilo personalizado con el color del partido
        st.markdown(f"""
        <div style="border-left: 4px solid {color}; padding-left: 0.75rem;">
            <h3 style="margin: 0; font-size: 1.1rem;">{party_name}</h3>
            <p style="margin: 0.5rem 0; font-size: 1.5rem; font-weight: bold;">{votes_pct}%</p>
            {f'<p style="margin: 0; font-size: 0.9rem;">{candidate}</p>' if candidate else ''}
            {f'<p style="margin: 0; font-size: 0.8rem; color: #94A3B8;">{position}</p>' if position else ''}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(close_container(), unsafe_allow_html=True)

def custom_card(html_content):
    """
    Crea una tarjeta personalizada con contenido HTML
    
    Args:
        html_content (str): Contenido HTML a mostrar dentro de la tarjeta
    """
    st.markdown(create_card_container(), unsafe_allow_html=True)
    st.markdown(html_content, unsafe_allow_html=True)
    st.markdown(close_container(), unsafe_allow_html=True) 