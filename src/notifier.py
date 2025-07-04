import requests
import time
from pathlib import Path
import configparser

class TelegramNotifier:
    def __init__(self, config_file='config/telegram.conf'):
        self.max_retries = 3
        self.timeout = 15
        self.load_config(config_file)
    
    def load_config(self, config_file):
        config = configparser.ConfigParser()
        if Path(config_file).exists():
            config.read(config_file)
            self.bot_token = config.get('telegram', 'bot_token', fallback='')
            self.chat_id = config.get('telegram', 'chat_id', fallback='')
        else:
            self.bot_token = ''
            self.chat_id = ''
    
    def send_alert(self, message):
        if not self.bot_token or not self.chat_id:
            print("Configuración de Telegram no completa")
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url, 
                    json=payload, 
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return True
                else:
                    print(f"Error HTTP {response.status_code}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"Intento {attempt + 1} fallido: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)  # Espera progresiva
                    continue
                return False
        
        return False
    