import pandas as pd
import pandas_ta as ta
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    @staticmethod
    def prepare_dataframe(ohlcv_data: list) -> pd.DataFrame:
        """
        Преобразует сырые данные CCXT в таблицу Pandas и рассчитывает индикаторы.
        """
        # Создаем DataFrame из массива списков
        df = pd.DataFrame(ohlcv_data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

        # Переводим timestamp из миллисекунд в нормальный формат даты
        df['time'] = pd.to_datetime(df['time'], unit='ms')

        # Рассчитываем RSI (стандартный период 14)
        df['RSI'] = ta.rsi(df['close'], length=14)

        # Рассчитываем MACD (стандартные параметры 12, 26, 9)
        # pandas-ta автоматически создаст 3 колонки:
        # MACD_12_26_9, MACDh_12_26_9 (Гистограмма) и MACDs_12_26_9 (Сигнальная линия)
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        df = pd.concat([df, macd], axis=1)

        return df

    @staticmethod
    def check_buy_signal(df: pd.DataFrame) -> dict:
        """
        Проверяет последние свечи на наличие паттерна бычьей дивергенции.
        Возвращает словарь с результатом и контекстом для Gemini.
        """
        if len(df) < 2:
            return {"signal": False, "context": None}

        # Берем текущую (последнюю закрытую) и предыдущую свечи
        current = df.iloc[-1]
        previous = df.iloc[-2]

        # 1. Цена обновила локальный минимум
        price_lower_low = current['low'] < previous['low']

        # 2. RSI находится в зоне перепроданности (< 30)
        rsi_oversold = current['RSI'] < 30

        # 3. Дивергенция MACD (гистограмма отрицательная, но начинает расти)
        macd_col = 'MACDh_12_26_9'
        macd_divergence = (current[macd_col] < 0) and (current[macd_col] > previous[macd_col])

        # Если все три условия совпали - генерируем первичный технический триггер
        if price_lower_low and rsi_oversold and macd_divergence:
            technical_context = {
                "price": float(current['close']),
                "rsi": float(current['RSI']),
                "macd_histogram": float(current[macd_col]),
                "description": "Сильная бычья дивергенция (Цена падает, RSI в перепроданности, гистограмма MACD растет)."
            }
            logger.info("Найден технический сетап для ЛОНГА!")
            return {"signal": True, "context": technical_context}

        return {"signal": False, "context": None}


# Создаем глобальный объект анализатора
analyzer = TechnicalAnalyzer()