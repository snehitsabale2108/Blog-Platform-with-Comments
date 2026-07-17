import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# Absolute path of the repo root (one level above app/)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))


def _make_sqlite_url(raw: str) -> str:
    """Ensure a sqlite:/// URL always uses an absolute file path.

    Alembic runs from an arbitrary cwd so relative SQLite paths like
    ``sqlite:///instance/dev.db`` fail.  We resolve them to absolute here.
    """
    if not raw.startswith("sqlite:///"):
        # postgres – rewrite scheme so SQLAlchemy uses psycopg3, not psycopg2
        if raw.startswith("postgres://"):
            return raw.replace("postgres://", "postgresql+psycopg://", 1)
        if raw.startswith("postgresql://"):
            return raw.replace("postgresql://", "postgresql+psycopg://", 1)
        return raw                     # mysql etc – leave untouched

    # Extract the file part after the three slashes
    file_part = raw[len("sqlite:///"):]

    # Already absolute (starts with / on Unix or a drive letter on Windows)
    if os.path.isabs(file_part):
        return raw

    # Relative – resolve from the repo root
    abs_path = os.path.abspath(os.path.join(ROOT_DIR, file_part))
    return "sqlite:///" + abs_path.replace("\\", "/")


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@inkwell.com")

    # File uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # Pagination
    POSTS_PER_PAGE = 12
    COMMENTS_PER_PAGE = 20

    # App metadata
    APP_NAME = "Inkwell"
    APP_URL = os.getenv("APP_URL", "http://localhost:5000")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # Default: absolute path to instance/dev.db in the repo root
    _default_db = "sqlite:///" + os.path.join(ROOT_DIR, "instance", "dev.db").replace("\\", "/")
    SQLALCHEMY_DATABASE_URI = _make_sqlite_url(
        os.getenv("DATABASE_URL", _default_db)
    )
    JWT_COOKIE_SECURE = False


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    JWT_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _make_sqlite_url(os.getenv("DATABASE_URL", ""))
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_CSRF_PROTECT = True


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
