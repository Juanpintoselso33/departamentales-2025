"""
Enriquecimiento de modelos electorales.

Este módulo añade capas de información derivada a los modelos canónicos:
1. Determina ganadores en cada nivel territorial.
2. Asigna bancas de ediles según la regla constitucional.
3. Calcula agregados nacionales para widgets comparativos.
"""

from copy import deepcopy
from typing import Dict, Any, List, Tuple

from pydantic import BaseModel

from domain.models import (
    ElectionSummary, Departamento, Municipio,
    PartidoDepartamento, PartidoMunicipio
)
from domain.enrichers.ediles_272 import ediles_por_lema


class DepartamentoEnriquecido(Departamento):
    """Modelo extendido de Departamento con información de ganador y ediles."""
    ganador: str = ""
    ediles: Dict[str, int] = {}


class MunicipioEnriquecido(Municipio):
    """Modelo extendido de Municipio con información de ganador y ediles."""
    ganador: str = ""
    ediles: Dict[str, int] = {}
    mayor: str = ""


class ElectionSummaryEnriquecido(ElectionSummary):
    """Modelo extendido de ElectionSummary con departamentos y municipios enriquecidos."""
    departamentos: List[DepartamentoEnriquecido] = []


def sumar_votos_por_lema(partidos: List[PartidoDepartamento | PartidoMunicipio]) -> Dict[str, int]:
    """
    Suma los votos totales por lema a partir de una lista de partidos.
    
    Args:
        partidos: Lista de PartidoDepartamento o PartidoMunicipio
        
    Returns:
        Diccionario con la suma de votos por lema
    """
    votos_por_lema = {}
    for partido in partidos:
        lema = partido.LN
        votos = partido.Tot
        
        if lema in votos_por_lema:
            votos_por_lema[lema] += votos
        else:
            votos_por_lema[lema] = votos
            
    return votos_por_lema


def enriquecer_municipio(municipio: Municipio) -> MunicipioEnriquecido:
    """
    Enriquece un objeto Municipio con ganador, ediles y alcalde.
    
    Args:
        municipio: Objeto Municipio a enriquecer
        
    Returns:
        MunicipioEnriquecido con campos ganador, ediles y alcalde
    """
    votos_por_lema = {}
    try:
        # Intentar construir votos_por_lema con más detalle en caso de error
        eleccion_data = getattr(municipio, 'Eleccion', [])
        if eleccion_data:
             votos_por_lema = {
                p.LN: p.Tot 
                for p in eleccion_data 
                if hasattr(p, 'LN') and hasattr(p, 'Tot') and p.Tot > 0
             }
        else:
            pass # No hacer nada si está vacío
            
    except Exception as e:
        votos_por_lema = {} # Asegurar que está vacío si hubo error
        
    # Usar "No disponible" como default
    ganador = max(votos_por_lema.items(), key=lambda x: x[1])[0] if votos_por_lema else "No disponible"
    
    ediles_por_partido = ediles_por_lema(votos_por_lema, total_ediles=5, mayoria_auto=3)
    
    # Usar "No disponible" como default
    alcalde_nombre = "No disponible" 
    lista_ganadora_votos = -1

    if ganador and ganador != "No disponible": # Solo buscar si hay un ganador válido
        partido_ganador_data = next((p for p in municipio.Eleccion if hasattr(p, 'LN') and p.LN == ganador), None)
        
        if partido_ganador_data and hasattr(partido_ganador_data, 'Municipio') and \
           hasattr(partido_ganador_data.Municipio, 'Sublemas'):
            
            for sublema in partido_ganador_data.Municipio.Sublemas:
                if hasattr(sublema, 'ListasMunicipio'):
                    for lista in sublema.ListasMunicipio:
                        votos_lista = getattr(lista, 'Tot', 0)
                        if votos_lista > lista_ganadora_votos:
                            lista_ganadora_votos = votos_lista
                            # Extraer nombre de Dsc si existe
                            alcalde_nombre_temp = getattr(lista, 'Dsc', None)
                            if alcalde_nombre_temp and isinstance(alcalde_nombre_temp, str):
                                alcalde_nombre = alcalde_nombre_temp # Actualizar solo si se encontró
                            else: # Si Dsc no existe o no es string, mantener el último válido o "No disponible"
                                if lista_ganadora_votos <= 0: # Si es la primera vez que falla, poner No disponible
                                     alcalde_nombre = "No disponible"
                                # else: mantener el valor anterior si ya había uno
                                
    # Asegurarse de que si no se encontró un candidato válido, quede "No disponible"
    if lista_ganadora_votos <= 0:
        alcalde_nombre = "No disponible"

    # Crear el objeto enriquecido
    municipio_enriquecido = MunicipioEnriquecido(
        **municipio.model_dump(), 
        ganador=ganador, 
        ediles=ediles_por_partido, 
        mayor=alcalde_nombre # Ahora usa "No disponible" como default claro
    )
    return municipio_enriquecido


