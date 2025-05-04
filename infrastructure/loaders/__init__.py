"""
Sistema de carga y detección automática de formatos de datos electorales.
Detecta la versión (año) del archivo JSON y utiliza el adaptador correspondiente.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Set, Any, Union, Tuple, Optional
import geopandas as gpd

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("infrastructure.loaders")

# Importar las dependencias del dominio
from domain.models import ElectionSummary
from domain.enrichers import ElectionSummaryEnriquecido
from domain.enrichers.enrich import enrich_department_data

# Importar los diferentes adaptadores
from . import v2020, v2025
from .cache import get_summary, get_streamlit_cached_summary

# Detectar si estamos en un entorno Streamlit para usar el caché apropiado
IN_STREAMLIT = 'streamlit' in os.path.basename(os.environ.get('_', ''))

# Firmas para detectar automáticamente la versión
_SIGNATURES: Dict[str, Set[str]] = {
    "v2020": {"DN", "TA", "TO", "TH", "Departamentales", "Municipales"},  # claves que existen en 2020
    # "v2025": {"VBLA", "VAN", ...},  # pendiente de definir cuando se conozca el formato
}

def detect_load(path: Union[str, Path]) -> ElectionSummary:
    """
    Detecta automáticamente el formato del archivo JSON y utiliza el adaptador correspondiente.
    
    Args:
        path: Ruta al archivo JSON
        
    Returns:
        ElectionSummary: Modelo canónico con los datos cargados
    """
    # Convertir a Path si es string
    if isinstance(path, str):
        path = Path(path)
        
    # Leer el primer elemento del JSON para detectar el formato
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if not data:
            raise RuntimeError("Archivo JSON vacío")
        
        first = data[0]
        keys = set(first.keys())
        
        # Verificar firmas
        if _SIGNATURES["v2020"].issubset(keys):
            return v2020.load(str(path))
        
        # Placeholder para futuras versiones
        # if _SIGNATURES["v2025"].issubset(keys):
        #     return v2025.load(str(path))
        
        # Si no se encontró una firma coincidente
        raise RuntimeError(f"Formato de archivo no reconocido. Claves encontradas: {keys}")

def load_election_data(year: int, data_dir: str = "data") -> Dict[str, Any]:
    """
    Carga los datos electorales de un año específico.
    
    Args:
        year (int): Año de la elección
        data_dir (str): Directorio base de datos
        
    Returns:
        Dict[str, Any]: Datos electorales procesados y enriquecidos
    """
    # Cargar datos crudos
    raw_data = _load_raw_data(year, data_dir)
    
    # Procesar datos por departamento
    processed_data = {}
    for dept_name, dept_data in raw_data.items():
        # Procesar datos básicos
        dept_processed = _process_department_data(dept_data)
        
        # Enriquecer datos con información adicional
        dept_enriched = enrich_department_data(dept_processed)
        
        processed_data[dept_name] = dept_enriched
    
    return processed_data

def _process_department_data(dept_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa los datos crudos de un departamento.
    
    Args:
        dept_data: Datos crudos del departamento
        
    Returns:
        Dict con los datos procesados
    """
    processed = {
        "name": dept_data.get("DN", ""),
        "id": dept_data.get("DI", ""),
        # Preservar datos originales de Departamentales
        "Departamentales": []
    }
    
    # Procesar votos por partido y candidatos
    votos_por_partido = {}
    party_candidates = {}
    
    # Procesar datos departamentales
    if "Departamentales" in dept_data:
        processed["Departamentales"] = dept_data["Departamentales"]
        for partido in dept_data["Departamentales"]:
            nombre_partido = partido.get("LN", "")
            votos = partido.get("Tot", 0)
            
            if nombre_partido:
                votos_por_partido[nombre_partido] = votos
                
                # Extraer candidatos desde las hojas
                if "Hojas" in partido:
                    candidatos = []
                    for hoja in partido["Hojas"]:
                        nombre_candidato = hoja.get("Dsc", "")  # Nombre del candidato
                        votos_hoja = hoja.get("Tot", 0)  # Votos de la hoja
                        votos_al_lema = hoja.get("VAL", 0)  # Votos al lema
                        
                        if nombre_candidato:
                            candidatos.append({
                                "nombre": nombre_candidato,
                                "votos_hojas": votos_hoja,
                                "votos_al_lema": votos_al_lema,
                                "votos": votos_hoja + votos_al_lema
                            })
                    
                    if candidatos:
                        # Guardar TODOS los candidatos, no solo el más votado
                        party_candidates[nombre_partido] = candidatos
    
    # Calcular porcentajes
    total_votos = sum(votos_por_partido.values()) if votos_por_partido else 0
    porcentajes = {}
    if total_votos > 0:
        porcentajes = {
            partido: round((votos / total_votos) * 100, 1)
            for partido, votos in votos_por_partido.items()
        }
    
    # Determinar partido ganador y candidato ganador
    partido_ganador = max(votos_por_partido.items(), key=lambda x: x[1])[0] if votos_por_partido else "No disponible"
    candidato_ganador = party_candidates.get(partido_ganador, [{"nombre": "No disponible"}])[0]["nombre"] if party_candidates else "No disponible"
    
    processed.update({
        "winning_party": partido_ganador,
        "mayor": candidato_ganador,
        "votes": votos_por_partido,
        "vote_percentages": porcentajes,
        "party_candidates": party_candidates,
        "all_candidates": True  # Flag para indicar que tenemos todos los candidatos
    })
    
    # Mantener los datos de Departamentales si existen
    if "Departamentales" in dept_data:
        departamentales_data = dept_data["Departamentales"]
        processed["Departamentales"] = departamentales_data # Mantener datos originales
        
        # Procesar listas de la Junta Departamental
        detailed_council_lists = []
        if isinstance(departamentales_data, list):
            for partido_data in departamentales_data:
                partido_nombre = partido_data.get("LN", "N/A")
                if "Junta" in partido_data and "Sublemas" in partido_data["Junta"]:
                    for sublema in partido_data["Junta"]["Sublemas"]:
                        sublema_nombre = sublema.get("Nombre", "N/A")
                        if "ListasJunta" in sublema:
                            for lista in sublema["ListasJunta"]:
                                lista_desc = lista.get("Dsc", "N/A")
                                votos_lista = lista.get("Tot", 0)
                                # Podríamos añadir más detalles si fuera necesario (LId, VAL, etc.)
                                detailed_council_lists.append({
                                    "Partido": partido_nombre,
                                    "Sublema": sublema_nombre,
                                    "Lista": lista_desc,
                                    "Votos": votos_lista
                                })
        
        processed["detailed_council_lists"] = detailed_council_lists
    
    # Procesar datos de municipios
    municipios = {}
    if "Municipales" in dept_data:
        for muni in dept_data["Municipales"]:
            muni_name = muni.get("MD", "").strip()
            if not muni_name:
                continue
                
            # Procesar votos por partido en el municipio
            votos_muni = {}
            for partido in muni.get("Eleccion", []):
                nombre_partido = partido.get("LN", "")
                votos = partido.get("Tot", 0)
                if nombre_partido:
                    votos_muni[nombre_partido] = votos
            
            # Calcular porcentajes municipales
            total_votos_muni = sum(votos_muni.values()) if votos_muni else 0
            porcentajes_muni = {}
            if total_votos_muni > 0:
                porcentajes_muni = {
                    partido: round((votos / total_votos_muni) * 100, 1)
                    for partido, votos in votos_muni.items()
                }
            
            # Determinar partido ganador municipal
            partido_ganador_muni = max(votos_muni.items(), key=lambda x: x[1])[0] if votos_muni else "No disponible"
            
            municipios[muni_name] = {
                "name": muni_name,
                "id": muni.get("MI", 0),
                "party": partido_ganador_muni,
                "mayor": "No disponible",  # Por ahora no tenemos este dato
                "votes": votos_muni,
                "vote_percentages": porcentajes_muni
            }
    
    processed["municipalities"] = municipios
    
    return processed

