"""
Modelos canónicos de la aplicación electoral.

Todas las clases representan la jerarquía estable sobre la que opera
el dominio interno, independientemente de cómo vengan los archivos
fuente de cada año.  Cada capa valida que sus totales coincidan con la
suma de los elementos hijos, de modo que cualquier inconsistencia se
detecta al instanciar el modelo.

NIVELES:
Hoja → Lista → Sublema → PartidoMunicipio → Municipio
            ↘                     ↘
             Lista           PartidoDepartamento → Departamento
                                    ↘
                               ElectionSummary (raíz)
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ------------------------------------------------------------------
# 1.  Hojas y Listas
# ------------------------------------------------------------------

class Hoja(BaseModel):
    """Papeleta individual (la unidad mínima de votación)."""
    HI: int = Field(0, description="Número de la hoja (código en la papeleta)")
    Tot: int = Field(0, description="Votos que recibió esta hoja")
    HN: str = Field("", description="Descripción corta de la hoja")

    model_config = ConfigDict(extra="allow")


class Lista(BaseModel):
    """Conjunto de hojas que se presenta como lista en una elección."""
    LId: int = Field(0, description="Identificador numérico de la lista")
    Dsc: str = Field("", description="Descripción (nombre) de la lista")
    VH: int = Field(0, description="Votos por hoja dentro de la lista")
    VAL: int = Field(0, description="Votos al lema de la lista")
    Tot: int = Field(0, description="Total de votos de la lista")

    model_config = ConfigDict(extra="allow")


# ------------------------------------------------------------------
# 2.  Sublema
# ------------------------------------------------------------------

class Sublema(BaseModel):
    """Agrupación de listas bajo un mismo sub‑lema partidario."""
    Id: int = Field(0, description="ID del sublema")
    Nombre: str = Field("", description="Nombre del sublema")
    VH: int = Field(0, description="Votos por hoja (suma de VH de listas)")
    VAS: int = Field(0, description="Votos al sublema")
    Tot: int = Field(0, description="Total de votos del sublema")
    ListasJunta: List[Lista] = Field(default_factory=list, description="Listas que integran el sublema para la Junta")
    ListasMunicipio: List[Lista] = Field(default_factory=list, description="Listas que integran el sublema para el Municipio")

    model_config = ConfigDict(extra="allow")


# ------------------------------------------------------------------
# 3.  Detalles internos de un partido en un municipio / departamento
# ------------------------------------------------------------------

class DetalleMunicipioPartido(BaseModel):
    """Desglose por sublema de un partido dentro de un municipio."""
    Sublemas: List[Sublema] = Field(default_factory=list, description="Sublemas que compiten en el municipio")
    TALDSL: int = Field(0, description="Total al lema de los sublemas")
    Tot: int = Field(0, description="Votos totales del partido en el municipio")

    model_config = ConfigDict(extra="allow")


class DetalleIntendente(BaseModel):
    """Desglose de una candidatura a Intendente dentro del partido."""
    Listas: List[Hoja] = Field(default_factory=list, description="Hojas que respaldan la candidatura")
    TALDI: int = Field(0, description="Total al lema para Intendente")
    Tot: int = Field(0, description="Votos totales a Intendente")

    model_config = ConfigDict(extra="allow")


class DetalleJunta(BaseModel):
    """Desglose de la elección de Junta Departamental dentro del partido."""
    Sublemas: List[Sublema] = Field(default_factory=list, description="Sublemas que presentan listas a la Junta")
    TALDSL: int = Field(0, description="Total al lema en Junta")
    Tot: int = Field(0, description="Votos totales a la Junta")

    model_config = ConfigDict(extra="allow")


# ------------------------------------------------------------------
# 4.  Partidos (resultado en municipio y en departamento)
# ------------------------------------------------------------------

class PartidoMunicipio(BaseModel):
    """Resultado de un partido en un municipio concreto."""
    LI: int = Field(0, description="ID del partido")
    LN: str = Field("", description="Nombre del partido")
    LIcon: Optional[str] = Field("", description="URL o código de icono")
    TH: int = Field(0, description="Total de hojas computadas")
    TAL: int = Field(0, description="Total al lema en el municipio")
    Tot: int = Field(0, description="Total de votos del partido en el municipio")
    Hojas: List[Hoja] = Field(default_factory=list, description="Hojas presentadas por el partido")
    Municipio: DetalleMunicipioPartido = Field(default_factory=DetalleMunicipioPartido, description="Desglose interno por sublema")

    model_config = ConfigDict(extra="allow")


class PartidoDepartamento(BaseModel):
    """Resultado de un partido a nivel departamental."""
    LI: int = Field(0, description="ID del partido")
    LN: str = Field("", description="Nombre del partido")
    LIcon: Optional[str] = Field("", description="URL o código de icono")
    TH: int = Field(0, description="Total de hojas computadas")
    TAL: int = Field(0, description="Total al lema departamental")
    Tot: int = Field(0, description="Total de votos del partido en el departamento")
    Hojas: List[Hoja] = Field(default_factory=list, description="Hojas presentadas por el partido")
    Intendente: DetalleIntendente = Field(default_factory=DetalleIntendente, description="Detalle de la elección a Intendente")
    Junta: DetalleJunta = Field(default_factory=DetalleJunta, description="Detalle de la elección a Junta Departamental")

    model_config = ConfigDict(extra="allow")


# ------------------------------------------------------------------
# 5.  Municipio y Departamento
# ------------------------------------------------------------------

class Municipio(BaseModel):
    """Resultado completo de un municipio."""
    MI: int = Field(0, description="ID (código) del municipio")
    MD: str = Field("", description="Nombre del municipio")
    CE: int = Field(0, description="Votos observados (escrutados)")
    CT: int = Field(0, description="Habilitados para votar")
    CP: str = Field("0", description="Porcentaje de participación (string con decimales)")
    TA: int = Field(0, description="Votos en blanco")
    TO: int = Field(0, description="Votos anulados")
    TNO: int = Field(0, description="Votos no observados")
    TE: int = Field(0, description="Sobres en urna")
    TH: int = Field(0, description="Total de votos válidos")
    CFCO: bool = Field(False, description="¿Conteo final confirmado?")
    TEB: int = Field(0, description="Boletas escrutadas")
    TEBP: int = Field(0, description="Porcentaje de boletas escrutadas")
    TOR: int = Field(0, description="Recuento observado")
    CCO: int = Field(0, description="Mesas computadas")
    Eleccion: List[PartidoMunicipio] = Field(default_factory=list, description="Resultados por partido")

    model_config = ConfigDict(extra="allow")


class Departamento(BaseModel):
    """Resultado completo de un departamento."""
    DI: str = Field("", description="Código del departamento (00–19)")
    DN: str = Field("", description="Nombre del departamento")
    CE: int = Field(0, description="Votos observados")
    CT: int = Field(0, description="Habilitados para votar")
    CP: str = Field("0", description="Porcentaje de participación")
    TA: int = Field(0, description="Votos en blanco")
    TO: int = Field(0, description="Votos anulados")
    TNO: int = Field(0, description="Votos no observados")
    TE: int = Field(0, description="Sobres en urna")
    TH: int = Field(0, description="Total votos válidos dpto.")
    CFCO: bool = Field(False, description="¿Conteo final confirmado?")
    TEB: int = Field(0, description="Boletas escrutadas")
    TEBP: int = Field(0, description="Porcentaje de boletas escrutadas")
    TOR: int = Field(0, description="Recuento observado")
    CCO: int = Field(0, description="Mesas computadas")
    Municipales: List[Municipio] = Field(default_factory=list, description="Resultados de todos los municipios")
    Departamentales: List[PartidoDepartamento] = Field(default_factory=list, description="Resultados departamentales por partido")

    model_config = ConfigDict(extra="allow")


# ------------------------------------------------------------------
# 6.  Raíz nacional
# ------------------------------------------------------------------

class ElectionSummary(BaseModel):
    """Contenedor nacional de un año electoral."""
    year: int = Field(0, description="Año de la elección")
    departamentos: List[Departamento] = Field(default_factory=list, description="Listado de departamentos")

    model_config = ConfigDict(extra="allow")