def enriquecer_departamento(departamento: Departamento) -> DepartamentoEnriquecido:
    """
    Enriquece un departamento con información de ganador y distribución de ediles.
    También enriquece todos sus municipios.
    
    Args:
        departamento: Objeto Departamento a enriquecer
        
    Returns:
        DepartamentoEnriquecido con campos ganador, ediles, y municipios enriquecidos
    """
    # Sumar votos por lema en el departamento
    votos_por_lema = sumar_votos_por_lema(departamento.Departamentales)
    
    # Determinar el ganador (lema con más votos)
    ganador = max(votos_por_lema.items(), key=lambda x: x[1])[0] if votos_por_lema else ""
    
    # Calcular distribución de ediles (31 ediles: 16 para ganador + 15 por D'Hondt)
    ediles = ediles_por_lema(votos_por_lema)
    
    # Enriquecer cada municipio del departamento
    municipios_enriquecidos = [
        enriquecer_municipio(municipio) for municipio in departamento.Municipales
    ]
    
    # Crear una copia modificada con los nuevos campos
    dto_enriquecido = DepartamentoEnriquecido(**departamento.model_dump())
    dto_enriquecido.ganador = ganador
    dto_enriquecido.ediles = ediles
    dto_enriquecido.Municipales = municipios_enriquecidos
    
    return dto_enriquecido


def enrich(summary: ElectionSummary) -> ElectionSummaryEnriquecido:
    """
    Enriquece un ElectionSummary con información de ganadores y ediles.
    
    Args:
        summary: Objeto ElectionSummary a enriquecer
        
    Returns:
        ElectionSummaryEnriquecido con departamentos y municipios enriquecidos
    """
    # Enriquecer cada departamento
    departamentos_enriquecidos = [
        enriquecer_departamento(departamento) for departamento in summary.departamentos
    ]
    
    # Crear una copia modificada con los departamentos enriquecidos
    return ElectionSummaryEnriquecido(
        year=summary.year,
        departamentos=departamentos_enriquecidos
    )


