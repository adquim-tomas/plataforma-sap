import logging
import unicodedata

from app.core.sap_client import SAPClient
from app.modules.shared.base_schema import BusinessError
from app.modules.articulos.datos_maestros.cambiar_familia.schema import CambiarFamiliaRow

logger = logging.getLogger(__name__)

# Catálogo de familias/subfamilias: tabla de usuario @LMM_FAM_META.
# En Service Layer una UDT se expone con prefijo 'U_' (igual que
# U_NX_LOCALIDADES, U_PJE_FLETE_FACT en el repo de referencia).
FAM_CATALOG_TABLE = "U_LMM_FAM_META"

# Columna que guarda la familia (= U_LMM_Familia del artículo).
# Confirmado contra U_LMM_FAM_META: la columna Name lista las familias
# (ADBLUE, COMBUSTIBLES, INSTALACIONES, …).
FAMILIA_COLUMN = "Name"

# Campo (UDF) que guarda la subfamilia (= U_LMM_FAMDET del artículo). En la
# ventana SAP la columna se titula "Familia Meta" y en Service Layer es
# U_LMM_FM (sus valores —OTROS, COMBUSTIBLES, …— coinciden con los que toma
# U_LMM_FAMDET en los artículos). `_detect_subfamilia_column` queda como red
# de seguridad por si el nombre cambiara.
SUBFAMILIA_COLUMN_DEFAULT = "U_LMM_FM"


def _norm(value: str | None) -> str:
    """
    Normaliza para comparar sin sensibilidad a mayúsculas, espacios ni acentos.
    El catálogo trae familias acentuadas (COSMÉTICA, JABÓN) y los operadores no
    siempre tipean la tilde — 'cosmetica' debe matchear 'COSMÉTICA'.
    """
    s = (value or "").strip().upper()
    # NFKD separa cada letra de su tilde; descartamos los diacríticos combinantes.
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


class FamiliaCatalog:
    """Catálogo de familias/subfamilias cargado una vez por batch."""

    def __init__(
        self,
        familias: dict[str, str],
        combos: dict[tuple[str, str], str],
    ) -> None:
        # familias: {familia_normalizada: valor_canónico_del_catálogo}
        self.familias = familias
        # combos: {(familia_norm, subfamilia_norm): subfamilia_canónica}
        self.combos = combos

    @property
    def loaded(self) -> bool:
        return bool(self.familias)

    def sample(self, n: int = 10) -> list[str]:
        return sorted(self.familias.values())[:n]

    def canon_familia(self, value: str | None) -> str | None:
        """Valor canónico del catálogo para una familia (o None si no está)."""
        return self.familias.get(_norm(value))

    def canon_subfamilia(self, familia: str | None, sub: str | None) -> str | None:
        """Valor canónico del catálogo para una subfamilia dada su familia."""
        return self.combos.get((_norm(familia), _norm(sub)))


class CambiarFamiliaValidator:
    """
    Valida familia/subfamilia contra el catálogo real (UDT U_LMM_FAM_META),
    no contra los artículos que ya las usan. Así las familias recién creadas
    se reconocen al instante y los valores inexistentes se rechazan (evita
    escribir familias fantasma en el UDF del artículo).

    El match es tolerante a mayúsculas/minúsculas y espacios: el catálogo está
    en MAYÚSCULAS y los operadores no siempre tipean igual.
    """

    @staticmethod
    def _detect_subfamilia_column(sample: dict) -> str | None:
        """Identifica el campo de subfamilia en una fila de la UDT."""
        if SUBFAMILIA_COLUMN_DEFAULT in sample:
            return SUBFAMILIA_COLUMN_DEFAULT
        # "Familia Meta" → campo U_LMM_FM; fallbacks por si el nombre cambiara.
        for token in ("_FM", "META", "FAMDET", "FAM"):
            for key in sample:
                if key.startswith("U_") and token in key.upper():
                    return key
        return None

    @staticmethod
    async def fetch_catalog(sap: SAPClient) -> FamiliaCatalog:
        """
        Lee la UDT completa UNA vez por batch.

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
            return FamiliaCatalog({}, {})

        subfam_col = CambiarFamiliaValidator._detect_subfamilia_column(rows[0])
        logger.info(
            "Catálogo familias %s: %d filas | columnas=%s | columna subfamilia=%s",
            FAM_CATALOG_TABLE, len(rows), list(rows[0].keys()), subfam_col,
        )

        familias: dict[str, str] = {}
        combos: dict[tuple[str, str], str] = {}
        for r in rows:
            fam_raw = (r.get(FAMILIA_COLUMN) or "").strip()
            if not fam_raw:
                continue
            familias[_norm(fam_raw)] = fam_raw
            if subfam_col:
                sub_raw = (r.get(subfam_col) or "").strip()
                if sub_raw:
                    combos[(_norm(fam_raw), _norm(sub_raw))] = sub_raw
        return FamiliaCatalog(familias, combos)

    @staticmethod
    def validate(
        row: CambiarFamiliaRow,
        catalog: FamiliaCatalog,
    ) -> list[BusinessError]:
        errors: list[BusinessError] = []

        # Si el catálogo no cargó, no podemos validar — dejamos pasar para que
        # SAP decida en el PATCH (y el warning del log delata el problema).
        if not catalog.loaded:
            return errors

        fam_norm = _norm(row.U_LMM_Familia)
        if row.U_LMM_Familia is not None and fam_norm != "":
            if fam_norm not in catalog.familias:
                ejemplos = ", ".join(catalog.sample())
                errors.append((
                    "U_LMM_Familia",
                    f"La familia '{row.U_LMM_Familia}' no existe en el catálogo "
                    f"de SAP ({len(catalog.familias)} familias, ej.: {ejemplos}…).",
                ))
                # Sin familia válida no tiene sentido chequear la combinación.
                return errors

        if (
            catalog.combos
            and row.U_LMM_Familia is not None
            and row.U_LMM_FAMDET is not None
            and _norm(row.U_LMM_FAMDET) != ""
        ):
            key = (fam_norm, _norm(row.U_LMM_FAMDET))
            if key not in catalog.combos:
                # Subfamilias válidas para esta familia, para guiar al operador.
                validas = sorted(
                    canon
                    for (f, _sub), canon in catalog.combos.items()
                    if f == fam_norm
                )
                hint = (
                    f" Válidas para '{row.U_LMM_Familia}': {', '.join(validas)}."
                    if validas else ""
                )
                errors.append((
                    "U_LMM_FAMDET",
                    f"La subfamilia '{row.U_LMM_FAMDET}' no está asociada a la "
                    f"familia '{row.U_LMM_Familia}' en el catálogo de SAP.{hint}",
                ))

        return errors
