import ccxt.async_support as ccxt
import logging
from typing import List, Any

# Настраиваем базовое логирование, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExchangeService:
    def __init__(self, exchange_id: str = 'currencycom'):
        """
        Инициализация подключения к криптобирже.
        По умолчанию используем currencycom (Dzengi.com).
        """
        try:
            # Динамически получаем класс биржи из CCXT
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'enableRateLimit': True,  # Включаем встроенную защиту от бана по IP (Rate Limit)
            })
            logger.info(f"Успешно инициализирован коннектор для биржи: {exchange_id}")
        except AttributeError:
            logger.error(f"Биржа {exchange_id} не найдена в библиотеке CCXT.")
            raise

    async def fetch_candles(self, symbol: str, timeframe: str, limit: int = 100) -> List[List[Any]]:
        """
        Запрашивает исторические свечи (OHLCV) для конкретной монеты.
        Формат ответа CCXT: [ [timestamp, open, high, low, close, volume], ... ]
        """
        try:
            # Асинхронный запрос к API биржи
            candles = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return candles
        except ccxt.NetworkError as e:
            logger.error(f"Ошибка сети при получении свечей {symbol}: {e}")
            raise
        except ccxt.ExchangeError as e:
            logger.error(f"Ошибка API биржи для {symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"Непредвиденная ошибка: {e}")
            raise

    async def close(self):
        """
        Асинхронные сессии в CCXT необходимо закрывать вручную,
        чтобы не возникало утечек памяти.
        """
        await self.exchange.close()

# Создаем глобальный объект сервиса для импорта в другие модули
exchange_api_service = ExchangeService()