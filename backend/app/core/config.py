from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # SAP B1
    SAP_BASE_URL: str  # https://sapserver:50000/b1s/v1
    SAP_COMPANY_DB: str  # CLPRDADQUIM / CLTSTADQUIM

    # Service account — para operaciones de la plataforma
    SAP_SERVICE_USER: str
    SAP_SERVICE_PASSWORD: str

    # Base de datos
    DATABASE_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_EXPIRE_MINUTES: int


settings = Settings()
