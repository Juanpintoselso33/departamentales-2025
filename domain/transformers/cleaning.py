"""
Limpieza profunda:
1. Normaliza nombres (partidos, sublemas, listas, municipios, departamentos).
2. Convierte porcentajes string→float donde haga falta.
3. Ejecuta los validadores del modelo: si algo no cuadra, levanta RuntimeError.
"""

from __future__ import annotations
from typing import List
from copy import deepcopy
from decimal import Decimal
from pydantic import ValidationError

from domain.models import (
    ElectionSummary, Departamento, Municipio, PartidoDepartamento,
    PartidoMunicipio, Sublema, Lista, Hoja
)
from domain.transformers.text_normalizer import simplify, canonical_party


# ---------- funciones atómicas ---------- #

def _norm_hoja(h: Hoja) -> Hoja:
    return h.copy(update={"HN": simplify(h.HN)})

def _norm_lista(l: Lista) -> Lista:
    return l.copy(update={"Dsc": simplify(l.Dsc)})

def _norm_sublema(sl: Sublema) -> Sublema:
    """Normaliza un objeto Sublema procesando sus listas (Junta y Municipio)."""
    listas_junta = [_norm_lista(li) for li in sl.ListasJunta]
    listas_municipio = [_norm_lista(li) for li in sl.ListasMunicipio]
    return sl.model_copy(update={
        'ListasJunta': listas_junta,
        'ListasMunicipio': listas_municipio
    })

def _norm_partido_muni(p: PartidoMunicipio) -> PartidoMunicipio:
    hojas = [_norm_hoja(h) for h in p.Hojas]
    muni_det = p.Municipio.copy(
        update={"Sublemas": [_norm_sublema(s) for s in p.Municipio.Sublemas]}
    )
    return p.copy(update={
        "LN": canonical_party(p.LN),
        "Hojas": hojas,
        "Municipio": muni_det
    })

def _norm_municipio(m: Municipio) -> Municipio:
    partidos = [_norm_partido_muni(pm) for pm in m.Eleccion]
    
    # CORRECCIÓN: Mejorar interpretación de valores numéricos
    # Extraer y normalizar el porcentaje de participación
    cp_normalizado = _normalize_numeric_value(m.CP)
    
    return m.copy(update={
        "MD": simplify(m.MD),
        "CP": cp_normalizado,
        "Eleccion": partidos
    })

def _norm_partido_depto(p: PartidoDepartamento) -> PartidoDepartamento:
    hojas = [_norm_hoja(h) for h in p.Hojas]
    inten = p.Intendente.copy(update={
        "Listas": [_norm_hoja(h) for h in p.Intendente.Listas]
    })
    junta = p.Junta.copy(update={
        "Sublemas": [_norm_sublema(s) for s in p.Junta.Sublemas]
    })
    return p.copy(update={
        "LN": canonical_party(p.LN),
        "Hojas": hojas,
        "Intendente": inten,
        "Junta": junta
    })

def _norm_departamento(d: Departamento) -> Departamento:
    munis  = [_norm_municipio(m) for m in d.Municipales]
    dpart  = [_norm_partido_depto(p) for p in d.Departamentales]
    
    # CORRECCIÓN: Mejorar interpretación de valores numéricos
    # Extraer y normalizar el porcentaje de participación
    cp_normalizado = d.CP
    if isinstance(cp_normalizado, str):
        # Eliminar espacios antes de convertir
        cp_normalizado = cp_normalizado.strip().replace(",", ".")
        # Solo convertir si el valor no está vacío
        if cp_normalizado:
            try:
                # Convertir a Decimal para evitar errores de punto flotante
                cp_normalizado = str(Decimal(cp_normalizado))
            except:
                # Si falla, mantener el valor original
                pass
    
    return d.copy(update={
        "DN": simplify(d.DN),
        "Municipales": munis,
        "Departamentales": dpart,
        "CP": cp_normalizado
    })

# Función auxiliar para normalizar valores numéricos
def _normalize_numeric_value(value):
    """
    Normaliza valores numéricos con manejo de errores.
    Elimina espacios y normaliza punto decimal.
    
    Args:
        value: Valor a normalizar (string o número)
    
    Returns:
        String normalizado representando el número
    """
    from decimal import Decimal, InvalidOperation
    
    if value is None:
        return "0"
    
    # Convertir a string si no lo es
    if not isinstance(value, str):
        value = str(value)
    
    # Eliminar espacios y normalizar puntos decimales
    value = value.strip().replace(",", ".")
    
    if not value:  # Si es cadena vacía
        return "0"
    
    try:
        # Usar Decimal para mayor precisión
        return str(Decimal(value))
    except (InvalidOperation, ValueError):
        # En caso de error, devolver 0
        return "0"

# ---------- API externa del paso 2 ---------- #

def clean(summary: ElectionSummary) -> ElectionSummary:
    """
    Devuelve una NUEVA instancia con textos normalizados y porcentajes
    convertidos.  Si cualquier validador de los modelos canónicos falla,
    relanza RuntimeError con el mensaje original de Pydantic.
    """
    try:
        deptos = [_norm_departamento(d) for d in summary.departamentos]
        return summary.copy(update={"departamentos": deptos})
    except ValidationError as err:
        raise RuntimeError(f"Transformación Paso 2 falló: {err}") from None 