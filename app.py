"""
Веб-интерфейс для агента аналитика данных
С отображением рассуждений и веб-поиском
Запуск: python web_app.py
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys
import os
import time
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.gigachat_llm import GigaChatLLM
from tools.web_search import web_search
from tools.data_analysis import analyze_correlation
from monitoring.metrics import MetricsCollector
from monitoring.evaluator import GigaChatJudge
from dotenv import load_dotenv

load_dotenv()


class ThinkingAgent:
    """Агент, который вызывает инструменты (включая веб-поиск)"""
    
    def __init__(self):
        self.llm = GigaChatLLM(temperature=0.3)
        self.tools = {
            "web_search": web_search,
            "analyze_correlation": analyze_correlation
        }
        
        self.tools_desc = """
Доступные инструменты:
- web_search(запрос) - поиск информации в интернете
- analyze_correlation(x,y,значения) - анализ корреляции

ВАЖНО: Используй эти инструменты когда нужно.
Не пиши формулы LaTeX. Пиши обычным текстом.
"""
    
    def process_query(self, query: str):
        """Обработка запроса с вызовом инструментов"""
        
        prompt = f"""{self.tools_desc}

Вопрос: {query}

Покажи рассуждения в формате:
Мысль: ...
Действие: название_инструмента
Вход: параметры
Наблюдение: результат

В конце дай Финальный ответ.

