# Módulo de Configuración

Este módulo centraliza toda la configuración de la aplicación.

## Archivos

- `settings.py`: Contiene configuración general, rutas y constantes.
- `theme.py`: Contiene configuración visual como colores y banderas de partidos.

## Uso

### Importación de configuración

```python
from settings.settings import PATHS

# Usar una ruta
file_path = PATHS["election_data_2020"]
```

### Personalización de temas

```python
from settings.theme import PARTY_COLORS, get_party_color

# Obtener color para un partido
color = get_party_color("Frente Amplio")  # Retorna "#1DB954"
```

## Variables de entorno

La configuración se puede personalizar mediante variables de entorno:

- `ELECTION_YEAR`: Año electoral (predeterminado: "2020")
- `DATA_DIR`: Directorio de datos (predeterminado: "data/")
- `DEBUG`: Activa modo depuración y auto-reload (establézcase a "1" para activar) 