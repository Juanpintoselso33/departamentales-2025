import pandas as pd
from typing import Dict, Any, List, Optional
from st_aggrid import GridOptionsBuilder

def create_progress_bar_renderer() -> str:
    """
    Crea un renderizador de barras de progreso para AgGrid.
    Devuelve código JavaScript como string para evitar problemas de serialización.
    
    Returns:
        String con código JavaScript para renderizar barras de progreso
    """
    return """
    function(params) {
        const value = params.value || 0;
        const pct = Math.round(value * 10) / 10;
        
        // Colores según el porcentaje
        let color = '#3498db';  // Azul por defecto
        if (pct > 50) {
            color = '#2ecc71';  // Verde para mayoritario
        } else if (pct > 30) {
            color = '#f39c12';  // Naranja para significativo
        }
        
        const barWidth = Math.min(pct, 100);
        
        // HTML para la barra de progreso
        return `
            <div style="display: flex; align-items: center; height: 100%;">
                <div style="width: ${barWidth}%; background-color: ${color}; height: 80%; border-radius: 2px;"></div>
                <div style="margin-left: 5px;">${pct.toFixed(1)}%</div>
            </div>
        `;
    }
    """

def create_department_table_options(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Crea opciones para una tabla de departamentos en AgGrid.
    
    Args:
        df: DataFrame con datos de departamentos
        
    Returns:
        Opciones configuradas para AgGrid
    """
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configurar columnas
    gb.configure_default_column(
        sortable=True,
        filterable=True,
        resizable=True
    )
    
    # Personalizar columna de porcentaje con barra de progreso
    if "pct" in df.columns:
        gb.configure_column(
            "pct",
            header_name="% Votos",
            type=["numericColumn"],
            valueFormatter="data.pct.toFixed(1) + '%'",
            cellRenderer=create_progress_bar_renderer()
        )
    
    # Personalizar columna de partido si existe
    if "partido" in df.columns:
        gb.configure_column("partido", header_name="Partido")
    
    return gb.build()

def create_party_vote_comparison(election_data: Dict[str, Dict]) -> pd.DataFrame:
    """
    Crea un DataFrame para comparar votos por partido entre departamentos.
    
    Args:
        election_data: Datos electorales por departamento
        
    Returns:
        DataFrame preparado para visualización
    """
    comparison_rows = []
    
    # Extraer datos de cada departamento
    for dept_name, dept_data in election_data.items():
        if "vote_percentages" in dept_data:
            # Añadir cada partido como una fila
            for party, pct in dept_data["vote_percentages"].items():
                comparison_rows.append({
                    "Departamento": dept_name,
                    "Partido": party,
                    "Porcentaje": float(pct)
                })
    
    # Crear DataFrame
    if comparison_rows:
        df = pd.DataFrame(comparison_rows)
        return df
    
    return pd.DataFrame(columns=["Departamento", "Partido", "Porcentaje"])

def prepare_summary_data(election_data: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Prepara un resumen nacional a partir de los datos por departamento.
    
    Args:
        election_data: Datos electorales por departamento
        
    Returns:
        Diccionario con datos resumidos para visualización
    """
    summary = {
        "intendencias": {},
        "ediles_totales": {},
        "department_winners": {}
    }
    
    # Procesar cada departamento
    for dept_name, dept_data in election_data.items():
        # Contar intendencias por partido
        if "winning_party" in dept_data:
            party = dept_data["winning_party"]
            if party not in summary["intendencias"]:
                summary["intendencias"][party] = 0
            summary["intendencias"][party] += 1
            
            # Almacenar ganador de cada departamento
            summary["department_winners"][dept_name] = party
        
        # Sumar ediles por partido
        if "council_seats" in dept_data:
            for party, seats in dept_data["council_seats"].items():
                if party not in summary["ediles_totales"]:
                    summary["ediles_totales"][party] = 0
                summary["ediles_totales"][party] += seats
    
    return summary 