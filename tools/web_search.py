from langchain.tools import tool
from ddgs import DDGS 

@tool
def web_search(query: str) -> str:
    """Поиск в интернете через DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            # Используем метод text для поиска
            results = list(ddgs.text(query, max_results=3))
            
            if results:
                # Формируем понятный ответ для агента
                search_results = []
                for r in results:
                    title = r.get('title', 'Без заголовка')
                    body = r.get('body', '')
                    href = r.get('href', '#')
                    search_results.append(f"Источник: {href}\nЗаголовок: {title}\n{body}")
                
                return "\n\n".join(search_results)
            else:
                return f"По запросу '{query}' ничего не найдено."
    except Exception as e:
        return f"Ошибка поиска: {str(e)}. Попробуйте другой запрос."


# Самотестирование
if __name__ == "__main__":
    print("Тестирование веб-поиска через DuckDuckGo...")
    
    result = web_search.invoke({"query": "ИПЦ Европа 2025"})
    
    print(f"Результат поиска (первые 500 символов):\n{result[:500]}")
    
    if result and len(result) > 50:
        print("\nТест пройден! Поиск работает.")
    else:
        print("\nТест не пройден")