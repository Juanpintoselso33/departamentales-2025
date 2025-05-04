"""
Implementación de la regla constitucional del artículo 272 para distribución de ediles.

Este módulo contiene funciones puras para calcular la distribución de ediles
según el artículo 272 de la Constitución uruguaya, que establece que:
1) El lema ganador recibe la mayoría absoluta de ediles (16), sin discusión.
2) El resto de los lemas compite por los ediles restantes (15), que se reparten
   en forma proporcional aplicando el método D'Hondt sobre los votos de cada uno.
"""

from typing import Dict, Tuple, List
import numpy as np


def ediles_por_lema(
    votos_por_lema: Dict[str, int],
    total_ediles: int = 31,
    mayoria_auto: int = 16
) -> Dict[str, int]:
    """
    Calcula la distribución de ediles según el artículo 272 de la Constitución uruguaya.
    
    Args:
        votos_por_lema: Diccionario con votos por lema
        total_ediles: Total de ediles a distribuir (default: 31 para Juntas Departamentales)
        mayoria_auto: Cantidad de ediles asignados automáticamente al ganador 
                     (default: 16 para Juntas Departamentales)
                     
    Returns:
        Diccionario con la cantidad de ediles asignados a cada lema
    """
    # Verificar que hay lemas
    if not votos_por_lema:
        return {}
    
    # Si solo hay un lema, asignar todos los ediles a ese lema
    if len(votos_por_lema) == 1:
        lema = next(iter(votos_por_lema))
        return {lema: total_ediles}
    
    # Convertir a arrays para mejor manipulación
    lemas = list(votos_por_lema.keys())
    votos = np.array([votos_por_lema[p] for p in lemas])
    
    # Identificar lema ganador (el que tiene más votos)
    indice_ganador = np.argmax(votos)
    lema_ganador = lemas[indice_ganador]
    
    # Primero, distribuir todos los ediles proporcionalmente usando D'Hondt
    cocientes = np.zeros((len(lemas), total_ediles))
    for i in range(len(lemas)):
        for j in range(total_ediles):
            cocientes[i, j] = votos[i] / (j + 1)
    
    # Aplanar la matriz para encontrar los mayores cocientes
    cocientes_flat = cocientes.flatten()
    indices_flat = np.argsort(cocientes_flat)[::-1][:total_ediles]
    
    # Contar cuántos ediles obtiene cada lema por el método D'Hondt
    ediles_dhondt = np.zeros(len(lemas), dtype=int)
    for idx in indices_flat:
        lema_idx = idx // total_ediles
        ediles_dhondt[lema_idx] += 1
    
    # Verificar si el lema ganador tiene al menos la mayoría automática
    if ediles_dhondt[indice_ganador] < mayoria_auto:
        # Si no tiene la mayoría, se le asigna la mayoría mínima
        ediles_faltantes = mayoria_auto - ediles_dhondt[indice_ganador]
        
        # Crear mascara para los otros lemas
        mascara_otros = np.ones(len(lemas), dtype=bool)
        mascara_otros[indice_ganador] = False
        
        # Total de ediles que tenían originalmente los otros lemas
        ediles_otros_original = ediles_dhondt[mascara_otros].sum()
        
        # Inicializar el array final de ediles
        ediles_final = np.zeros(len(lemas), dtype=int)
        ediles_final[indice_ganador] = mayoria_auto
        
        # Ediles restantes a distribuir entre los otros lemas
        ediles_restantes = total_ediles - mayoria_auto
        
        # Si los otros lemas tienen ediles y hay que redistribuir
        if ediles_otros_original > 0 and ediles_restantes > 0:
            # Crear nuevos cocientes solo para los lemas no ganadores
            cocientes_otros = np.zeros((np.sum(mascara_otros), total_ediles))
            for i, lema_idx in enumerate(np.where(mascara_otros)[0]):
                for j in range(total_ediles):
                    cocientes_otros[i, j] = votos[lema_idx] / (j + 1)
            
            # Aplanar y ordenar
            cocientes_otros_flat = cocientes_otros.flatten()
            indices_otros_flat = np.argsort(cocientes_otros_flat)[::-1][:ediles_restantes]
            
            # Distribuir los ediles restantes
            for idx in indices_otros_flat:
                lema_rel_idx = idx // total_ediles
                lema_abs_idx = np.where(mascara_otros)[0][lema_rel_idx]
                ediles_final[lema_abs_idx] += 1
                
        # Convertir los valores de NumPy a Python int antes de retornar
        return {lemas[i]: int(ediles_final[i]) for i in range(len(lemas))}
    else:
        # Si ya tiene la mayoría, mantener la distribución D'Hondt original
        # Convertir los valores de NumPy a Python int antes de retornar
        return {lemas[i]: int(ediles_dhondt[i]) for i in range(len(lemas))}


# Mantenemos esta función para compatibilidad, aunque ya no se usa
def distribuir_dhondt(
    votos: Dict[str, int],
    distribucion: Dict[str, int],
    ediles_a_distribuir: int
) -> None:
    """
    Distribuye ediles usando el método D'Hondt.
    Modifica el diccionario 'distribucion' in-place.
    
    Args:
        votos: Diccionario con votos por lema
        distribucion: Diccionario con la distribución actual de ediles (modificado in-place)
        ediles_a_distribuir: Cantidad de ediles a distribuir
    """
    # Crear una lista de tuplas (lema, votos / (ediles_actuales + 1))
    cocientes: List[Tuple[str, float]] = []
    
    # Distribuir los ediles restantes
    for _ in range(ediles_a_distribuir):
        # Calcular cocientes para cada lema
        cocientes.clear()
        for lema, votos_lema in votos.items():
            divisor = distribucion[lema] + 1
            cociente = votos_lema / divisor
            cocientes.append((lema, cociente))
        
        # Encontrar el lema con el cociente más alto
        lema_max, _ = max(cocientes, key=lambda x: x[1])
        
        # Asignar un edil al lema con el cociente más alto
        distribucion[lema_max] += 1 