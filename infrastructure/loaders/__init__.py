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
from domain.enrichers.municipal_concejales import _calculate_pure_dhondt

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

def load_election_data(source_type: str, source_location: Union[str, Path]) -> Optional[Tuple[ElectionSummaryEnriquecido, Dict[str, Any]]]:
    """
    Carga los datos electorales desde una fuente especificada (API o JSON).
    Para datos de 2025 desde API, siempre obtiene datos frescos sin usar caché.
    
    Args:
        source_type (str): Tipo de fuente ('json' o 'api')
        source_location (Union[str, Path]): Ruta al archivo JSON o URL de la API
        
    Returns:
        Tuple opcional con ElectionSummaryEnriquecido y estadísticas, o None si hay error
    """
    # FORZAR RECARGA PARA API 2025
    # Si es la API de 2025, obligamos que siempre obtenga datos frescos
    if source_type == 'api' and (isinstance(source_location, str) and '2025' in source_location):
        from domain.pipeline import build_dataset
        print("IMPORTANTE: Obteniendo datos sin caché para API 2025")
        # Cargar datos crudos sin caché
        raw_data = load_election_data_from_api(str(source_location))
        if raw_data:
            try:
                # Procesar los datos con el pipeline
                result = build_dataset(raw_data=raw_data)
                return result
            except Exception as e:
                print(f"Error al procesar datos sin caché de API 2025: {e}")
                return None
        else:
            # Intentar con backup local como último recurso
            try:
                backup_path = Path(__file__).parent.parent.parent / 'data' / 'election_data' / '2025' / 'results_2025.json'
                if backup_path.exists():
                    print(f"Fallback: Cargando datos de backup local: {backup_path}")
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        import json
                        raw_data = json.load(f)
                    result = build_dataset(raw_data=raw_data)
                    return result
            except Exception as e:
                print(f"Error en fallback a backup local: {e}")
            return None
    
    # Para el resto de fuentes, usar la caché normal
    if IN_STREAMLIT:
        result = get_streamlit_cached_summary(source_type, source_location)
    else:
        result = get_summary(source_type, source_location)
    
    return result

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
            "all_candidates": True,  # Flag para indicar que tenemos todos los candidatos
            "junta_departamental_lists": []  # Se calcula después
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
            votos_muni = {}
            if hasattr(muni, 'Eleccion'):
                for partido_muni in muni.Eleccion:
                    if hasattr(partido_muni, 'LN') and hasattr(partido_muni, 'Tot'):
                        votos_muni[partido_muni.LN] = partido_muni.Tot
                muni_data["votes"] = votos_muni
                total_votes_muni = sum(votos_muni.values())
                if total_votes_muni > 0:
                    for party, votes in votos_muni.items():
                        muni_data["vote_percentages"][party] = round((votes / total_votes_muni) * 100, 1)

            # --- INICIO: Extracción y Cálculo D'Hondt para Listas Municipales --- 
            temp_listas_muni = []
            # Iterar para extraer info base de las listas municipales
            if hasattr(muni, 'Eleccion'):
                for partido_data in muni.Eleccion:
                    partido_ln = partido_data.LN
                    # Crear lookup VH -> HN para este partido a nivel municipal (si aplica)
                    vh_to_hn_lookup_muni = {h.Tot: h.HN for h in partido_data.Hojas if hasattr(h, 'Tot') and hasattr(h, 'HN') and h.Tot > 0} if hasattr(partido_data, 'Hojas') else {}

                    if hasattr(partido_data, 'Municipio') and hasattr(partido_data.Municipio, 'Sublemas'):
                        for sublema in partido_data.Municipio.Sublemas:
                             # Intentar obtener nombre del sublema de forma más robusta
                             sublema_nombre = getattr(sublema, 'Sublema', getattr(sublema, 'Nombre', '-')) 
                             if hasattr(sublema, 'ListasMunicipio'):
                                for lista_obj in sublema.ListasMunicipio:
                                    # Extraer datos crudos
                                    votos_totales = getattr(lista_obj, 'Tot', 0)
                                    desc_raw = getattr(lista_obj, 'Dsc', None) # Default a None si no existe
                                    
                                    # Intentar obtener número de lista robustamente (HI -> NumeroLista -> numeroLista -> numerolista -> LId)
                                    numero_lista_raw = getattr(lista_obj, 'HI', None)
                                    if numero_lista_raw is None:
                                        numero_lista_raw = getattr(lista_obj, 'NumeroLista', None)
                                    if numero_lista_raw is None:
                                        numero_lista_raw = getattr(lista_obj, 'numeroLista', None) # Probar camelCase
                                    if numero_lista_raw is None:
                                        numero_lista_raw = getattr(lista_obj, 'numerolista', None) # Probar lowercase
                                    if numero_lista_raw is None:
                                        numero_lista_raw = getattr(lista_obj, 'LId', 'N/A') # Fallback final a LId o N/A
                                    
                                    # Procesar descripción para obtener primer candidato (con fallback)
                                    primer_candidato = "N/A"
                                    if desc_raw and isinstance(desc_raw, str) and desc_raw != "N/A":
                                        potential_candidates = desc_raw.split('  ')
                                        cleaned_candidates = [name.strip() for name in potential_candidates if name.strip()]
                                        if cleaned_candidates:
                                            primer_candidato = cleaned_candidates[0]
                                        else:
                                            # Fallback si split falla: usar Dsc truncado
                                            primer_candidato = desc_raw[:50] + '...' if len(desc_raw) > 50 else desc_raw 
                                    
                                    # Crear el diccionario con las claves esperadas por el frontend
                                    lista_dict = {
                                        'Partido': partido_ln,
                                        'Sublema': sublema_nombre, # Usar el valor extraído
                                        'Nº Lista': numero_lista_raw, 
                                        'Primer Candidato': primer_candidato, 
                                        'Votos': votos_totales, 
                                        '_Dsc': desc_raw 
                                    }
                                    
                                    # Añadir a la lista temporal
                                    if votos_totales >= 0:
                                       temp_listas_muni.append(lista_dict)
            
            # --- Ahora aplicar D'Hondt a temp_listas_muni --- 
            # (El resto de la lógica D'Hondt que ya añadimos permanece igual,
            # operando sobre temp_listas_muni y guardando en 
            # muni_data["municipal_council_lists"])
            listas_final_muni = []
            concejales_por_partido = muni_data.get("council_seats", {})
            
            if concejales_por_partido and temp_listas_muni:
                # Agrupar por partido
                lists_grouped_by_party: Dict[str, List[Dict]] = {}
                for lista_d in temp_listas_muni:
                    party = lista_d.get("Partido")
                    if party:
                        if party not in lists_grouped_by_party:
                            lists_grouped_by_party[party] = []
                        lists_grouped_by_party[party].append(lista_d)
                
                parties_with_seats = list(concejales_por_partido.keys())
                
                # Calcular D'Hondt para partidos con escaños
                for party in parties_with_seats:
                    seats_for_party = concejales_por_partido.get(party, 0)
                    if seats_for_party > 0 and party in lists_grouped_by_party:
                        party_lists = lists_grouped_by_party[party]
                        lists_with_seats = _calculate_pure_dhondt(party_lists, seats_for_party)
                        listas_final_muni.extend(lists_with_seats)
                
                # Añadir listas de partidos sin escaños
                parties_in_lists = set(lists_grouped_by_party.keys())
                parties_without_seats = parties_in_lists - set(parties_with_seats)
                for party in parties_without_seats:
                     party_lists = lists_grouped_by_party[party]
                     for l in party_lists:
                         l['Concejales_Asignados'] = 0
                         l['Resto_Dhondt'] = 0.0
                     listas_final_muni.extend(party_lists)
            
            else: 
                # ... (asignar 0 concejales si no aplica D'Hondt)
                listas_final_muni = temp_listas_muni # Asegurarse que se asignan los datos base

            # Guardar resultado en la clave correcta para el frontend
            muni_data["municipal_council_lists"] = listas_final_muni
            # --- FIN: Extracción y Cálculo D'Hondt para Listas Municipales ---

            # Añadir el municipio procesado al departamento
            dept_data["municipalities"][muni_data["name"]] = muni_data
            
        result[dept_data["name"]] = dept_data
        
    return result

# Re-exportar las funciones públicas
__all__ = ['detect_load', 'load_election_data'] 