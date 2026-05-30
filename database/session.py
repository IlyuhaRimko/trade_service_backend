from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import settings

# 1. Создаем асинхронный движок
engine = create_async_engine(
    settings.async_database_url,
    echo=False, # Поставь True, если захочешь видеть все SQL-запросы в консоли
    future=True
)

# 2. Создаем фабрику сессий (через нее мы будем делать запросы к БД)
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 3. Dependency (Зависимость) для FastAPI
# Эта функция будет выдавать новую сессию для каждого запроса и закрывать ее после
async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()