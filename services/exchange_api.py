import aiohttp
import logging
import socket
import asyncio
from typing import List, Any

logger = logging.getLogger(__name__)


class ExchangeService:
    def __init__(self):
        # Базовый URL публичного API Dzengi.com
        self.base_url = "https://api-adapter.dzengi.com/api/v1"
        self.session = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            from aiohttp.resolver import ThreadedResolver
            connector = aiohttp.TCPConnector(
                resolver=ThreadedResolver(),
                family=socket.AF_INET,
                use_dns_cache=False
            )
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session

    async def fetch_candles(self, symbol: str, timeframe: str, limit: int = 100) -> List[List[Any]]:
        """
        Запрашивает текущие свечи (OHLCV).
        """
        session = await self._get_session()
        endpoint = f"{self.base_url}/klines"

        params = {
            "symbol": symbol,
            "interval": timeframe,
            "limit": limit
        }

        try:
            async with session.get(endpoint, params=params) as response:
                # ВЫВОДИМ ПОЛНЫЙ СФОРМИРОВАННЫЙ URL ЗАПРОСА
                logger.info(f"🔗 Ссылка отправленного запроса: {response.url}")

                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Ошибка API Dzengi HTTP {response.status}: {text}")
                    return []

                data = await response.json()

                # ВЫВОДИМ ПРЕВЬЮ ПОЛУЧЕННОГО ОТВЕТА (первые 2 свечи, чтобы не спамить консоль)
                logger.info(f"📥 Получен ответ от сервера. Всего свечей: {len(data)}. Превью данных: {data[:2]}")

                ohlcv = []
                for candle in data:
                    ohlcv.append([
                        int(candle[0]), float(candle[1]), float(candle[2]),
                        float(candle[3]), float(candle[4]), float(candle[5])
                    ])
                return ohlcv

        except Exception as e:
            logger.error(f"Сетевая ошибка при получении свечей {symbol}: {e}")
            return []

    async def fetch_historical_candles(self, symbol: str, timeframe: str, start_time: int, end_time: int) -> list:
        """
        Скачивает исторические свечи кусками для бэктеста.
        """
        session = await self._get_session()
        endpoint = f"{self.base_url}/klines"
        all_candles = []
        current_start = start_time

        while current_start < end_time:
            params = {
                "symbol": symbol,
                "interval": timeframe,
                "limit": 1000,
                "startTime": current_start,
                "endTime": end_time
            }
            try:
                async with session.get(endpoint, params=params) as response:
                    # ВЫВОДИМ ПОЛНЫЙ URL ДЛЯ КАЖДОЙ СТРАНИЦЫ ИСТОРИИ
                    logger.info(f"🔗 Ссылка исторического запроса: {response.url}")

                    if response.status != 200:
                        text = await response.text()
                        logger.error(f"Ошибка пагинации HTTP {response.status}: {text}")
                        break

                    data = await response.json()
                    if not data:
                        break

                    # Выводим превью пакета данных
                    logger.info(f"📥 Скачан пакет истории. Получено свечей: {len(data)}")

                    for candle in data:
                        all_candles.append([
                            int(candle[0]), float(candle[1]), float(candle[2]),
                            float(candle[3]), float(candle[4]), float(candle[5])
                        ])

                    last_candle_time = int(data[-1][0])
                    current_start = last_candle_time + 1
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Ошибка пагинации исторических свечей: {e}")
                break

        return all_candles

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()


exchange_api_service = ExchangeService()