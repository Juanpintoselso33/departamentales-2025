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

# Palabras comunes con acentos en nombres propios
COMMON_ACCENTED_WORDS = {
    "MARIA": "María",
    "JOSE": "José",
    "JOSE LUIS": "José Luis",
    "JOSE MARIA": "José María",
    "JESUS": "Jesús",
    "MARTIN": "Martín",
    "ANGEL": "Ángel",
    "SEBASTIAN": "Sebastián",
    "ANDRES": "Andrés",
    "RAMON": "Ramón",
    "CESAR": "César",
    "ALVARO": "Álvaro",
    "GERMAN": "Germán",
    "RAUL": "Raúl",
    "OSCAR": "Óscar",
    "JOAQUIN": "Joaquín",
}

# Palabras que no deben capitalizarse en nombres
LOWERCASE_WORDS = ['de', 'del', 'la', 'las', 'los', 'y', 'e', 'a', 'en', 'el']

def format_candidate_name(raw_name: str) -> str:
    """
    Formatea correctamente un nombre de candidato.
    1. Capitaliza cada palabra.
    2. Aplica acentos en palabras comunes donde corresponde.
    3. Mantiene conectores en minúscula ("de", "del", etc.)
    4. Extrae solo el primer candidato si hay varios separados por "y" o similar.
    
    Args:
        raw_name: Nombre en formato crudo (mayúsculas, sin acentos, etc.)
        
    Returns:
        Nombre formateado correctamente
    """
    if not raw_name or raw_name == "No disponible":
        return "No disponible"
    
    # Convertir a string si no lo es
    raw_name = str(raw_name).strip()
    
    # Patrones para extraer primer candidato
    patterns = [
        r'^([^/]+)/',          # Formato "Nombre1/Nombre2"
        r'^([^y]+) y ',        # Formato "Nombre1 y Nombre2"
        r'^([^-]+)-',          # Formato "Nombre1-Nombre2"
        r'^([^,]+),',          # Formato "Nombre1, Nombre2"
        r'^([^\(]+)\(',        # Formato "Nombre1 (Nombre2"
    ]
    
    # Intentar extraer el primer candidato según los patrones
    for pattern in patterns:
        import re
        match = re.search(pattern, raw_name)
        if match:
            raw_name = match.group(1).strip()
            break
    
    # Dividir en palabras y capitalizar cada una
    words = raw_name.lower().split()
    capitalized = []
    
    for i, word in enumerate(words):
        # Verificar si existe una versión con acento
        upper_word = word.upper()
        if upper_word in COMMON_ACCENTED_WORDS:
            capitalized.append(COMMON_ACCENTED_WORDS[upper_word])
        # Verificar si es una palabra que debe ir en minúscula (excepto al inicio)
        elif word.lower() in LOWERCASE_WORDS and i > 0:
            capitalized.append(word.lower())
        # Caso normal: capitalizar
        else:
            # Manejar palabras con apóstrofes o caracteres especiales
            if "'" in word:
                parts = word.split("'")
                capitalized.append("'".join(p.capitalize() for p in parts))
            else:
                capitalized.append(word.capitalize())
    
    # Unir todo y devolver
    return " ".join(capitalized) 