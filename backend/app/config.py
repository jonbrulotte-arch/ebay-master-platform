from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://ebay_platform:ebay_platform@localhost:5432/ebay_platform"
    database_url_sync: str = "postgresql://ebay_platform:ebay_platform@localhost:5432/ebay_platform"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "change-me-to-a-random-secret-key"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    ebay_redirect_uri: str = "http://localhost:8000/api/v1/auth/ebay/callback"
    ebay_sandbox: bool = True

    aliexpress_app_key: str = ""
    aliexpress_app_secret: str = ""

    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "ebay-platform-images"
    s3_public_url: str = "http://localhost:9000/ebay-platform-images"

    fernet_key: str = ""

    cors_origins: list[str] = ["http://localhost:3000"]
    sentry_dsn: str = ""
    environment: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
