"""
HeadHunter Vacancy Parser & Requirements Analyzer
Парсер вакансий HeadHunter с анализом требований
"""

import requests
import time
import re
from collections import Counter
from html import unescape
import json

def clean_html(html_text):
    """Удаляет HTML теги и очищает текст"""
    if not html_text:
        return ""
    # Удаляем HTML теги
    clean = re.sub(r'<[^>]+>', ' ', html_text)
    # Декодируем HTML entities
    clean = unescape(clean)
    # Нормализуем пробелы
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def get_vacancies(text="Системный аналитик", area=1, pages=10):
    """
    Получает вакансии с HeadHunter API
    area=1 - Москва
    """
    all_vacancies = []
    
    for page in range(pages):
        url = "https://api.hh.ru/vacancies"
        params = {
            "text": text,
            "area": area,
            "per_page": 100,
            "page": page
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('items'):
                break
                
            all_vacancies.extend(data['items'])
            print(f"Страница {page + 1}: получено {len(data['items'])} вакансий")
            
            # Проверяем, есть ли ещё страницы
            if page >= data.get('pages', 0) - 1:
                break
                
            time.sleep(0.25)  # Пауза между запросами
            
        except requests.RequestException as e:
            print(f"Ошибка при получении страницы {page}: {e}")
            break
    
    print(f"\nВсего найдено вакансий: {len(all_vacancies)}")
    return all_vacancies

def get_vacancy_details(vacancy_id):
    """Получает детальную информацию о вакансии"""
    url = f"https://api.hh.ru/vacancies/{vacancy_id}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка при получении вакансии {vacancy_id}: {e}")
        return None

def extract_requirements(description):
    """Извлекает требования из описания вакансии"""
    requirements = []
    
    # Ключевые слова и навыки для поиска
    keywords = [
        # Методологии и подходы
        r'agile', r'scrum', r'kanban', r'waterfall', r'lean',
        # Нотации и документация
        r'bpmn', r'uml', r'use[- ]?case', r'user[- ]?story', r'user stories',
        r'техническ\w* задани\w*', r'ТЗ', r'SRS', r'BRD', r'FRD',
        r'swagger', r'openapi', r'api[- ]?документ\w*',
        # Инструменты
        r'jira', r'confluence', r'miro', r'figma', r'visio', r'draw\.io', r'lucidchart',
        r'notion', r'trello', r'asana', r'youtrack',
        r'postman', r'insomnia', r'soapui',
        r'git', r'gitlab', r'github', r'bitbucket',
        # Базы данных и SQL
        r'sql', r'postgresql', r'mysql', r'oracle', r'mongodb', r'redis',
        r'clickhouse', r'elasticsearch',
        # Интеграции
        r'rest\s?api', r'soap', r'graphql', r'grpc', r'websocket',
        r'kafka', r'rabbitmq', r'activemq',
        r'json', r'xml', r'yaml',
        # Навыки
        r'python', r'java', r'javascript', r'c#', r'php',
        r'аналитическ\w* мышлен\w*', r'системн\w* мышлен\w*',
        r'коммуникаб\w*', r'коммуникатив\w*',
        r'презентац\w*', r'переговор\w*',
        r'английск\w* язык\w*', r'english',
        # Области знаний
        r'e-commerce', r'fintech', r'банк\w*', r'финанс\w*',
        r'erp', r'crm', r'1с', r'sap',
        r'bi', r'power\s?bi', r'tableau', r'superset',
        r'data\s?warehouse', r'dwh', r'etl',
        r'machine\s?learning', r'ml', r'data\s?science',
        r'микросервис\w*', r'microservice',
        r'облачн\w*', r'cloud', r'aws', r'azure', r'gcp',
        r'docker', r'kubernetes', r'k8s',
        # Опыт
        r'опыт\w* работ\w*', r'опыт от \d',
        r'высшее образовани\w*',
        r'техническ\w* образовани\w*',
    ]
    
    description_lower = description.lower()
    
    for keyword in keywords:
        if re.search(keyword, description_lower, re.IGNORECASE):
            # Нормализуем найденное слово
            match = re.search(keyword, description_lower, re.IGNORECASE)
            if match:
                found = match.group(0).strip()
                requirements.append(found.upper() if len(found) <= 4 else found.title())
    
    return requirements

def extract_key_skills(vacancy_details):
    """Извлекает ключевые навыки из API ответа"""
    skills = []
    if vacancy_details and 'key_skills' in vacancy_details:
        skills = [skill['name'] for skill in vacancy_details['key_skills']]
    return skills

