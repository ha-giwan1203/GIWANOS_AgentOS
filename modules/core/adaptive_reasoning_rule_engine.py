
import json
import psutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

JUDGMENT_RULES_PATH = 'C:/giwanos/config/judgment_rules.json'

class RuleEngine:
    def __init__(self, rule_file):
        with open(rule_file, 'r', encoding='utf-8') as f:
            self.rules = json.load(f)

    def get_applicable_rules(self, system_conditions):
        applicable_rules = []
        for rule in self.rules:
            conditions_met = True
            for cond_key, cond_val in rule["conditions"].items():
                system_value = system_conditions.get(cond_key, None)
                if system_value is None:
                    conditions_met = False
                    break
                if isinstance(cond_val, (int, float)) and system_value < cond_val:
                    conditions_met = False
                    break
            if conditions_met:
                applicable_rules.append(rule)
        return applicable_rules

def get_current_system_conditions():
    return {
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    }

def execute_actions(actions):
    for action in actions:
        logging.info(f'Action: {action["action"]}, Description: {action["description"]}')
        # 실제 Action 구현 가능

def evaluate_rules(engine):
    conditions = get_current_system_conditions()
    logging.info(f'Current system conditions: {conditions}')
    rules = engine.get_applicable_rules(conditions)
    
    if not rules:
        logging.info('No applicable rules found for the current system conditions.')
        return
    
    for rule in rules:
        logging.info(f'Executing rule: {rule["id"]}')
        execute_actions(rule["actions"])

def main():
    engine = RuleEngine(JUDGMENT_RULES_PATH)
    evaluate_rules(engine)

if __name__ == "__main__":
    main()
