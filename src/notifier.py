import os
import requests
import time
import logging
from typing import Dict
from pathlib import Path
from dotenv import load_dotenv

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TelegramNotifier:
    def __init__(self):
        """Inicializa el notificador con configuración desde variables de entorno"""
        # Cargar variables de entorno
        env_path = Path(__file__).parent.parent / "config" / ".env"
        load_dotenv(dotenv_path=env_path)
        
        # Configuración esencial
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Configuración opcional
        self.timeout = int(os.getenv('TELEGRAM_TIMEOUT', '10'))
        self.max_retries = int(os.getenv('TELEGRAM_RETRIES', '3'))
        self.retry_delay = int(os.getenv('TELEGRAM_RETRY_DELAY', '2'))
        
        # Plantilla de mensaje configurable
        self.alert_template = os.getenv(
            'ALERT_MESSAGE',
            '⚠️ **Nuevo dispositivo detectado**\n'
            '▸ MAC: `{mac}`\n'
            '▸ IP: `{ip}`\n'
            '▸ Fabricante: `{vendor}`\n'
            '▸ Hora: `{timestamp}`'
        )

    def _validate_config(self) -> bool:
        """Valida que la configuración sea correcta"""
        if not self.bot_token or not self.chat_id:
            logging.error("Configuración incompleta. Se requieren TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID")
            return False
        return True

    def _format_message(self, device_info: Dict) -> str:
        """Formatea el mensaje de alerta usando la plantilla"""
        try:
            return self.alert_template.format(
                mac=device_info.get('mac', 'DESCONOCIDO'),
                ip=device_info.get('ip', 'DESCONOCIDO'),
                vendor=device_info.get('vendor', 'DESCONOCIDO'),
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
            )
        except KeyError as e:
            logging.error(f"Falta clave en device_info: {str(e)}")
            return "⚠️ Nuevo dispositivo detectado (formato incorrecto)"

    def send_alert(self, device_info: Dict) -> bool:
        """Envía notificación a Telegram con mejor manejo de errores"""
        if not self._validate_config():
            logging.error("Configuración de Telegram incompleta")
            return False

        try:
            message = self._format_message(device_info)
            if not message:
                logging.error("No se pudo formatear el mensaje")
                return False

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }

            for attempt in range(1, self.max_retries + 1):
                try:
                    response = requests.post(
                        url,
                        json=payload,
                        timeout=self.timeout
                    )
                    
                    response.raise_for_status()  # Lanza excepción para códigos 4XX/5XX
                    
                    logging.info(f"Notificación enviada: {device_info.get('mac')}")
                    return True
                    
                except requests.exceptions.RequestException as e:
                    error_msg = f"Intento {attempt}: Error al enviar - "
                    if hasattr(e, 'response') and e.response:
                        error_msg += f"HTTP {e.response.status_code}: {e.response.text}"
                    else:
                        error_msg += str(e)
                    logging.error(error_msg)
                    
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay * attempt)
                        
            logging.error(f"Fallo después de {self.max_retries} intentos")
            return False
            
        except Exception as e:
            logging.error(f"Error inesperado al enviar alerta: {str(e)}")
            return False  
    def test_connection(self) -> bool:
        """Prueba la conexión con la API de Telegram"""
        if not self._validate_config():
            return False

        try:
            response = requests.get(
                f"https://api.telegram.org/bot{self.bot_token}/getMe",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                bot_info = response.json()
                logging.info(f"Conexión exitosa con @{bot_info['result']['username']}")
                return True
                
            error_msg = response.json().get('description', 'Error desconocido')
            logging.error(f"Error de API: {error_msg}")
            return False
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error de conexión: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Error inesperado: {str(e)}")
            return False


if __name__ == "__main__":
    # Prueba de funcionamiento
    print("=== Prueba de TelegramNotifier ===")
    notifier = TelegramNotifier()
    
    if notifier.test_connection():
        print("\nProbando envío de mensaje...")
        test_device = {
            'mac': '00:11:22:33:44:55',
            'ip': '192.168.1.100',
            'vendor': 'Fabricante de prueba'
        }
        if notifier.send_alert(test_device):
            print("✅ Prueba exitosa! Revisa tu Telegram")
        else:
            print("❌ Fallo al enviar. Revisa los logs")
    else:
        print("❌ Conexión fallida. Verifica tu configuración")