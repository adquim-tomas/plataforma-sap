from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # SAP B1
    SAP_BASE_URL: str  # https://sapserver:50000/b1s/v1
    SAP_COMPANY_DB: str  # CLPRDADQUIM / CLTSTADQUIM
    # Validación del certificado TLS de SAP. True por defecto (producción cloud).
    # On-prem con cert autofirmado: mantener True y apuntar SAP_CA_BUNDLE al
    # bundle CA; solo como último recurso usar False (expone a MITM).
    SAP_VERIFY_SSL: bool = True
    # Path al bundle CA para SAP on-prem con cert autofirmado (ej. "/certs/sap-ca.pem").
    # Vacío = usar el store del sistema operativo.
    SAP_CA_BUNDLE: str = ""

    # Service account — para operaciones de la plataforma
    SAP_SERVICE_USER: str
    SAP_SERVICE_PASSWORD: str


    # Base de datos
    DATABASE_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_EXPIRE_MINUTES: int

    # CORS — orígenes permitidos separados por coma (ej. "https://app.adquim.com,http://localhost:5173")
    ALLOWED_ORIGINS: str = "http://localhost:5173,https://blue-tree-01660d90f.7.azurestaticapps.net"

    # Rate limiting — máximo de requests por IP en ventana de 60s. 0 desactiva.
    RATE_LIMIT_PER_MINUTE: int = 120

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
