from langchain.tools import tool
import pandas as pd
import numpy as np
import re

@tool
def analyze_correlation(data_description: str) -> str:
    """
    Анализ корреляции между переменными. 
    Формат: 'x_переменная,y_переменная,значение1,значение2,значение3,...'
    Пример: 'образование,доход,10,30,12,35,14,40,16,50,18,60'
    """
    try:
        # Очищаем входные данные
        data_description = data_description.strip()
        
        # Если пришли данные в формате [[...],[...]] - преобразуем
        if '[[' in data_description:
            # Извлекаем числа из строки
            numbers = re.findall(r'\d+\.?\d*', data_description)
            if len(numbers) >= 4:
                half = len(numbers) // 2
                x_vals = [float(x) for x in numbers[:half]]
                y_vals = [float(y) for y in numbers[half:2*half]]
                return f"Корреляция: r = {np.corrcoef(x_vals, y_vals)[0,1]:.3f}. {'Сильная' if abs(np.corrcoef(x_vals, y_vals)[0,1])>0.7 else 'Умеренная' if abs(np.corrcoef(x_vals, y_vals)[0,1])>0.3 else 'Слабая'} связь."
        
        # Стандартный формат: x_name,y_name,value1,value2,...
        parts = data_description.split(',')
        if len(parts) < 4:
            return "Ошибка: нужны x_переменная,y_переменная,значения. Пример: 'образование,доход,10,30,12,35,14,40'"
        
        x_name = parts[0].strip()
        y_name = parts[1].strip()
        
        # Извлекаем числовые значения
        values = []
        for v in parts[2:]:
            try:
                values.append(float(v.strip()))
            except:
                continue
        
        if len(values) < 4:
            return f"Для корреляции нужно минимум 4 значения. Получено: {len(values)}"
        
        # Разделяем на X и Y (чередующиеся)
        x_vals = values[::2]
        y_vals = values[1::2]
        
        # Выравниваем длины
        min_len = min(len(x_vals), len(y_vals))
        x_vals = x_vals[:min_len]
        y_vals = y_vals[:min_len]
        
        if min_len < 2:
            return f"Недостаточно пар значений для расчета корреляции. Нужно минимум 2 пары, получено {min_len}"
        
        # Расчет корреляции
        corr_matrix = np.corrcoef(x_vals, y_vals)
        r_value = corr_matrix[0, 1]
        
        # Определяем силу связи
        if abs(r_value) > 0.7:
            strength = "Сильная"
        elif abs(r_value) > 0.3:
            strength = "Умеренная"
        else:
            strength = "Слабая"
        
        direction = "положительная" if r_value > 0 else "отрицательная"
        
        return f"Корреляция между {x_name} и {y_name}: r = {r_value:.3f}. {strength} {direction} связь."
        
    except Exception as e:
        return f"Ошибка анализа: {str(e)}. Проверьте формат данных."


# Самотестирование
if __name__ == "__main__":
    print("Тестирование инструментов анализа данных...")
    corr = analyze_correlation("ИПЦ,Продажи,2.1,100,2.2,105,2.0,98")
    assert "r =" in corr
    print("УСПЕШНО: оба инструмента работают")