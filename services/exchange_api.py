import aiohttp
import logging
import socket
from typing import List, Any

logger = logging.getLogger(__name__)


class ExchangeService:
    def __init__(self):
        self.base_url = "https://api-adapter.dzengi.com/api/v1"
        self.session = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            # Принудительно заставляем aiohttp использовать системный DNS Windows,
            # игнорируя мертвые VPN-адаптеры
            from aiohttp.resolver import ThreadedResolver

            connector = aiohttp.TCPConnector(
                resolver=ThreadedResolver(),  # Системный резолвер
                family=socket.AF_INET,  # Только IPv4
                use_dns_cache=False  # Никакого кэша
            )
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session

    async def fetch_candles(self, symbol: str, timeframe: str, limit: int = 100) -> List[List[Any]]:
        """
        Запрашивает исторические свечи (OHLCV) напрямую через REST API Dzengi.
        """
        session = await self._get_session()
        endpoint = f"{self.base_url}/klines"

        # Формируем параметры запроса по документации Dzengi
        params = {
            "symbol": symbol,
            "interval": timeframe,
            "limit": limit
        }

        try:
            async with session.get(endpoint, params=params) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Ошибка API Dzengi HTTP {response.status}: {text}")
                    return []

                data = await response.json()

                # Структура ответа API Dzengi (как у Binance):
                # [ [Open time, Open, High, Low, Close, Volume, ...] ]
                ohlcv = []
                for candle in data:
                    ohlcv.append([
                        int(candle[0]),  # timestamp (ms)
                        float(candle[1]),  # open
                        float(candle[2]),  # high
                        float(candle[3]),  # low
                        float(candle[4]),  # close
                        float(candle[5])  # volume
                    ])
                return ohlcv

        except Exception as e:
            logger.error(f"Сетевая ошибка при получении свечей {symbol}: {e}")
            return []

    async def close(self):
        """Корректное закрытие HTTP-сессии при остановке демона."""
        if self.session and not self.session.closed:
            await self.session.close()


# Создаем глобальный объект сервиса для импорта
exchange_api_service = ExchangeService()