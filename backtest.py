import asyncio
import logging
from datetime import datetime, timezone

from services.exchange_api import exchange_api_service
from services.news_parser import news_parser_service
from services.ai_analyzer import ai_analyzer_service
from trading.indicators import analyzer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


async def run_backtest():
    symbol = "BTC/USDT"
    timeframe = "4h"

    # 1. Задаем период: Весь 2025 год
    start_dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_dt = datetime(2025, 12, 31, 23, 59, tzinfo=timezone.utc)

    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)

    logging.info(f"Скачиваем историю {symbol} за 2025 год...")
    ohlcv = await exchange_api_service.fetch_historical_candles(symbol, timeframe, start_ms, end_ms)
    logging.info(f"Успешно скачано {len(ohlcv)} свечей.")

    if not ohlcv:
        return

    # 2. Математика: ищем все точки входа
    df = analyzer.prepare_dataframe(ohlcv)
    signals = analyzer.get_all_signals(df)

    logging.info(f"Найдено {len(signals)} точек идеальной дивергенции за 2025 год.\n" + "=" * 50)

    # 3. Передаем каждую точку в ИИ как "Машину времени"
    for i, sig in enumerate(signals):
        point_time = sig['time']
        timestamp_ms = int(point_time.timestamp() * 1000)

        logging.info(f"\n[{i + 1}/{len(signals)}] Сигнал от: {point_time} | Цена входа: {sig['context']['price']}$")

        # Получаем новости за неделю до этого сигнала
        news_context = await news_parser_service.fetch_historical_news(symbol, timestamp_ms, limit=10)

        # Спрашиваем ИИ (Gemini понятия не имеет, что было после этой даты)
        ai_decision = await ai_analyzer_service.analyze_signal(symbol, sig['context'], news_context)

        if ai_decision:
            if ai_decision.action.value == "BUY":
                logging.info(f"🟢 ИИ ГОВОРИТ ПОКУПАТЬ (Уверенность: {ai_decision.confidence})")
            else:
                logging.info(f"🔴 ИИ ОТКЛОНИЛ СДЕЛКУ (Уверенность: {ai_decision.confidence})")

            logging.info(f"Логика ИИ: {ai_decision.reasoning}")
            logging.info("-" * 50)

            # Ставим паузу 4 секунды между запросами, чтобы Google API нас не забанил за спам
            await asyncio.sleep(4)

    await exchange_api_service.close()
    logging.info("\nБэктест завершен! Теперь открой график на TradingView и проверь эти даты.")


if __name__ == "__main__":
    # Запускаем скрипт
    asyncio.run(run_backtest()) 