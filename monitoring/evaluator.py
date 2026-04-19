"""
Оценка качества ответов с помощью GigaChat
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.gigachat_llm import GigaChatLLM
from dotenv import load_dotenv

load_dotenv()


class GigaChatJudge:
    """Судья на базе GigaChatLLM"""
    
    def __init__(self, temperature: float = 0.1):
        """Используем GigaChatLLM"""
        self.judge = GigaChatLLM(temperature=temperature)
    
    def evaluate_response(self, query: str, response: str) -> dict:
        """Оценка ответа"""
        prompt = f"""Ты объективный Data Science эксперт-оценщик. 

Оцени этот ответ по шкале 0.0-1.0:

ВОПРОС: {query}
ОТВЕТ: {response}

Критерии оценки:
- ПОЛНОТА (0.0-1.0): насколько ответ полный и исчерпывающий?
- ТОЧНОСТЬ (0.0-1.0): верны ли факты, числа, формулы? 
- ЯСНОСТЬ (0.0-1.0): насколько понятное и структурированное изложение?

ОТВЕТЬ СТРОГО в формате:
полнота: X.XX
точность: X.XX  
ясность: X.XX

НЕ добавляй ничего лишнего."""

        try:
            # Используем GigaChatLLM
            raw_output = self.judge.call(prompt=prompt)
            
            # Извлекаем текст ответа
            if isinstance(raw_output, dict) and 'choices' in raw_output:
                result_text = raw_output['choices'][0]['message']['content']
            elif isinstance(raw_output, str):
                result_text = raw_output
            else:
                result_text = str(raw_output)
            
            # Парсим четкий формат
            scores = {}
            for metric in ['полнота', 'точность', 'ясность']:
                # Ищем паттерн "полнота: 0.85"
                match = re.search(rf'{metric}\s*:\s*(\d+\.\d+)', result_text, re.IGNORECASE)
                if match:
                    scores[metric] = float(match.group(1))
            
            # Финальные значения
            completeness = scores.get('полнота', 0.5)
            accuracy = scores.get('точность', 0.5)
            clarity = scores.get('ясность', 0.5)
            
            # Ограничиваем от 0 до 1
            completeness = max(0.0, min(1.0, completeness))
            accuracy = max(0.0, min(1.0, accuracy))
            clarity = max(0.0, min(1.0, clarity))
            
            overall = (completeness + accuracy + clarity) / 3
            
            return {
                "полнота": round(completeness, 2),
                "точность": round(accuracy, 2),
                "ясность": round(clarity, 2),
                "общая_оценка": round(overall, 2)
            }
            
        except Exception as e:
            print(f"Ошибка оценки: {e}")
            # Возвращаем значения по умолчанию при ошибке
            return {
                "полнота": 0.5,
                "точность": 0.5, 
                "ясность": 0.5,
                "общая_оценка": 0.5
            }


# Самотестирование
if __name__ == "__main__":
    print("Тестирование GigaChat судьи")
    
    judge = GigaChatJudge(temperature=0.1)
    
    test_query = "Что такое корреляция?"
    test_response = "Корреляция - это статистическая связь между двумя переменными."
    
    result = judge.evaluate_response(test_query, test_response)
    
    print(f"\nРезультаты оценки:")
    print(f"  Полнота: {result['полнота']}")
    print(f"  Точность: {result['точность']}")
    print(f"  Ясность: {result['ясность']}")
    print(f"  Общая оценка: {result['общая_оценка']}")