def analyze_vacancies(vacancies, max_details=200):
    """Анализирует вакансии и собирает статистику по требованиям"""
    all_skills = []
    all_requirements = []
    salary_data = []
    experience_data = []
    
    print(f"\nАнализируем детали вакансий (до {max_details} шт.)...")
    
    for i, vacancy in enumerate(vacancies[:max_details]):
        if i % 20 == 0:
            print(f"Обработано: {i}/{min(len(vacancies), max_details)}")
        
        # Получаем детальную информацию
        details = get_vacancy_details(vacancy['id'])
        
        if details:
            # Ключевые навыки из API
            skills = extract_key_skills(details)
            all_skills.extend(skills)
            
            # Требования из описания
            description = clean_html(details.get('description', ''))
            requirements = extract_requirements(description)
            all_requirements.extend(requirements)
            
            # Зарплата
            salary = details.get('salary')
            if salary and salary.get('from'):
                salary_data.append({
                    'from': salary.get('from'),
                    'to': salary.get('to'),
                    'currency': salary.get('currency')
                })
            
            # Опыт
            exp = details.get('experience', {}).get('name')
            if exp:
                experience_data.append(exp)
        
        time.sleep(0.1)  # Пауза между запросами
    
    return {
        'skills': Counter(all_skills),
        'requirements': Counter(all_requirements),
        'salary': salary_data,
        'experience': Counter(experience_data),
        'total_analyzed': min(len(vacancies), max_details)
    }

def print_results(analysis):
    """Выводит результаты анализа"""
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТЫ АНАЛИЗА ВАКАНСИЙ СИСТЕМНОГО АНАЛИТИКА (МОСКВА)")
    print("="*60)
    
    print(f"\nПроанализировано вакансий: {analysis['total_analyzed']}")
    
    # Ключевые навыки (из API HeadHunter)
    print("\n" + "-"*60)
    print("КЛЮЧЕВЫЕ НАВЫКИ (из тегов HH, топ-30):")
    print("-"*60)
    for skill, count in analysis['skills'].most_common(30):
        bar = "█" * min(count // 2, 30)
        print(f"{skill:40} | {count:3} | {bar}")
    
    # Требования из описаний
    print("\n" + "-"*60)
    print("ТРЕБОВАНИЯ ИЗ ОПИСАНИЙ (топ-30):")
    print("-"*60)
    for req, count in analysis['requirements'].most_common(30):
        bar = "█" * min(count // 2, 30)
        print(f"{req:40} | {count:3} | {bar}")
    
    # Требуемый опыт
    print("\n" + "-"*60)
    print("ТРЕБУЕМЫЙ ОПЫТ:")
    print("-"*60)
    for exp, count in analysis['experience'].most_common():
        pct = count / analysis['total_analyzed'] * 100
        bar = "█" * int(pct // 2)
        print(f"{exp:40} | {count:3} ({pct:.1f}%) | {bar}")
    
    # Статистика по зарплатам
    if analysis['salary']:
        print("\n" + "-"*60)
        print("СТАТИСТИКА ПО ЗАРПЛАТАМ (RUB):")
        print("-"*60)
        rub_salaries = [s for s in analysis['salary'] if s['currency'] == 'RUR']
        if rub_salaries:
            from_values = [s['from'] for s in rub_salaries if s['from']]
            to_values = [s['to'] for s in rub_salaries if s['to']]
            
            if from_values:
                print(f"Минимальная 'от': {min(from_values):,} ₽")
                print(f"Максимальная 'от': {max(from_values):,} ₽")
                print(f"Средняя 'от': {sum(from_values) // len(from_values):,} ₽")
            if to_values:
                print(f"Средняя 'до': {sum(to_values) // len(to_values):,} ₽")
            print(f"Вакансий с указанной зарплатой: {len(rub_salaries)} из {analysis['total_analyzed']}")

def save_results(analysis, filename="hh_analysis_results.json"):
    """Сохраняет результаты в JSON файл"""
    results = {
        'skills': dict(analysis['skills'].most_common(50)),
        'requirements': dict(analysis['requirements'].most_common(50)),
        'experience': dict(analysis['experience']),
        'total_analyzed': analysis['total_analyzed']
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nРезультаты сохранены в {filename}")

def main():
    print("HeadHunter Vacancy Analyzer")
    print("Поиск: Системный аналитик, Москва")
    print("-" * 40)
    
    # Получаем вакансии
    vacancies = get_vacancies(
        text="Системный аналитик",
        area=1,  # Москва
        pages=10  # До 1000 вакансий
    )
    
    if not vacancies:
        print("Вакансии не найдены!")
        return
    
    # Анализируем
    analysis = analyze_vacancies(vacancies, max_details=200)
    
    # Выводим результаты
    print_results(analysis)
    
    # Сохраняем
    save_results(analysis)

if __name__ == "__main__":
    main()
