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
import math

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
        
        # Procesar listas para la Junta Departamental
        for partido in depto.Departamentales:
            partido_nombre_norm = _get_norm_party_name(partido.LN)
            for sublema in partido.Junta.Sublemas:
                for lista_junta in sublema.ListasJunta:
                    # BUSCAR HN usando la coincidencia VH == Tot
                    numero_lista = "N/A"  # Valor por defecto
                    hojas_partido = partido.Hojas # Acceder a las hojas del partido padre
                    hojas_encontradas = [h for h in hojas_partido if h.Tot == lista_junta.VH]

                    if len(hojas_encontradas) == 1:
                        numero_lista = hojas_encontradas[0].HN
                    elif len(hojas_encontradas) > 1:
                        # Log/Warn: Múltiples hojas coinciden con VH (inesperado)
                        log.warning(f"Múltiples hojas encontradas para {partido_nombre_norm} - Sublema {sublema.Nombre} - Lista VH {lista_junta.VH} en Depto {depto.DN}")
                    # else: No se encontró ninguna hoja (VH podría ser 0 o datos inconsistentes)

                    # Extraer y procesar candidatos
                    candidatos_str = lista_junta.Dsc
                    primer_candidato = _extract_first_candidate(candidatos_str)

                    junta_departamental_lists.append({
                        "Partido": partido_nombre_norm,
                        "Sublema": _simplify(sublema.Nombre),
                        "NumeroLista": numero_lista, # Usar el HN encontrado
                        "Candidatos": primer_candidato, # Mostrar solo el primero para la tabla
                        "VotosLista": lista_junta.Tot,
                        "VH": lista_junta.VH, # Guardar VH para posible depuración o uso futuro
                        # Los campos de Ediles/Resto se calcularán después
                    })
        
        # --- CÁLCULO DE EDILES Y RESTOS (SEPARADO) ---
        listas_con_ediles = []
        listas_agrupadas = {}
        votos_por_partido_junta = {}

        # Agrupar listas ya extraídas por partido
        for lista_info in processed["junta_departamental_lists"]:
            partido = lista_info["Partido"]
            if partido not in listas_agrupadas:
                listas_agrupadas[partido] = []
                votos_por_partido_junta[partido] = 0
            listas_agrupadas[partido].append(lista_info.copy()) 
            votos_por_partido_junta[partido] += lista_info["Votos"]

        # Calcular ediles para cada partido
        for partido, listas_del_partido in listas_agrupadas.items():
            total_ediles_partido = dept_data["council_seats"].get(partido, 0)
            total_votos_partido = votos_por_partido_junta.get(partido, 0)
            listas_procesadas_partido = [] # Para guardar listas de este partido con ediles/resto
            
            if total_ediles_partido > 0 and total_votos_partido > 0:
                cociente = total_votos_partido / total_ediles_partido
                ediles_asignados_cociente = 0
                listas_para_resto = []

                # 1. Asignar por cociente y calcular resto
                for lista_data in listas_del_partido:
                    ediles_cociente = int(lista_data["Votos"] / cociente) if cociente > 0 else 0
                    resto = lista_data["Votos"] - (ediles_cociente * cociente) if cociente > 0 else lista_data["Votos"]
                    lista_data["Ediles"] = ediles_cociente
                    lista_data["Resto"] = resto 
                    ediles_asignados_cociente += ediles_cociente
                    listas_para_resto.append(lista_data)
                
                # 2. Asignar por resto
                ediles_restantes = total_ediles_partido - ediles_asignados_cociente
                umbral_resto = -1.0
                listas_ordenadas_resto = sorted(listas_para_resto, key=lambda x: x["Resto"], reverse=True)
                
                if ediles_restantes > 0 and len(listas_ordenadas_resto) >= ediles_restantes:
                    umbral_resto = listas_ordenadas_resto[ediles_restantes - 1]["Resto"]

                # Asignar ediles por resto y calcular votos faltantes
                for i, lista_data in enumerate(listas_ordenadas_resto):
                    obtuvo_edil_resto = False
                    if ediles_restantes > 0 and i < ediles_restantes:
                        lista_data["Ediles"] += 1
                        obtuvo_edil_resto = True
                    
                    # Calcular votos faltantes
                    if obtuvo_edil_resto:
                        lista_data["VotosParaEdilResto"] = 0
                    elif umbral_resto >= 0 and lista_data["Resto"] < umbral_resto:
                        votos_faltantes = math.floor(umbral_resto - lista_data["Resto"]) + 1
                        lista_data["VotosParaEdilResto"] = int(max(0, votos_faltantes))
                    else:
                        lista_data["VotosParaEdilResto"] = None
                        
                    # Redondear resto y añadir a la lista procesada del partido
                    lista_data["Resto"] = round(lista_data["Resto"], 4)
                    listas_procesadas_partido.append(lista_data)
                    
            else: # Partido sin ediles o sin votos
                for lista_data in listas_del_partido:
                    lista_data["Ediles"] = 0
                    lista_data["Resto"] = 0.0
                    lista_data["VotosParaEdilResto"] = None
                    listas_procesadas_partido.append(lista_data)
            
            # Agregar las listas procesadas de este partido a la lista final
            listas_con_ediles.extend(listas_procesadas_partido)
            
        # Ordenar y reemplazar la lista original en dept_data
        listas_con_ediles.sort(key=lambda x: (x["Partido"], -x["Votos"]))
        processed["junta_departamental_lists"] = listas_con_ediles
        # --- FIN CÁLCULO DE EDILES --- 

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
                votos_partido_total = partido.get("Tot", 0) # Votos totales del partido en el municipio
                
                if nombre_partido:
                    votos_muni[nombre_partido] = votos_partido_total
            
            # Calcular porcentajes municipales
            votos_muni_total = sum(votos_muni.values())
            percentages_muni = {}
            if votos_muni_total > 0:
                percentages_muni = {
                    partido: round((votos / votos_muni_total) * 100, 1)
                    for partido, votos in votos_muni.items()
                }
            
            # Determinar partido ganador municipal
            partido_ganador_muni = max(votos_muni.items(), key=lambda x: x[1])[0] if votos_muni else "No disponible"
            
            municipios[muni_name] = {
                "name": muni_name,
                "id": muni.get("MI", 0),
                "party": partido_ganador_muni,
                "mayor": "No disponible",  # Se calculará después en el enricher
                "votes": votos_muni,
                "vote_percentages": percentages_muni,
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
        
        # Procesar listas para la Junta Departamental
        temp_listas_info = [] # Lista temporal para info base
        if hasattr(depto, 'Departamentales'):
            for partido_data in depto.Departamentales:
                partido_nombre = partido_data.LN if hasattr(partido_data, 'LN') else "N/A"
                # Crear lookup VH -> HN para este partido (mejor esfuerzo)
                vh_to_hn_lookup = {h.Tot: h.HN for h in partido_data.Hojas if hasattr(h, 'Tot') and hasattr(h, 'HN') and h.Tot > 0}
                
                if hasattr(partido_data, 'Junta') and hasattr(partido_data.Junta, 'Sublemas'):
                    for sublema in partido_data.Junta.Sublemas:
                        sublema_nombre = sublema.Nombre if hasattr(sublema, 'Nombre') else "N/A"
                        if hasattr(sublema, 'ListasJunta'): 
                            for lista in sublema.ListasJunta:
                                votos_totales_lista = lista.Tot if hasattr(lista, 'Tot') else 0
                                if votos_totales_lista <= 0: continue # Saltar listas sin votos
                                
                                lista_desc_raw = lista.Dsc if hasattr(lista, 'Dsc') else "N/A"
                                votos_hoja_lista = lista.VH if hasattr(lista, 'VH') else 0
                                
                                # Buscar NumeroLista (HN) usando VH como clave en el lookup
                                numero_hoja = vh_to_hn_lookup.get(votos_hoja_lista, "N/A")
                                
                                # Procesar candidatos
                                candidatos_list = []
                                if lista_desc_raw != "N/A":
                                    potential_candidates = lista_desc_raw.split('  ')
                                    candidatos_list = [name.strip() for name in potential_candidates if name.strip()]
                                
                                temp_listas_info.append({
                                    "Partido": partido_nombre,
                                    "Sublema": sublema_nombre,
                                    "NumeroLista": numero_hoja, # Puede ser "N/A"
                                    "Candidatos": candidatos_list,
                                    "Votos": votos_totales_lista # Votos totales de la lista
                                })
        
        # Asignar la información base extraída
        dept_data["junta_departamental_lists"] = temp_listas_info
        
        # --- CÁLCULO DE EDILES Y RESTOS (SEPARADO) ---
        listas_con_ediles = []
        listas_agrupadas = {}
        votos_por_partido_junta = {}

        # Agrupar listas ya extraídas por partido
        for lista_info in dept_data["junta_departamental_lists"]:
            partido = lista_info["Partido"]
            if partido not in listas_agrupadas:
                listas_agrupadas[partido] = []
                votos_por_partido_junta[partido] = 0
            listas_agrupadas[partido].append(lista_info.copy()) 
            votos_por_partido_junta[partido] += lista_info["Votos"]

        # Calcular ediles para cada partido
        for partido, listas_del_partido in listas_agrupadas.items():
            total_ediles_partido = dept_data["council_seats"].get(partido, 0)
            total_votos_partido = votos_por_partido_junta.get(partido, 0)
            listas_procesadas_partido = [] # Para guardar listas de este partido con ediles/resto
            
            if total_ediles_partido > 0 and total_votos_partido > 0:
                cociente = total_votos_partido / total_ediles_partido
                ediles_asignados_cociente = 0
                listas_para_resto = []

                # 1. Asignar por cociente y calcular resto
                for lista_data in listas_del_partido:
                    ediles_cociente = int(lista_data["Votos"] / cociente) if cociente > 0 else 0
                    resto = lista_data["Votos"] - (ediles_cociente * cociente) if cociente > 0 else lista_data["Votos"]
                    lista_data["Ediles"] = ediles_cociente
                    lista_data["Resto"] = resto 
                    ediles_asignados_cociente += ediles_cociente
                    listas_para_resto.append(lista_data)
                
                # 2. Asignar por resto
                ediles_restantes = total_ediles_partido - ediles_asignados_cociente
                umbral_resto = -1.0
                listas_ordenadas_resto = sorted(listas_para_resto, key=lambda x: x["Resto"], reverse=True)
                
                if ediles_restantes > 0 and len(listas_ordenadas_resto) >= ediles_restantes:
                    umbral_resto = listas_ordenadas_resto[ediles_restantes - 1]["Resto"]

                # Asignar ediles por resto y calcular votos faltantes
                for i, lista_data in enumerate(listas_ordenadas_resto):
                    obtuvo_edil_resto = False
                    if ediles_restantes > 0 and i < ediles_restantes:
                        lista_data["Ediles"] += 1
                        obtuvo_edil_resto = True
                    
                    # Calcular votos faltantes
                    if obtuvo_edil_resto:
                        lista_data["VotosParaEdilResto"] = 0
                    elif umbral_resto >= 0 and lista_data["Resto"] < umbral_resto:
                        votos_faltantes = math.floor(umbral_resto - lista_data["Resto"]) + 1
                        lista_data["VotosParaEdilResto"] = int(max(0, votos_faltantes))
                    else:
                        lista_data["VotosParaEdilResto"] = None
                        
                    # Redondear resto y añadir a la lista procesada del partido
                    lista_data["Resto"] = round(lista_data["Resto"], 4)
                    listas_procesadas_partido.append(lista_data)
                    
            else: # Partido sin ediles o sin votos
                for lista_data in listas_del_partido:
                    lista_data["Ediles"] = 0
                    lista_data["Resto"] = 0.0
                    lista_data["VotosParaEdilResto"] = None
                    listas_procesadas_partido.append(lista_data)
            
            # Agregar las listas procesadas de este partido a la lista final
            listas_con_ediles.extend(listas_procesadas_partido)
            
        # Ordenar y reemplazar la lista original en dept_data
        listas_con_ediles.sort(key=lambda x: (x["Partido"], -x["Votos"]))
        dept_data["junta_departamental_lists"] = listas_con_ediles
        # --- FIN CÁLCULO DE EDILES --- 

        # Procesar cada municipio
        for muni in depto.Municipales: # muni es un MunicipioEnriquecido
            # Crear datos del municipio usando los datos ya enriquecidos
            muni_data = {
                "name": muni.MD,
                "id": muni.MI,
                "party": muni.ganador, # Partido ganador calculado por enricher
                "mayor": muni.mayor,  # Alcalde calculado por enricher
                "votes": {}, # Se poblará después
                "vote_percentages": {}, # Se poblará después
                "council_seats": muni.ediles, # Concejales calculados por enricher
                "municipal_council_lists": [] # INICIALIZAR LISTA VACÍA
            }
            
            # Poblar votos por partido (esto sí viene del modelo base)
            votos_muni_total = 0
            for partido in muni.Eleccion:
                nombre_partido = partido.LN
                votos_partido = partido.Tot
                muni_data["votes"][nombre_partido] = votos_partido
                votos_muni_total += votos_partido
                
                # --- INICIO EXTRACCIÓN LISTAS MUNICIPALES (NUEVO) ---
                # DEBUG: Imprimir info del partido procesado a nivel municipal
                # print(f"DEBUG: Procesando Municipio={muni.MD}, Partido={nombre_partido}") 
                if hasattr(partido, 'Municipio') and hasattr(partido.Municipio, 'Sublemas'):
                    # print(f"DEBUG:   Encontrados {len(partido.Municipio.Sublemas)} sublemas para {nombre_partido} en {muni.MD}")
                    for i, sublema in enumerate(partido.Municipio.Sublemas):
                        sublema_nombre = sublema.Nombre if hasattr(sublema, 'Nombre') else "N/A"
                        # print(f"DEBUG:     Procesando Sublema {i}: {sublema_nombre}")
                        # Comprobar si existe ListasMunicipio y si tiene contenido
                        if hasattr(sublema, 'ListasMunicipio') and sublema.ListasMunicipio:
                            # print(f"DEBUG:       Encontradas {len(sublema.ListasMunicipio)} ListasMunicipio en sublema {sublema_nombre}")
                            for j, lista in enumerate(sublema.ListasMunicipio):
                                # print(f"DEBUG:         Procesando ListaMunicipio {j}")
                                lista_desc_raw = lista.Dsc if hasattr(lista, 'Dsc') else "N/A"
                                votos_lista_total = lista.Tot if hasattr(lista, 'Tot') else 0
                                votos_hoja_lista_muni = lista.VH if hasattr(lista, 'VH') else 0
                                
                                # Buscar NumeroLista (Hoja HN)
                                numero_hoja_muni = "N/A"
                                if hasattr(partido, 'Hojas') and votos_hoja_lista_muni > 0:
                                    hoja_corr_muni = next((h for h in partido.Hojas if hasattr(h, 'Tot') and h.Tot == votos_hoja_lista_muni), None)
                                    if hoja_corr_muni and hasattr(hoja_corr_muni, 'HN'):
                                        numero_hoja_muni = hoja_corr_muni.HN
                                        
                                # Procesar descripción para extraer candidatos
                                candidatos_list_muni = []
                                if lista_desc_raw != "N/A":
                                    potential_candidates_muni = lista_desc_raw.split('  ')
                                    candidatos_list_muni = [name.strip() for name in potential_candidates_muni if name.strip()]
                                
                                if votos_lista_total > 0:
                                    # print(f"DEBUG:           Añadiendo lista {numero_hoja_muni} con {votos_lista_total} votos y {len(candidatos_list_muni)} candidatos.")
                                    muni_data["municipal_council_lists"].append({
                                        "Partido": nombre_partido,
                                        "Sublema": sublema_nombre,
                                        "NumeroLista": numero_hoja_muni, 
                                        "Candidatos": candidatos_list_muni,
                                        "Votos": votos_lista_total
                                    })
                                else:
                                    # print(f"DEBUG:           Omitiendo lista {numero_hoja_muni} por tener 0 votos.")
                                    pass # Añadir pass para bloque else vacío
                        else:
                            # print(f"DEBUG:       Sublema {sublema_nombre} NO tiene ListasMunicipio o está vacía.")
                            pass # Añadir pass para bloque else vacío
                else:
                    # print(f"DEBUG:   Partido {nombre_partido} NO tiene Municipio.Sublemas")
                    pass # Añadir pass para bloque else vacío
                # --- FIN EXTRACCIÓN LISTAS MUNICIPALES --- 
            
            # Calcular porcentajes para el municipio
            if votos_muni_total > 0:
                for partido_nombre, votos_num in muni_data["votes"].items():
                    muni_data["vote_percentages"][partido_nombre] = round((votos_num / votos_muni_total) * 100, 1)
                    
            dept_data["municipalities"][muni.MD] = muni_data
            
        # Agregar departamento al resultado
        result[depto.DN] = dept_data
        
    return result

# Re-exportar las funciones públicas
__all__ = ['detect_load', 'load_election_data', 'load_geo_data'] 