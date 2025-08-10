"""Daily OpenAI usage cost logger for VELOS."""
import openai, datetime, pathlib, os, json

BASE_DIR = pathlib.Path(__file__).resolve().parents[3]
LOG_FILE = BASE_DIR / 'data' / 'logs' / 'system_cost.log'
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

openai.api_key = os.getenv('OPENAI_API_KEY')

def log_cost():
    try:
        usage = openai.api_usage.retrieve()
        line = f"{datetime.date.today()} | {usage['total_usage_usd']}"
        with LOG_FILE.open('a', encoding='utf-8') as f:
            f.write(line + '\n')
        print('Logged cost:', line)
    except Exception as e:
        print('Cost logging failed:', e)

if __name__ == '__main__':
    log_cost()


