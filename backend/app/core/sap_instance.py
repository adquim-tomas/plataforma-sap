# app/core/sap_instance.py
import asyncio
import logging

from app.core.config import settings
from app.core.sap_client import SAPClient

logger = logging.getLogger(__name__)

# Pool de SAPClients del service account, uno por CompanyDB. Cada operador
# elige su CompanyDB al login (`user.company_db`) y los uploads usan el
# cliente del pool correspondiente — así un operador que entra a PROD no
# trabaja contra TEST por accidente (problema previo: existía una sola sesión
# fija a `settings.SAP_COMPANY_DB`).
#
# Cada cliente mantiene su propia sesión y se relogea solo cuando expira; el
# pool se cierra en el shutdown de la app.
_clients: dict[str, SAPClient] = {}
_lock = asyncio.Lock()


async def get_sap_client(company_db: str) -> SAPClient:
    """
    Devuelve (creando si hace falta) el SAPClient del service account contra
    `company_db`. Cachea por CompanyDB para que sesiones concurrentes no
    abran logins redundantes.
    """
    async with _lock:
        client = _clients.get(company_db)
        if client is not None:
            return client
        client = SAPClient()
        await client.login(
            company_db,
            settings.SAP_SERVICE_USER,
            settings.SAP_SERVICE_PASSWORD,
        )
        _clients[company_db] = client
        logger.info("SAP service client warmed for CompanyDB=%s", company_db)
        return client


async def get_default_sap_client() -> SAPClient:
    """Atajo: cliente de la CompanyDB default (`settings.SAP_COMPANY_DB`). Lo
    usa `/health/sap` y el lifespan al arrancar."""
    return await get_sap_client(settings.SAP_COMPANY_DB)


async def close_all() -> None:
    """Cierra todos los clientes del pool — para el shutdown del app."""
    async with _lock:
        for company_db, client in list(_clients.items()):
            try:
                await client.logout()
            except Exception as exc:  # noqa: BLE001 — shutdown best-effort
                logger.warning("logout de SAP para %s falló: %s", company_db, exc)
        _clients.clear()


# DEPRECATED alias: el código nuevo debe usar `get_sap_client(user.company_db)`.
# Se mantiene mientras quede algún consumidor del singleton; cuando todos los
# call sites migren, removerlo. Health y lifespan usan get_default_sap_client.
async def _default_for_legacy() -> SAPClient:
    return await get_default_sap_client()
