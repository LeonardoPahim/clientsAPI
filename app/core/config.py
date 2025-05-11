from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    PROJECT_NAME: str = "Favorite Products API"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/db"
    FAKESTOREAPI_URL: str = "https://fakestoreapi.com"

    SECRET_KEY: str = "placeholder_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    MASTER_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    MASTER_USERNAME: str = "admin"
    MASTER_PASSWORD_HASH: str = "placeholder_hash"

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"

settings = Settings()