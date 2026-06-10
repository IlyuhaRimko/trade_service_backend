import pandas as pd
import pandas_ta as ta
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    @staticmethod
    def prepare_dataframe(ohlcv_data: list, lower_zone: int = 20, upper_zone: int = 80) -> pd.DataFrame:
        """
        Преобразует сырые данные и принимает динамические зоны для Stochastic RSI.
        """
        df = pd.DataFrame(ohlcv_data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')

        stoch = ta.stochrsi(df['close'], length=14, rsi_length=14, k=3, d=3)

        k_col = [c for c in stoch.columns if 'k' in c.lower()][0]
        d_col = [c for c in stoch.columns if 'd' in c.lower()][0]

        df['stoch_k'] = stoch[k_col]
        df['stoch_d'] = stoch[d_col]

        df['prev_k'] = df['stoch_k'].shift(1)
        df['prev_d'] = df['stoch_d'].shift(1)

        # Используем ПЕРЕДАННЫЕ параметры lower_zone и upper_zone вместо жестких 20/80
        df['buy_cross'] = (df['stoch_k'] > df['stoch_d']) & \
                          (df['prev_k'] <= df['prev_d']) & \
                          (df['stoch_k'] < lower_zone)

        df['sell_cross'] = (df['stoch_k'] < df['stoch_d']) & \
                           (df['prev_k'] >= df['prev_d']) & \
                           (df['stoch_k'] > upper_zone)

        df.set_index('time', inplace=True)
        return df

    @staticmethod
    def get_mtf_signals(df_4h: pd.DataFrame, df_1h: pd.DataFrame, df_30m: pd.DataFrame, conf_lower: int = 30,
                        conf_upper: int = 70) -> list:
        """
        Мульти-таймфреймовый анализатор (MTF).
        Главный триггер: 4H (строгое перекрестие).
        Подтверждение: 1H и 30M (просто нахождение %K в экстремальных зонах внутри окна).
        """
        signals = []

        # Пробегаемся по всем 4-часовым свечам
        for timestamp, row_4h in df_4h.iloc[30:].iterrows():
            close_time = timestamp + pd.Timedelta(hours=4)

            # Вырезаем окна младших ТФ
            window_1h = df_1h.loc[timestamp: timestamp + pd.Timedelta(hours=3)]
            window_30m = df_30m.loc[timestamp: timestamp + pd.Timedelta(hours=3, minutes=30)]

            # --- ПРОВЕРКА НА ЛОНГ (ПОКУПКА) ---
            if row_4h['buy_cross']:
                # МАГИЯ ЗДЕСЬ: Ищем не перекрестие, а просто факт падения stoch_k < conf_lower
                # .any() означает: "падала ли линия %K ниже зоны хотя бы на одной свече в этом окне?"
                conf_1h = (window_1h['stoch_k'] < conf_lower).any() if not window_1h.empty else False
                conf_30m = (window_30m['stoch_k'] < conf_lower).any() if not window_30m.empty else False

                # У тебя стоит 'and' - жесткое подтверждение от ОБОИХ младших ТФ
                if conf_1h and conf_30m:
                    signals.append({
                        "time": close_time,
                        "action": "BUY",
                        "price": float(row_4h['close']),
                        "context": {
                            "4h_stoch_k": round(float(row_4h['stoch_k']), 2),
                            "confirmed_by_1h": bool(conf_1h),
                            "confirmed_by_30m": bool(conf_30m)
                        }
                    })

            # --- ПРОВЕРКА НА ШОРТ (ПРОДАЖА) ---
            elif row_4h['sell_cross']:
                # Аналогично: заходила ли линия %K в зону перекупленности (> conf_upper)
                conf_1h = (window_1h['stoch_k'] > conf_upper).any() if not window_1h.empty else False
                conf_30m = (window_30m['stoch_k'] > conf_upper).any() if not window_30m.empty else False

                if conf_1h and conf_30m:
                    signals.append({
                        "time": close_time,
                        "action": "SELL",
                        "price": float(row_4h['close']),
                        "context": {
                            "4h_stoch_k": round(float(row_4h['stoch_k']), 2),
                            "confirmed_by_1h": bool(conf_1h),
                            "confirmed_by_30m": bool(conf_30m)
                        }
                    })

        return signals


analyzer = TechnicalAnalyzer()