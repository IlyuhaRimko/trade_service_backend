from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Sequence

from database.models import MarketDataOHLCV
from repositories.base import BaseRepository

class MarketDataRepository(BaseRepository[MarketDataOHLCV]):
    def __init__(self):
        super().__init__(MarketDataOHLCV)

    async def get_recent_candles(
        self, db: AsyncSession, symbol: str, timeframe: str, limit: int = 100
    ) -> Sequence[MarketDataOHLCV]:
        """
        Получить последние N свечей для конкретной монеты и таймфрейма,
        отсортированные по времени по убыванию (от свежих к старым).
        """
        query = (
            select(self.model)
            .filter(self.model.symbol == symbol, self.model.timeframe == timeframe)
            .order_by(desc(self.model.time))
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

# Создаем готовый объект репозитория для импорта в другие части программы
market_data_repo = MarketDataRepository()