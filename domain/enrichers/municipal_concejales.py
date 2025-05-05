"""
Enriquecedor para calcular la asignación de concejales municipales por lista
usando el método D'Hondt puro dentro de cada partido.
"""

from typing import Dict, List, Any
import copy

def _calculate_pure_dhondt(lists_data: List[Dict[str, Any]], total_seats: int) -> List[Dict[str, Any]]:
    """
    Calcula la asignación de escaños usando el método D'Hondt puro para un conjunto de listas.

    Args:
        lists_data (list): Lista de diccionarios, cada uno representando una lista.
                           Debe contener al menos la clave 'Votos'.
        total_seats (int): Número total de escaños a asignar entre estas listas.

    Returns:
        list: La lista de entrada actualizada con las claves 'Concejales_Asignados' y 'Resto_Dhondt'.
    """
    if not lists_data or total_seats <= 0:
        for lista in lists_data:
            lista['Concejales_Asignados'] = 0
            lista['Resto_Dhondt'] = 0.0
        return lists_data

    # Inicializar escaños y cocientes
    for lista in lists_data:
        lista['Concejales_Asignados'] = 0
        lista['cocientes'] = [] # Almacenará Votos/1, Votos/2, ...
        votos = lista.get('Votos', 0)
        if votos > 0:
            for i in range(1, total_seats + 1):
                lista['cocientes'].append(votos / i)
        else:
            lista['cocientes'] = [0.0] * total_seats

    # Asignar escaños
    cocientes_global = []
    for i, lista in enumerate(lists_data):
        for cociente in lista['cocientes']:
            cocientes_global.append((cociente, i))

    cocientes_global.sort(key=lambda x: x[0], reverse=True)

    last_cociente_value = 0.0
    assigned_seats = 0
    for i in range(len(cocientes_global)):
        if assigned_seats >= total_seats:
            break # Salir si ya asignamos todos los escaños
            
        cociente_val, lista_index = cocientes_global[i]
        if cociente_val > 0:
            lists_data[lista_index]['Concejales_Asignados'] += 1
            last_cociente_value = cociente_val
            assigned_seats += 1
        else:
            break # No asignar más si los cocientes son 0

    # Calcular Resto D'Hondt (cociente del último escaño asignado a la lista)
    for lista in lists_data:
        if lista['Concejales_Asignados'] > 0:
            votos = lista.get('Votos', 0)
            if votos > 0:
                divisor = lista['Concejales_Asignados']
                lista['Resto_Dhondt'] = votos / divisor
            else:
                lista['Resto_Dhondt'] = 0.0
        else:
            lista['Resto_Dhondt'] = 0.0
        if 'cocientes' in lista:
           del lista['cocientes'] # Limpiar

    return lists_data

def enrich_municipal_concejales(election_data: Any) -> Dict[str, Any]:
    """
    Enriquece los datos electorales calculando la asignación de concejales por lista
    para cada municipio.

    Aplica el método D'Hondt puro dentro de cada partido que obtuvo escaños en el municipio.
    Modifica la estructura de datos *en una copia profunda*.

    Args:
        election_data (Dict[str, Any]): El diccionario original de datos electorales.

    Returns:
        Dict[str, Any]: Una copia profunda del diccionario de datos electorales,
                      con la clave 'municipal_council_lists' actualizada en cada municipio
                      para incluir 'Concejales_Asignados' y 'Resto_Dhondt'.
    """
    # Crear una copia profunda para no modificar el objeto original
    enriched_data_obj = copy.deepcopy(election_data)

    # Convertir el objeto Pydantic (o similar) a un diccionario
    # Usar model_dump() para Pydantic v2+, o dict() para v1
    enriched_dict = None
    if hasattr(enriched_data_obj, 'model_dump'):
        enriched_dict = enriched_data_obj.model_dump(mode='python')
    elif hasattr(enriched_data_obj, 'dict'):
        enriched_dict = enriched_data_obj.dict()
    elif isinstance(enriched_data_obj, dict):
        enriched_dict = enriched_data_obj # Ya era un dict, usar la copia
    else:
        # Si no se puede convertir, lanzar un error claro
        raise TypeError(f"El tipo de dato de entrada ({type(enriched_data_obj)}) no se pudo convertir a diccionario para el enriquecimiento.")

    # Ahora iterar sobre el diccionario convertido
    for dept_name, dept_data in enriched_dict.items():
        if isinstance(dept_data, dict) and "municipalities" in dept_data:
            municipalities = dept_data.get("municipalities", {})
            for muni_name, muni_data in municipalities.items():
                if isinstance(muni_data, dict):
                    council_seats_by_party = muni_data.get("council_seats", {})
                    all_lists_original = muni_data.get("municipal_council_lists", []) 
                    
                    # Crear una lista para almacenar las listas procesadas de este municipio
                    processed_muni_lists = []

                    if council_seats_by_party and all_lists_original:
                        parties_with_seats = list(council_seats_by_party.keys())
                        
                        # Agrupar listas por partido para procesar D'Hondt
                        lists_grouped_by_party: Dict[str, List[Dict]] = {}
                        for lista in all_lists_original:
                            party = lista.get("Partido")
                            if party:
                                if party not in lists_grouped_by_party:
                                    lists_grouped_by_party[party] = []
                                lists_grouped_by_party[party].append(lista)
                        
                        # Procesar partidos con escaños
                        for party in parties_with_seats:
                            seats_for_party = council_seats_by_party.get(party, 0)
                            if seats_for_party > 0 and party in lists_grouped_by_party:
                                party_lists = lists_grouped_by_party[party]
                                lists_with_seats = _calculate_pure_dhondt(party_lists, seats_for_party)
                                processed_muni_lists.extend(lists_with_seats)
                        
                        # Añadir listas de partidos sin escaños (asegurando asignación 0)
                        parties_in_lists = set(lists_grouped_by_party.keys())
                        parties_without_seats = parties_in_lists - set(parties_with_seats)
                        for party in parties_without_seats:
                             party_lists = lists_grouped_by_party[party]
                             for l in party_lists:
                                 l['Concejales_Asignados'] = 0
                                 l['Resto_Dhondt'] = 0.0
                             processed_muni_lists.extend(party_lists)
                        
                        # Reemplazar la lista del municipio con la procesada
                        muni_data["municipal_council_lists"] = processed_muni_lists
                    
                    else: # Si no hay escaños o listas, asignar 0 a todas
                        # Modificar enriched_dict
                        current_lists = muni_data.get("municipal_council_lists", [])
                        for l in current_lists:
                            l['Concejales_Asignados'] = 0
                            l['Resto_Dhondt'] = 0.0
                        # No es necesario reasignar la lista si se modificó in-place
                        # muni_data["municipal_council_lists"] = current_lists

    # Devolver el diccionario modificado
    return enriched_dict 