from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # SAP B1
    SAP_BASE_URL: str  # https://sapserver:50000/b1s/v1
    SAP_COMPANY_DB: str  # CLPRDADQUIM / CLTSTADQUIM
    # Validación del certificado TLS de SAP. False para on-prem con cert
    # autofirmado; True cuando SAP exponga un cert válido (producción cloud).
    SAP_VERIFY_SSL: bool = False

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
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # Rate limiting — máximo de requests por IP en ventana de 60s. 0 desactiva.
    RATE_LIMIT_PER_MINUTE: int = 120

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
