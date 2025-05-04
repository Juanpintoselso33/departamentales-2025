"""
Smoke‑test del pipeline completo y exportación de datos
"""

from pathlib import Path
import sys, pathlib
import json
import os

ROOT = pathlib.Path(__file__).resolve().parents[1]   # carpeta del proyecto
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from infrastructure.loaders.cache import get_summary
# … resto del test …

SAMPLE_PATH = "data/election_data/2020/results_2020.json"


def test_pipeline(sample_path: str = SAMPLE_PATH, export_data: bool = True):
    if not Path(sample_path).exists():
        print("❌ Archivo no encontrado:", sample_path)
        return

    try:
        summary, stats = get_summary(sample_path)
    except Exception as e:
        print("❌ Pipeline lanzó excepción:", e)
        return

    # 1) departamentos cargados
    if not summary.departamentos:
        print("❌ No se cargaron departamentos")
        return

    # 2) verificación departamental
    for d in summary.departamentos:
        if sum(d.ediles.values()) != 31 or d.ediles.get(d.ganador, 0) < 16:
            print("❌ Inconsistencia en departamento", d.DN)
            return
        for m in d.Municipales:
            if sum(m.ediles.values()) != 5:
                print("❌ Inconsistencia en municipio", m.MD)
                return

    # 3) estadísticas nacionales
    keys = {"votos_totales", "porcentajes", "departamentos_ganados", "municipios_ganados"}
    if not keys <= stats.keys():
        print("❌ Stats nacionales incompletas")
        return

    print("✅ Pipeline completo funcionando correctamente")
    
    # 4) Exportar datos si se solicita
    if export_data:
        export_pipeline_data(summary, stats)


def export_pipeline_data(summary, stats):
    """Exporta los datos tal como salen de la pipeline"""
    try:
        # Directorio de salida
        output_dir = Path("data/pipeline_output")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Exportar estadísticas nacionales
        with open(output_dir / "stats_nacionales.json", "w", encoding="utf-8") as f:
            # Utilizamos model_dump_json solo para los modelos Pydantic
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        # Mostrar algunos datos para verificación
        print("\n===== DATOS DE LA PIPELINE =====")
        print(f"Año electoral: {summary.year}")
        print(f"Total departamentos procesados: {len(summary.departamentos)}")
        
        # Mostrar información de partidos a nivel nacional
        print("\nEstadísticas nacionales:")
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"  {key}: {len(value)} elementos")
            else:
                print(f"  {key}: {value}")
        
        # Exportar un resumen de cada departamento
        deptos_summary = []
        for depto in summary.departamentos:
            depto_data = {
                "nombre": depto.DN,
                "codigo": depto.DI,
                "ganador": depto.ganador,
                "total_ediles": sum(depto.ediles.values()),
                "ediles_por_partido": depto.ediles,
                "municipios": len(depto.Municipales),
                "total_votos": depto.TH
            }
            deptos_summary.append(depto_data)
            
            # Guardar datos crudos del departamento
            depto_dict = depto.model_dump(mode='json')
            with open(output_dir / f"depto_{depto.DI}.json", "w", encoding="utf-8") as f:
                json.dump(depto_dict, f, ensure_ascii=False, indent=2)
        
        # Guardar resumen de departamentos
        with open(output_dir / "deptos_resumen.json", "w", encoding="utf-8") as f:
            json.dump(deptos_summary, f, ensure_ascii=False, indent=2)
            
        print(f"\nDatos exportados a: {output_dir}")
        
    except Exception as e:
        print(f"❌ Error al exportar datos: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    # Si se pasa una ruta como argumento, usarla como fuente de datos
    if len(sys.argv) > 1:
        test_pipeline(sys.argv[1])
    else:
        test_pipeline()
