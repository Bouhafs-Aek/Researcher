from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./researcher.db"
    openalex_mailto: str | None = None
    crossref_mailto: str | None = None
    app_env: str = "development"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
