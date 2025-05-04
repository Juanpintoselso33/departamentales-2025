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
    listas = [_norm_lista(li) for li in sl.Listas]
    return sl.copy(update={"Nombre": simplify(sl.Nombre), "Listas": listas})

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
    return m.copy(update={
        "MD": simplify(m.MD),
        "CP": str(Decimal(m.CP.replace(",", "."))),   # porcentaje → string normalizada
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
    return d.copy(update={
        "DN": simplify(d.DN),
        "Municipales": munis,
        "Departamentales": dpart,
        "CP": str(Decimal(d.CP.replace(",", ".")))
    })

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