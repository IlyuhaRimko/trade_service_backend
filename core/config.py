from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Указываем переменные, которые Pydantic должен найти в .env
    DATABASE_URL: str

    # В будущем добавим сюда API-ключи:
    GEMINI_API_KEY: str
    # CRYPTOPANIC_API_KEY: str

    @property
    def async_database_url(self) -> str:
        # FastAPI требует асинхронного подключения (asyncpg).
        # Этот метод автоматически меняет 'postgresql://' на 'postgresql+asyncpg://'
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

    # Указываем, откуда брать настройки
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Создаем глобальный объект настроек
settings = Settings()