import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from services.exchange_api import exchange_api_service
from trading.daemon import trading_daemon

# Настраиваем красивый вывод логов в консоль
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ==========================
    # СТАРТ ПРИЛОЖЕНИЯ
    # ==========================
    logging.info("Запуск системы Проект Трейд-Сервис...")

    # Запускаем нашего демона как фоновую асинхронную задачу
    daemon_task = asyncio.create_task(trading_daemon.run())

    yield  # Здесь FastAPI работает и слушает входящие запросы

    # ==========================
    # ОСТАНОВКА ПРИЛОЖЕНИЯ
    # ==========================
    logging.info("Получен сигнал на остановку. Завершение работы...")

    # 1. Останавливаем бесконечный цикл демона
    daemon_task.cancel()

    # 2. Корректно закрываем сессии к криптобирже, чтобы не было утечек памяти
    await exchange_api_service.close()

    logging.info("Все соединения успешно закрыты. До свидания!")


# Создаем само приложение
app = FastAPI(
    title="Trade Service API",
    description="SaaS платформа для алготрейдинга с ИИ",
    version="0.1.0",
    lifespan=lifespan
)


# Простейший эндпоинт для проверки статуса (Health Check)
@app.get("/api/v1/status")
async def get_status():
    return {
        "status": "online",
        "message": "Торговый демон успешно работает в фоне"
    }