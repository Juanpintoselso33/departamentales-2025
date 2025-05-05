"""
Infraestructura de la aplicación.
Contiene adaptadores para interactuar con fuentes de datos y servicios externos.
"""

# Re-exportar funciones principales para facilitar importaciones
from infrastructure.loaders import load_election_data, detect_load

__all__ = ["load_election_data", "detect_load"] 