def aggregate(summary: ElectionSummaryEnriquecido) -> Dict[str, Any]:
    """
    Genera estadísticas agregadas a nivel nacional.
    
    Args:
        summary: ElectionSummaryEnriquecido con información de ganadores y ediles
        
    Returns:
        Diccionario con estadísticas nacionales
    """
    # Inicializar estructuras de datos
    votos_por_lema = {}
    departamentos_por_lema = {}
    municipios_por_lema = {}
    ediles_por_lema = {}
    
    # CORRECCIÓN: Los votos válidos son únicamente la suma de votos ya asignados a partidos
    # Antes se usaba total_votos = 0 y se sumaba incrementalmente
    total_votos_validos = 0
    
    # Recorrer todos los departamentos y municipios
    for depto in summary.departamentos:
        # Sumar votos por lema a nivel departamental
        for partido in depto.Departamentales:
            lema = partido.LN
            # CORRECCIÓN: Usamos Tot que son los votos válidos asignados al partido
            votos = partido.Tot
            
            if lema in votos_por_lema:
                votos_por_lema[lema] += votos
            else:
                votos_por_lema[lema] = votos
                
            # CORRECCIÓN: Sumamos únicamente votos válidos (Tot de cada partido)
            total_votos_validos += votos
        
        # Contar departamentos ganados por lema
        ganador_depto = depto.ganador
        if ganador_depto:
            departamentos_por_lema[ganador_depto] = departamentos_por_lema.get(ganador_depto, 0) + 1
        
        # Sumar ediles por lema a nivel nacional
        for lema, ediles in depto.ediles.items():
            if lema in ediles_por_lema:
                ediles_por_lema[lema] += ediles
            else:
                ediles_por_lema[lema] = ediles
        
        # Contar municipios ganados por lema
        for municipio in depto.Municipales:
            ganador_muni = municipio.ganador
            if ganador_muni:
                # La ley establece que el alcalde corresponde al partido más votado
                # Esto ya está reflejado en el campo "ganador" del municipio
                municipios_por_lema[ganador_muni] = municipios_por_lema.get(ganador_muni, 0) + 1
    
    # CORRECCIÓN: Calcular porcentajes nacionales usando solo votos válidos
    # Excluimos completamente los votos anulados (TO) y observados (TNO) del cálculo
    porcentajes_nacionales = {}
    if total_votos_validos > 0:
        for lema, votos in votos_por_lema.items():
            porcentajes_nacionales[lema] = round((votos / total_votos_validos) * 100, 2)
    
    # Determinar lema más votado a nivel nacional
    lema_mas_votado = None
    if votos_por_lema:
        lema_mas_votado = max(votos_por_lema.items(), key=lambda x: x[1])[0]
    
    # Devolver estadísticas completas
    return {
        # Votos y porcentajes
        "votos_por_lema": votos_por_lema,
        "porcentajes_nacionales": porcentajes_nacionales,
        "total_votos": total_votos_validos,  # CORRECCIÓN: Usar la suma de votos válidos
        
        # Distribución territorial
        "departamentos_por_lema": departamentos_por_lema,
        "municipios_por_lema": municipios_por_lema,
        "ediles_por_lema": ediles_por_lema,
        
        # Partido más votado
        "lema_mas_votado": lema_mas_votado,
        
        # Alias para compatibilidad con código existente
        "votos_totales": total_votos_validos,
        "porcentajes": porcentajes_nacionales,
        "departamentos_ganados": departamentos_por_lema,
        "municipios_ganados": municipios_por_lema
    }


