#!/usr/bin/env python3
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import ipaddress
from inventory import FileInventory
from scanner import NetworkScanner
from notifier import TelegramNotifier

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('netScanAlert.log'),
        logging.StreamHandler()
    ]
)

class NetScanAlert:
    def __init__(self):
        """Inicializa el sistema de monitoreo de red"""
        self.inventory = FileInventory()
        self.scanner = NetworkScanner(self.inventory)
        self.notifier = TelegramNotifier()
        self.scan_interval = 300  # 5 minutos entre escaneos
        self.last_scan_time = None

    def load_network_ranges(self) -> List[str]:
        """Carga y valida los rangos de red a monitorear"""
        networks_file = Path('config/networks.txt')
        
        if not networks_file.exists():
            logging.warning("Archivo networks.txt no encontrado, usando red por defecto")
            return ['192.168.1.0/24']
        
        try:
            with open(networks_file, 'r') as f:
                networks = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            valid_networks = []
            for net in networks:
                try:
                    # Validar el formato de la red
                    network = ipaddress.ip_network(net, strict=False)
                    valid_networks.append(str(network))
                    logging.debug(f"Red válida cargada: {network}")
                except ValueError as e:
                    logging.warning(f"Red inválida en networks.txt: {net} - {str(e)}")
            
            return valid_networks if valid_networks else ['192.168.1.0/24']
        except Exception as e:
            logging.error(f"Error leyendo networks.txt: {str(e)}")
            return ['192.168.1.0/24']

    def scan_networks(self) -> List[Dict]:
        """Escanea todas las redes configuradas"""
        networks = self.load_network_ranges()
        devices = []
        
        for network in networks:
            try:
                logging.info(f"Escaneando red: {network}")
                devices.extend(self.scanner.scan_single_network(network))
            except Exception as e:
                logging.error(f"Error escaneando {network}: {str(e)}")
                continue
        
        return devices

    def process_new_devices(self, devices: List[Dict]) -> None:
        """Procesa los dispositivos detectados"""
        new_devices = []
        
        for device in devices:
            try:
                if not self.inventory.device_exists(device['mac']):
                    # Validar la IP antes de procesar
                    if not self.inventory.validate_ip(device['ip']):
                        logging.warning(f"IP inválida detectada: {device['ip']}")
                        continue
                    
                    self.inventory.add_device(**device)
                    new_devices.append(device)
                    logging.info(f"Nuevo dispositivo: {device['mac']} ({device['ip']})")
            except Exception as e:
                logging.error(f"Error procesando dispositivo: {str(e)}")
                continue
        
        # Notificar sobre nuevos dispositivos
        if new_devices and self.notifier:
            for device in new_devices:
                try:
                    if not self.notifier.send_alert(device):
                        logging.warning(f"Fallo al notificar sobre {device['mac']}")
                except Exception as e:
                    logging.error(f"Error enviando notificación: {str(e)}")

    def run(self):
        """Ejecuta el monitoreo continuo"""
        logging.info("Iniciando NetScanAlert")
        logging.info(f"Intervalo de escaneo: {self.scan_interval} segundos")
        
        try:
            while True:
                start_time = datetime.now()
                self.last_scan_time = start_time.isoformat()
                
                logging.info("Iniciando ciclo de escaneo...")
                devices = self.scan_networks()
                self.process_new_devices(devices)
                
                # Calcular tiempo de espera para el próximo escaneo
                elapsed = (datetime.now() - start_time).total_seconds()
                sleep_time = max(0, self.scan_interval - elapsed)
                
                logging.info(f"Ciclo completado. Esperando {sleep_time:.1f} segundos...")
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logging.info("Deteniendo NetScanAlert...")
        except Exception as e:
            logging.critical(f"Error crítico: {str(e)}")
            raise

def main():
    """Función principal"""
    try:
        # Verificar estructura básica
        required_dirs = ['config', 'data']
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                print(f"Error: Directorio '{dir_path}' no encontrado")
                print("Ejecute 'python cli.py init' primero")
                return
        
        # Iniciar aplicación
        app = NetScanAlert()
        app.run()
    except Exception as e:
        logging.critical(f"Error inicializando la aplicación: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()