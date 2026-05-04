"""הגדרות האפליקציה - נטענות מ-environment variables"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-CHANGE-IN-PRODUCTION"
    DATABASE_URL: str = "sqlite:///./kidstrade.db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # שבוע
    ALGORITHM: str = "HS256"
    ENVIRONMENT: str = "development"

    # CORS - איזה דומיינים רשאים לפנות ל-API
    ALLOWED_ORIGINS: str = "*"  # ב-development. בפרודקשן - הדומיין של ה-frontend

    # Resend email
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev"

    # חוקי האפליקציה
    MIN_AGE: int = 13
    MAX_AGE: int = 18
    MAX_PRODUCT_PRICE: float = 500.0
    MAX_PRODUCT_IMAGES: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"  # מתעלם ממשתני סביבה לא ידועים

    def get_database_url(self) -> str:
        """
        Render נותנת DATABASE_URL בפורמט postgres://
        אבל SQLAlchemy החדש דורש postgresql://
        """
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


settings = Settings()
