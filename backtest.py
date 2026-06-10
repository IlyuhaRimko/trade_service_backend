import asyncio
import logging
from datetime import datetime, timezone

from services.exchange_api import exchange_api_service
from trading.indicators import analyzer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


async def run_backtest():
    # ИСПРАВЛЕНО: Меняем несуществующий BTC/USDT на правильный фиатный BTC/USD
    symbol = "BTC/USD"

    start_dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_dt = datetime(2025, 12, 31, 23, 59, tzinfo=timezone.utc)

    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)

    logging.info(f"Скачиваем историю {symbol} за 2025 год...")
    ohlcv_4h = await exchange_api_service.fetch_historical_candles(symbol, "4h", start_ms, end_ms)
    ohlcv_1h = await exchange_api_service.fetch_historical_candles(symbol, "1h", start_ms, end_ms)
    ohlcv_30m = await exchange_api_service.fetch_historical_candles(symbol, "30m", start_ms, end_ms)

    if not ohlcv_4h or not ohlcv_1h or not ohlcv_30m:
        logging.error("Не удалось скачать все таймфреймы!")
        return

    logging.info("Готовим данные и рассчитываем Stochastic RSI...")

    # Задаем жесткий триггер для 4-часовика
    df_4h = analyzer.prepare_dataframe(ohlcv_4h, lower_zone=20, upper_zone=80)

    # Для 1H и 30M можно вообще не передавать зоны, они тут больше не нужны!
    df_1h = analyzer.prepare_dataframe(ohlcv_1h)
    df_30m = analyzer.prepare_dataframe(ohlcv_30m)

    logging.info("Ищем мульти-таймфреймовые сигналы...")
    # Передаем пороги подтверждения для младших таймфреймов (30 и 70)
    signals = analyzer.get_mtf_signals(df_4h, df_1h, df_30m, conf_lower=30, conf_upper=70)

    logging.info(f"\nНайдено {len(signals)} идеальных MTF сигналов за 2025 год.\n" + "=" * 50)

    for i, sig in enumerate(signals):
        action_icon = "🟢 ПОКУПКА (LONG)" if sig['action'] == "BUY" else "🔴 ПРОДАЖА (SHORT)"
        print(f"[{i + 1}/{len(signals)}] Дата входа: {sig['time']} | {action_icon} по {sig['price']}$")
        print(f"      4H Stoch_K: {sig['context']['4h_stoch_k']}")
        print(f"      Подтверждено 1H:  {'Да' if sig['context']['confirmed_by_1h'] else 'Нет'}")
        print(f"      Подтверждено 30M: {'Да' if sig['context']['confirmed_by_30m'] else 'Нет'}")
        print("-" * 45)

    await exchange_api_service.close()


if __name__ == "__main__":
    asyncio.run(run_backtest())