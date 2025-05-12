# Mapa de Elecciones Departamentales Uruguay

Aplicación interactiva para visualizar los resultados de las elecciones departamentales de Uruguay. Desarrollada con Streamlit, ofrece una interfaz dinámica para explorar los datos electorales a nivel nacional, departamental y municipal.

## 🚀 Características

- **Visualización geográfica**: Mapa interactivo con resultados por departamento
- **Múltiples niveles de análisis**: Vistas nacional, departamental y municipal
- **Datos históricos**: Resultados de elecciones 2015 y 2020
- **Preparada para 2025**: Configurada para mostrar datos en tiempo real
- **Cálculo automático**: Distribución de cargos electivos (intendentes, ediles, alcaldes, concejales)
- **Interfaz adaptativa**: Diseño responsive y amigable para el usuario

## 💻 Tecnologías

- **Streamlit**: Framework principal para la interfaz
- **Pandas**: Procesamiento de datos
- **Pydantic**: Modelado y validación de datos
- **Plotly**: Visualizaciones interactivas
- **GeoPandas**: Visualización geoespacial

## 🛠️ Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/Juanpintoselso33/departamentales-2025.git
cd departamentales-2025
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
# En Windows
venv\Scripts\activate
# En macOS/Linux
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## 🖥️ Uso

Ejecutar la aplicación:
```bash
streamlit run app.py
```

La aplicación estará disponible en http://localhost:8501

### Guía rápida:

- **Año Electoral**: Seleccione el año de la elección (2015, 2020)
- **Selector Principal**: Use el menú desplegable para elegir:
  - **NACIONAL**: Resumen general del país
  - **[Departamento]**: Detalle del departamento seleccionado
- **Mapa**: Visualiza el partido ganador por departamento

## 📁 Estructura del proyecto

```
├── app/                   # Componentes de la interfaz de usuario
│   ├── components/        # Componentes reutilizables
│   │   ├── dashboards/    # Visualizaciones específicas
│   │   └── ui/            # Elementos de la interfaz
├── domain/                # Lógica de negocio y modelos
│   ├── enrichers/         # Enriquecedores de datos
│   ├── transformers/      # Transformadores de datos
├── infrastructure/        # Acceso a datos y servicios externos
│   ├── loaders/           # Cargadores de datos
├── data/                  # Datos electorales y geoespaciales
├── utils/                 # Utilidades generales
├── settings/              # Configuración de la aplicación
├── app.py                 # Punto de entrada de la aplicación
└── requirements.txt       # Dependencias del proyecto
```

## ⚙️ Configuración

Las configuraciones principales se encuentran en:
- `settings/settings.py`: Rutas a archivos de datos, mapeos y constantes
- `settings/theme.py`: Configuración visual y temática

## 🔍 Características detalladas

1. **Vista Nacional**:
   - Mapa interactivo de resultados por departamento
   - Distribución de intendencias por partido
   - Distribución de ediles por partido
   - Distribución de alcaldías por partido

2. **Vista Departamental**:
   - Resultados detallados para cada departamento
   - Distribución de bancas en la Junta Departamental
   - Intendente electo y porcentaje de votos
   - Visualización de municipios del departamento

3. **Vista Municipal**:
   - Resultados para cada municipio
   - Alcalde electo
   - Composición del Concejo Municipal

## 🤝 Contribución

Si deseas contribuir al proyecto:

1. Haz un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/amazing-feature`)
3. Realiza tus cambios y haz commit (`git commit -m 'Agregar funcionalidad'`)
4. Sube tus cambios (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. 

## 📊 Disclaimer

Los cálculos de asignación de cargos (Ediles, Concejales) son interpretaciones realizadas por esta aplicación y pueden diferir de los resultados oficiales de la Corte Electoral.

## Mejoras Recientes

Se han implementado las siguientes mejoras para garantizar mayor precisión y claridad en los resultados:

### 1. Corrección del cálculo de votos válidos
- Implementamos la metodología exacta de la Corte Electoral: los votos válidos son exclusivamente la suma de votos ya asignados a partidos.
- Usamos directamente la suma de los valores `Tot` de cada partido en `Departamentales`.
- Excluimos completamente los votos observados (TO) del cálculo de porcentajes.

### 2. Mejora en el formato de nombres de candidatos
- Implementamos una función mejorada que capitaliza correctamente cada palabra.
- Agregamos reconocimiento de acentos específicos en nombres comunes (María, José, etc.).
- Implementamos patrones para detectar y extraer solo el primer candidato de una lista.
- Mejoramos el manejo de nombres compuestos y conectores (de, del, etc.).

### 3. Implementación de candidatos indefinidos
- Si no se encuentra un nombre de candidato específico, se muestra "Candidato de [partido]" como valor por defecto.

### 4. Mejora de avisos sobre datos preliminares
- Implementamos advertencias claras cuando el porcentaje escrutado es menor al 10%.
- Agregamos una columna de "Advertencia" que indica explícitamente "ADVERTENCIA: Datos preliminares".

### 5. Corrección en la interpretación de campos numéricos
- Implementamos conversión segura de strings a números con manejo de errores.
- Usamos `strip()` para eliminar espacios antes de la conversión.

---

Desarrollado por Lic. Juan Ignacio Pintos Elso. 