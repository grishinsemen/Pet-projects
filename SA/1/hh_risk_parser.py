"""
HeadHunter Risk/AML Analyst Vacancy Parser v2
Более точный парсер вакансий по рискам и AML
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

def get_vacancies(text, area=1, pages=10):
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
            print(f"  Страница {page + 1}: {len(data['items'])} вакансий")
            
            if page >= data.get('pages', 0) - 1:
                break
                
            time.sleep(0.25)
            
        except requests.RequestException as e:
            print(f"Ошибка: {e}")
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

def extract_risk_requirements(description):
    requirements = []
    
    keywords = [
        # AML/KYC/Compliance
        (r'aml', 'AML'),
        (r'kyc', 'KYC'),
        (r'kyb', 'KYB'),
        (r'cft', 'ПОД/ФТ'),
        (r'под/фт', 'ПОД/ФТ'),
        (r'fatf', 'FATF'),
        (r'115-фз', '115-ФЗ'),
        (r'легализаци\w*', 'ПОД (легализация)'),
        (r'отмывани\w*', 'ПОД (отмывание)'),
        (r'финансирован\w* террор\w*', 'ФТ'),
        (r'комплаенс|compliance', 'Compliance'),
        (r'fraud|фрод', 'Fraud/Фрод'),
        (r'антифрод', 'Антифрод'),
        (r'pep|публичн\w* должностн\w*', 'PEP'),
        (r'санкци\w*|sanctions', 'Санкции'),
        (r'росфинмониторинг', 'Росфинмониторинг'),
        (r'внутренн\w* контрол\w*', 'Внутренний контроль'),
        (r'due diligence', 'Due Diligence'),
        
        # Типы рисков
        (r'кредитн\w* риск\w*|credit risk', 'Кредитный риск'),
        (r'операционн\w* риск\w*', 'Операционный риск'),
        (r'рыночн\w* риск\w*|market risk', 'Рыночный риск'),
        (r'ликвидност\w*|liquidity', 'Риск ликвидности'),
        (r'репутационн\w* риск\w*', 'Репутационный риск'),
        (r'правов\w* риск\w*', 'Правовой риск'),
        (r'риск-менеджмент|risk management', 'Риск-менеджмент'),
        (r'\bvar\b|value at risk', 'VaR'),
        (r'стресс-тест\w*|stress test', 'Стресс-тестирование'),
        (r'basel|базель', 'Basel/Базель'),
        (r'\birb\b', 'IRB-подход'),
        (r'\bpd\b', 'PD (вероятность дефолта)'),
        (r'\blgd\b', 'LGD'),
        (r'\bead\b', 'EAD'),
        
        # Инструменты
        (r'\bsql\b', 'SQL'),
        (r'python', 'Python'),
        (r'\bsas\b', 'SAS'),
        (r'\br\b(?=\s|,|$)', 'R'),
        (r'excel', 'Excel'),
        (r'power\s?bi', 'Power BI'),
        (r'tableau', 'Tableau'),
        (r'scoring|скоринг', 'Скоринг'),
        (r'машинн\w* обучен\w*|machine learning', 'ML'),
        (r'моделирован\w*', 'Моделирование'),
        
        # Банковские знания
        (r'мсфо|ifrs', 'МСФО/IFRS'),
        (r'gaap', 'GAAP'),
        (r'внутренн\w* аудит\w*', 'Внутренний аудит'),
        
        # Сертификаты
        (r'\bcfa\b', 'CFA'),
        (r'\bfrm\b', 'FRM'),
        (r'\bcams\b', 'CAMS'),
        
        # Образование
        (r'высшее образовани\w*', 'Высшее образование'),
        (r'экономическ\w* образовани\w*', 'Экономическое образование'),
        (r'финансов\w* образовани\w*', 'Финансовое образование'),
        (r'юридическ\w* образовани\w*', 'Юридическое образование'),
        
        # Языки
        (r'английск\w* язык\w*|english', 'Английский язык'),
    ]
    
    description_lower = description.lower()
    
    for pattern, label in keywords:
        if re.search(pattern, description_lower, re.IGNORECASE):
            requirements.append(label)
    
    return list(set(requirements))

def extract_key_skills(vacancy_details):
    skills = []
    if vacancy_details and 'key_skills' in vacancy_details:
        skills = [skill['name'] for skill in vacancy_details['key_skills']]
    return skills

def analyze_vacancies(vacancies, max_details=100, filter_titles=None):
    all_skills = []
    all_requirements = []
    salary_data = []
    experience_data = []
    titles = []
    
    count = 0
    
    for i, vacancy in enumerate(vacancies):
        if count >= max_details:
            break
            
        # Фильтр по названию если нужно
        if filter_titles:
            title_lower = vacancy['name'].lower()
            if not any(f in title_lower for f in filter_titles):
                continue
        
        count += 1
        
        if count % 20 == 0:
            print(f"  Обработано: {count}/{max_details}")
        
        titles.append(vacancy['name'])
        
        details = get_vacancy_details(vacancy['id'])
        
        if details:
            skills = extract_key_skills(details)
            all_skills.extend(skills)
            
            description = clean_html(details.get('description', ''))
            requirements = extract_risk_requirements(description)
            all_requirements.extend(requirements)
            
            salary = details.get('salary')
            if salary and salary.get('from'):
                salary_data.append({
                    'from': salary.get('from'),
                    'to': salary.get('to'),
                    'currency': salary.get('currency')
                })
            
            exp = details.get('experience', {}).get('name')
            if exp:
                experience_data.append(exp)
        
        time.sleep(0.1)
    
    return {
        'skills': Counter(all_skills),
        'requirements': Counter(all_requirements),
        'salary': salary_data,
        'experience': Counter(experience_data),
        'titles': Counter(titles),
        'total_analyzed': count
    }

def print_results(analysis, name):
    print("\n" + "="*70)
    print(f"РЕЗУЛЬТАТЫ: {name}")
    print("="*70)
    print(f"Проанализировано вакансий: {analysis['total_analyzed']}")
    
    # Названия
    print("\n--- ПОПУЛЯРНЫЕ НАЗВАНИЯ ВАКАНСИЙ ---")
    for title, count in analysis['titles'].most_common(10):
        print(f"  {count:2} | {title[:60]}")
    
    # Ключевые навыки
    print("\n--- КЛЮЧЕВЫЕ НАВЫКИ (из тегов HH) ---")
    for skill, count in analysis['skills'].most_common(20):
        bar = "█" * min(count, 20)
        print(f"  {skill:40} | {count:2} | {bar}")
    
    # Требования
    print("\n--- ТРЕБОВАНИЯ ИЗ ОПИСАНИЙ ---")
    for req, count in analysis['requirements'].most_common(25):
        bar = "█" * min(count, 20)
        print(f"  {req:40} | {count:2} | {bar}")
    
    # Опыт
    print("\n--- ТРЕБУЕМЫЙ ОПЫТ ---")
    for exp, count in analysis['experience'].most_common():
        pct = count / max(analysis['total_analyzed'], 1) * 100
        print(f"  {exp:40} | {count:2} ({pct:.0f}%)")
    
    # Зарплаты
    if analysis['salary']:
        print("\n--- ЗАРПЛАТЫ (RUB) ---")
        rub = [s for s in analysis['salary'] if s['currency'] == 'RUR']
        if rub:
            from_vals = [s['from'] for s in rub if s['from']]
            to_vals = [s['to'] for s in rub if s['to']]
            if from_vals:
                print(f"  Средняя 'от': {sum(from_vals) // len(from_vals):,} ₽")
            if to_vals:
                print(f"  Средняя 'до': {sum(to_vals) // len(to_vals):,} ₽")
            print(f"  Вакансий с зп: {len(rub)}")

def save_results(analysis, filename):
    results = {
        'skills': dict(analysis['skills'].most_common(40)),
        'requirements': dict(analysis['requirements'].most_common(40)),
        'experience': dict(analysis['experience']),
        'titles': dict(analysis['titles'].most_common(15)),
        'total_analyzed': analysis['total_analyzed']
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nСохранено: {filename}")

def main():
    all_results = {}
    
    # 1. AML/Compliance специалисты
    print("\n" + "="*70)
    print("ПОИСК #1: AML / Compliance / ПОД/ФТ")
    print("="*70)
    
    vacancies1 = get_vacancies(
        text='NAME:(AML OR "ПОД/ФТ" OR комплаенс OR compliance OR "финансовый мониторинг")',
        area=1,
        pages=5
    )
    
    if vacancies1:
        analysis1 = analyze_vacancies(vacancies1, max_details=80)
        print_results(analysis1, "AML / Compliance")
        save_results(analysis1, "hh_aml_results.json")
        all_results['aml'] = analysis1
    
    # 2. Риск-аналитики
    print("\n" + "="*70)
    print("ПОИСК #2: Риск-аналитик / Риск-менеджер")
    print("="*70)
    
    vacancies2 = get_vacancies(
        text='NAME:(риск аналитик OR риск-аналитик OR риск-менеджер OR "risk analyst" OR "risk manager")',
        area=1,
        pages=5
    )
    
    if vacancies2:
        analysis2 = analyze_vacancies(vacancies2, max_details=80)
        print_results(analysis2, "Риск-аналитик")
        save_results(analysis2, "hh_risk_analyst_results.json")
        all_results['risk'] = analysis2
    
    # 3. Антифрод
    print("\n" + "="*70)
    print("ПОИСК #3: Антифрод / Fraud Analyst")
    print("="*70)
    
    vacancies3 = get_vacancies(
        text='NAME:(антифрод OR fraud OR фрод)',
        area=1,
        pages=5
    )
    
    if vacancies3:
        analysis3 = analyze_vacancies(vacancies3, max_details=50)
        print_results(analysis3, "Антифрод")
        save_results(analysis3, "hh_antifraud_results.json")
        all_results['antifraud'] = analysis3
    
    # 4. Кредитный риск
    print("\n" + "="*70)
    print("ПОИСК #4: Кредитный риск / Скоринг")
    print("="*70)
    
    vacancies4 = get_vacancies(
        text='NAME:("кредитный риск" OR скоринг OR scoring OR "credit risk")',
        area=1,
        pages=5
    )
    
    if vacancies4:
        analysis4 = analyze_vacancies(vacancies4, max_details=50)
        print_results(analysis4, "Кредитный риск")
        save_results(analysis4, "hh_credit_risk_results.json")
        all_results['credit_risk'] = analysis4
    
    # Общая статистика
    print("\n\n" + "="*70)
    print("ИТОГОВАЯ СТАТИСТИКА ПО ВСЕМ РИСК-НАПРАВЛЕНИЯМ")
    print("="*70)
    
    combined_skills = Counter()
    combined_requirements = Counter()
    total_count = 0
    
    for name, analysis in all_results.items():
        combined_skills.update(analysis['skills'])
        combined_requirements.update(analysis['requirements'])
        total_count += analysis['total_analyzed']
    
    print(f"\nВсего проанализировано: {total_count} вакансий")
    
    print("\n>>> ТОП-25 НАВЫКОВ ПО ВСЕМ НАПРАВЛЕНИЯМ <<<")
    for skill, count in combined_skills.most_common(25):
        bar = "█" * min(count, 25)
        print(f"  {skill:45} | {count:3} | {bar}")
    
    print("\n>>> ТОП-30 ТРЕБОВАНИЙ ПО ВСЕМ НАПРАВЛЕНИЯМ <<<")
    for req, count in combined_requirements.most_common(30):
        bar = "█" * min(count, 25)
        print(f"  {req:45} | {count:3} | {bar}")
    
    # Сохраняем общую статистику
    combined_results = {
        'skills': dict(combined_skills.most_common(50)),
        'requirements': dict(combined_requirements.most_common(50)),
        'total_analyzed': total_count
    }
    
    with open('hh_risk_combined_results.json', 'w', encoding='utf-8') as f:
        json.dump(combined_results, f, ensure_ascii=False, indent=2)
    
    print("\n\nСохранено: hh_risk_combined_results.json")

if __name__ == "__main__":
    main()
