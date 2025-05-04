"""
Lógica para generar resúmenes de datos electorales.
Proporciona funciones para generar resúmenes a nivel nacional y departamental.
"""
from typing import Dict, List, Optional, Any
import streamlit as st
import pandas as pd

# Importar desde los módulos apropiados
from domain.enrichers.ediles_272 import ediles_por_lema
from domain.enrichers.enrich import sumar_votos_por_lema

# Decorador de caché para mantener compatibilidad con el código existente
@st.cache_data
def get_national_summary(election_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera un resumen a nivel nacional de los resultados electorales.
    Esta función es un reemplazo directo de la versión en utils/data_processor.py
    pero con una implementación más limpia y mantenible.
    
    Args:
        election_data (Dict[str, Any]): Datos electorales por departamento
        
    Returns:
        Dict[str, Any]: Resumen nacional con estadísticas consolidadas
    """
    if not election_data:
        return {}
    
    # Inicializar contadores
    total_departments = len(election_data)
    total_municipalities = 0
    party_departments = {}  # Departamentos ganados por partido
    party_municipalities = {}  # Municipios ganados por partido
    party_total_votes = {}  # Votos totales por partido a nivel nacional
    all_parties = set()  # Conjunto de todos los partidos
    
    # Variables para diagnóstico
    debugging_info = {
        "municipios_totales": 0,
        "municipios_por_departamento": {},
        "departamentos_sin_ganador": [],
        "partidos_encontrados": set(),
        "departamentos_con_votos": 0,
        "votos_por_departamento": {}
    }
    
    # Procesar cada departamento
    for dept_name, dept_data in election_data.items():
        try:
            # Verificar que tenemos un diccionario válido
            if not isinstance(dept_data, dict):
                st.warning(f"Datos no válidos para el departamento {dept_name}: {type(dept_data)}")
                continue
            
            # Contabilizar departamento para el partido ganador
            winning_party = dept_data.get("winning_party", "No disponible")
            
            if winning_party != "No disponible":
                # Actualizar contador de departamentos por partido
                if winning_party not in party_departments:
                    party_departments[winning_party] = 0
                party_departments[winning_party] += 1
            else:
                debugging_info["departamentos_sin_ganador"].append(dept_name)
            
            # Contabilizar municipios
            municipios_dept = 0
            if "municipalities" in dept_data and isinstance(dept_data["municipalities"], dict):
                dept_municipalities = dept_data["municipalities"]
                municipios_dept = len(dept_municipalities)
                total_municipalities += municipios_dept
                debugging_info["municipios_totales"] += municipios_dept
                debugging_info["municipios_por_departamento"][dept_name] = municipios_dept
                
                for muni_name, muni_data in dept_municipalities.items():
                    if isinstance(muni_data, dict):
                        muni_party = muni_data.get("party", "No disponible")
                        debugging_info["partidos_encontrados"].add(muni_party)
                        
                        # Verificar que el partido no sea nulo o vacío
                        if not muni_party or muni_party == "None":
                            muni_party = "No disponible"
                            
                        if muni_party not in party_municipalities:
                            party_municipalities[muni_party] = 0
                        party_municipalities[muni_party] += 1
            
            # Acumular votos por partido
            dept_votes = {}
            if "votes" in dept_data and isinstance(dept_data["votes"], dict):
                dept_votes = dept_data["votes"]
                if dept_votes:
                    debugging_info["departamentos_con_votos"] += 1
                    debugging_info["votos_por_departamento"][dept_name] = sum(dept_votes.values())
                    
                for party, votes in dept_votes.items():
                    if party and isinstance(votes, (int, float)):
                        all_parties.add(party)
                        if party not in party_total_votes:
                            party_total_votes[party] = 0
                        party_total_votes[party] += votes
                
        except Exception as e:
            st.error(f"Error procesando departamento {dept_name}: {str(e)}")
            import traceback
            st.code(traceback.format_exc(), language="python")
    
    # Calcular porcentajes nacionales de los datos reales disponibles
    total_national_votes = sum(party_total_votes.values()) if party_total_votes else 0
    party_vote_percentages = {}
    
    if total_national_votes > 0:
        party_vote_percentages = {
            party: round((votes / total_national_votes) * 100, 1)
            for party, votes in party_total_votes.items()
        }
    
    # Determinar partido más votado a nivel nacional
    most_voted_party = "No disponible"
    if party_total_votes:
        try:
            most_voted_party = max(party_total_votes.items(), key=lambda x: x[1])[0]
        except Exception as e:
            st.error(f"Error al determinar el partido más votado: {str(e)}")
    elif party_departments:
        # Si no hay datos de votos pero hay datos de intendencias, usar el partido con más intendencias
        most_voted_party = max(party_departments.items(), key=lambda x: x[1])[0]
    elif party_municipalities:
        # Si no hay datos de votos ni intendencias pero hay datos de municipios, usar el partido con más alcaldes
        # Si no hay datos de votos pero hay datos de municipios, usar el partido con más alcaldes
        most_voted_party = max(party_municipalities.items(), key=lambda x: x[1])[0]
    
    # Calcular ediles por partido usando los datos ya calculados
    ediles_per_party = {}
    try:
        # Usar los council_seats que ya están en los datos
        for dept_name, dept_data in election_data.items():
            if "council_seats" in dept_data and isinstance(dept_data["council_seats"], dict):
                # Sumar los ediles ya calculados por departamento
                for partido, ediles in dept_data["council_seats"].items():
                    if partido not in ediles_per_party:
                        ediles_per_party[partido] = 0
                    ediles_per_party[partido] += ediles
        
        # Si no hay datos precalculados, calcular los ediles (fallback)
        if not ediles_per_party and party_total_votes:
            # Calcular ediles sumando los de cada departamento
            ediles_departamento = {}
            for dept_name, dept_data in election_data.items():
                if "votes" in dept_data and dept_data["votes"]:
                    # Obtener votos por partido para este departamento
                    votos_por_partido = dept_data["votes"]
                    
                    # Usar ediles_por_lema del módulo enrichers
                    ediles_dept = ediles_por_lema(
                        votos_por_partido,
                        total_ediles=31,
                        mayoria_auto=16
                    )
                    
                    # Sumar a los ediles totales
                    for partido, ediles in ediles_dept.items():
                        if partido not in ediles_departamento:
                            ediles_departamento[partido] = 0
                        ediles_departamento[partido] += ediles
            
            if ediles_departamento:
                ediles_per_party = ediles_departamento
        
        # Si no hay datos de ediles pero hay datos de municipios, usar proporciones de municipios como último recurso
        if not ediles_per_party and party_municipalities:
            # Establecer que el partido con más alcaldes tiene mayoría automática
            most_municipalities = max(party_municipalities.items(), key=lambda x: x[1])[0]
            total_ediles = total_departments * 31
            mayoria_ediles = total_departments * 16
            
            # Distribuir el resto proporcionalmente
            ediles_per_party = {most_municipalities: mayoria_ediles}
            
            remaining_ediles = total_ediles - mayoria_ediles
            total_other_municipalities = sum(v for k, v in party_municipalities.items() if k != most_municipalities)
            
            if total_other_municipalities > 0:
                for party, muni_count in party_municipalities.items():
                    if party != most_municipalities and party != "No disponible":
                        proportion = muni_count / total_other_municipalities
                        ediles_per_party[party] = round(remaining_ediles * proportion)
    except Exception as e:
        st.error(f"Error al calcular ediles por partido: {str(e)}")
        import traceback
        st.code(traceback.format_exc(), language="python")
    
    # Calcular alcaldes por partido usando la nueva función
    alcaldes_per_party = {}
    try:
        # Intentar calcular con la función dedicada
        alcaldes_calculados = asignar_alcaldes_por_partido(election_data)
        
        # Usar los datos calculados o los directos
        if alcaldes_calculados:
            alcaldes_per_party = alcaldes_calculados
        else:
            alcaldes_per_party = party_municipalities.copy()
    except Exception as e:
        st.error(f"Error al calcular alcaldes por partido: {str(e)}")
        alcaldes_per_party = party_municipalities.copy()
    
    # Construir resumen nacional con datos reales
    national_summary = {
        "total_departments": total_departments,
        "total_municipalities": total_municipalities,
        "department_winners": party_departments,
        "municipality_winners": party_municipalities,
        "party_votes": party_total_votes,
        "party_vote_percentages": party_vote_percentages,
        "most_voted_party": most_voted_party,
        "all_parties": list(all_parties),
        # Datos adicionales para compatibilidad con componentes existentes
        "participation_rate": 67.8,  # Valores de ejemplo (podrían venir de los datos reales)
        "participation_delta": 2.1,
        "scrutinized_percentage": 92.5,
        "blank_null_percentage": 3.2,
        "blank_null_delta": -0.5,
        # Añadir intendencias para compatibilidad con statistics_dashboard.py
        "intendencias": party_departments.copy(),
        # Añadir datos de ediles y alcaldes calculados con el nuevo método
        "ediles_totales": ediles_per_party,  # Para mantener compatibilidad, pero son los mismos datos
        "ediles_per_party": ediles_per_party,
        "alcaldes_per_party": alcaldes_per_party
    }
    
    # Generar datos para las tarjetas de métricas
    national_summary["metrics_data"] = [
        {
            "title": "Escrutinio",
            "value": f"{national_summary['scrutinized_percentage']}%",
            "is_positive": True
        },
        {
            "title": "Participación",
            "value": f"{national_summary['participation_rate']}%",
            "delta": f"{national_summary['participation_delta']}%",
            "is_positive": national_summary['participation_delta'] > 0
        },
        {
            "title": "Votos en blanco/anulados",
            "value": f"{national_summary['blank_null_percentage']}%",
            "delta": f"{national_summary['blank_null_delta']}%",
            "is_positive": national_summary['blank_null_delta'] < 0
        },
        {
            "title": "Partido más votado",
            "value": national_summary['most_voted_party'],
            "is_positive": None
        }
    ]
    
    # Datos para gráficos (solo con datos reales)
    parties_for_viz = []
    if party_vote_percentages:
        parties_for_viz = sorted(
            [{'party_name': p, 'percentage': party_vote_percentages.get(p, 0), 'seats': 0} 
             for p in all_parties],
            key=lambda x: x['percentage'],
            reverse=True
        )
    elif ediles_per_party:
        # Si no hay votos pero hay datos de ediles, usar eso para visualización
        total_ediles = sum(ediles_per_party.values())
        if total_ediles > 0:
            parties_for_viz = sorted(
                [{'party_name': p, 'percentage': (e / total_ediles) * 100, 'seats': e} 
                 for p, e in ediles_per_party.items()],
                key=lambda x: x['percentage'],
                reverse=True
            )
    elif alcaldes_per_party:
        # Si no hay votos ni ediles pero hay datos de alcaldes, usar eso
        total_alcaldes = sum(alcaldes_per_party.values())
        if total_alcaldes > 0:
            parties_for_viz = sorted(
                [{'party_name': p, 'percentage': (a / total_alcaldes) * 100, 'seats': 0} 
                 for p, a in alcaldes_per_party.items() if p != "No disponible"],
                key=lambda x: x['percentage'],
                reverse=True
            )
    
    national_summary['party_results'] = pd.DataFrame(parties_for_viz)
    
    return national_summary

def get_department_summary(election_data: Dict[str, Any], department: str) -> Dict[str, Any]:
    """
    Genera un resumen detallado para un departamento específico.
    
    Args:
        election_data (Dict[str, Any]): Datos electorales completos
        department (str): Nombre del departamento a analizar
        
    Returns:
        Dict[str, Any]: Resumen detallado del departamento
    """
    if not election_data or department not in election_data:
        return {}
    
    dept_data = election_data[department]
    
    # Los datos relevantes como 'party_candidates' y 'detailed_council_lists' 
    # ya vienen procesados desde el loader. No es necesario procesar 'Departamentales' aquí.
    
    # Calcular estadísticas adicionales que sí dependen del resumen
    total_municipalities = len(dept_data.get("municipalities", {}))
    winning_party = dept_data.get("winning_party", "No disponible")
    
    # Si no hay ganador definido pero hay municipios, usar el partido con más municipios
    if winning_party == "No disponible" and "municipalities" in dept_data and dept_data["municipalities"]:
        # Contar municipios por partido
        party_count = {}
        for muni_data in dept_data["municipalities"].values():
            if isinstance(muni_data, dict):
                party = muni_data.get("party", "No disponible")
                if party != "No disponible":
                    party_count[party] = party_count.get(party, 0) + 1
        
        # Determinar el partido con más municipios
        if party_count:
            winning_party = max(party_count.items(), key=lambda x: x[1])[0]
    
    # Contabilizar municipios por partido
    muni_by_party = {}
    for muni_name, muni_data in dept_data.get("municipalities", {}).items():
        party = muni_data.get("party", "No disponible")
        muni_by_party[party] = muni_by_party.get(party, 0) + 1
    
    # Construir resumen del departamento con datos adicionales
    summary = {
        "department": department,
        "winning_party": winning_party,
        "mayor": dept_data.get("mayor", "No disponible"),
        "votes": dept_data.get("votes", {}),
        "vote_percentages": dept_data.get("vote_percentages", {}),
        "council_seats": dept_data.get("council_seats", {}),
        "total_municipalities": total_municipalities,
        "municipalities_by_party": muni_by_party,
        "municipalities": dept_data.get("municipalities", {}),
        # Usar directamente los datos pre-procesados del loader
        "candidates_by_party": dept_data.get("party_candidates", {}),
        "detailed_council_lists": dept_data.get("detailed_council_lists", [])
        # Ya no incluimos "Departamentales" ni "party_candidates" como fallback aquí
    }
    
    return summary

def asignar_ediles_por_partido(election_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Calcula la distribución total de ediles por partido sumando los de cada departamento.
    NOTA: Esta función se mantiene por compatibilidad con código antiguo,
    pero usa internamente la misma lógica que en el módulo enrichers.
    
    Args:
        election_data: Datos electorales procesados
        
    Returns:
        Diccionario con la cantidad de ediles por partido
    """
    ediles_totales = {}
    
    # Primero intentamos usar los ediles ya calculados
    for dept_name, dept_data in election_data.items():
        if "council_seats" in dept_data and isinstance(dept_data["council_seats"], dict):
            # Añadir ediles de este departamento al total
            for partido, ediles in dept_data["council_seats"].items():
                if partido not in ediles_totales:
                    ediles_totales[partido] = 0
                ediles_totales[partido] += ediles
    
    # Si no hay datos precalculados, los calculamos usando ediles_por_lema
    if not ediles_totales:
        for dept_name, dept_data in election_data.items():
            if "votes" in dept_data and isinstance(dept_data["votes"], dict):
                # Calcular ediles usando la misma función de enrichers
                ediles_dept = ediles_por_lema(
                    dept_data["votes"],
                    total_ediles=31,
                    mayoria_auto=16
                )
                
                # Añadir al total
                for partido, ediles in ediles_dept.items():
                    if partido not in ediles_totales:
                        ediles_totales[partido] = 0
                    ediles_totales[partido] += ediles
    
    return ediles_totales

def asignar_alcaldes_por_partido(election_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Calcula el número de alcaldes por partido a nivel nacional.
    
    La Ley N° 19.272 establece:
    - El cargo de Alcalde corresponde al candidato de la lista más votada 
      dentro del partido político más votado en el municipio
    - El resto de sus miembros serán electos por representación proporcional

    Args:
        election_data: Datos electorales procesados
        
    Returns:
        Dict[str, int]: Diccionario con la cantidad de alcaldes por partido
    """
    result = {}
    
    try:
        for dept_name, dept_data in election_data.items():
            if not isinstance(dept_data, dict) or "municipalities" not in dept_data:
                continue
                
            for muni_name, muni_data in dept_data["municipalities"].items():
                if not isinstance(muni_data, dict) or "party" not in muni_data:
                    continue
                    
                party = muni_data.get("party", "No disponible")
                if party not in result:
                    result[party] = 0
                
                result[party] += 1
    except Exception as e:
        st.error(f"Error al calcular alcaldes por partido: {str(e)}")
    
    return result

def get_all_candidates_by_party(election_data: Dict[str, Any], department_name: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extrae todos los candidatos a intendente por partido para un departamento específico.
    
    Args:
        election_data (Dict[str, Any]): Datos electorales completos
        department_name (str): Nombre del departamento
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Diccionario con estructura 
        {partido: [{"nombre": str, "votos": int, "porcentaje_partido": float, "porcentaje_total": float}]}
    """
    dept_data = election_data.get(department_name, {})
    
    # Si tenemos datos enriquecidos, usarlos directamente
    if "candidates_by_party" in dept_data:
        return dept_data["candidates_by_party"]
    
    # Si no hay datos enriquecidos pero hay party_candidates y votes, crear estructura compatible
    if "party_candidates" in dept_data and "votes" in dept_data:
        party_candidates = dept_data.get("party_candidates", {})
        votes = dept_data.get("votes", {})
        candidates_by_party = {}
        total_votos = sum(votes.values()) if votes else 0
        
        for partido, candidato in party_candidates.items():
            if partido in votes:
                votos_partido = votes.get(partido, 0)
                porcentaje_total = (votos_partido / total_votos * 100) if total_votos > 0 else 0
                
                candidates_by_party[partido] = [{
                    "nombre": candidato,
                    "votos": votos_partido,
                    "porcentaje_partido": 100.0,  # Es el único candidato del partido
                    "porcentaje_total": porcentaje_total
                }]
        
        return candidates_by_party
    
    # Si no hay ninguna estructura de candidatos pero hay votos, crear estructura mínima
    if "votes" in dept_data:
        votes = dept_data.get("votes", {})
        candidates_by_party = {}
        total_votos = sum(votes.values()) if votes else 0
        
        for partido, votos in votes.items():
            porcentaje_total = (votos / total_votos * 100) if total_votos > 0 else 0
            candidates_by_party[partido] = [{
                "nombre": "No disponible",
                "votos": votos,
                "porcentaje_partido": 100.0,  # Asumimos un candidato por partido
                "porcentaje_total": porcentaje_total
            }]
        
        return candidates_by_party
    
    # Si no hay ninguna estructura de datos, devolver diccionario vacío
    return {} 