import os
import requests
import time
import logging
from typing import Dict, Optional
from ipaddress import ip_address
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
        load_dotenv()
        
        # Configuración esencial
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Configuración opcional con valores por defecto
        self.timeout = int(os.getenv('TELEGRAM_TIMEOUT', '10'))
        self.max_retries = int(os.getenv('TELEGRAM_RETRIES', '3'))
        self.retry_delay = int(os.getenv('TELEGRAM_RETRY_DELAY', '2'))
        self.log_level = os.getenv('LOG_LEVEL', 'info').lower()
        
        # Plantilla de mensaje configurable
        self.alert_template = os.getenv(
            'ALERT_MESSAGE',
            '⚠️ **Nuevo dispositivo detectado**\n'
            '▸ MAC: `{mac}`\n'
            '▸ IP: `{ip}`\n'
            '▸ Fabricante: `{vendor}`\n'
            '▸ Hora: `{timestamp}`'
        )

    def _log(self, message: str, level: str = 'info') -> None:
        """Registro de eventos interno con niveles de log"""
        if level == 'debug' and self.log_level not in ['debug']:
            return
        elif level == 'info' and self.log_level in ['warning', 'error']:
            return
        elif level == 'warning' and self.log_level == 'error':
            return
        
        getattr(logging, level)(message)

    def _sanitize_ip(self, ip_str: str) -> str:
        """Normaliza y valida una dirección IP para mostrar"""
        try:
            return str(ip_address(ip_str))
        except ValueError:
            self._log(f"IP inválida detectada: {ip_str}", 'warning')
            return ip_str  # Devuelve el original si no es IP válida

    def _format_message(self, device_info: Dict) -> str:
        """Formatea el mensaje de alerta usando la plantilla"""
        safe_ip = self._sanitize_ip(device_info.get('ip', 'DESCONOCIDO'))
        
        return self.alert_template.format(
            mac=device_info.get('mac', 'DESCONOCIDO'),
            ip=safe_ip,
            vendor=device_info.get('vendor', 'DESCONOCIDO'),
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
        )

    def test_connection(self) -> bool:
        """Prueba la conexión con la API de Telegram"""
        if not self.bot_token or not self.chat_id:
            self._log("Configuración de Telegram incompleta", 'error')
            return False

        try:
            response = requests.get(
                f"https://api.telegram.org/bot{self.bot_token}/getMe",
                timeout=self.timeout
            )
            if response.status_code == 200:
                self._log("Conexión con Telegram verificada", 'debug')
                return True
            
            self._log(f"Error en la API de Telegram: {response.text}", 'warning')
            return False
            
        except Exception as e:
            self._log(f"Error probando conexión: {str(e)}", 'error')
            return False

    def send_alert(self, device_info: Dict) -> bool:
        """
        Envía una notificación a Telegram sobre un nuevo dispositivo
        
        Args:
            device_info: Diccionario con información del dispositivo
                Debe contener: mac, ip, vendor
        
        Returns:
            bool: True si la notificación se envió correctamente
        """
        if not self.bot_token or not self.chat_id:
            self._log("No se puede enviar alerta - Configuración de Telegram incompleta", 'error')
            return False

        message = self._format_message(device_info)
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    json={
                        'chat_id': self.chat_id,
                        'text': message,
                        'parse_mode': 'Markdown',
                        'disable_web_page_preview': True
                    },
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    self._log(f"Alerta enviada: {device_info.get('mac')}", 'debug')
                    return True
                
                # Manejo de errores específicos de Telegram
                error_msg = response.json().get('description', 'Error desconocido')
                self._log(f"Error de Telegram (intento {attempt + 1}): {error_msg}", 'warning')
                
                # Backoff exponencial para reintentos
                time.sleep(self.retry_delay * (attempt + 1))
                
            except requests.exceptions.RequestException as e:
                self._log(f"Error de conexión (intento {attempt + 1}): {str(e)}", 'warning')
                time.sleep(self.retry_delay * (attempt + 1))
                continue
                
            except Exception as e:
                self._log(f"Error inesperado (intento {attempt + 1}): {str(e)}", 'error')
                break

        self._log(f"Fallo al enviar alerta después de {self.max_retries} intentos", 'error')
        return False

    def send_custom_message(self, text: str) -> bool:
        """Envía un mensaje personalizado a Telegram"""
        if not self.bot_token or not self.chat_id:
            self._log("Configuración incompleta para enviar mensaje", 'error')
            return False

        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={
                    'chat_id': self.chat_id,
                    'text': text,
                    'parse_mode': 'Markdown'
                },
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            self._log(f"Error enviando mensaje personalizado: {str(e)}", 'error')
            return False


if __name__ == "__main__":
    # Prueba de funcionamiento
    notifier = TelegramNotifier()
    
    print("=== Prueba de Notificador Telegram ===")
    print(f"Configuración cargada: {'✅' if notifier.bot_token and notifier.chat_id else '❌'}")
    
    if notifier.test_connection():
        print("✅ Conexión con Telegram exitosa")
        
        # Prueba de envío de alerta
        test_device = {
            'mac': '00:11:22:33:44:55',
            'ip': '192.168.1.100',
            'vendor': 'Fabricante de Prueba'
        }
        
        print("\nEnviando alerta de prueba...")
        if notifier.send_alert(test_device):
            print("✅ Alerta de prueba enviada correctamente")
        else:
            print("❌ Fallo al enviar alerta de prueba")
    else:
        print("❌ No se pudo conectar con Telegram")
        print("Verifica tu configuración en .env")