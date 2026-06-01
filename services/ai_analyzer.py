import json
import logging
from google import genai
from google.genai import types
from core.config import settings
from schemas.trade import GeminiSignalResponse

logger = logging.getLogger(__name__)


class AIAnalyzer:
    def __init__(self):
        # Инициализируем новый клиент google-genai
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = 'gemini-2.5-flash'  # Можно использовать 1.5-flash или 2.5-flash

    async def analyze_signal(
            self,
            symbol: str,
            technical_context: dict,
            news_context: str
    ) -> GeminiSignalResponse | None:
        """
        Отправляет технические данные и новости в Gemini для принятия решения.
        Возвращает валидированный Pydantic-объект.
        """

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

        try:
            logger.info(f"Отправка данных в Gemini для {symbol}...")

            # Асинхронный вызов через новый SDK
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                    # Новый SDK сам понимает схемы Pydantic!
                    response_schema=GeminiSignalResponse,
                )
            )

            # Парсим полученный JSON
            result = GeminiSignalResponse.model_validate_json(response.text)

            logger.info(f"Решение ИИ: {result.action.value} (Уверенность: {result.confidence})")
            logger.info(f"Логика ИИ: {result.reasoning}")

            return result

        except Exception as e:
            logger.error(f"Сбой при обращении к Gemini API: {e}")
            return None


# Создаем глобальный объект сервиса
ai_analyzer_service = AIAnalyzer()