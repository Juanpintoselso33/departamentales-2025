"""
Script para validar la normalización de nombres de departamentos.
Verifica que la normalización funcione correctamente para todos los casos de prueba.
"""
import json
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar los módulos
sys.path.append(str(Path(__file__).parent.parent))

from domain.transformers import (
    normalize_department_name,
    get_display_department_name,
    normalize_for_comparison,
    find_matching_name
)

def validate_normalizations():
    """
    Valida que las normalizaciones funcionen correctamente para todos los casos de prueba.
    """
    # Casos de prueba para nombres de departamentos
    test_cases = [
        # [Original, Esperado para normalización, Esperado para display]
        ["Rio Negro", "Río Negro", "Río Negro"],
        ["RIO NEGRO", "Río Negro", "Río Negro"],
        ["Rìo Negro", "Río Negro", "Río Negro"],  # Con acento grave
        ["San Jose", "San José", "San José"],
        ["SAN JOSÉ", "San José", "San José"],
        ["TREINTA Y TRES", "Treinta y Tres", "Treinta y Tres"],
        ["treinta y tres", "Treinta y Tres", "Treinta y Tres"],
        ["Treinta Y Tres", "Treinta y Tres", "Treinta y Tres"],
        ["CERRO LARGO", "Cerro Largo", "Cerro Largo"],
        ["cerro  largo", "Cerro Largo", "Cerro Largo"],  # Con espacios extras
    ]
    
    # Validar normalización de nombres
    print("\n=== Validación de normalización de nombres ===")
    for original, expected_norm, expected_display in test_cases:
        norm_result = normalize_department_name(original)
        display_result = get_display_department_name(original)
        
        if norm_result == expected_norm and display_result == expected_display:
            print(f"✅ [{original}] -> Norm: [{norm_result}], Display: [{display_result}]")
        else:
            print(f"❌ [{original}] -> Norm: [{norm_result}] (expected: {expected_norm}), Display: [{display_result}] (expected: {expected_display})")
    
    # Validar búsqueda por normalización
    print("\n=== Validación de búsqueda por normalización ===")
    candidates = ["Río Negro", "San José", "Cerro Largo", "Treinta y Tres", "Montevideo"]
    search_terms = ["rio negro", "RÍO NEGRO", "Rìo Negro", "SanJose", "treinta  y tres"]
    
    for term in search_terms:
        match = find_matching_name(term, candidates)
        if match:
            print(f"✅ Búsqueda: [{term}] -> Encontrado: [{match}]")
        else:
            print(f"❌ Búsqueda: [{term}] -> No encontrado")
    
    # Validar comparación de nombres
    print("\n=== Validación de comparación de nombres ===")
    comparison_pairs = [
        ("Río Negro", "rio negro", True),
        ("Rìo Negro", "RÍO NEGRO", True),
        ("SAN JOSÉ", "san jose", True),
        ("Treinta y Tres", "TREINTA Y TRES", True),
        ("Montevideo", "Flores", False)
    ]
    
    for name1, name2, expected in comparison_pairs:
        result = normalize_for_comparison(name1) == normalize_for_comparison(name2)
        if result == expected:
            print(f"✅ Comparación: [{name1}] == [{name2}] -> {result}")
        else:
            print(f"❌ Comparación: [{name1}] == [{name2}] -> {result} (expected: {expected})")
    
    return True

if __name__ == "__main__":
    validate_normalizations() 