import aiohttp
import logging

logger = logging.getLogger(__name__)


class NewsParser:
    def __init__(self):
        # Используем бесплатный эндпоинт CryptoCompare (CCData)
        self.base_url = "https://min-api.cryptocompare.com/data/v2/news/"

    async def fetch_recent_news(self, symbol: str, limit: int = 10) -> str:
        """
        Запрашивает последние новости по конкретной монете через API CryptoCompare.
        Возвращает готовую строку (summary) для вставки в промпт ИИ.
        """
        # Превращаем торговую пару "BTC/USDT" в базовую монету "BTC"
        coin = symbol.split('/')[0] if '/' in symbol else symbol

        params = {
            "lang": "EN",  # Английские новости для Gemini
            "categories": coin,  # Фильтр по нужной монете
            "sortOrder": "latest"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка API CryptoCompare: HTTP {response.status}")
                        return "Новостной фон временно недоступен."

                    data = await response.json()

                    # Структура ответа CCData хранит массив новостей в ключе 'Data'
                    results = data.get("Data", [])[:limit]

                    if not results:
                        return f"Нет свежих новостей по монете {coin} за последнее время."

                    # Собираем компактный список: "- Заголовок (Источник)"
                    news_lines = [
                        f"- {item.get('title', 'Без заголовка')} ({item.get('source_info', {}).get('name', 'Unknown')})"
                        for item in results
                    ]

                    return "\n".join(news_lines)

        except Exception as e:
            logger.error(f"Ошибка при получении новостей для {symbol}: {e}")
            return "Ошибка сбора новостей."


# Создаем глобальный объект сервиса
news_parser_service = NewsParser()