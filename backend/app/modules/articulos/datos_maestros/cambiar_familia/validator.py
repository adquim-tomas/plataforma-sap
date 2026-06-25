import logging

from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import BusinessError
from app.modules.articulos.datos_maestros.cambiar_familia.schema import CambiarFamiliaRow

logger = logging.getLogger(__name__)

# Catálogo de familias/subfamilias: tabla de usuario @LMM_FAM_META.
# En Service Layer una UDT se expone con prefijo 'U_' (igual que
# U_NX_LOCALIDADES, U_PJE_FLETE_FACT en el repo de referencia).
FAM_CATALOG_TABLE = "U_LMM_FAM_META"

# Columna que guarda la familia (= U_LMM_Familia del artículo).
FAMILIA_COLUMN = "Name"

# Campo (UDF) que guarda la subfamilia (= U_LMM_FAMDET del artículo). En la
# ventana SAP la columna se titula "Familia Meta". Si el nombre real del campo
# en Service Layer difiere, `_detect_subfamilia_column` lo resuelve buscando
# entre los campos U_ presentes.
SUBFAMILIA_COLUMN_DEFAULT = "U_FAM_META"


class CambiarFamiliaValidator:
    """
    Valida familia/subfamilia contra el catálogo real (UDT U_LMM_FAM_META),
    no contra los artículos que ya las usan. Así las familias recién creadas
    se reconocen al instante y los valores inexistentes se rechazan (evita
    escribir familias fantasma en el UDF del artículo).
    """

    @staticmethod
    def _detect_subfamilia_column(sample: dict) -> str | None:
        """Identifica el campo de subfamilia en una fila de la UDT."""
        if SUBFAMILIA_COLUMN_DEFAULT in sample:
            return SUBFAMILIA_COLUMN_DEFAULT
        # "Familia Meta" → el campo suele contener META; si no, FAM.
        for token in ("META", "FAMDET", "FAM"):
            for key in sample:
                if key.startswith("U_") and token in key.upper():
                    return key
        return None

    @staticmethod
    async def fetch_catalog(
        sap: SAPClient,
    ) -> tuple[set[str], set[tuple[str, str]]]:
        """
        Lee la UDT completa UNA vez por batch y devuelve:
          - familias: set de valores válidos de familia (columna Name)
          - combos:   set de (familia, subfamilia) válidos

        Loguea las columnas reales de la tabla y la columna de subfamilia
        detectada, para confirmar el mapeo sin adivinar a ciegas.
        """
        rows = await sap.get_all(FAM_CATALOG_TABLE)
        if not rows:
            logger.warning(
                "Catálogo de familias %s vacío o inaccesible — "
                "no se podrá validar familias contra el catálogo.",
                FAM_CATALOG_TABLE,
            )
            return set(), set()

        subfam_col = CambiarFamiliaValidator._detect_subfamilia_column(rows[0])
        logger.info(
            "Catálogo familias %s: %d filas | columnas=%s | columna subfamilia=%s",
            FAM_CATALOG_TABLE, len(rows), list(rows[0].keys()), subfam_col,
        )

        familias: set[str] = set()
        combos: set[tuple[str, str]] = set()
        for r in rows:
            fam = (r.get(FAMILIA_COLUMN) or "").strip()
            if not fam:
                continue
            familias.add(fam)
            if subfam_col:
                sub = (r.get(subfam_col) or "").strip()
                if sub:
                    combos.add((fam, sub))
        return familias, combos

    @staticmethod
    def validate(
        row: CambiarFamiliaRow,
        valid_familias: set[str],
        valid_combos: set[tuple[str, str]],
    ) -> list[BusinessError]:
        errors: list[BusinessError] = []

        if row.U_LMM_Familia is not None and row.U_LMM_Familia != "":
            if row.U_LMM_Familia not in valid_familias:
                errors.append((
                    "U_LMM_Familia",
                    f"La familia '{row.U_LMM_Familia}' no existe en el catálogo "
                    "de familias de SAP.",
                ))
                # Sin familia válida no tiene sentido chequear la combinación.
                return errors

        # Validar la combinación solo si tenemos catálogo de subfamilias
        # (`valid_combos` vacío = no se pudo detectar la columna; se omite el
        # chequeo en vez de rechazar todo).
        if (
            valid_combos
            and row.U_LMM_Familia is not None
            and row.U_LMM_FAMDET is not None
            and row.U_LMM_FAMDET != ""
        ):
            if (row.U_LMM_Familia, row.U_LMM_FAMDET) not in valid_combos:
                errors.append((
                    "U_LMM_FAMDET",
                    f"La subfamilia '{row.U_LMM_FAMDET}' no está asociada a la "
                    f"familia '{row.U_LMM_Familia}' en el catálogo de SAP.",
                ))

        return errors