def _process_party_data(partido: Any) -> Dict[str, Any]:
    """
    Procesa los datos de un partido.
    
    Args:
        partido (Any): Datos del partido
        
    Returns:
        Dict[str, Any]: Datos procesados del partido
    """
    if not partido:
        return {}
        
    partido_dict = {
        "LI": getattr(partido, "LI", 0),
        "LN": getattr(partido, "LN", ""),
        "Tot": getattr(partido, "Tot", 0)
    }
    
    # Procesar datos de Intendente
    if hasattr(partido, "Intendente"):
        partido_dict["Intendente"] = {
            "Listas": [],
            "Tot": getattr(partido.Intendente, "Tot", 0)
        }
        
        if hasattr(partido.Intendente, "Listas"):
            for lista in partido.Intendente.Listas:
                lista_dict = {
                    "HI": getattr(lista, "HI", 0),
                    "HN": getattr(lista, "HN", ""),
                    "Tot": getattr(lista, "Tot", 0)
                }
                partido_dict["Intendente"]["Listas"].append(lista_dict)
    
    return partido_dict

def _process_municipality_data(municipio: Any) -> Dict[str, Any]:
    """
    Procesa los datos de un municipio.
    
    Args:
        municipio (Any): Datos del municipio
        
    Returns:
        Dict[str, Any]: Datos procesados del municipio
    """
    if not municipio:
        return {}
        
    return {
        "MI": getattr(municipio, "MI", 0),
        "MD": getattr(municipio, "MD", ""),
        "Tot": getattr(municipio, "Tot", 0),
        "Eleccion": [
            _process_party_data(partido)
            for partido in getattr(municipio, "Eleccion", [])
            if partido
        ]
    }

