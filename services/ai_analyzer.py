import json
import logging
import asyncio
from google import genai
from google.genai import types
from core.config import settings
from schemas.trade import GeminiSignalResponse

logger = logging.getLogger(__name__)


class AIAnalyzer:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = 'gemini-2.5-flash'

    def _analyze_sync(self, symbol: str, technical_context: dict, news_context: str) -> GeminiSignalResponse:
        """Синхронный метод для обхода багов aiohttp на Windows"""
        prompt = f"""
        Ты - strict risk-manager квантового хедж-фонда.
        Твоя задача: проанализировать технический паттерн и фундаментальный новостной фон, 
        чтобы одобрить или отклонить торговую сделку.

        ТОРГОВЫЙ ИНСТРУМЕНТ: {symbol}

        1. ТЕХНИЧЕСКИЙ СИГНАЛ:
        {json.dumps(technical_context, indent=2, ensure_ascii=False)}

        2. ФУНДАМЕНТАЛЬНЫЙ ФОН:
        {news_context}

        ПРАВИЛА:
        - Если новости содержат FUD, хакерские атаки, проблемы с регуляторами или обвал рынка - возвращай action "REJECT" с низкой confidence.
        - Если новости нейтральные, позитивные или не касаются монеты напрямую, а технический сигнал сильный - возвращай "BUY".
        - Оценивай confidence от 0.0 до 1.0.
        """

        # Заметь: здесь мы используем синхронный вызов (без .aio)
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=GeminiSignalResponse,
            )
        )
        return GeminiSignalResponse.model_validate_json(response.text)

    async def analyze_signal(self, symbol: str, technical_context: dict,
                             news_context: str) -> GeminiSignalResponse | None:
        """Асинхронная обертка для нашего демона"""
        try:
            logger.info(f"Отправка данных в Gemini для {symbol}...")

            # Запускаем синхронный код в отдельном системном потоке
            result = await asyncio.to_thread(self._analyze_sync, symbol, technical_context, news_context)

            logger.info(f"Решение ИИ: {result.action.value} (Уверенность: {result.confidence})")
            logger.info(f"Логика ИИ: {result.reasoning}")

            return result

        except Exception as e:
            logger.error(f"Сбой при обращении к Gemini API: {e}")
            return None


ai_analyzer_service = AIAnalyzer()