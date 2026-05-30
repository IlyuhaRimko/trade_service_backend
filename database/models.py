import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    api_keys = relationship("ApiKey", back_populates="user")
    trades = relationship("Trade", back_populates="user")


class ApiKey(Base):
    __tablename__ = 'api_keys'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    exchange = Column(String, nullable=False)
    encrypted_api_key = Column(String, nullable=False)
    encrypted_secret = Column(String, nullable=False)

    user = relationship("User", back_populates="api_keys")


class MarketDataOHLCV(Base):
    __tablename__ = 'market_data_ohlcv'
    # В TimescaleDB time является ключевым полем для партицирования
    time = Column(DateTime, primary_key=True, nullable=False)
    symbol = Column(String, primary_key=True, nullable=False)  # e.g., "BTC/USDT"
    timeframe = Column(String, primary_key=True, nullable=False)  # e.g., "1H", "4H"
    open = Column(Numeric, nullable=False)
    high = Column(Numeric, nullable=False)
    low = Column(Numeric, nullable=False)
    close = Column(Numeric, nullable=False)
    volume = Column(Numeric, nullable=False)


class AiAnalysisLog(Base):
    __tablename__ = 'ai_analysis_logs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    technical_context = Column(JSONB, nullable=False)
    prompt_sent = Column(String, nullable=False)
    gemini_response = Column(JSONB, nullable=False)


class Trade(Base):
    __tablename__ = 'trades'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)  # "LONG" / "SHORT"
    status = Column(String, nullable=False, default="OPEN")  # "OPEN", "CLOSED", "REJECTED"
    entry_price = Column(Numeric, nullable=False)
    stop_loss = Column(Numeric, nullable=False)
    take_profit = Column(Numeric, nullable=True)
    volume_percentage = Column(Numeric, nullable=False)
    is_recovery = Column(Boolean, default=False)

    user = relationship("User", back_populates="trades")