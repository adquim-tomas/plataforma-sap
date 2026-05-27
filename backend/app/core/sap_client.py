import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


# ── Excepciones tipadas ──────────────────────────────────────────────────────

class SAPError(Exception):
    """Base para todos los errores del cliente SAP."""
    pass

class SAPAuthError(SAPError):
    """Credenciales inválidas o sesión no iniciada."""
    def __init__(self, message: str = "", status_code: int | None = None):
        # status_code permite al caller sugerir el HTTP status final
        # (ej: 401 desde /auth/login en vez del 502 default).
        self.status_code = status_code
        super().__init__(message)

class SAPNotFoundError(SAPError):
    """El recurso solicitado no existe en SAP."""
    pass

class SAPValidationError(SAPError):
    """SAP rechazó el payload (400). Contiene el mensaje de SAP."""
    def __init__(self, message: str, sap_code: int | None = None):
        self.sap_code = sap_code
        super().__init__(message)

class SAPConnectionError(SAPError):
    """No se pudo conectar al servidor SAP."""
    pass


# ── Modelo de sesión ─────────────────────────────────────────────────────────

class _SAPSession(BaseModel):
    session_id: str
    b1session: str
    routeid: str
    expires_at: datetime  # login_time + (SessionTimeout - 2 min de margen)

    @property
    def is_valid(self) -> bool:
        return datetime.now() < self.expires_at


# ── Cliente principal ────────────────────────────────────────────────────────

