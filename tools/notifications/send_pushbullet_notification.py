
import requests, os
from dotenv import load_dotenv

load_dotenv('C:/giwanos/config/.env')

def send_pushbullet_alert(body, title='VELOS 시스템 알림'):
    headers = {
        'Access-Token': os.getenv('NOTIFICATION_TOKEN'),
        'Content-Type': 'application/json'
    }
    data = {'type': 'note', 'title': title, 'body': body}
    requests.post(os.getenv('MOBILE_NOTIFICATION_URL'), json=data, headers=headers)