Начни:"""
        
        try:
            result = self.llm.call(prompt=prompt)
            full_response = result["choices"][0]["message"]["content"]
            
            thinking_lines = []
            final_answer = ""
            in_final = False
            
            lines = full_response.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                if line.startswith('Действие:'):
                    action = line.replace('Действие:', '').strip()
                    if i + 1 < len(lines) and lines[i+1].strip().startswith('Вход:'):
                        input_line = lines[i+1].strip().replace('Вход:', '').strip()
                        tool_name = action.split()[0] if action.split() else action
                        
                        if tool_name in self.tools:
                            try:
                                tool_result = self.tools[tool_name](input_line)
                                thinking_lines.append(line)
                                thinking_lines.append(lines[i+1].strip())
                                thinking_lines.append(f"Наблюдение: {tool_result}")
                                i += 2
                            except Exception as e:
                                thinking_lines.append(line)
                                thinking_lines.append(lines[i+1].strip())
                                thinking_lines.append(f"Наблюдение: Ошибка: {str(e)}")
                                i += 2
                        else:
                            thinking_lines.append(line)
                            i += 1
                    else:
                        thinking_lines.append(line)
                        i += 1
                elif 'Финальный ответ:' in line:
                    in_final = True
                    final_answer = line.replace('Финальный ответ:', '').strip()
                    i += 1
                elif in_final:
                    final_answer += ' ' + line.strip()
                    i += 1
                else:
                    if line:
                        thinking_lines.append(line)
                    i += 1
            
            if not final_answer:
                for line in reversed(lines):
                    line_stripped = line.strip()
                    if not any([
                        line_stripped.startswith('Мысль:'),
                        line_stripped.startswith('Действие:'),
                        line_stripped.startswith('Вход:'),
                        line_stripped.startswith('Наблюдение:'),
                        line_stripped.startswith('Источник:')
                    ]):
                        final_answer = line_stripped
                        break
            
            final_answer = self._clean_answer(final_answer)
            
            return {
                "thinking": '\n'.join(thinking_lines),
                "answer": final_answer
            }
            
        except Exception as e:
            return {
                "thinking": f"Ошибка: {str(e)}",
                "answer": f"Ошибка: {str(e)}"
            }
    
    def _clean_answer(self, text: str) -> str:
        text = re.sub(r'\.{3,}$', '', text)
        text = re.sub(r'…+$', '', text)
        text = re.sub(r'^\s*Финальный ответ:\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


# Инициализация
if not os.getenv("GIGACHAT_CLIENT_ID"):
    print("ОШИБКА: Ключи GigaChat не найдены в .env")
    sys.exit(1)

print("Инициализация агента...")
agent = ThinkingAgent()
metrics = MetricsCollector()
print("Агент готов")

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>DS Analyst Agent</title>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f0f2f5;
        }
        .container {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
        }
        .subtitle {
            color: #7f8c8d;
            margin-bottom: 20px;
        }
        .chat-layout {
            display: flex;
            gap: 20px;
            min-height: 500px;
        }
        .thinking-area {
            flex: 1;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #fafafa;
            display: flex;
            flex-direction: column;
        }
        .thinking-header {
            padding: 10px;
            background-color: #2c3e50;
            color: white;
            border-radius: 8px 8px 0 0;
            font-weight: bold;
        }
        .thinking-content {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            min-height: 400px;
            max-height: 500px;
            font-family: monospace;
            font-size: 13px;
            white-space: pre-wrap;
        }
        .response-area {
            flex: 1;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #fafafa;
            display: flex;
            flex-direction: column;
        }
        .response-header {
            padding: 10px;
            background-color: #27ae60;
            color: white;
            border-radius: 8px 8px 0 0;
            font-weight: bold;
        }
        .response-content {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            min-height: 400px;
            max-height: 500px;
            line-height: 1.5;
        }        
        .input-area {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        input {
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            padding: 12px 24px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        button:hover {
            background-color: #2980b9;
        }
        button:disabled {
            background-color: #95a5a6;
            cursor: not-allowed;
        }
        .stats {
            margin-top: 20px;
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
            font-size: 12px;
        }
        .stats h4 {
            margin: 0 0 10px 0;
            color: #2c3e50;
        }
        .stats-row {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 10px;
        }
        .stats-item {
            background-color: white;
            padding: 8px 12px;
            border-radius: 5px;
            min-width: 120px;
        }
        .stats-item strong {
            color: #3498db;
        }
        .loading {
            color: #7f8c8d;
            font-style: italic;
            text-align: center;
            padding: 20px;
        }
        .clear-btn {
            background-color: #95a5a6;
        }
        .clear-btn:hover {
            background-color: #7f8c8d;
        }
        .error {
            color: red;
        }
        .metrics-divider {
            border-top: 1px solid #ddd;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI-агент аналитик данных</h1>
        <div class="subtitle">Агент показывает процесс рассуждения, затем дает ответ</div>
        
        <div class="chat-layout">
            <div class="thinking-area">
                <div class="thinking-header">Процесс рассуждения</div>
                <div class="thinking-content" id="thinkingContent">
                    <div class="loading">Ожидание запроса...</div>
                </div>
            </div>
            
            <div class="response-area">
                <div class="response-header">Финальный ответ</div>
                <div class="response-content" id="responseContent">
                    <div class="loading">Ожидание запроса...</div>
                </div>
            </div>
        </div>       
                
        <div class="input-area">
            <input type="text" id="queryInput" placeholder="Введите ваш вопрос..." autofocus>
            <button onclick="sendQuery()" id="sendBtn">Отправить</button>
            <button onclick="clearChat()" class="clear-btn">Очистить</button>
        </div>
        
        <div class="stats" id="stats">
            <div class="loading">Ожидание запроса...</div>
        </div>
    </div>
    
    <script>
        function escapeHtml(text) {
            if (!text) return '';
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#39;");
        }

        function formatStats(stats, latency) {
            if (!stats) return '<div class="loading">Нет данных</div>';
            
            return `
                <h4>Статистика по последним запросам</h4>
                <div class="stats-row">
                    <div class="stats-item"><strong>Перплексия:</strong> ${stats.avg_perplexity || 0}</div>
                    <div class="stats-item"><strong>Релевантность:</strong> ${stats.avg_relevance || 0}</div>
                    <div class="stats-item"><strong>Задержка:</strong> ${stats.avg_latency || 0} мс</div>
                    <div class="stats-item"><strong>Всего запросов:</strong> ${stats.total_queries || 0}</div>
                </div>
                <div class="metrics-divider"></div>
                <h4>Оценка качества ответа (GigaChat Judge)</h4>
                <div class="stats-row">
                    <div class="stats-item"><strong>Полнота:</strong> ${stats.avg_completeness || 0}</div>
                    <div class="stats-item"><strong>Точность:</strong> ${stats.avg_accuracy || 0}</div>
                    <div class="stats-item"><strong>Ясность:</strong> ${stats.avg_clarity || 0}</div>
                    <div class="stats-item"><strong>Общая оценка:</strong> ${stats.avg_overall || 0}</div>
                </div>
                <div class="metrics-divider"></div>
                <div class="stats-row">
                    <div class="stats-item"><strong>Текущая задержка:</strong> ${latency} мс</div>
                </div>
            `;
        }

        async function sendQuery() {
            const input = document.getElementById('queryInput');
            const query = input.value.trim();
            if (!query) return;

            const sendBtn = document.getElementById('sendBtn');
            sendBtn.disabled = true;
            sendBtn.textContent = 'Отправка...';

            const thinkingEl = document.getElementById('thinkingContent');
            const responseEl = document.getElementById('responseContent');
            const statsEl = document.getElementById('stats');

            thinkingEl.innerHTML = '<div class="loading">Агент думает...</div>';
            responseEl.innerHTML = '<div class="loading">Агент думает...</div>';
            statsEl.innerHTML = '<div class="loading">Расчет метрик...</div>';

            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: query})
                });

                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }

                const data = await response.json();
                
                thinkingEl.innerHTML = escapeHtml(data.thinking || '').replace(/\\n/g, '<br>');
                responseEl.innerHTML = escapeHtml(data.answer || '').replace(/\\n/g, '<br>');
                
                if (data.stats) {
                    statsEl.innerHTML = formatStats(data.stats, data.latency);
                } else {
                    statsEl.innerHTML = '<div class="loading">Метрики не получены</div>';
                }

            } catch (error) {
                console.error('Ошибка:', error);
                responseEl.innerHTML = '<span class="error">Ошибка: ' + escapeHtml(error.message) + '</span>';
                statsEl.innerHTML = '<div class="loading">Ошибка получения метрик</div>';
            } finally {
                sendBtn.disabled = false;
                sendBtn.textContent = 'Отправить';
                input.value = '';
                input.focus();
            }
        }

        function clearChat() {
            document.getElementById('thinkingContent').innerHTML = '<div class="loading">Ожидание запроса...</div>';
            document.getElementById('responseContent').innerHTML = '<div class="loading">Ожидание запроса...</div>';
            document.getElementById('stats').innerHTML = '<div class="loading">Ожидание запроса...</div>';
            document.getElementById('queryInput').value = '';
        }

        document.getElementById('queryInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendQuery();
            }
        });
    </script>
</body>
</html>
'''


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/ask':
            length = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(length))
            query = data.get('query', '')
            
            start_time = time.time()
            result = agent.process_query(query)
            latency_ms = (time.time() - start_time) * 1000
            
            print(f"Обработка запроса: {query[:50]}...")
            metric_data = metrics.collect(query, result['answer'], latency_ms, False)
            
            stats = metrics.get_summary()
            stats_data = None
            if stats:
                stats_data = {
                    "avg_perplexity": stats.get('средняя_perplexity', 0),
                    "avg_relevance": stats.get('средняя_relevance', 0),
                    "avg_latency": stats.get('средняя_задержка_мс', 0),
                    "total_queries": stats.get('всего_запросов', 0),
                    "avg_completeness": stats.get('средняя_полнота', 0),
                    "avg_accuracy": stats.get('средняя_точность', 0),
                    "avg_clarity": stats.get('средняя_ясность', 0),
                    "avg_overall": stats.get('средняя_общая_оценка', 0)
                }
            
            response = {
                "thinking": result['thinking'],
                "answer": result['answer'],
                "latency": f"{latency_ms:.0f}",
                "stats": stats_data
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


def run():
    port = 8000
    server = HTTPServer(('127.0.0.1', port), Handler)
    print("\n" + "="*50)
    print("Сервер запущен")
    print("="*50)
    print(f"Откройте: http://127.0.0.1:{port}")
    print("Для остановки нажмите Ctrl+C")
    print("="*50 + "\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")


if __name__ == "__main__":
    run()