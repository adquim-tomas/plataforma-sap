from pydantic import ConfigDict, Field

from app.modules.shared.base_schema import RowBase

# ── Acción: Bloqueo masivo por retiro de cobertura COFASE ────────────────────
#
# Equivalente a `SN.bloqueo_masivo_COFASE` / `update_many_bloqueo_cofase` en
# `classsocio.py:103` de Pedro. El operador solo entrega CardCode; el resto
# de los cambios (Valid, Frozen, U_tipo_linea, CreditLimit, MaxCommitment,
# FreeText apendado con fecha) se aplican server-side, sin parametrizar.


class BloqueoCofaseRow(RowBase):
    """
    Fila del Excel para Bloqueo COFASE.

    Única columna aceptada: CardCode. Cualquier otra es rechazada (extra="forbid").
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    CardCode: str = Field(..., description="CN+RUT clientes, PN+RUT proveedores")
