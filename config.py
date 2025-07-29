"""Configuration settings for the FastReader application.

This module centralizes environment-variable based configuration.

If an environment variable isn't provided, sensible defaults suitable
for local development are used. When running via Docker Compose, the
compose file will supply the appropriate values.
"""

import os


class Config:
    """Base configuration class."""

    # Secret key isn't needed for sessions since we don't provide auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-key")

    # File storage location; defaults to `uploads` under project root
    UPLOAD_FOLDER: str = os.getenv(
        "UPLOAD_FOLDER",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads"),
    )

    # Database connection string. When using Docker Compose this
    # environment variable will be set to something like:
    # postgresql://postgres:postgres@db:5432/fastreader
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fastreader"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False


def ensure_directories(cfg: Config) -> None:
    """Create necessary directories such as the upload folder.

    Args:
        cfg: The application configuration object.
    """

    os.makedirs(cfg.UPLOAD_FOLDER, exist_ok=True)