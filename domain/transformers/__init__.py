"""
Módulo de transformers para procesamiento de datos electorales.
Provee herramientas para validar, normalizar y enriquecer los datos electorales.
"""

# Exportar las funciones principales de text_normalizer
from domain.transformers.text_normalizer import (
    simplify,
    canonical_party,
    normalize_for_comparison,
    normalize_department_name,
    normalize_party_name,
    get_display_department_name,
    are_names_equivalent,
    find_matching_name
)

# Exportar la función principal de cleaning
from domain.transformers.cleaning import clean

# Mantener compatibilidad con código existente
from domain.transformers.geo_transformer import transform_department_geodata, transform_municipality_geodata 