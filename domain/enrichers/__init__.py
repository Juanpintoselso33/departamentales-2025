"""
Módulo de enriquecimiento de datos electorales.
Proporciona funciones para añadir información derivada a los modelos canónicos.
"""

from domain.enrichers.enrich import enrich, aggregate, ElectionSummaryEnriquecido
from domain.enrichers.ediles_272 import ediles_por_lema 