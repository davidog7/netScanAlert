import requests
import configparser

class TelegramNotifier:
    def __init__(self, config_file='config/telegram.conf'):
        config = configparser.ConfigParser()
        config.read(config_file)
        
        self.bot_token = config.get('telegram', 'bot_token', fallback='')
        self.chat_id = config.get('telegram', 'chat_id', fallback='')
    
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
        
        try:
            response = requests.post(url, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Error enviando alerta: {e}")
            return False