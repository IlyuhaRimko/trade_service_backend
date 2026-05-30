import asyncio
import logging
from database.session import async_session_maker
from database.models import AiAnalysisLog
from services.exchange_api import exchange_api_service
from services.news_parser import news_parser_service
from services.ai_analyzer import ai_analyzer_service
from trading.indicators import analyzer

logger = logging.getLogger(__name__)


class TradingDaemon:
    def __init__(self):
        # Для MVP берем биткоин и эфир
        self.symbols = ["BTC/USDT", "ETH/USDT"]
        self.timeframe = "4h"
        # Проверяем рынок раз в 5 минут (для 4-часовика этого более чем достаточно)
        self.sleep_interval = 300

    async def run(self):
        logger.info("🚀 Торговый демон запущен. Начинаю мониторинг рынка...")
        while True:
            for symbol in self.symbols:
                try:
                    await self.process_symbol(symbol)
                except Exception as e:
                    logger.error(f"Ошибка при обработке {symbol}: {e}")

            logger.info(f"Цикл завершен. Демон спит {self.sleep_interval} секунд...")
            await asyncio.sleep(self.sleep_interval)

    async def process_symbol(self, symbol: str):
        logger.info(f"[{symbol}] Сбор рыночных данных...")

        # 1. Получаем свечи с биржи
        ohlcv = await exchange_api_service.fetch_candles(symbol, self.timeframe, limit=100)
        if not ohlcv:
            return

        # 2. Ищем дивергенции (Mean Reversion)
        df = analyzer.prepare_dataframe(ohlcv)
        tech_result = analyzer.check_buy_signal(df)

        if not tech_result["signal"]:
            logger.info(f"[{symbol}] Нет технических сетапов на вход.")
            return

        logger.warning(f"[{symbol}] ТРИГГЕР! Найден технический паттерн. Собираю новости...")

        # 3. Собираем новостной сентимент
        news_context = await news_parser_service.fetch_recent_news(symbol, limit=5)

        # 4. Отправляем пакет данных в ИИ
        ai_decision = await ai_analyzer_service.analyze_signal(
            symbol=symbol,
            technical_context=tech_result["context"],
            news_context=news_context
        )

        if not ai_decision:
            return

        # 5. Сохраняем логику ИИ в базу данных (для будущего бэктеста и дебага)
        async with async_session_maker() as db:
            log_entry = AiAnalysisLog(
                symbol=symbol,
                technical_context=tech_result["context"],
                prompt_sent=news_context,
                gemini_response=ai_decision.model_dump()  # Сохраняем Pydantic модель как JSON
            )
            db.add(log_entry)
            await db.commit()

        # 6. Финальное торговое решение
        if ai_decision.action.value == "BUY" and ai_decision.confidence >= 0.7:
            logger.warning(f"🟢 СИГНАЛ НА ПОКУПКУ {symbol}! Уверенность ИИ: {ai_decision.confidence}")
            logger.info(f"Логика ИИ: {ai_decision.reasoning}")
            # Здесь в будущем мы добавим отправку реального ордера на биржу

        elif ai_decision.action.value == "REJECT":
            logger.error(f"🔴 ИИ ОТКЛОНИЛ СДЕЛКУ по {symbol}. Причина: {ai_decision.reasoning}")


# Создаем глобальный объект демона
trading_daemon = TradingDaemon()