class SAPClient:
    """
    Cliente async para SAP B1 Service Layer.

    Maneja sesión automáticamente — no es necesario pasar cookie/node
    en ninguna llamada. Se autentica al primer uso y renueva la sesión
    cuando está por expirar.

    Uso básico:
        sap = SAPClient()
        await sap.login("CLPRDADQUIM", "user", "pass")

        ### GET con paginación automática
        items = await sap.get_all("Items")

        ### POST
        result = await sap.post("PurchaseOrders", payload)

        ### PATCH
        await sap.patch("BusinessPartners('C001')", payload)

        ### DELETE
        await sap.delete("U_NX_LOCALIDADES(5)")
    """

    BASE_URL = settings.SAP_BASE_URL  # https://host:50000/b1s/v1/
    PAGE_SIZE = 200                    # máximo que acepta el server
    SESSION_MARGIN = timedelta(minutes=2)

    def __init__(self) -> None:
        self._session: _SAPSession | None = None
        self._credentials: dict[str, str] = {}
        self._lock = asyncio.Lock()  # evita race condition en relogin
        self._http = httpx.AsyncClient(
            # On-prem con cert autofirmado → SAP_VERIFY_SSL=False; cert válido → True
            verify=settings.SAP_VERIFY_SSL,
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

    # ── Auth ─────────────────────────────────────────────────────────────────

    async def login(self, company_db: str, username: str, password: str) -> None:
        """
        Inicia sesión en SAP B1. Guarda credenciales para relogin automático.
        Equivalente al classCredential.logIn() actual, pero guarda estado interno.
        """
        self._credentials = {
            "CompanyDB": company_db,
            "UserName": username,
            "Password": password,
        }
        await self._do_login()

    async def logout(self) -> None:
        """Cierra la sesión activa en SAP."""
        if not self._session:
            return
        try:
            await self._http.post(
                f"{self.BASE_URL}/Logout",
                headers=self._auth_headers(),
            )
        except Exception:
            pass  # si falla el logout no es crítico
        finally:
            self._session = None
            self._credentials = {}
            logger.info("SAP session closed")

    async def _do_login(self) -> None:
        """Ejecuta el POST /Login y construye el objeto de sesión."""
        if not self._credentials:
            raise SAPAuthError("No credentials set. Call login() first.")
        try:
            response = await self._http.post(
                f"{self.BASE_URL}/Login",
                json=self._credentials,
            )
        except httpx.TransportError as e:
            # Cubre ConnectError, ConnectTimeout, ReadTimeout, PoolTimeout, etc.
            # Un SL que conecta a nivel TCP pero no responde al /Login no debe
            # colgar el caller (lifespan, health, upload): lo traducimos a un
            # error de dominio tipado.
            raise SAPConnectionError(f"Cannot reach SAP server: {e}") from e

        if response.status_code == 401:
            raise SAPAuthError("Invalid SAP credentials.")
        _raise_for_status(response)

        data = response.json()
        timeout_minutes = int(data.get("SessionTimeout", 30))

        self._session = _SAPSession(
            session_id=data["SessionId"],
            b1session=response.cookies["B1SESSION"],
            routeid=response.cookies["ROUTEID"],
            expires_at=datetime.now() + timedelta(minutes=timeout_minutes) - self.SESSION_MARGIN,
        )
        logger.info(f"SAP session started — expires at {self._session.expires_at}")

    async def _ensure_session(self) -> None:
        """
        Verifica que la sesión esté activa. Si expiró, hace relogin.
        Usa un lock para que requests concurrentes no hagan N relogins.
        """
        async with self._lock:
            if self._session is None or not self._session.is_valid:
                logger.info("SAP session expired or missing — re-authenticating")
                await self._do_login()

    def _auth_headers(self) -> dict[str, str]:
        """Construye el header Cookie que espera SAP."""
        if not self._session:
            raise SAPAuthError("No active session.")
        return {
            "Cookie": f"B1SESSION={self._session.b1session}; ROUTEID={self._session.routeid}",
            "Prefer": f"odata.maxpagesize={self.PAGE_SIZE}",
            "Content-Type": "application/json",
        }

    # ── Operaciones CRUD ─────────────────────────────────────────────────────

    async def get(self, resource: str, params: dict | None = None) -> dict[str, Any]:
        """
        GET /b1s/v1/{resource}
        Para un único recurso (e.g. "Items('A001')").
        """
        await self._ensure_session()
        response = await self._http.get(
            f"{self.BASE_URL}/{resource}",
            headers=self._auth_headers(),
            params=params,
        )
        if response.status_code == 404:
            raise SAPNotFoundError(f"Resource not found: {resource}")
        _raise_for_status(response)
        return response.json()

    async def get_all(
        self,
        resource: str,
        filters: str | None = None,
        select: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        GET con paginación automática. Recorre todos los odata.nextLink
        hasta agotar los resultados.

        Equivalente al patrón while next_link repetido en todos los archivos actuales.

        Args:
            resource: entidad SAP (e.g. "BusinessPartners", "Items")
            filters:  string OData $filter (e.g. "CardType eq 'cCustomer'")
            select:   lista de campos a traer (e.g. ["CardCode", "CardName"])
        """
        await self._ensure_session()

        params: dict[str, str] = {}
        if filters:
            params["$filter"] = filters
        if select:
            params["$select"] = ",".join(select)

        results: list[dict[str, Any]] = []
        url: str | None = f"{self.BASE_URL}/{resource}"

        while url:
            response = await self._http.get(
                url,
                headers=self._auth_headers(),
                params=params if url == f"{self.BASE_URL}/{resource}" else None,
            )
            _raise_for_status(response)
            data = response.json()

            results.extend(data.get("value", []))
            url = data.get("odata.nextLink")  # None si no hay más páginas

        logger.debug(f"get_all({resource}) → {len(results)} records")
        return results

    async def post(self, resource: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        POST /b1s/v1/{resource} — crea un nuevo documento en SAP.
        Equivalente a add_data.add_json() actual.
        """
        await self._ensure_session()
        response = await self._http.post(
            f"{self.BASE_URL}/{resource}",
            headers=self._auth_headers(),
            json=payload,
        )
        _raise_for_status(response)
        return response.json() if response.content else {}

    async def patch(self, resource: str, payload: dict[str, Any]) -> None:
        """
        PATCH /b1s/v1/{resource} — actualiza un documento existente.
        Equivalente a load_data.load_json() actual.
        SAP devuelve 204 No Content en éxito.
        """
        await self._ensure_session()
        response = await self._http.patch(
            f"{self.BASE_URL}/{resource}",
            headers=self._auth_headers(),
            json=payload,
        )
        _raise_for_status(response)

    async def delete(self, resource: str) -> None:
        """
        DELETE /b1s/v1/{resource}
        Equivalente a delete_data.delete_row() actual.
        """
        await self._ensure_session()
        response = await self._http.delete(
            f"{self.BASE_URL}/{resource}",
            headers=self._auth_headers(),
        )
        if response.status_code == 404:
            raise SAPNotFoundError(f"Resource not found: {resource}")
        _raise_for_status(response)

    # ── Context manager ────────────────────────────────────────────────────────

    async def __aenter__(self) -> "SAPClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.logout()
        await self._http.aclose()


# ── Helper privado ─────────────────────────────────────────────────────────────

def _raise_for_status(response: httpx.Response) -> None:
    """
    Traduce códigos de error HTTP a excepciones tipadas del dominio.
    SAP B1 devuelve detalles del error en response.json()["error"]["message"].
    """
    if response.status_code < 400:
        return

    message = _extract_sap_message(response)
    code = response.status_code

    if code == 401:
        raise SAPAuthError(message)
    if code == 404:
        raise SAPNotFoundError(message)
    if code in (400, 422):
        raise SAPValidationError(message, sap_code=code)
    raise SAPError(f"SAP error {code}: {message}")


def _extract_sap_message(response: httpx.Response) -> str:
    """Extrae el mensaje legible del JSON de error de SAP B1."""
    try:
        return response.json()["error"]["message"]["value"]
    except Exception:
        return response.text or f"HTTP {response.status_code}"
