# Módulo de Infraestructura

Este módulo contiene la lógica para interactuar con recursos externos como archivos, APIs o bases de datos.

## Archivos

- `loaders.py`: Contiene funciones para cargar datos electorales y geográficos.

## Uso

### Carga de datos electorales

```python
from infrastructure.loaders import load_election_data
from settings.settings import PATHS

# Cargar datos electorales
election_data = load_election_data(PATHS["election_data_2020"])
```

### Carga de datos geográficos

```python
from infrastructure.loaders import load_geo_data
from settings.settings import PATHS

# Cargar shapefile
gdf = load_geo_data(PATHS["departments_shapefile"])
```

## Compatibilidad con el código existente

Las funciones en este módulo están diseñadas para ser compatibles con el código existente:

- Mantienen las mismas firmas de método
- Utilizan los mismos formatos de datos
- Mantienen la misma lógica de cacheo con Streamlit

Sin embargo, internamente se han mejorado para usar:

- Manejo de errores más robusto
- Tipado estático para mejor documentación
- Separación clara entre carga de datos y lógica de negocio 