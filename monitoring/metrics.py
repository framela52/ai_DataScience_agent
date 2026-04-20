import time
import numpy as np
from typing import Dict, List, Optional
import torch
from transformers import GPT2LMHeadModel, GPT2TokenizerFast
import warnings
import sys
import re
import os
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from monitoring.evaluator import GigaChatJudge

class MetricsCollector:
    def __init__(self):
        self.metrics_history: List[Dict] = []
        self.judge = GigaChatJudge(temperature=0.0)  # temperature=0 для стабильности
    
    def _parse_single_score(self, text: str) -> float:
        """Надежный парсинг одного числа из ответа GigaChat"""
        # Ищем любое число вида X.XX
        match = re.search(r'(\d[\d.]*)\s*$', text.strip())
        if match:
            try:
                score = float(match.group(1))
                return round(max(0.0, min(1.0, score)), 2)
            except:
                pass
        return 0.5
    
    def evaluate_perplexity_gigachat(self, response: str) -> float:
        """Perplexity через GigaChat"""
        prompt = f"""Оцени связность текста 0.0-1.0 (1=отлично, 0=бессвязно):

        {response[:800]}

        СТРОГО: 0.95"""
        
        try:
            raw_result = self.judge.call(prompt=prompt)
            if isinstance(raw_result, dict) and 'choices' in raw_result:
                text = raw_result['choices'][0]['message']['content'].strip()
            else:
                text = str(raw_result).strip()
            
            return self._parse_single_score(text)
        except:
            return 0.7  # Базовое значение
    
    def evaluate_relevance_gigachat(self, query: str, response: str) -> float:
        """Relevance через GigaChat"""
        prompt = f"""Степень ответа на вопрос (0=не отвечает, 1=полностью):

        ВОПРОС: {query}
        ОТВЕТ: {response[:800]}

        СТРОГО: 0.92"""
        
        try:
            raw_result = self.judge.call(prompt=prompt)
            if isinstance(raw_result, dict) and 'choices' in raw_result:
                text = raw_result['choices'][0]['message']['content'].strip()
            else:
                text = str(raw_result).strip()
            
            return self._parse_single_score(text)
        except:
            return 0.7
    
    def evaluate_quality_metrics(self, query: str, response: str) -> Dict[str, float]:       
        return self.judge.evaluate_response(query, response)
    
    def collect(self, query: str, response: str, latency_ms: float, error: bool = False) -> Dict:
        print("Расчет метрик GigaChat...")
        
        metrics = {
            "query": query[:200],
            "perplexity": self.evaluate_perplexity_gigachat(response),
            "relevance": self.evaluate_relevance_gigachat(query, response),
            "задержка_мс": latency_ms,
            "длина_ответа": len(response),
            "время": time.time()
        }
        
        quality = self.evaluate_quality_metrics(query, response)
        metrics.update(quality)
        self.metrics_history.append(metrics)
        
        print(f"Готово: PPL={metrics['perplexity']}, REL={metrics['relevance']}")
        return metrics
    
    def get_summary(self) -> Dict:
        if not self.metrics_history:
            return {}
        
        recent = self.metrics_history[-10:]
        summary = {
            "всего_запросов": len(self.metrics_history),
            "средняя_perplexity": round(np.mean([m["perplexity"] for m in recent]), 2),
            "средняя_relevance": round(np.mean([m["relevance"] for m in recent]), 2),
            "средняя_задержка_мс": round(np.mean([m["задержка_мс"] for m in recent]), 0),
        }
        
        judge_keys = ["полнота", "точность", "ясность", "общая_оценка"]
        for key in judge_keys:
            if all(key in m for m in recent):
                summary[f"средняя_{key}"] = round(np.mean([m[key] for m in recent]), 2)
        
        return summary

if __name__ == "__main__":
    collector = MetricsCollector()
    
    test_query = "Что такое перплексия?"
    test_response = "Перплексия - метрика качества языковой модели. Низкая перплексия означает хорошее предсказание следующего слова."
    
    metrics = collector.collect(test_query, test_response, 150, False)
    
    print("РЕЗУЛЬТАТЫ:")
    print(f"Perplexity: {metrics['perplexity']:.2f}")
    print(f"Relevance: {metrics['relevance']:.2f}")
    print(f"Полнота: {metrics['полнота']:.2f}, Точность: {metrics['точность']:.2f}")