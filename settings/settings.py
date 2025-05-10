"""
Configuración centralizada de la aplicación.
Maneja rutas, constantes y configuración de aplicación.
"""
import os
from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.parent

# Año electoral de los datos (configurable por variable de entorno)
ELECTION_YEAR = os.environ.get("ELECTION_YEAR", "2020")

# Directorio de datos (configurable por variable de entorno)
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))

# URL del proxy para la API 2025 (puede ser local o en la nube)
API_PROXY_2025 = os.environ.get("API_PROXY_2025")

# Rutas de archivos
PATHS = {
    "departments_geojson": DATA_DIR / "shapefiles/uruguay_deptal/departments.geojson",
    "municipalities_geojson": DATA_DIR / "shapefiles/uruguay_municipios/municipalities.geojson",
    "election_data_2020": DATA_DIR / "election_data/2020/results_2020.json",
    "election_data_2015": DATA_DIR / "election_data/2015/results_2015.json",
    # URL API 2025 (usa proxy si está definido, si no la original)
    "API_URL_2025": API_PROXY_2025 or "https://eleccionesdepartamentales2025.corteelectoral.gub.uy/JSON/ResumenGeneral_P_DPTOS.json?1746811418963", 
}

# Mapeo de nombres de departamentos (para normalización)
DEPARTMENT_NAME_MAPPING = {
    "ARTIGAS": "Artigas",
    "CANELONES": "Canelones",
    "CERRO LARGO": "Cerro Largo",
    "COLONIA": "Colonia",
    "DURAZNO": "Durazno",
    "FLORES": "Flores", 
    "FLORIDA": "Florida",
    "LAVALLEJA": "Lavalleja",
    "MALDONADO": "Maldonado",
    "MONTEVIDEO": "Montevideo",
    "PAYSANDU": "Paysandú",
    "RIO NEGRO": "Río Negro",
    "RIVERA": "Rivera",
    "ROCHA": "Rocha",
    "SALTO": "Salto",
    "SAN JOSE": "San José",
    "SORIANO": "Soriano",
    "TACUAREMBO": "Tacuarembó",
    "TREINTA Y TRES": "Treinta y Tres"
}

# Coordenadas por defecto para el mapa
# Centro ajustado para visualizar mejor Uruguay en su proporción vertical
DEFAULT_MAP_CENTER = [-32.7, -56.0]  # Centrado ligeramente más al norte para mostrar todo el país
DEFAULT_MAP_ZOOM = 7.0  # Zoom ajustado para ver todo el país (modificado para mejor experiencia de usuario)

# Límites de navegación para el mapa (Uruguay)
# Estos límites definen el rectángulo en el que se puede navegar, evitando salirse del área de interés
MAP_BOUNDS = [
    [-30.0, -59.0],  # Esquina superior izquierda (noroeste)
    [-35.0, -53.0]   # Esquina inferior derecha (sureste)
]

# Opciones de visualización
VIEW_OPTIONS = {
    "Partido ganador": "winning_party",
    "Porcentaje de votos": "vote_percentage"
}

# Configuración para colormap de porcentajes
PERCENTAGE_COLORMAP = {
    "colors": ['#FEF0D9', '#FDCC8A', '#FC8D59', '#E34A33', '#B30000'],
    "index": [30, 40, 50, 60, 70],
    "vmin": 30,
    "vmax": 70
}

# Modo debug (activa auto-reload)
DEBUG = os.environ.get("DEBUG", "0") == "1"

# Configuración para auto-reload (similar a nodemon)
AUTO_RELOAD_CONFIG = {
    "enabled": DEBUG,
    "watch_dirs": [".", "utils", "app", "data", "domain", "infrastructure", "settings"],
    "exclude_dirs": [".git", "__pycache__", ".streamlit", "venv"],
    "watch_extensions": [".py", ".json", ".png"]
} 