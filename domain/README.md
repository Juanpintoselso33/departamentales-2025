# Módulo de Dominio

Este módulo contiene la lógica de negocio pura de la aplicación, independiente de la interfaz de usuario.

## Archivos

- `electoral.py`: Contiene la lógica para el cálculo de ediles y métricas electorales.
- `summary.py`: Contiene la lógica para generar resúmenes a nivel nacional y departamental.

## Uso

### Lógica Electoral

```python
from domain.electoral import asignar_ediles, calcular_porcentajes

# Votos por partido
votos = {
    "Partido A": 1200,
    "Partido B": 800,
    "Partido C": 500
}

# Calcular porcentajes
porcentajes = calcular_porcentajes(votos)
# {'Partido A': 48.0, 'Partido B': 32.0, 'Partido C': 20.0}

# Asignar ediles (por defecto 31 ediles)
ediles = asignar_ediles(votos)
# {'Partido A': 15, 'Partido B': 10, 'Partido C': 6}
```

### Resúmenes de datos

```python
from domain.summary import get_national_summary, get_department_summary

# Generar resumen nacional
resumen = get_national_summary(election_data)

# Generar resumen para un departamento específico
resumen_montevideo = get_department_summary(election_data, "Montevideo")
```

## Principios de diseño

- **Pureza funcional**: Las funciones en esta capa son puras, sin efectos secundarios.
- **Independencia de UI**: No hay importaciones de Streamlit ni referencias a la interfaz.
- **Independencia de infraestructura**: No hay acceso directo a bases de datos o archivos. 