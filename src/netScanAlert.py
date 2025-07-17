#!/usr/bin/env python3
import time
import logging
import os
import sys
import signal
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('netScanAlert.log'),
        logging.StreamHandler()
    ]
)

BASE_DIR = Path(__file__).parent.parent
ENV_PATH = BASE_DIR / "config" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class NetScanAlert:
    def __init__(self):
        """Inicializa el sistema de monitoreo"""
        self.running = False
        self.scan_interval = float(os.getenv('SCAN_INTERVAL', '100'))
        
        # Configurar manejo de señales
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        
        from inventory import FileInventory
        from scanner import NetworkScanner
        from notifier import TelegramNotifier
        
        self.inventory = FileInventory()
        self.scanner = NetworkScanner(self.inventory)
        self.notifier = TelegramNotifier()

    def _handle_signal(self, signum, frame):
        """Maneja señales de terminación"""
        self.running = False
        logging.info("Recibida señal de terminación, finalizando...")

    def load_network_config(self) -> List[Dict]:
        """Carga configuración de redes"""
        networks_file = BASE_DIR / "config" / "networks.txt"
        
        if not networks_file.exists():
            return [{'interface': 'eth0', 'network': '192.168.1.0/24'}]
        
        try:
            with open(networks_file, 'r') as f:
                configs = []
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if ':' in line:
                        interface, network = line.split(':', 1)
                        configs.append({
                            'interface': interface.strip(),
                            'network': network.strip()
                        })
                    else:
                        configs.append({
                            'interface': 'eth0',
                            'network': line.strip()
                        })
                return configs
        except Exception as e:
            logging.error(f"Error leyendo networks.txt: {str(e)}")
            return []

    def scan_networks(self) -> List[Dict]:
        """Escanea todas las redes configuradas"""
        network_configs = self.load_network_config()
        all_devices = []
        
        for config in network_configs:
            network = config['network']
            interface = config['interface']
            
            try:
                logging.info(f"\n{'='*50}")
                logging.info(f"Escaneando {network} en {interface}")
                
                devices = self.scanner.scan_network(network, interface)
                if devices:
                    logging.info(f"Dispositivos encontrados ({len(devices)}):")
                    for device in devices:
                        logging.info(f" - IP: {device['ip']} | MAC: {device['mac']}")
                    all_devices.extend(devices)
                else:
                    logging.warning("No se encontraron dispositivos")
                    
            except Exception as e:
                logging.error(f"Error escaneando {network}: {str(e)}")
        
        return all_devices

    def process_new_devices(self, devices: List[Dict]) -> None:
        """Procesa nuevos dispositivos con identificación única para remotos"""
        new_devices = []
        
        for device in devices:
            try:
                # Para dispositivos remotos sin MAC, usamos IP como identificador
                device_id = device['ip'] if device['mac'] == '00:00:00:00:00:00' else device['mac']
                
                if not self.inventory.device_exists(device_id):
                    try:
                        self.inventory.add_device(
                            mac=device['mac'],
                            ip=device['ip'],
                            vendor=device.get('vendor', 'Desconocido'),
                            os_info=device.get('os', 'unknown'),
                            name=device.get('name', '')
                        )
                        new_devices.append(device)
                        logging.info(f"Nuevo dispositivo registrado: {device['ip']}")
                    except Exception as e:
                        logging.error(f"Error registrando {device['ip']}: {str(e)}")
                        
            except Exception as e:
                logging.error(f"Error procesando dispositivo: {str(e)}")
                continue
        
        if new_devices:
            self._send_notifications(new_devices)
            
    def _send_notifications(self, devices: List[Dict]) -> None:
        """Envía notificaciones sobre nuevos dispositivos"""
        if not hasattr(self, 'notifier') or not self.notifier:
            return
            
        for device in devices:
            try:
                if not self.notifier.send_alert(device):
                    logging.warning(f"Fallo al notificar sobre {device['ip']}")
            except Exception as e:
                logging.error(f"Error enviando notificación: {str(e)}")

    def run(self):
        """Ejecuta el monitoreo continuo"""
        logging.info("Iniciando NetScanAlert")
        self.running = True
        
        try:
            while self.running:
                start_time = datetime.now()
                
                devices = self.scan_networks()
                self.process_new_devices(devices)
                
                elapsed = (datetime.now() - start_time).total_seconds()
                sleep_time = max(0, self.scan_interval - elapsed)
                
                if sleep_time > 0:
                    logging.info(f"Esperando {sleep_time:.1f} segundos...")
                    for _ in range(int(sleep_time * 10)):
                        if not self.running:
                            break
                        time.sleep(0.1)
                
        except Exception as e:
            logging.critical(f"Error crítico: {str(e)}")
        finally:
            logging.info("NetScanAlert detenido")

def main():
    """Función principal"""
    try:
        # Verificar estructura básica
        required_dirs = ['config', 'data']
        missing_dirs = [d for d in required_dirs if not (BASE_DIR / d).exists()]
        
        if missing_dirs:
            print(f"Error: Directorios faltantes: {', '.join(missing_dirs)}")
            print("Ejecute primero: python cli.py init")
            return
        
        # Iniciar aplicación
        NetScanAlert().run()
        
    except Exception as e:
        logging.critical(f"Error inicializando: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()