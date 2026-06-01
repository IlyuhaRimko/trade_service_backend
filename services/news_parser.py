import aiohttp
import logging
import socket
from aiohttp.resolver import ThreadedResolver

logger = logging.getLogger(__name__)

class NewsParser:
    def __init__(self):
        self.base_url = "https://min-api.cryptocompare.com/data/v2/news/"

    def _get_connector(self):
        # Тот самый системный DNS-резолвер для обхода фантомных VPN
        return aiohttp.TCPConnector(
            resolver=ThreadedResolver(),
            family=socket.AF_INET,
            use_dns_cache=False
        )

    async def fetch_recent_news(self, symbol: str, limit: int = 10) -> str:
        coin = symbol.split('/')[0] if '/' in symbol else symbol
        params = {"lang": "EN", "categories": coin, "sortOrder": "latest"}
        try:
            async with aiohttp.ClientSession(connector=self._get_connector()) as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        return "Новостной фон временно недоступен."
                    data = await response.json()
                    results = data.get("Data", [])[:limit]
                    if not results:
                        return f"Нет свежих новостей по монете {coin}."
                    news_lines = [f"- {item.get('title')} ({item.get('source_info', {}).get('name', 'Unknown')})" for item in results]
                    return "\n".join(news_lines)
        except Exception as e:
            logger.error(f"Ошибка при получении новостей: {e}")
            return "Ошибка сбора новостей."

    async def fetch_historical_news(self, symbol: str, timestamp_ms: int, limit: int = 10) -> str:
        coin = symbol.split('/')[0] if '/' in symbol else symbol
        ts_seconds = int(timestamp_ms / 1000)
        params = {"lang": "EN", "categories": coin, "sortOrder": "latest", "lTs": ts_seconds}
        try:
            async with aiohttp.ClientSession(connector=self._get_connector()) as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        return "Новостной фон недоступен."
                    data = await response.json()
                    results = data.get("Data", [])[:limit]
                    if not results:
                        return f"Нет новостей по {coin} за этот исторический период."
                    news_lines = [f"- {item.get('title')} ({item.get('source_info', {}).get('name', 'Unknown')})" for item in results]
                    return "\n".join(news_lines)
        except Exception as e:
            logger.error(f"Ошибка исторических новостей: {e}")
            return "Ошибка сбора новостей."

news_parser_service = NewsParser()