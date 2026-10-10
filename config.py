import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Session Security Settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # XAMPP MySQL database settings
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "queueless_db")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))

    @property
    def DATABASE_URI(self):
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
