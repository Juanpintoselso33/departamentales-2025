"""
Script auxiliar para convertir shapefiles a GeoJSON.
Este script se ejecutará una sola vez para generar los archivos GeoJSON necesarios.
"""

import geopandas as gpd
import json
from pathlib import Path

# Configuración directa en el script
DEPARTMENT_NAME_MAPPING = {
    'ARTIGAS': 'Artigas',
    'CANELONES': 'Canelones',
    'CERRO LARGO': 'Cerro Largo',
    'COLONIA': 'Colonia',
    'DURAZNO': 'Durazno',
    'FLORES': 'Flores',
    'FLORIDA': 'Florida',
    'LAVALLEJA': 'Lavalleja',
    'MALDONADO': 'Maldonado',
    'MONTEVIDEO': 'Montevideo',
    'PAYSANDU': 'Paysandú',
    'RIO NEGRO': 'Río Negro',
    'RIVERA': 'Rivera',
    'ROCHA': 'Rocha',
    'SALTO': 'Salto',
    'SAN JOSE': 'San José',
    'SORIANO': 'Soriano',
    'TACUAREMBO': 'Tacuarembó',
    'TREINTA Y TRES': 'Treinta y Tres'
}

def normalize_properties(gdf: gpd.GeoDataFrame, is_department: bool = True) -> gpd.GeoDataFrame:
    """Normaliza las propiedades del GeoDataFrame."""
    gdf = gdf.copy()
    
    if is_department:
        # Para departamentos
        gdf['name'] = gdf['depto'].map(
            lambda x: DEPARTMENT_NAME_MAPPING.get(x.upper(), x.title())
        )
    else:
        # Para municipios
        gdf['name'] = gdf['municipio']
        gdf['department'] = gdf['depto'].map(
            lambda x: DEPARTMENT_NAME_MAPPING.get(x.upper(), x.title())
        )
    
    # Mantener solo las columnas necesarias y la geometría
    keep_cols = ['name', 'geometry'] if is_department else ['name', 'department', 'geometry']
    return gdf[keep_cols]

def convert_and_save(shapefile_path: str, output_path: str, is_department: bool = True) -> None:
    """Convierte un shapefile a GeoJSON y lo guarda."""
    print(f"Procesando: {shapefile_path}")
    
    # Leer shapefile
    gdf = gpd.read_file(shapefile_path)
    print(f"Columnas originales: {gdf.columns.tolist()}")
    
    # Normalizar propiedades
    gdf = normalize_properties(gdf, is_department)
    print(f"Columnas normalizadas: {gdf.columns.tolist()}")
    
    # Crear directorio si no existe
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar como GeoJSON
    geojson_data = json.loads(gdf.to_json())
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)
    
    print(f"Archivo guardado en: {output_path}")

def main():
    """Función principal que ejecuta las conversiones."""
    # Rutas de entrada (shapefiles)
    dept_shapefile = "data/shapefiles/uruguay_deptal/limites_departamentales_igm_20220211.shp"
    muni_shapefile = "data/shapefiles/uruguay_municipios/municipios_2020.shp"
    
    # Rutas de salida (en el mismo directorio que los shapefiles)
    dept_output = "data/shapefiles/uruguay_deptal/departments.geojson"
    muni_output = "data/shapefiles/uruguay_municipios/municipalities.geojson"
    
    print("Iniciando conversión de shapefiles a GeoJSON...")
    
    # Convertir departamentos
    print("\nProcesando departamentos...")
    convert_and_save(
        dept_shapefile,
        dept_output,
        is_department=True
    )
    
    # Convertir municipios
    print("\nProcesando municipios...")
    convert_and_save(
        muni_shapefile,
        muni_output,
        is_department=False
    )
    
    print("\n¡Conversión completada!")
    print(f"Archivos GeoJSON generados en los mismos directorios que los shapefiles")

if __name__ == "__main__":
    main() 