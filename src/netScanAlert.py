#!/usr/bin/env python3
import time
import logging
import os
import ipaddress
import sys
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

# Configuración de rutas - subimos un nivel para llegar a la raíz del proyecto
BASE_DIR = Path(__file__).parent.parent
ENV_PATH = BASE_DIR / "config" / ".env"

# Cargar variables de entorno
load_dotenv(dotenv_path=ENV_PATH)

class NetScanAlert:
    def __init__(self):
        """Inicializa el sistema de monitoreo de red"""
        # Cargar configuración desde .env con valores por defecto
        self.scan_interval = float(os.getenv('SCAN_INTERVAL', '300'))
        self.log_level = os.getenv('LOG_LEVEL', 'info').upper()
        
        # Configurar nivel de logging
        logging.getLogger().setLevel(self.log_level)
        
        # Inicializar componentes
        from inventory import FileInventory
        from scanner import NetworkScanner
        from notifier import TelegramNotifier
        
        self.inventory = FileInventory()
        self.scanner = NetworkScanner(self.inventory)
        self.notifier = TelegramNotifier()
        
        logging.info(f"Iniciando NetScanAlert (Intervalo: {self.scan_interval}s, Log: {self.log_level})")

    def load_network_config(self) -> List[Dict]:
        """Carga y valida la configuración de redes e interfaces a monitorear"""
        networks_file = BASE_DIR / "config" / "networks.txt"
        
        if not networks_file.exists():
            logging.warning("Archivo networks.txt no encontrado, usando configuración por defecto")
            return [{'interface': 'eth0', 'network': '192.168.1.0/24'}]
        
        try:
            with open(networks_file, 'r') as f:
                configs = []
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Formato: interfaz:red
                    if ':' in line:
                        interface, network = line.split(':', 1)
                        configs.append({
                            'interface': interface.strip(),
                            'network': network.strip()
                        })
                    else:
                        # Solo red, usamos interfaz por defecto
                        configs.append({
                            'interface': 'eth0',
                            'network': line.strip()
                        })
            
            # Validar las configuraciones
            valid_configs = []
            for config in configs:
                try:
                    ipaddress.ip_network(config['network'], strict=False)
                    valid_configs.append(config)
                    logging.debug(f"Configuración válida cargada: {config}")
                except ValueError as e:
                    logging.warning(f"Red inválida en networks.txt: {config['network']} - {str(e)}")
            
            return valid_configs if valid_configs else [{'interface': 'eth0', 'network': '192.168.1.0/24'}]
        except Exception as e:
            logging.error(f"Error leyendo networks.txt: {str(e)}")
            return [{'interface': 'eth0', 'network': '192.168.1.0/24'}]

    def scan_networks(self) -> List[Dict]:
        """Escanea todas las redes configuradas"""
        network_configs = self.load_network_config()
        devices = []
        
        for config in network_configs:
            try:
                logging.info(f"Escaneando red: {config['network']} en interfaz {config['interface']}")
                devices.extend(self.scanner.scan_network(
                    network=config['network'],
                    interface=config['interface']
                ))
            except Exception as e:
                logging.error(f"Error escaneando {config['network']}: {str(e)}")
                continue
        
        return devices

    def process_new_devices(self, devices: List[Dict]) -> None:
        """Procesa los dispositivos detectados"""
        new_devices = []
        
        for device in devices:
            try:
                if not self.inventory.device_exists(device['mac']):
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
        logging.info(f"Configuración cargada desde: {ENV_PATH}")
        logging.info(f"Intervalo de escaneo: {self.scan_interval} segundos")
        
        try:
            while True:
                start_time = datetime.now()
                logging.info("Iniciando ciclo de escaneo...")
                
                devices = self.scan_networks()
                self.process_new_devices(devices)
                
                # Calcular tiempo de espera dinámico
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
        missing_dirs = []
        
        for dir_name in required_dirs:
            dir_path = BASE_DIR / dir_name
            if not dir_path.exists():
                missing_dirs.append(str(dir_path))
        
        if missing_dirs:
            print("\n".join([
                "❌ Error: Directorios requeridos no encontrados:",
                *missing_dirs,
                "",
                "Ejecute primero: python cli.py init"
            ]))
            return
        
        # Verificar archivo .env
        if not ENV_PATH.exists():
            print(f"\n❌ Archivo de configuración no encontrado: {ENV_PATH}")
            print("Ejecute primero: python cli.py init")
            return
        
        # Iniciar aplicación
        app = NetScanAlert()
        app.run()
        
    except Exception as e:
        logging.critical(f"Error inicializando la aplicación: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
