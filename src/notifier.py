   import os
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

class TelegramNotifier:
    def __init__(self):
        # Cargar variables de entorno
        load_dotenv()
        
        # Configuración básica
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.log_level = os.getenv('LOG_LEVEL', 'warning').lower()
        self.alert_message = os.getenv('ALERT_MESSAGE', '⚠️ ALERTA: Nuevo dispositivo detectado')
        
        # Configuración de conexión
        self.timeout = int(os.getenv('TELEGRAM_TIMEOUT', '10'))
        self.max_retries = int(os.getenv('TELEGRAM_RETRIES', '3'))
        self.retry_delay = int(os.getenv('TELEGRAM_RETRY_DELAY', '2'))

    def _should_log(self, level):
        """Determina si un mensaje debe ser logueado según el nivel configurado"""
        levels = {
            'debug': 0,
            'info': 1,
            'warning': 2,
            'error': 3
        }
        current_level = levels.get(self.log_level, 2)
        return levels.get(level, 0) >= current_level

    def _log(self, message, level='info'):
        """Registro de eventos interno"""
        if self._should_log(level):
            print(f"[{level.upper()}] {message}")

    def send_alert(self, device_info):
        """
        Envía una alerta a Telegram con información del dispositivo
        
        Args:
            device_info (dict): Diccionario con información del dispositivo
                Ejemplo: {'mac': '00:11:22:33:44:55', 'ip': '192.168.1.100', 'vendor': 'Vendor Name'}
        """
        if not self.bot_token or not self.chat_id:
            self._log("Configuración de Telegram incompleta en .env", 'error')
            return False

        # Formatear el mensaje
        message = self.alert_message.format(
            mac=device_info.get('mac', 'DESCONOCIDO'),
            ip=device_info.get('ip', 'DESCONOCIDO'),
            vendor=device_info.get('vendor', 'Fabricante desconocido'),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )

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
                    self._log(f"Alerta enviada correctamente: {message}", 'debug')
                    return True
                
                self._log(f"Error HTTP {response.status_code}: {response.text}", 'warning')
                
            except requests.exceptions.RequestException as e:
                self._log(f"Intento {attempt + 1} fallido: {str(e)}", 'warning')
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
            
            except Exception as e:
                self._log(f"Error inesperado: {str(e)}", 'error')
                break

        self._log(f"No se pudo enviar la alerta después de {self.max_retries} intentos", 'error')
        return False

    def test_connection(self):
        """Prueba la conexión con la API de Telegram"""
        if not self.bot_token or not self.chat_id:
            return False, "Configuración incompleta"
        
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{self.bot_token}/getMe",
                timeout=self.timeout
            )
            return response.status_code == 200, response.text
        except Exception as e:
            return False, str(e)

if __name__ == "__main__":
    # Prueba de funcionamiento
    notifier = TelegramNotifier()
    print("Probando conexión con Telegram...")
    success, message = notifier.test_connection()
    print(f"✅ Conexión exitosa" if success else f"❌ Error: {message}")
    
    if success:
        print("Enviando mensaje de prueba...")
        test_device = {
            'mac': '00:11:22:33:44:55',
            'ip': '192.168.1.100',
            'vendor': 'Fabricante de prueba'
        }
        notifier.send_alert(test_device)