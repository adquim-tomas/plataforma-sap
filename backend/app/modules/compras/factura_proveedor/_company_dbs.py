# Catálogo de CompanyDBs por empresa del ecosistema H&Co.
#
# Convención de nombres SAP: `CL{ENV}{EMPRESA}` donde ENV ∈ {PRD, TST}.
# Las acciones de Factura de Proveedores (ENAP/Esmax/inter-empresa) son
# Adquim-only: Pedro las corre siempre desde una sesión de Adquim (TST en
# pruebas, PRD en producción). Adclean no tiene esta funcionalidad; Adgreen es
# el destino de inter-empresa, no el origen.
#
# Otros módulos (datos maestros, gestión de clientes, etc.) no tienen
# restricción — el operador trabaja desde la empresa donde inició sesión.

ADQUIM_DBS: tuple[str, ...] = ("CLPRDADQUIM", "CLTSTADQUIM")
ADCLEAN_DBS: tuple[str, ...] = ("CLPRD_ADCLEAN", "CLTST1ADCLEAN")
ADGREEN_DBS: tuple[str, ...] = ("CLPRDADGREEN", "CLTSTADGREEN")

ALL_COMPANY_DBS: tuple[str, ...] = ADQUIM_DBS + ADCLEAN_DBS + ADGREEN_DBS
