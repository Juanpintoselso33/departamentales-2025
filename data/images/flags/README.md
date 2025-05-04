# Imágenes de Banderas de Partidos Políticos

Para utilizar las banderas de los partidos políticos en la visualización del mapa, debes añadir imágenes de las banderas en este directorio.

## Instrucciones

1. Guarda las imágenes de las banderas de los partidos con los siguientes nombres:
   - `frente_amplio.png` - Bandera del Frente Amplio
   - `partido_nacional.png` - Bandera del Partido Nacional
   - `partido_colorado.png` - Bandera del Partido Colorado
   - `cabildo_abierto.png` - Bandera de Cabildo Abierto
   - `partido_independiente.png` - Bandera del Partido Independiente
   - `partido_de_la_gente.png` - Bandera del Partido de la Gente
   - `otros.png` - Imagen para otros partidos

2. Asegúrate de que las imágenes estén en formato PNG y tengan un tamaño adecuado (recomendado: 100x100 píxeles).

3. Para una mejor visualización, es recomendable que las imágenes tengan un patrón repetible o que sean representativas del partido.

## Configuración

Puedes activar o desactivar el uso de las banderas en lugar de colores modificando la variable `USE_PARTY_FLAGS` en el archivo `utils/config.py`:

```python
# Para usar banderas
USE_PARTY_FLAGS = True

# Para usar colores (comportamiento original)
USE_PARTY_FLAGS = False
```

## Añadir Nuevos Partidos

Si necesitas añadir un nuevo partido, sigue estos pasos:

1. Añade la imagen de la bandera en este directorio con un nombre descriptivo
2. Actualiza el diccionario `PARTY_FLAGS` en `utils/config.py` para incluir el nuevo partido
3. Asegúrate de también añadir un color para el partido en `PARTY_COLORS` 