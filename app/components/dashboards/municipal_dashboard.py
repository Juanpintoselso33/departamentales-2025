"""
Dashboard para la visualización de datos electorales a nivel municipal.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
import json # Importar json para pretty print

from app.components.ui.cards import info_card, party_card # Mantener si se usan
from app.components.ui.charts import create_party_pie_chart, render_chart
from app.components.ui.tables import display_results_table # Puede necesitar adaptación
from app.components.ui.containers import section_container, tabs_container, stylable_container
# from app.components.ui.parliament_chart import render_parliament_chart # Eliminado

# Asumiendo que get_party_color está disponible o se moverá a utils
from settings.theme import get_party_color 

# --- Funciones Auxiliares D'Hondt eliminadas --- 
# --- La lógica ahora está en domain/enrichers/municipal_concejales.py ---

# --- get_municipal_summary eliminado --- 
# --- El dashboard ahora recibe los datos pre-procesados y enriquecidos --- 

def display_municipal_dashboard(election_data: Dict, department_name: str, municipality_name: str):
    """
    Muestra un dashboard completo con información electoral de un municipio.
    
    Args:
        election_data (dict): Datos electorales completos **y enriquecidos**.
        department_name (str): Nombre del departamento.
        municipality_name (str): Nombre del municipio a mostrar.
    """
    # Acceder directamente a los datos del municipio dentro de election_data
    muni_data = None # Inicializar
    error_msg = None
    try:
        dept_data = election_data.get(department_name, {})
        municipalities = dept_data.get("municipalities", {})
        muni_data = municipalities.get(municipality_name)

        if not muni_data or not isinstance(muni_data, dict):
            error_msg = f"No se encontraron datos válidos para el municipio '{municipality_name}' en '{department_name}'."
            
        elif not muni_data.get("votes"):
            st.warning(f"No hay datos de votos disponibles para el municipio {municipality_name}")

    except Exception as e:
        error_msg = f"Error accediendo a los datos del municipio {municipality_name}: {e}"
        import traceback
        st.code(traceback.format_exc())

    # --- INICIO DEBUG --- 
    with st.expander("🔍 DEBUG: Datos Municipales Recibidos por el Dashboard", expanded=True):
        st.write(f"Departamento: `{department_name}`, Municipio: `{municipality_name}`")
        if error_msg:
            st.error(f"Error al obtener muni_data: {error_msg}")
        elif muni_data:
            st.subheader("Diccionario `muni_data` completo:")
            try:
                # Usar json.dumps para formatear bien, manejar posible error
                st.json(json.dumps(muni_data, indent=2, ensure_ascii=False))
            except Exception as json_e:
                st.error(f"Error al serializar muni_data a JSON: {json_e}")
                st.write("Mostrando representación directa:")
                st.write(muni_data) 

            st.divider()
            st.subheader("Contenido específico de `muni_data.get('municipal_council_lists')`:")
            council_lists_data = muni_data.get("municipal_council_lists") # No poner default aquí para ver si existe
            
            if council_lists_data is None:
                st.error("¡ERROR! La clave `municipal_council_lists` NO fue encontrada en `muni_data`.")
            elif not isinstance(council_lists_data, list):
                st.error(f"¡ERROR! El valor para `municipal_council_lists` NO es una lista. Es de tipo: {type(council_lists_data)}")
                st.write("Valor encontrado:")
                st.write(council_lists_data)
            elif not council_lists_data:
                st.warning("La clave `municipal_council_lists` fue encontrada, pero la lista está VACÍA.")
            else:
                st.success("La clave `municipal_council_lists` fue encontrada y contiene elementos.")
                st.write(f"Número de listas encontradas: {len(council_lists_data)}")
                st.json(json.dumps(council_lists_data, indent=2, ensure_ascii=False))
                st.divider()
                st.subheader("Claves del primer elemento en `municipal_council_lists`:")
                try:
                    first_item_keys = list(council_lists_data[0].keys()) if isinstance(council_lists_data[0], dict) else "El primer elemento no es un diccionario."
                    st.write(first_item_keys)
                    st.write("Claves esperadas para la tabla: `Partido`, `Sublema`, `Nº Lista`, `Primer Candidato`, `Votos`, `Concejales Asignados`, `Resto D'Hondt`")
                except Exception as key_e:
                    st.error(f"Error al obtener las claves del primer elemento: {key_e}")
        else:
            st.warning("El objeto `muni_data` es None o vacío después del intento de carga.")
    # --- FIN DEBUG --- 

    # Si hubo error fatal al cargar, no continuar con la UI
    if error_msg and not muni_data:
        st.error(error_msg) # Mostrar el error principal
        return 
    
    # Si muni_data está vacío pero no hubo error fatal (ej. solo faltan votos)
    # podemos decidir si mostrar algo o no. Por ahora, intentaremos mostrar.
    if not muni_data:
        st.warning("No se pudo cargar la información detallada del municipio.")
        return

    # Inyectar CSS (similar al departamental, ajustar si es necesario)
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
        margin-top: 0 !important; /* Añadido para consistencia */
    }
    /* Ajustar espaciado de los separadores */
    hr {
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
     /* Alinear columnas */
    [data-testid="column"] {
        padding: 0 !important;
        margin-top: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # PRIMERA FILA: Título, información del alcalde y distribución de votos
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title(f"Municipio: {muni_data.get('name', municipality_name)}")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Gráfico de Torta de Votos Municipales
        votos = muni_data.get("votes", {})
        if votos:
            votos_filtrados = {party: vote for party, vote in votos.items() if vote > 0}
            if votos_filtrados:
                pie_chart = create_party_pie_chart(votos_filtrados, show_percentages=True)
                render_chart(pie_chart, height="300px")
            else:
                st.info("No hay votos válidos para mostrar en el gráfico.")
        else:
            st.info("No hay datos de votos para este municipio.")
            
    with col2:
        # Información del Alcalde
        # winning_party = muni_data.get("winning_party", "No disponible") # IGNORAR EL VALOR QUE VIENE
        mayor = muni_data.get("mayor", "No disponible")
        votos = muni_data.get("votes", {})
        total_votes = sum(votos.values()) if votos else 0
        
        # --- RECALCULAR GANADOR Y VOTOS DIRECTAMENTE DESDE 'votes' --- 
        winning_party = "No disponible" # Default
        winner_votes = 0
        if votos: 
            try:
                # Encontrar la clave (partido) con el máximo valor (votos)
                winning_party = max(votos.items(), key=lambda item: item[1])[0]
                winner_votes = votos.get(winning_party, 0) # Obtener votos del ganador recalculado
            except ValueError: # Manejar caso donde votos está vacío después de filtrar?
                winning_party = "No disponible"
                winner_votes = 0
        # --- FIN RECALCULO --- 
        
        vote_percentage = (winner_votes / total_votes * 100) if total_votes > 0 else 0
        party_color = get_party_color(winning_party)

        # --- DEBUG: Valores para tarjeta de alcalde --- 
        # st.sidebar.write("--- DEBUG Tarjeta Alcalde ---")
        # st.sidebar.write(f"Municipio: {municipality_name}")
        # st.sidebar.write(f"Valor de winning_party (ORIGINAL): {muni_data.get('winning_party')}") # Mostrar original
        # st.sidebar.write(f"Valor de winning_party (RECALCULADO): {winning_party}") # Mostrar recalculado
        # st.sidebar.write(f"Diccionario de votos: {votos}")
        # st.sidebar.write(f"Valor de winner_votes (buscado con recalculado): {winner_votes}")
        # st.sidebar.write(f"Valor de vote_percentage: {vote_percentage}")
        # st.sidebar.write("------------------------------")
        # --- FIN DEBUG (Eliminado) --- 

        with stylable_container(
            key=f"mayor_info_{municipality_name.replace(' ','_')}", # Key más específica
            css_styles=f"""
                {{
                    background-color: rgba(30, 41, 59, 0.5);
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    border-radius: 8px;
                    padding: 1.5rem;
                    margin: 0 0 1rem 0; /* Ajuste margen */
                    height: 300px; /* Intentar fijar altura similar al gráfico */
                    display: flex;
                    flex-direction: column;
                    justify-content: center; /* Centrar contenido verticalmente */
                }}
            """
        ):
            st.markdown("""
                <div style='font-size: 1.1rem; color: rgba(255,255,255,0.7); margin-bottom: 1rem; text-align: center;'>
                Alcalde/sa Electo/a
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <div style='
                    border-left: 4px solid {party_color};
                    padding-left: 0.75rem;
                    margin-bottom: 1.5rem;
                    background: linear-gradient(90deg, rgba({party_color.lstrip('#')}, 0.1) 0%, rgba(30, 41, 59, 0) 100%);
                '>
                    <h2 style='margin: 0; font-size: 1.4rem; color: white;'>{winning_party}</h2>
                </div>
            """, unsafe_allow_html=True)
            
            # Mostrar nombre del alcalde(s)
            # El campo 'mayor' puede contener varios nombres, los mostramos
            mayor_display = mayor.replace("  ", "<br>") # Simple reemplazo para posible formato
            st.markdown(f"""
                <div style='display: flex; align-items: center; margin-bottom: 1.5rem; padding: 0.75rem; background: rgba(0,0,0,0.2); border-radius: 4px;'>
                    <div style='font-size: 1.5rem; margin-right: 0.75rem; color: rgba(255,255,255,0.6);'>👤</div>
                    <div style='color: white; font-size: 1.0rem; line-height: 1.3;'>{mayor_display}</div>
                </div>
            """, unsafe_allow_html=True)

            # Métricas (Votos y Porcentaje del Partido Ganador)
            st.markdown(f"""
                <div style='display: flex; justify-content: space-around; align-items: center; margin-top: 1rem;'>
                    <div style='text-align: center;'>
                        <div style='font-size: 1.5rem; font-weight: bold; color: white;'>{vote_percentage:.1f}%</div>
                        <div style='color: rgba(255,255,255,0.6); font-size: 0.9rem;'>Partido Ganador</div>
                    </div>
                    <div style='text-align: center;'>
                        <div style='font-size: 1.5rem; font-weight: bold; color: white;'>{total_votes:,}</div>
                        <div style='color: rgba(255,255,255,0.6); font-size: 0.9rem;'>Total Votos Mun.</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # Cierre de main-header
    st.markdown("<hr>", unsafe_allow_html=True) # Separador

    # SEGUNDA FILA: Resultados detallados (sin pestañas)
    st.header("Resultados Detallados del Municipio")
    
    # Mostrar tabla de listas al concejo municipal (ahora directamente bajo Resultados Detallados)
    st.subheader("Resultados por Lista al Concejo Municipal")
    # Acceder al campo correcto con los datos enriquecidos
    listas_data = muni_data.get("municipal_council_lists", [])
    if listas_data:
        # Convertir a DataFrame para mostrar en tabla
        try:
            df_listas = pd.DataFrame(listas_data)
            st.write("--- DEBUG: DataFrame Creado ---") # Debug
            st.dataframe(df_listas.head()) # Debug: Mostrar head del df raw
        except Exception as e:
            st.error(f"Error al crear DataFrame desde listas_data: {e}")
            st.json(listas_data) # Mostrar los datos que causaron error
            return # Salir si no se puede crear el DataFrame

        # Seleccionar y renombrar columnas para la tabla
        # Asegurarse que las claves aquí coinciden EXACTAMENTE con las del diccionario
        column_config = {
            "Partido": "Partido",
            "Sublema": "Sublema",
            "Nº Lista": "Nº Lista", 
            "Primer Candidato": "Primer Candidato", # Clave EXACTA del diccionario
            "Votos": "Votos",
            "Concejales_Asignados": "Concejales",
            "Resto_Dhondt": "Resto D'Hondt"
        }
        
        # Verificar que las columnas existen antes de seleccionarlas (más robusto)
        available_cols_stripped = [c.strip() for c in df_listas.columns]
        cols_to_show = []
        missing_cols = []
        for expected_col in column_config.keys():
            if expected_col.strip() in available_cols_stripped:
                cols_to_show.append(expected_col) # Usar la clave original
            else:
                missing_cols.append(expected_col)
        
        if missing_cols:
            st.warning(f"DEBUG: Columnas esperadas no encontradas en el DataFrame: {missing_cols}")
            st.write("Columnas disponibles:", df_listas.columns.tolist())

        if not cols_to_show:
            st.error("Error: Ninguna columna esperada encontrada para mostrar la tabla de listas.")
            return

        # Crear el DataFrame para mostrar, renombrando columnas
        try:
            df_display = df_listas[cols_to_show].rename(columns=column_config)
        except KeyError as e:
             st.error(f"Error al seleccionar/renombrar columnas: {e}")
             st.write("Columnas a mostrar:", cols_to_show)
             st.write("Columnas disponibles en df:", df_listas.columns.tolist())
             return

        # Configuración de columnas para Streamlit (opcional, para formato)
        st_column_config = {
             "Concejales": st.column_config.NumberColumn(format="%d"),
             "Resto D'Hondt": st.column_config.NumberColumn(format="%.2f")
        }
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config=st_column_config
        )

        # --- INICIO DISCLAIMER --- 
        st.caption("""
        **Nota:** El cálculo de la asignación de concejales por lista mediante el método D'Hondt es una interpretación realizada por esta aplicación basada en los votos por lista y el total de escaños por partido, y **no representa un dato oficial de la Corte Electoral**. Pueden existir reglas adicionales o ajustes no contemplados.
        """)
        # --- FIN DISCLAIMER --- 

    else:
        st.info("No hay datos sobre listas al concejo municipal (o el campo 'municipal_council_lists' está vacío) para este municipio.")

# Ejemplo de cómo podrías llamarlo (esto iría en app.py eventualmente)
# if __name__ == '__main__':
#     # Esto es solo para prueba y requiere datos de ejemplo
#     # Cargar datos de ejemplo 'election_data_sample' 
#     # department = "Canelones" 
#     # municipality = "A  CIUDAD DE LA COSTA" # Usar el ejemplo del usuario
#     # display_municipal_dashboard(election_data_sample, department, municipality)
#     st.warning("Ejecución directa de este script requiere datos de ejemplo.") 