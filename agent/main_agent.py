import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.gigachat_llm import GigaChatLLM
from dotenv import load_dotenv

load_dotenv()


class GigaChatAgent:
    """Простой агент на GigaChat"""
    
    def __init__(self):
        self.client_id = os.getenv("GIGACHAT_CLIENT_ID")
        self.client_secret = os.getenv("GIGACHAT_CLIENT_SECRET")
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Ошибка: Ключи GigaChat не найдены в .env файле\n"
                "Добавьте в файл .env:\n"
                "GIGACHAT_CLIENT_ID=ваш_client_id\n"
                "GIGACHAT_CLIENT_SECRET=ваш_client_secret"
            )
        
        print("Инициализация GigaChat агента...")
        self.llm = GigaChatLLM(temperature=0.3)
    
    def run(self, query: str) -> str:
        """Запуск агента - возвращает только финальный ответ"""
        
        prompt = f"""Ты эксперт-аналитик данных. Ответь на вопрос кратко и по существу.

        Вопрос: {query}

        Ответ:"""
        
        try:
            result = self.llm.call(prompt=prompt)
            response = result["choices"][0]["message"]["content"]
            # Убираем многоточия
            response = response.rstrip('...').rstrip('.').strip()
            return response
        except Exception as e:
            return f"Ошибка: {str(e)}"


def run_analysis(query: str) -> str:
    """Запуск анализа"""
    agent = GigaChatAgent()
    return agent.run(query)


if __name__ == "__main__":
    agent = GigaChatAgent()
    
    test_queries = [
        "Что такое корреляция?",
        "Как инфляция влияет на ВВП?",
        "Есть ли связь между образованием и доходом?"
    ]
    
    for q in test_queries:
        print(f"\nВопрос: {q}")
        print(f"Ответ: {agent.run(q)}")
        print("-" * 40)