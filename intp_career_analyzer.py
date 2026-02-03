"""
HeadHunter Career Analyzer for INTP with Applied Informatics
Анализ вакансий для INTP с образованием "Прикладная информатика"
без сильного программирования, с гибридом
"""

import requests
import time
import re
from collections import Counter
from html import unescape
import json

def clean_html(html_text):
    if not html_text:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', html_text)
    clean = unescape(clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def get_vacancies(text, area=1, pages=5):
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
            
            if page >= data.get('pages', 0) - 1:
                break
                
            time.sleep(0.2)
            
        except requests.RequestException as e:
            print(f"  Ошибка: {e}")
            break
    
    return all_vacancies

def get_vacancy_details(vacancy_id):
    url = f"https://api.hh.ru/vacancies/{vacancy_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

def check_hybrid_remote(vacancy_details):
    """Проверяет возможность удалёнки/гибрида"""
    if not vacancy_details:
        return "Офис"
    
    schedule = vacancy_details.get('schedule', {})
    schedule_id = schedule.get('id', '')
    schedule_name = schedule.get('name', '')
    
    if 'remote' in schedule_id or 'удален' in schedule_name.lower():
        return "Удалёнка"
    
    # Проверяем описание на упоминание гибрида
    description = vacancy_details.get('description', '').lower()
    if 'гибрид' in description or 'hybrid' in description or 'удаленн' in description:
        return "Гибрид/Удалёнка"
    
    return "Офис"

def check_no_experience(vacancy_details):
    """Проверяет, подходит ли для джуна"""
    if not vacancy_details:
        return False
    
    exp = vacancy_details.get('experience', {})
    exp_id = exp.get('id', '')
    
    return exp_id in ['noExperience', 'between1And3']

def extract_coding_level(description):
    """Оценивает уровень требований к программированию"""
    description_lower = description.lower()
    
    heavy_coding = [
        r'разработ\w* программ\w*',
        r'написание кода',
        r'backend', r'frontend', r'fullstack',
        r'java developer', r'python developer',
        r'react', r'angular', r'vue',
        r'node\.js', r'django', r'flask',
        r'spring', r'microservices',
    ]
    
    light_coding = [
        r'sql', r'python', r'скрипт\w*',
        r'автоматизац\w*', r'парсинг',
    ]
    
    no_coding = [
        r'без программирован\w*',
        r'не требуется программирован\w*',
    ]
    
    for pattern in no_coding:
        if re.search(pattern, description_lower):
            return 0
    
    heavy_count = sum(1 for p in heavy_coding if re.search(p, description_lower))
    light_count = sum(1 for p in light_coding if re.search(p, description_lower))
    
    if heavy_count >= 2:
        return 3  # Heavy coding
    elif heavy_count == 1:
        return 2  # Medium coding
    elif light_count > 0:
        return 1  # Light coding/scripting
    return 0  # No coding

def analyze_role(vacancies, role_name, max_details=60):
    """Анализирует вакансии для конкретной роли"""
    all_skills = []
    all_requirements = []
    salary_data = []
    experience_data = []
    work_format = []
    coding_levels = []
    junior_count = 0
    hybrid_count = 0
    
    count = 0
    
    for vacancy in vacancies:
        if count >= max_details:
            break
        
        details = get_vacancy_details(vacancy['id'])
        
        if not details:
            continue
            
        count += 1
        
        # Ключевые навыки
        if 'key_skills' in details:
            skills = [s['name'] for s in details['key_skills']]
            all_skills.extend(skills)
        
        # Формат работы
        format_type = check_hybrid_remote(details)
        work_format.append(format_type)
        if format_type != "Офис":
            hybrid_count += 1
        
        # Junior-friendly
        if check_no_experience(details):
            junior_count += 1
        
        # Уровень кодинга
        description = clean_html(details.get('description', ''))
        coding = extract_coding_level(description)
        coding_levels.append(coding)
        
        # Зарплата
        salary = details.get('salary')
        if salary and salary.get('from') and salary.get('currency') == 'RUR':
            salary_data.append({
                'from': salary.get('from'),
                'to': salary.get('to')
            })
        
        # Опыт
        exp = details.get('experience', {}).get('name')
        if exp:
            experience_data.append(exp)
        
        time.sleep(0.1)
    
    # Статистика
    avg_coding = sum(coding_levels) / len(coding_levels) if coding_levels else 0
    
    return {
        'role': role_name,
        'total': len(vacancies),
        'analyzed': count,
        'skills': Counter(all_skills),
        'experience': Counter(experience_data),
        'salary': salary_data,
        'work_format': Counter(work_format),
        'junior_friendly': junior_count,
        'hybrid_remote': hybrid_count,
        'avg_coding_level': avg_coding,
    }

def print_role_results(result):
    """Выводит результаты для роли"""
    print(f"\n{'='*70}")
    print(f"📌 {result['role']}")
    print(f"{'='*70}")
    print(f"Вакансий найдено: {result['total']} | Проанализировано: {result['analyzed']}")
    
    # Метрики для INTP
    junior_pct = result['junior_friendly'] / result['analyzed'] * 100 if result['analyzed'] else 0
    hybrid_pct = result['hybrid_remote'] / result['analyzed'] * 100 if result['analyzed'] else 0
    coding = result['avg_coding_level']
    
    coding_text = "🟢 Минимальный" if coding < 1 else "🟡 Лёгкий (SQL/скрипты)" if coding < 2 else "🟠 Средний" if coding < 2.5 else "🔴 Высокий"
    
    print(f"\n🎯 МЕТРИКИ ДЛЯ INTP:")
    print(f"  • Без опыта/Junior: {result['junior_friendly']}/{result['analyzed']} ({junior_pct:.0f}%)")
    print(f"  • Гибрид/Удалёнка: {result['hybrid_remote']}/{result['analyzed']} ({hybrid_pct:.0f}%)")
    print(f"  • Уровень кодинга: {coding_text} ({coding:.1f}/3)")
    
    # Зарплаты
    if result['salary']:
        from_vals = [s['from'] for s in result['salary']]
        print(f"\n💰 Зарплата:")
        print(f"  • Средняя 'от': {sum(from_vals) // len(from_vals):,} ₽")
        print(f"  • Мин/Макс: {min(from_vals):,} - {max(from_vals):,} ₽")
    
    # Опыт
    print(f"\n📊 Требуемый опыт:")
    for exp, cnt in result['experience'].most_common():
        pct = cnt / result['analyzed'] * 100
        print(f"  • {exp}: {cnt} ({pct:.0f}%)")
    
    # Топ скиллы
    print(f"\n🛠️ Топ-15 навыков:")
    for skill, cnt in result['skills'].most_common(15):
        bar = "█" * min(cnt, 15)
        print(f"  {skill:40} | {cnt:2} | {bar}")
    
    return result

def calculate_intp_score(result):
    """Рассчитывает INTP-совместимость роли (0-100)"""
    score = 50  # Базовый балл
    
    # +20 за низкий кодинг
    coding = result['avg_coding_level']
    if coding < 1:
        score += 20
    elif coding < 2:
        score += 10
    elif coding >= 2.5:
        score -= 10
    
    # +15 за гибрид/удалёнку
    hybrid_pct = result['hybrid_remote'] / result['analyzed'] * 100 if result['analyzed'] else 0
    if hybrid_pct >= 30:
        score += 15
    elif hybrid_pct >= 15:
        score += 8
    
    # +15 за доступность джунам
    junior_pct = result['junior_friendly'] / result['analyzed'] * 100 if result['analyzed'] else 0
    if junior_pct >= 30:
        score += 15
    elif junior_pct >= 15:
        score += 8
    
    # +10 за аналитическую работу (INTP любит анализ)
    analytical_skills = ['аналитическое мышление', 'анализ данных', 'аналитика', 
                        'системное мышление', 'исследовани']
    skill_names = [s.lower() for s in result['skills'].keys()]
    analytical_count = sum(1 for a in analytical_skills if any(a in s for s in skill_names))
    if analytical_count >= 2:
        score += 10
    
    # +5 за хорошую зарплату
    if result['salary']:
        avg_salary = sum(s['from'] for s in result['salary']) / len(result['salary'])
        if avg_salary >= 150000:
            score += 5
    
    return min(100, max(0, score))

def main():
    print("="*70)
    print("🎯 АНАЛИЗ IT-ВАКАНСИЙ ДЛЯ INTP")
    print("   Прикладная информатика | Без опыта | Минимум кода | Гибрид")
    print("="*70)
    
    # Роли для анализа (подходящие для INTP без желания кодить)
    roles = [
        ('NAME:("бизнес аналитик" OR "бизнес-аналитик" OR "business analyst")', "Бизнес-аналитик"),
        ('NAME:("системный аналитик" OR "system analyst")', "Системный аналитик"),
        ('NAME:("продуктовый аналитик" OR "product analyst")', "Продуктовый аналитик"),
        ('NAME:(тестировщик OR QA OR "ручной тестировщик" OR "manual qa")', "QA/Тестировщик (ручной)"),
        ('NAME:("технический писатель" OR "technical writer" OR "tech writer")', "Технический писатель"),
        ('NAME:("аналитик данных" OR "data analyst") NOT NAME:(senior OR lead)', "Аналитик данных (Junior)"),
        ('NAME:("менеджер проектов" OR "project manager" OR PM) NOT NAME:(senior)', "Менеджер проектов"),
        ('NAME:(product owner OR "владелец продукта" OR PO)', "Product Owner"),
        ('NAME:("ux исследователь" OR "ux researcher" OR "user researcher")', "UX Researcher"),
        ('NAME:(пресейл OR presale OR "it консультант" OR "it-консультант")', "IT-Консультант/Presale"),
    ]
    
    all_results = []
    
    for search_query, role_name in roles:
        print(f"\n⏳ Загружаю: {role_name}...")
        
        vacancies = get_vacancies(search_query, area=1, pages=3)
        
        if not vacancies:
            print(f"  ❌ Вакансии не найдены")
            continue
        
        print(f"  ✓ Найдено {len(vacancies)} вакансий, анализирую...")
        
        result = analyze_role(vacancies, role_name, max_details=50)
        result['intp_score'] = calculate_intp_score(result)
        
        all_results.append(result)
        print_role_results(result)
    
    # Итоговый рейтинг
    print("\n\n" + "="*70)
    print("🏆 ИТОГОВЫЙ РЕЙТИНГ ДЛЯ INTP (сортировка по совместимости)")
    print("="*70)
    
    sorted_results = sorted(all_results, key=lambda x: x['intp_score'], reverse=True)
    
    print(f"\n{'Роль':<30} | Score | Вакансий | Джуны | Гибрид | Код")
    print("-"*70)
    
    for r in sorted_results:
        junior_pct = r['junior_friendly'] / r['analyzed'] * 100 if r['analyzed'] else 0
        hybrid_pct = r['hybrid_remote'] / r['analyzed'] * 100 if r['analyzed'] else 0
        coding = r['avg_coding_level']
        coding_icon = "🟢" if coding < 1 else "🟡" if coding < 2 else "🟠" if coding < 2.5 else "🔴"
        
        print(f"{r['role']:<30} | {r['intp_score']:>3}   | {r['total']:>5}    | {junior_pct:>3.0f}%  | {hybrid_pct:>3.0f}%   | {coding_icon}")
    
    # Сохраняем результаты
    save_data = []
    for r in sorted_results:
        save_data.append({
            'role': r['role'],
            'intp_score': r['intp_score'],
            'total_vacancies': r['total'],
            'junior_friendly_pct': r['junior_friendly'] / r['analyzed'] * 100 if r['analyzed'] else 0,
            'hybrid_remote_pct': r['hybrid_remote'] / r['analyzed'] * 100 if r['analyzed'] else 0,
            'coding_level': r['avg_coding_level'],
            'top_skills': dict(r['skills'].most_common(20)),
            'experience': dict(r['experience']),
        })
    
    with open('hh_intp_career_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Результаты сохранены в hh_intp_career_analysis.json")

if __name__ == "__main__":
    main()
