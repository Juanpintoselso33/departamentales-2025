"""
Módulo para normalización de textos y nombres geográficos.
Centraliza todas las operaciones de normalización para mantener consistencia.
"""

from typing import Dict, Any, List, Optional, Union, Callable
from unicodedata import normalize
import re
from settings.settings import DEPARTMENT_NAME_MAPPING
from pathlib import Path
import json

# Mapa de caracteres con acento a sin acento para normalización
ACCENT_MAP = {
    'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
    'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
    'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u',
    'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
    'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
    'À': 'A', 'È': 'E', 'Ì': 'I', 'Ò': 'O', 'Ù': 'U',
    'Ä': 'A', 'Ë': 'E', 'Ï': 'I', 'Ö': 'O', 'Ü': 'U',
    'Â': 'A', 'Ê': 'E', 'Î': 'I', 'Ô': 'O', 'Û': 'U'
}

# Correcciones especiales para departamentos problemáticos
SPECIAL_DEPT_FIXES = {
    "RÌO NEGRO": "RIO NEGRO",  # Acento grave incorrecto
    "RÍO NEGRO": "RIO NEGRO",  # Acento normal
    "PAYSANDÚ": "PAYSANDU",
    "TACUAREMBÓ": "TACUAREMBO",
    "SAN JOSÉ": "SAN JOSE",
    "TREINTA Y TRES": "TREINTA Y TRES",
    "CERRO LARGO": "CERRO LARGO"
}

# Mapeo de departamentos para display con acentos correctos
DISPLAY_DEPT_NAMES = {
    "rio negro": "Río Negro",
    "paysandu": "Paysandú",
    "tacuarembo": "Tacuarembó",
    "san jose": "San José",
    "treinta y tres": "Treinta y Tres"
}

# Normalización de nombres de partidos políticos
PARTY_NAME_FIXES = {
    "PARTIDO CABILDO ABIERTO": "Cabildo Abierto",
    "Partido Cabildo Abierto": "Cabildo Abierto",
    "CABILDO ABIERTO": "Cabildo Abierto",
    "PARTIDO ASAMBLEA POPULAR": "Asamblea Popular",
    "Partido Asamblea Popular": "Asamblea Popular",
    "ASAMBLEA POPULAR": "Asamblea Popular"
}

# Tabla de alias → forma oficial (editable en infra/conf/party_aliases.json)
try:
    _ALIASES = json.loads(Path("infrastructure/conf/party_aliases.json").read_text("utf‑8"))
except FileNotFoundError:
    _ALIASES = {}
    # Si no existe el archivo, usaremos un diccionario vacío 
    # y luego se puede crear el archivo

_RE_WS      = re.compile(r"\s+")
_RE_ALNUM   = re.compile(r"[^A-Z0-9 ]")

def simplify(txt: str) -> str:
    """Mayúsculas, sin acentos ni signos: 'Frente Amplio' → 'FRENTE AMPLIO'."""
    t = normalize("NFKD", txt).encode("ascii", "ignore").decode()
    t = _RE_WS.sub(" ", t.upper()).strip()
    return _RE_ALNUM.sub("", t)

def canonical_party(raw: str) -> str:
    """Devuelve la etiqueta oficial según la tabla de alias o la versión *Title Case*."""
    key = simplify(raw)
    return _ALIASES.get(key, raw.title())

# Funciones compatibles con el código existente
normalize_for_comparison = simplify

def normalize_department_name(name: str) -> str:
    """Versión compatible con el código existente."""
    key = simplify(name)
    # Intentar buscar en el mapeo oficial
    for dept_name in DEPARTMENT_NAME_MAPPING.keys():
        if simplify(dept_name) == key:
            return DEPARTMENT_NAME_MAPPING[dept_name]
    # Si no se encontró, devolver la versión normalizada
    return name.title()

def normalize_party_name(name: str) -> str:
    """Versión compatible con el código existente."""
    return canonical_party(name)

# Mantener otras funciones necesarias para compatibilidad
def get_display_department_name(name: str) -> str:
    """Obtiene el nombre para mostrar de un departamento."""
    key = simplify(name)
    for dept_name, display_name in DEPARTMENT_NAME_MAPPING.items():
        if simplify(dept_name) == key:
            return display_name
    return name.title()

def are_names_equivalent(name1: str, name2: str) -> bool:
    """Determina si dos nombres son equivalentes."""
    return simplify(name1) == simplify(name2)

def find_matching_name(target: str, candidates: list) -> str | None:
    """Busca el nombre que mejor coincide con el objetivo."""
    target_simple = simplify(target)
    for candidate in candidates:
        if simplify(candidate) == target_simple:
            return candidate
    return None 