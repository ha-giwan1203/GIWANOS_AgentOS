
import json
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

FEEDBACK_PATH = 'C:/giwanos/data/reports/evaluation_feedback.json'
JUDGMENT_RULES_PATH = 'C:/giwanos/config/judgment_rules.json'

def load_feedback():
    with open(FEEDBACK_PATH, 'r', encoding='utf-8') as file:
        feedback = json.load(file)
    logging.info('Loaded latest evaluation feedback.')
    return feedback

def load_judgment_rules():
    with open(JUDGMENT_RULES_PATH, 'r', encoding='utf-8') as file:
        rules = json.load(file)
    
    # 키 이름 'name'으로 수정하여 리스트를 딕셔너리로 변환
    if isinstance(rules, list):
        rules = {item['name']: item['value'] for item in rules}

    logging.info('Loaded current judgment rules.')
    return rules

def adjust_rules_based_on_feedback(feedback, rules):
    disk_usage = feedback.get('disk_usage_percent', 0)
    
    if disk_usage > 85:
        rules['disk_cleanup_threshold_days'] = max(1, rules.get('disk_cleanup_threshold_days', 3) - 1)
        logging.info('Disk usage high; reduced cleanup threshold days.')
    elif disk_usage < 70:
        rules['disk_cleanup_threshold_days'] = min(7, rules.get('disk_cleanup_threshold_days', 3) + 1)
        logging.info('Disk usage low; increased cleanup threshold days.')
    
    cpu_usage = feedback.get('cpu_usage_percent', 0)
    memory_usage = feedback.get('memory_usage_percent', 0)
    
    rules['cpu_usage_limit'] = np.clip(90 - cpu_usage / 2, 70, 90)
    rules['memory_usage_limit'] = np.clip(1200 - memory_usage * 5, 500, 1200)
    
    logging.info(f'Adjusted CPU limit: {rules["cpu_usage_limit"]}%, Memory limit: {rules["memory_usage_limit"]}MB')

    return rules

def save_updated_rules(rules):
    with open(JUDGMENT_RULES_PATH, 'w', encoding='utf-8') as file:
        json.dump(rules, file, indent=4)
    logging.info('Judgment rules updated and saved successfully.')

def main():
    feedback = load_feedback()
    rules = load_judgment_rules()
    updated_rules = adjust_rules_based_on_feedback(feedback, rules)
    save_updated_rules(updated_rules)

if __name__ == "__main__":
    main()
