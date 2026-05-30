import google.generativeai as genai
import json
import logging
from core.config import settings
from schemas.trade import GeminiSignalResponse

logger = logging.getLogger(__name__)


class AIAnalyzer:
    def __init__(self):
        # Инициализируем API ключ
        self.api_key = settings.GEMINI_API_KEY
        genai.configure(api_key=self.api_key)

        # Настраиваем модель
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',  # Быстрая модель для трейдинга
            generation_config=genai.GenerationConfig(
                temperature=0.1,  # Почти ноль для строгих, детерминированных ответов
                response_mime_type="application/json",
                # МАГИЯ: Заставляем Gemini отвечать строго по нашей Pydantic схеме!
                response_schema=GeminiSignalResponse
            )
        )

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

        # Формируем жесткий системный промпт
        prompt = f"""
        Ты - strict risk-manager квантового хедж-фонда.
        Твоя задача: проанализировать технический паттерн и фундаментальный новостной фон, 
        чтобы одобрить или отклонить торговую сделку.

        ТОРГОВЫЙ ИНСТРУМЕНТ: {symbol}

        1. ТЕХНИЧЕСКИЙ СИГНАЛ (от нашего алгоритма):
        {json.dumps(technical_context, indent=2, ensure_ascii=False)}

        2. ФУНДАМЕНТАЛЬНЫЙ ФОН (последние новости с рынка):
        {news_context}

        ПРАВИЛА ПРИНЯТИЯ РЕШЕНИЯ:
        - Если новости содержат FUD, хакерские атаки, проблемы с регуляторами (SEC) или обвал рынка - ТЫ ОБЯЗАН ВЕРНУТЬ action "REJECT" с низкой confidence.
        - Если новости нейтральные, позитивные или не касаются монеты напрямую, а технический сигнал сильный - возвращай "BUY".
        - Оценивай confidence от 0.0 до 1.0 на основе ясности картины.
        """

        try:
            logger.info(f"Отправка данных в Gemini для {symbol}...")
            # Делаем асинхронный вызов к ИИ
            response = await self.model.generate_content_async(prompt)

            # Поскольку мы указали response_schema, response.text ГАРАНТИРОВАННО
            # содержит правильный JSON. Парсим его нашей Pydantic схемой:
            result = GeminiSignalResponse.model_validate_json(response.text)

            logger.info(f"Решение ИИ: {result.action.value} (Уверенность: {result.confidence})")
            logger.info(f"Логика ИИ: {result.reasoning}")

            return result

        except Exception as e:
            logger.error(f"Сбой при обращении к Gemini API: {e}")
            return None


# Создаем глобальный объект сервиса
ai_analyzer_service = AIAnalyzer()