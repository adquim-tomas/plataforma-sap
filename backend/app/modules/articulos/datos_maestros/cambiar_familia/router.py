from app.core.sap_client import SAPClient
from app.modules.shared.base_router import BaseUploadHandler
from app.modules.shared.base_schema import BusinessError
from app.modules.articulos.datos_maestros.cambiar_familia.sap_service import (
    CambiarFamiliaSAPService,
)
from app.modules.articulos.datos_maestros.cambiar_familia.schema import (
    CambiarFamiliaRow,
)
from app.modules.articulos.datos_maestros.cambiar_familia.validator import (
    CambiarFamiliaValidator,
)


class CambiarFamiliaHandler(BaseUploadHandler[CambiarFamiliaRow]):
    """
    pre_validate_batch: lee UNA vez el catálogo de familias (UDT
    U_LMM_FAM_META) y construye los sets de familias y combinaciones
    familia→subfamilia válidas. La validación por fila los consulta en memoria.

    La familia/subfamilia se valida contra el catálogo real (no contra los
    artículos que ya las usan), así una familia recién creada se reconoce de
    inmediato y un valor inexistente se rechaza — evita escribir familias
    fantasma en el UDF del artículo.

    La existencia del ItemCode la valida SAP en el PATCH (un 404 se reporta
    como error de fila); no se pre-carga la tabla Items completa.
    """

    def __init__(self) -> None:
        self._valid_familias: set[str] = set()
        self._valid_combos: set[tuple[str, str]] = set()

    @property
    def schema_class(self) -> type[CambiarFamiliaRow]:
        return CambiarFamiliaRow

    @property
    def sap_module(self) -> str:
        return "articulos/items/cambiar_familia"

    async def pre_validate_batch(self, sap: SAPClient) -> None:
        self._valid_familias, self._valid_combos = (
            await CambiarFamiliaValidator.fetch_catalog(sap)
        )

    async def validate(
        self, sap: SAPClient, row: CambiarFamiliaRow
    ) -> list[BusinessError]:
        return CambiarFamiliaValidator.validate(
            row, self._valid_familias, self._valid_combos
        )

    async def apply_sap(self, sap: SAPClient, row: CambiarFamiliaRow) -> None:
        await CambiarFamiliaSAPService.update(sap, row)

    def audit_resource_id(self, row: CambiarFamiliaRow) -> str:
        return row.ItemCode

    def build_after(self, row: CambiarFamiliaRow) -> dict:
        after: dict = {}
        if row.U_LMM_Familia is not None:
            after["U_LMM_Familia"] = row.U_LMM_Familia
        if row.U_LMM_FAMDET is not None:
            after["U_LMM_FAMDET"] = row.U_LMM_FAMDET
        return after
