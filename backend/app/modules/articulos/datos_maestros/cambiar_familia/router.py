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
    FamiliaCatalog,
)

# Catálogo de familias cacheado POR CompanyDB. El handler es un singleton
# compartido por todas las requests/empresas; guardar el catálogo en `self`
# permitiría que un operador de otra empresa lo pisara (validar contra la base
# equivocada). Keyear por company_db aísla cada empresa. Se refresca en cada
# batch (`pre_validate_batch`), así una familia recién creada se reconoce ya.
_CATALOGS: dict[str, FamiliaCatalog] = {}
_EMPTY_CATALOG = FamiliaCatalog({}, {})


class CambiarFamiliaHandler(BaseUploadHandler[CambiarFamiliaRow]):
    """
    pre_validate_batch: lee UNA vez por batch el catálogo de familias (UDT
    U_LMM_FAM_META) de la CompanyDB del operador y lo cachea por empresa. La
    validación por fila lo consulta en memoria.

    La familia/subfamilia se valida contra el catálogo real (no contra los
    artículos que ya las usan), así una familia recién creada se reconoce de
    inmediato y un valor inexistente se rechaza — evita escribir familias
    fantasma en el UDF del artículo.

    La existencia del ItemCode la valida SAP en el PATCH (un 404 se reporta
    como error de fila); no se pre-carga la tabla Items completa.
    """

    @property
    def schema_class(self) -> type[CambiarFamiliaRow]:
        return CambiarFamiliaRow

    @property
    def sap_module(self) -> str:
        return "articulos/items/cambiar_familia"

    @staticmethod
    def _catalog_for(sap: SAPClient) -> FamiliaCatalog:
        return _CATALOGS.get(sap.company_db or "", _EMPTY_CATALOG)

    async def pre_validate_batch(self, sap: SAPClient) -> None:
        # Asignación a la clave de la empresa: atómica en el event loop, sin
        # await intermedio → sin condición de carrera entre empresas.
        _CATALOGS[sap.company_db or ""] = (
            await CambiarFamiliaValidator.fetch_catalog(sap)
        )

    async def validate(
        self, sap: SAPClient, row: CambiarFamiliaRow
    ) -> list[BusinessError]:
        return CambiarFamiliaValidator.validate(row, self._catalog_for(sap))

    async def apply_sap(self, sap: SAPClient, row: CambiarFamiliaRow) -> None:
        # Escribir el valor canónico del catálogo (no el casing crudo del Excel)
        # para no introducir variantes de mayúsculas en el UDF del artículo.
        catalog = self._catalog_for(sap)
        if catalog.loaded:
            canon_fam = catalog.canon_familia(row.U_LMM_Familia)
            if canon_fam is not None:
                row.U_LMM_Familia = canon_fam
            canon_sub = catalog.canon_subfamilia(
                row.U_LMM_Familia, row.U_LMM_FAMDET
            )
            if canon_sub is not None:
                row.U_LMM_FAMDET = canon_sub
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
