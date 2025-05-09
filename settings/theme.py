"""
Configuración visual y de temas para la aplicación.
Centraliza colores, estilos y recursos visuales.
"""
import random
import hashlib
from pathlib import Path
from typing import Optional

# Directorio de imágenes
IMAGE_DIR = Path(__file__).parent.parent / "data/images"

# Colores para los partidos políticos
PARTY_COLORS = {
    "Frente Amplio": "#3366CC",     # Azul oscuro
    "Partido Nacional": "#46C2FC",  # Azul claro
    "Partido Colorado": "#FF4136",  # Rojo
    "Cabildo Abierto": "#FFD700",   # Amarillo/dorado
    "Partido Independiente": "#673AB7", # Violeta
    "Partido de la Gente": "#58E75F", # Verde claro
    "Asamblea Popular": "#5e100cff", # Rojo oscuro
    "Partido Ecologista Radical Intransigente": "#0C5C02", # Verde oscuro
    "Partido Verde Animalista": "#6B946BFF", # Verde
    "Concertacion": "#FFC0CB", # Rosado
    "Coalicion Republicana": "#FFC0CB", # Rosado
    "Unidad Popular": "#5E100CFF", # Rojo oscuro
    "Partido Digital": "#FFA500", # Naranja
    "Partido Constitucional Ambientalista": "#EEFFC0FF", # Verde claro
    "Avanzar Republicano": "#C0FBFFFF", # Azul claro
    "No disponible": "#CCCCCC",     # Gris
    "Otros": "#AAAAAA"              # Gris oscuro
}

# Rutas a las imágenes de banderas de los partidos
PARTY_FLAGS = {
    "Frente Amplio": IMAGE_DIR / "flags/frente_amplio.png",
    "Partido Nacional": IMAGE_DIR / "flags/partido_nacional.png",
    "Partido Colorado": IMAGE_DIR / "flags/partido_colorado.png",
    "Cabildo Abierto": IMAGE_DIR / "flags/cabildo_abierto.png",
    "Partido Independiente": IMAGE_DIR / "flags/partido_independiente.png",
    "Partido de la Gente": IMAGE_DIR / "flags/partido_de_la_gente.png",
    "Otros": IMAGE_DIR / "flags/otros.png"
}

# Configuración para usar banderas o colores en el mapa
USE_PARTY_FLAGS = True

def get_random_color_for_party(party_name: str) -> str:
    """
    Genera un color aleatorio pero consistente para un partido.
    
    Args:
        party_name (str): Nombre del partido
        
    Returns:
        str: Código de color hexadecimal
    """
    # Usar el nombre del partido como semilla para generar un color consistente
    hash_object = hashlib.md5(party_name.encode())
    hash_hex = hash_object.hexdigest()
    
    # Usar los primeros 6 caracteres del hash como color
    return f"#{hash_hex[:6]}"

def get_party_color(party_name: str) -> str:
    """
    Obtiene el color asignado a un partido político.
    
    Args:
        party_name (str): Nombre del partido
        
    Returns:
        str: Código de color hexadecimal
    """
    return PARTY_COLORS.get(party_name, get_random_color_for_party(party_name))

def get_percentage_color(percentage: float) -> str:
    """
    Obtiene un color basado en el porcentaje.
    
    Args:
        percentage (float): Porcentaje (0-100)
        
    Returns:
        str: Código de color hexadecimal
    """
    from settings.settings import PERCENTAGE_COLORMAP
    
    # Get color scheme from settings
    colors = PERCENTAGE_COLORMAP["colors"]
    index = PERCENTAGE_COLORMAP["index"]
    
    # Make sure percentage is a number
    try:
        percentage = float(percentage)
    except (ValueError, TypeError):
        return "#CCCCCC"  # Default gray for invalid values
    
    # Find the right color
    for i, threshold in enumerate(index):
        if percentage <= threshold:
            return colors[i]
    
    # If higher than the highest threshold
    return colors[-1] 