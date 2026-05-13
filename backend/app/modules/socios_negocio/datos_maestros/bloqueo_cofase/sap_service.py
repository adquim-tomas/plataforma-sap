from datetime import date

from app.core.sap_client import SAPClient
from app.modules.socios_negocio.datos_maestros.bloqueo_cofase.schema import (
    BloqueoCofaseRow,
)

# Valores fijos del bloqueo — el operador no los decide.
_TIPO_LINEA_BLOQUEADO = "Sin línea"
_CREDIT_LIMIT_BLOQUEADO = 0
_MAX_COMMITMENT_BLOQUEADO = 0
_COMMENT_SUFIJO = "COBERTURA RETIRADA"


class BloqueoCofaseSAPService:
    """
    Bloqueo masivo por retiro de cobertura COFASE.

    Patrón Pedro (`bloqueo_masivo_COFASE`):
      1. GET el FreeText actual del BP.
      2. Appendear "\\r{DD-MM-YYYY} COBERTURA RETIRADA" al comentario existente
         (o usarlo solo si no había comentario).
      3. PATCH con Valid=tNO, Frozen=tYES, U_tipo_linea="Sin línea",
         CreditLimit=0, MaxCommitment=0, FreeText con la línea apendada.
    """

    @staticmethod
    async def update(sap: SAPClient, row: BloqueoCofaseRow) -> None:
        # 1. GET FreeText actual.
        bp_data = await sap.get(
            f"BusinessPartners('{row.CardCode}')",
            params={"$select": "FreeText"},
        )
        current_comment: str | None = bp_data.get("FreeText")

        # 2. Construir el comentario nuevo. Pedro usa formato DD-MM-YYYY y
        #    prefija con \r para que SAP lo muestre en línea aparte.
        today = date.today().strftime("%d-%m-%Y")
        new_line = f"\r{today} {_COMMENT_SUFIJO}"
        new_comment = (current_comment or "") + new_line

        # 3. PATCH con todos los campos del bloqueo.
        payload = {
            "Valid":          "tNO",
            "Frozen":         "tYES",
            "U_tipo_linea":   _TIPO_LINEA_BLOQUEADO,
            "CreditLimit":    _CREDIT_LIMIT_BLOQUEADO,
            "MaxCommitment":  _MAX_COMMITMENT_BLOQUEADO,
            "FreeText":       new_comment,
        }
        await sap.patch(f"BusinessPartners('{row.CardCode}')", payload)
