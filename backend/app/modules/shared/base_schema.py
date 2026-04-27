from pydantic import BaseModel, ConfigDict


class RowBase(BaseModel):
    """
    Base para todos los schemas de fila Excel.
    Cada módulo hereda de esta clase y define sus propios campos.

    ConfigDict extra='forbid' asegura que columnas inesperadas
    en el Excel sean reportadas como error en vez de ignoradas.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,   # limpia espacios en strings automáticamente
        populate_by_name=True,
    )


class DocumentLineBase(RowBase):
    """
    Base para líneas de documentos (OC, Facturas, Notas de Venta, etc.)
    Los documentos con líneas heredan de acá.
    """
    pass
