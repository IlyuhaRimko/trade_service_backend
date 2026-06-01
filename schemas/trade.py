from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from enum import Enum
from uuid import UUID


# ==========================================
# 1. Схемы для работы с ИИ (Gemini Pro)
# ==========================================

class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    REJECT = "REJECT"


class GeminiSignalResponse(BaseModel):
    """Схема, по которой Gemini обязан вернуть нам JSON-ответ"""
    action: TradeAction = Field(
        ...,
        description="Торговое действие: BUY (покупать), SELL (продавать), HOLD (держать) или REJECT (отклонить технический сигнал)"
    )
    # ИЗМЕНЕНИЕ ЗДЕСЬ: Убрали ge=0.0 и le=1.0
    confidence: float = Field(
        ...,
        description="Уровень уверенности ИИ в сигнале от 0.0 до 1.0"
    )
    reasoning: str = Field(
        ...,
        description="Подробное логическое объяснение решения на основе технического и фундаментального (новостного) фона"
    )


# ==========================================
# 2. Схемы для сделок (База данных / API)
# ==========================================

class TradeBase(BaseModel):
    """Базовая информация о сделке"""
    symbol: str = Field(..., example="BTC/USDT")
    side: str = Field(..., example="LONG")
    entry_price: float = Field(..., gt=0)
    stop_loss: float = Field(..., gt=0)
    take_profit: Optional[float] = None
    volume_percentage: float = Field(..., gt=0, le=100)
    is_recovery: bool = False


class TradeCreate(TradeBase):
    """Схема для создания новой сделки (требует ID пользователя)"""
    user_id: UUID


class TradeResponse(TradeBase):
    """Схема для отдачи данных о сделке (например, на фронтенд)"""
    id: UUID
    status: str

    # Эта настройка позволяет Pydantic автоматически читать данные из объектов SQLAlchemy
    model_config = ConfigDict(from_attributes=True)