def enrich_candidates_data(depto_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Enriquece los datos de candidatos por partido, mejorando sus nombres y calculando porcentajes.
    
    Args:
        depto_data: Datos del departamento
        
    Returns:
        Diccionario con candidatos enriquecidos por partido
    """
    candidates_by_party = {}
    
    # Si no hay estructura de datos Departamentales, devolver vacío
    if "Departamentales" not in depto_data:
        return {}
    
    # Calcular total de votos para porcentajes globales
    total_votos = 0
    for partido in depto_data["Departamentales"]:
        # Sumar votos totales de Intendente si existen
        if "Intendente" in partido and "Tot" in partido["Intendente"]:
            # CORRECCIÓN: Usamos strip() para eliminar espacios antes de la conversión
            try:
                # Conversión segura con manejo de errores
                votos_str = str(partido["Intendente"]["Tot"]).strip()
                total_votos += float(votos_str)
            except (ValueError, TypeError):
                # Si hay error de conversión, intentamos continuar
                pass
    
    # Procesar cada partido
    for partido in depto_data["Departamentales"]:
        partido_nombre = partido.get("LN", "")
        
        # Inicializar lista de candidatos para este partido
        candidates_by_party[partido_nombre] = []
        
        # Calcular votos totales del partido para porcentajes internos
        votos_partido = 0
        if "Intendente" in partido and "Tot" in partido["Intendente"]:
            try:
                # CORRECCIÓN: Conversión segura con strip() para eliminar espacios
                votos_str = str(partido["Intendente"]["Tot"]).strip()
                votos_partido = float(votos_str)
            except (ValueError, TypeError):
                pass
            
        # Procesar candidatos desde Intendente.Listas
        if "Intendente" in partido and "Listas" in partido["Intendente"]:
            for candidato in partido["Intendente"]["Listas"]:
                # CORRECCIÓN: Usar la nueva función para formatear nombres
                from domain.transformers.text_normalizer import format_candidate_name
                nombre_crudo = candidato.get("Dsc", "")
                nombre = format_candidate_name(nombre_crudo)
                
                # Si no se pudo obtener un nombre, usar partido como fallback
                if not nombre or nombre == "No disponible":
                    nombre = f"Candidato de {partido_nombre}"
                
                # Convertir valores a números con manejo de errores
                try:
                    votos = float(str(candidato.get("Tot", 0)).strip())
                    votos_hojas = float(str(candidato.get("VH", 0)).strip())
                    votos_al_lema = float(str(candidato.get("VAL", 0)).strip())
                except (ValueError, TypeError):
                    votos = 0
                    votos_hojas = 0
                    votos_al_lema = 0
                    
                # Calcular porcentajes
                porcentaje_partido = (votos / votos_partido * 100) if votos_partido > 0 else 0
                porcentaje_total = (votos / total_votos * 100) if total_votos > 0 else 0
                
                candidates_by_party[partido_nombre].append({
                    "nombre": nombre,
                    "votos": votos,
                    "votos_hojas": votos_hojas,
                    "votos_al_lema": votos_al_lema,
                    "porcentaje_partido": porcentaje_partido,
                    "porcentaje_total": porcentaje_total,
                    # NUEVO: Agregar advertencia para datos preliminares
                    "advertencia": "ADVERTENCIA: Datos preliminares" if votos_partido > 0 and porcentaje_total < 10 else ""
                })
            
            # Ordenar candidatos por votos pero mantener todos
            candidates_by_party[partido_nombre].sort(key=lambda x: x["votos"], reverse=True)
    
    return candidates_by_party


def enrich_listas_data(depto_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Enriquece los datos de listas con información de ediles y votos.
    
    Args:
        depto_data: Datos del departamento
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Diccionario con listas por partido incluyendo ediles y resto
    """
    listas_by_party = {}
    total_votos_departamento = 0
    
    # Si tenemos datos en formato Departamentales, procesarlos
    if "Departamentales" in depto_data:
        # Primero calculamos el total de votos válidos del departamento
        total_votos_departamento = sum(partido.get("Tot", 0) for partido in depto_data["Departamentales"])
        
        # Procesamos cada partido
        for partido in depto_data["Departamentales"]:
            partido_nombre = partido.get("LN", "")
            votos_partido = partido.get("Tot", 0)
            
            if not partido_nombre:
                continue
                
            listas_by_party[partido_nombre] = []
            
            # Obtener el total de ediles asignados al partido
            total_ediles_partido = depto_data.get("ediles", {}).get(partido_nombre, 0)
            
            # Procesar listas del partido
            if "Hojas" in partido:
                listas_temp = []
                for lista in partido["Hojas"]:
                    votos_lista = lista.get("Tot", 0)
                    numero_lista = lista.get("HI", "")
                    nombre_lista = lista.get("HN", "")
                    
                    # Calcular porcentajes
                    porcentaje_partido = (votos_lista / votos_partido * 100) if votos_partido > 0 else 0
                    porcentaje_total = (votos_lista / total_votos_departamento * 100) if total_votos_departamento > 0 else 0
                    
                    # Buscar sublema en la Junta si existe
                    sublema = ""
                    if "Junta" in partido and "Sublemas" in partido["Junta"]:
                        for sub in partido["Junta"]["Sublemas"]:
                            for lista_junta in sub.get("ListasJunta", []):
                                if str(lista_junta.get("VH", 0)) == str(votos_lista):
                                    sublema = sub.get("Nombre", "")
                                    break
                            if sublema:
                                break
                    
                    listas_temp.append({
                        "numero": numero_lista,
                        "nombre": nombre_lista,
                        "sublema": sublema,
                        "votos": votos_lista,
                        "porcentaje_partido": porcentaje_partido,
                        "porcentaje_total": porcentaje_total,
                        "ediles": 0,  # Se calculará después
                        "resto": 0     # Se calculará después
                    })
                
                # Ordenar listas por votos
                listas_temp.sort(key=lambda x: x["votos"], reverse=True)
                
                # Calcular cociente electoral del partido
                if total_ediles_partido > 0:
                    cociente = votos_partido / total_ediles_partido
                    
                    # Primera vuelta: asignar ediles por cociente entero
                    ediles_asignados = 0
                    for lista in listas_temp:
                        ediles_lista = int(lista["votos"] / cociente)
                        lista["ediles"] = ediles_lista
                        lista["resto"] = lista["votos"] - (ediles_lista * cociente)
                        ediles_asignados += ediles_lista
                    
                    # Segunda vuelta: asignar ediles restantes por mayor resto
                    ediles_restantes = total_ediles_partido - ediles_asignados
                    if ediles_restantes > 0:
                        # Ordenar por resto
                        listas_temp.sort(key=lambda x: x["resto"], reverse=True)
                        for i in range(ediles_restantes):
                            if i < len(listas_temp):
                                listas_temp[i]["ediles"] += 1
                                listas_temp[i]["resto"] = 0  # El resto se consumió
                
                # Volver a ordenar por votos para la presentación final
                listas_temp.sort(key=lambda x: x["votos"], reverse=True)
                listas_by_party[partido_nombre] = listas_temp
    
    return listas_by_party


def calcular_ediles_por_lista(votos_lista: int, votos_partido: int, total_ediles_partido: int) -> Tuple[int, float]:
    """
    Calcula cuántos ediles corresponden a una lista y cuál es su resto.
    
    Args:
        votos_lista: Votos de la lista
        votos_partido: Votos totales del partido
        total_ediles_partido: Total de ediles que obtuvo el partido
        
    Returns:
        Tuple[int, float]: (ediles asignados, resto de votos)
    """
    if votos_partido == 0:
        return 0, 0
        
    # Calcular el cociente electoral del partido
    cociente = votos_partido / total_ediles_partido if total_ediles_partido > 0 else float('inf')
    
    # Calcular ediles
    ediles = int(votos_lista / cociente) if cociente > 0 else 0
    
    # Calcular resto
    resto = votos_lista - (ediles * cociente) if cociente > 0 else votos_lista
    
    return ediles, resto


def enrich_department_data(depto_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enriquece los datos de un departamento con información adicional."""
    enriched_data = depto_data.copy()
    
    # Enriquecer datos de listas y ediles
    listas_result = enrich_listas_data(depto_data)
    if listas_result:
        enriched_data["listas_data"] = listas_result
    
    candidatos_intendente = []
    
    # Caso 1: Datos detallados (con Departamentales)
    if "Departamentales" in depto_data:
        total_votos = 0
        
        # Primero calculamos el total de votos válidos
        for partido in depto_data["Departamentales"]:
            total_votos += partido.get("Tot", 0)
        
        # Procesamos los candidatos de cada partido
        for partido in depto_data["Departamentales"]:
            partido_nombre = partido.get("LN", "")
            if "Intendente" in partido and "Listas" in partido["Intendente"]:
                for candidato in partido["Intendente"]["Listas"]:
                    votos = candidato.get("Tot", 0)
                    porcentaje = (votos / total_votos * 100) if total_votos > 0 else 0
                    
                    candidatos_intendente.append({
                        "nombre": candidato.get("Dsc", ""),
                        "partido": partido_nombre,
                        "votos_totales": votos,
                        "votos_hojas": candidato.get("VH", 0),
                        "votos_al_lema": candidato.get("VAL", 0),
                        "porcentaje": round(porcentaje, 2)
                    })
    
    # Caso 2: Datos simplificados (con party_candidates)
    elif "party_candidates" in depto_data and "votes" in depto_data:
        total_votos = sum(depto_data["votes"].values())
        
        for partido, candidato in depto_data["party_candidates"].items():
            votos = depto_data["votes"].get(partido, 0)
            porcentaje = depto_data["vote_percentages"].get(partido, 0)
            
            candidatos_intendente.append({
                "nombre": candidato,
                "partido": partido,
                "votos_totales": votos,
                "votos_hojas": votos,  # En este formato no tenemos el desglose
                "votos_al_lema": 0,    # En este formato no tenemos el desglose
                "porcentaje": round(porcentaje, 2)
            })
    
    # Ordenar candidatos por votos
    candidatos_intendente.sort(key=lambda x: x["votos_totales"], reverse=True)
    
    # Agregar información de debug
    debug_info = {
        "departamento": depto_data.get("DN", ""),
        "tiene_departamentales": "Departamentales" in depto_data,
        "candidatos_encontrados": len(candidatos_intendente),
        "partidos_con_candidatos": len(set(c["partido"] for c in candidatos_intendente)),
        "detalle_candidatos": [
            {
                "nombre": c["nombre"],
                "partido": c["partido"],
                "votos": c["votos_totales"],
                "votos_hojas": c["votos_hojas"],
                "votos_al_lema": c["votos_al_lema"],
                "porcentaje": c["porcentaje"]
            } for c in candidatos_intendente
        ]
    }
    
    # Agregar datos enriquecidos
    enriched_data["candidatos_intendente"] = candidatos_intendente
    enriched_data["debug"] = debug_info
    
    # Resto del enriquecimiento...
    if "votes" not in enriched_data and "Departamentales" in depto_data:
        enriched_data["votes"] = sumar_votos_por_lema(depto_data.get("Departamentales", []))
    
    if "vote_percentages" not in enriched_data and "votes" in enriched_data:
        total_votos = sum(enriched_data["votes"].values())
        enriched_data["vote_percentages"] = {
            partido: (votos / total_votos * 100) if total_votos > 0 else 0
            for partido, votos in enriched_data["votes"].items()
        }
    
    if "council_seats" not in enriched_data and "votes" in enriched_data:
        enriched_data["council_seats"] = ediles_por_lema(enriched_data["votes"])
    
    return enriched_data


def get_intendente_candidates_details(depto_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extrae los detalles de los candidatos a intendente con sus votos y porcentajes.
    
    Args:
        depto_data: Datos del departamento (puede ser el objeto Departamento o un diccionario)
        
    Returns:
        Lista de diccionarios con información detallada de cada candidato
    """
    candidates = []
    total_votos = 0
    
    # Si tenemos datos en formato Departamentales, procesarlos
    if "Departamentales" in depto_data:
        # CORRECCIÓN: Cálculo de votos válidos usando la metodología oficial
        # Primero calculamos el total de votos para los porcentajes
        for partido in depto_data["Departamentales"]:
            if "Intendente" in partido and "Tot" in partido["Intendente"]:
                try:
                    # Conversión segura con strip() para eliminar espacios
                    votos_str = str(partido["Intendente"]["Tot"]).strip()
                    total_votos += float(votos_str)
                except (ValueError, TypeError):
                    # Si hay error de conversión, continuamos
                    pass
        
        # Luego procesamos cada candidato
        for partido in depto_data["Departamentales"]:
            if "Intendente" in partido and "Listas" in partido["Intendente"]:
                partido_nombre = partido.get("LN", "")
                votos_partido = 0
                
                # Obtener los votos totales del partido para calcular porcentajes internos
                try:
                    if "Tot" in partido["Intendente"]:
                        votos_str = str(partido["Intendente"]["Tot"]).strip()
                        votos_partido = float(votos_str)
                except (ValueError, TypeError):
                    pass
                
                for candidato in partido["Intendente"]["Listas"]:
                    # CORRECCIÓN: Mejor formato de nombres
                    from domain.transformers.text_normalizer import format_candidate_name
                    nombre_crudo = candidato.get("Dsc", "")
                    nombre_formateado = format_candidate_name(nombre_crudo)
                    
                    # Si no se encontró un nombre, usar el partido como fallback
                    if not nombre_formateado or nombre_formateado == "No disponible":
                        nombre_formateado = f"Candidato de {partido_nombre}"
                    
                    # Conversión segura de valores numéricos
                    try:
                        votos = float(str(candidato.get("Tot", 0)).strip())
                        votos_hojas = float(str(candidato.get("VH", 0)).strip())
                        votos_al_lema = float(str(candidato.get("VAL", 0)).strip())
                    except (ValueError, TypeError):
                        votos = 0
                        votos_hojas = 0
                        votos_al_lema = 0
                    
                    # Calcular porcentajes
                    porcentaje_total = (votos / total_votos * 100) if total_votos > 0 else 0
                    porcentaje_partido = (votos / votos_partido * 100) if votos_partido > 0 else 0
                    
                    # CORRECCIÓN: Determinar si los datos son muy preliminares
                    es_preliminar = votos_partido > 0 and porcentaje_total < 10
                    
                    candidates.append({
                        "nombre": nombre_formateado,
                        "partido": partido_nombre,
                        "votos": votos,
                        "votos_hojas": votos_hojas,
                        "votos_al_lema": votos_al_lema,
                        "porcentaje": round(porcentaje_total, 2),
                        "porcentaje_partido": round(porcentaje_partido, 2),
                        # NUEVO: Agregar información sobre escrutinio
                        "advertencia": "ADVERTENCIA: Datos preliminares" if es_preliminar else "",
                        "es_preliminar": es_preliminar
                    })
    
    # Ordenar por votos de mayor a menor
    candidates.sort(key=lambda x: x["votos"], reverse=True)
    return candidates 