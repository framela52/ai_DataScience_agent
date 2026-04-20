import os
import requests
import urllib3
import re
import json
from dotenv import load_dotenv

load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GigaChatLLM:
    """Клиент GigaChat с поддержкой"""
    
    def __init__(self, temperature: float = 0.3):
        self.api_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.client_id = os.getenv("GIGACHAT_CLIENT_ID")
        self.client_secret = os.getenv("GIGACHAT_CLIENT_SECRET")
        self.temperature = temperature
        self.access_token = None
        
        if not self.client_id or not self.client_secret:
            raise ValueError("GIGACHAT_CLIENT_ID и GIGACHAT_CLIENT_SECRET должны быть в .env")
        
        self.authenticate()
    
    def authenticate(self):
        """Аутентификация"""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": os.getenv("RQ_UID", "123e4567-e89b-12d3-a456-426614174000")
        }
        
        data = {
            "scope": "GIGACHAT_API_PERS",
            "grant_type": "client_credentials"
        }
        
        auth = (self.client_id, self.client_secret)
        
        response = requests.post(
            self.auth_url,
            headers=headers,
            data=data,
            auth=auth,
            verify=False
        )
        
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            print("GigaChat: Аутентификация успешна")
        else:
            raise Exception(f"Ошибка аутентификации: {response.status_code} - {response.text}")
    
    def call(self, prompt: str = None, messages: list = None, functions: list = None) -> dict:
        """
        Генерация текста
        
        Args:
            prompt: простой текстовый запрос
            messages: список сообщений для диалога
            functions: список функций для function calling
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "RqUID": os.getenv("RQ_UID", "123e4567-e89b-12d3-a456-426614174000")
        }
        
        # Формируем сообщения
        if messages is None and prompt:
            messages = [{"role": "user", "content": prompt}]
        
        payload = {
            "model": "GigaChat-Pro",
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 2000
        }
        
        # Добавляем функции если есть
        if functions:
            payload["functions"] = functions
            payload["function_call"] = "auto"
        
        response = requests.post(
            f"{self.api_url}/chat/completions",
            headers=headers,
            json=payload,
            verify=False,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Ошибка генерации: {response.status_code} - {response.text}")
    
    def _call(self, prompt: str, messages: list = None, functions: list = None) -> dict:
        """Обертка для обратной совместимости"""
        return self.call(prompt=prompt, messages=messages, functions=functions)


# Тест
if __name__ == "__main__":
    print("="*50)
    print("ТЕСТ GigaChat")
    print("="*50)
    
    llm = GigaChatLLM()
    
    # Тест
    result = llm.call(prompt="Назови одним словом: что такое корреляция?")
    print(f"\nПростой запрос: {result['choices'][0]['message']['content']}")
        
    print("\nТест завершен")