def load_geo_data(path: Union[str, Path]) -> Optional[gpd.GeoDataFrame]:
    """
    Carga datos geográficos desde un shapefile.
    
    Args:
        path: Ruta al shapefile
        
    Returns:
        GeoDataFrame con los datos geográficos o None si hay error
    """
    try:
        if not Path(path).exists():
            log.error(f"No se encontró el archivo: {path}")
            return None
            
        log.info(f"Cargando datos geográficos desde: {path}")
        
        # Añadir caché si estamos en Streamlit
        if IN_STREAMLIT:
            try:
                import streamlit as st
                @st.cache_data(ttl=3600)
                def cached_geo_load(p):
                    return gpd.read_file(p)
                gdf = cached_geo_load(path)
            except ImportError:
                gdf = gpd.read_file(path)
        else:
            gdf = gpd.read_file(path)
            
        log.info(f"Datos geográficos cargados correctamente: {len(gdf)} registros")
        return gdf
        
    except Exception as e:
        log.error(f"Error al cargar datos geográficos: {str(e)}")
        if os.getenv("DEBUG") == "1":
            import traceback
            log.debug(traceback.format_exc())
        return None

def _transform_to_frontend_format(
    summary: ElectionSummaryEnriquecido, 
    stats: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """
    Transforma el modelo enriquecido al formato esperado por el frontend.
    
    Args:
        summary: ElectionSummaryEnriquecido con resultados de la elección
        stats: Estadísticas nacionales
        
    Returns:
        Dict: Datos en formato compatible con el frontend
    """
    result = {}
    
    # Procesar cada departamento
    for depto in summary.departamentos:
        # Crear entrada para este departamento
        dept_data = {
            "name": depto.DN,
            "id": depto.DI,
            "winning_party": depto.ganador,
            "mayor": "No disponible",
            "votes": {},
            "vote_percentages": {},
            "council_seats": depto.ediles,
            "municipalities": {},
            "party_candidates": {},  # Lista completa de candidatos por partido
            "all_candidates": True  # Flag para indicar que tenemos todos los candidatos
        }
        
        # Procesar candidatos por partido
        for partido in depto.Departamentales:
            partido_nombre = partido.LN
            candidatos = []
            
            # Buscar todos los candidatos a Intendente en este partido
            if hasattr(partido, 'Intendente') and hasattr(partido.Intendente, 'Listas'):
                for candidato in partido.Intendente.Listas:
                    nombre_candidato = candidato.Dsc if hasattr(candidato, 'Dsc') else "No disponible"
                    votos_totales = candidato.Tot if hasattr(candidato, 'Tot') else 0
                    votos_hojas = candidato.VH if hasattr(candidato, 'VH') else 0
                    votos_al_lema = candidato.VAL if hasattr(candidato, 'VAL') else 0
                    
                    candidatos.append({
                        "nombre": nombre_candidato,
                        "votos": votos_totales,
                        "votos_hojas": votos_hojas,
                        "votos_al_lema": votos_al_lema
                    })
            
            # Guardar todos los candidatos del partido
            if candidatos:
                dept_data["party_candidates"][partido_nombre] = candidatos
                
                # El candidato con más votos será el intendente si este es el partido ganador
                if partido_nombre == depto.ganador:
                    candidato_ganador = max(candidatos, key=lambda x: x["votos"])
                    dept_data["mayor"] = candidato_ganador["nombre"]
        
        # Agregar votos por partido a nivel departamental
        for partido in depto.Departamentales:
            dept_data["votes"][partido.LN] = partido.Tot
            
        # Calcular porcentajes
        total_votes = sum(dept_data["votes"].values())
        if total_votes > 0:
            for party, votes in dept_data["votes"].items():
                dept_data["vote_percentages"][party] = round((votes / total_votes) * 100, 1)
        
        # Procesar listas de Junta Departamental (sin guardar la estructura original compleja)
        detailed_council_lists = []
        if hasattr(depto, 'Departamentales'):
            for partido_data in depto.Departamentales:
                partido_nombre = partido_data.LN if hasattr(partido_data, 'LN') else "N/A"
                if hasattr(partido_data, 'Junta') and hasattr(partido_data.Junta, 'Sublemas'):
                    for sublema in partido_data.Junta.Sublemas:
                        sublema_nombre = sublema.Nombre if hasattr(sublema, 'Nombre') else "N/A"
                        if hasattr(sublema, 'ListasJunta'):
                            for lista in sublema.ListasJunta:
                                lista_desc = lista.Dsc if hasattr(lista, 'Dsc') else "N/A"
                                votos_lista = lista.Tot if hasattr(lista, 'Tot') else 0
                                # Podríamos añadir más detalles si fuera necesario (LId, VAL, etc.)
                                detailed_council_lists.append({
                                    "Partido": partido_nombre,
                                    "Sublema": sublema_nombre,
                                    "Lista": lista_desc,
                                    "Votos": votos_lista
                                })
        dept_data["detailed_council_lists"] = detailed_council_lists

        # Procesar cada municipio
        for muni in depto.Municipales:
            # Crear datos del municipio
            muni_data = {
                "name": muni.MD,
                "id": muni.MI,
                "party": muni.ganador,
                "mayor": "No disponible",  # Valor predeterminado
                "votes": {},
                "vote_percentages": {},
                "council_seats": muni.ediles
            }
            
            # Si hay información de alcalde en los datos originales, usarla
            if hasattr(muni, 'CAlcalde') and muni.CAlcalde:
                muni_data["mayor"] = muni.CAlcalde
                
            if hasattr(muni, 'CAlcaldeIcon') and muni.CAlcaldeIcon:
                muni_data["mayor_icon"] = muni.CAlcaldeIcon
            
            # Agregar votos por partido a nivel municipal
            for partido in muni.Eleccion:
                muni_data["votes"][partido.LN] = partido.Tot
            
            # Intentar obtener el candidato más votado del partido ganador del municipio
            if muni.ganador:
                # Buscar el partido ganador en los datos municipales
                for partido in muni.Eleccion:
                    if partido.LN == muni.ganador:
                        # Para el partido más votado, determinar el candidato más votado
                        if hasattr(partido, 'Municipio') and hasattr(partido.Municipio, 'Sublemas'):
                            # Buscar la lista más votada dentro del partido
                            sublema_mas_votado = None
                            max_votos_sublema = 0
                            
                            for sublema in partido.Municipio.Sublemas:
                                if hasattr(sublema, 'Tot') and sublema.Tot > max_votos_sublema:
                                    max_votos_sublema = sublema.Tot
                                    sublema_mas_votado = sublema
                            
                            # Si encontramos el sublema más votado, buscar la lista más votada
                            if sublema_mas_votado and hasattr(sublema_mas_votado, 'ListasMunicipio'):
                                lista_mas_votada = None
                                max_votos_lista = 0
                                
                                for lista in sublema_mas_votado.ListasMunicipio:
                                    if hasattr(lista, 'Tot') and lista.Tot > max_votos_lista:
                                        max_votos_lista = lista.Tot
                                        lista_mas_votada = lista
                                
                                # Si encontramos la lista más votada, extraer su candidato
                                if lista_mas_votada:
                                    if hasattr(lista_mas_votada, 'Dsc') and lista_mas_votada.Dsc:
                                        muni_data["mayor"] = lista_mas_votada.Dsc
            
            # Calcular porcentajes
            total_muni_votes = sum(muni_data["votes"].values())
            if total_muni_votes > 0:
                for party, votes in muni_data["votes"].items():
                    muni_data["vote_percentages"][party] = round((votes / total_muni_votes) * 100, 1)
                    
            # Agregar municipio al diccionario del departamento
            dept_data["municipalities"][muni.MD] = muni_data
            
        # Agregar departamento al resultado
        result[depto.DN] = dept_data
        
    return result

# Re-exportar las funciones públicas
__all__ = ['detect_load', 'load_election_data', 'load_geo_data'] 