# app/core/sap_instance.py
from app.core.config import settings
from app.core.sap_client import SAPClient

# Singleton del service account — se inicializa en el lifespan de main.py
sap_service = SAPClient()


async def login_company_client(company_db: str) -> SAPClient:
    """
    Crea y autentica un `SAPClient` transitorio contra una CompanyDB puntual,
    usando el mismo service account. Lo usa la carga inter-empresa, que necesita
    dos sesiones simultáneas (Adquim origen + Adgreen destino) — algo que el
    singleton de una sola empresa no cubre. El caller es responsable de cerrarlo
    (`await client.logout()` / `await client.__aexit__(...)`).
    """
    client = SAPClient()
    await client.login(
        company_db,
        settings.SAP_SERVICE_USER,
        settings.SAP_SERVICE_PASSWORD,
    )
    return client