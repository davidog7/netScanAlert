import subprocess
import re
import ipaddress
import logging
from typing import List, Dict, Optional
from pathlib import Path
from inventory import FileInventory

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class NetworkScanner:
    def __init__(self, inventory: FileInventory):
        """
        Inicializa el escáner de red con referencia al inventario.
        
        Args:
            inventory: Instancia de FileInventory para gestión de dispositivos
        """
        self.inventory = inventory
        self.arp_timeout = 500  # milisegundos para timeout de arp-scan
        self.scan_batch_size = 64  # Número de IPs por lote de escaneo

    def _validate_network(self, network_str: str) -> bool:
        """
        Valida que una cadena sea una red válida.
        
        Args:
            network_str: Cadena a validar como red
            
        Returns:
            bool: True si es una red válida
        """
        try:
            ipaddress.ip_network(network_str, strict=False)
            return True
        except ValueError:
            return False

    def _parse_arp_output(self, output: str) -> List[Dict]:
        """
        Procesa la salida de arp-scan y devuelve dispositivos encontrados.
        
        Args:
            output: Salida de texto de arp-scan
            
        Returns:
            List[Dict]: Lista de dispositivos encontrados
        """
        devices = []
        arp_pattern = re.compile(
            r'^\s*((?:\d{1,3}\.){3}\d{1,3})\s+'
            r'((?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})\s+'
            r'(.+?)\s*$',
            re.MULTILINE
        )
        
        for match in arp_pattern.finditer(output):
            ip_str, mac, vendor = match.groups()
            devices.append({
                'ip': ip_str,
                'mac': mac.upper().replace('-', ':'),  # Normaliza MAC
                'vendor': vendor.strip()
            })
                
        return devices

    def scan_network(self, network: str, interface: str = 'eth0') -> List[Dict]:
        """
        Escanea una única red y devuelve dispositivos encontrados.
        
        Args:
            network: Red en formato CIDR a escanear
            interface: Interfaz de red a usar (por defecto 'eth0')
            
        Returns:
            List[Dict]: Dispositivos encontrados con sus datos
        """
        if not self._validate_network(network):
            logging.warning(f"Red inválida omitida: {network}")
            return []
            
        logging.info(f"Escaneando red: {network} en interfaz {interface}")
        
        try:
            result = subprocess.run(
                ['sudo', 'arp-scan', '-I', interface, f'--timeout={self.arp_timeout}', network],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logging.error(f"Error en arp-scan: {result.stderr}")
                return []
                
            return self._parse_arp_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            logging.warning(f"Timeout al escanear red {network}")
            return []
        except Exception as e:
            logging.error(f"Error ejecutando arp-scan: {str(e)}")
            return []


if __name__ == "__main__":
    # Prueba de funcionamiento
    print("=== Prueba de NetworkScanner ===")
    
    # Configuración de prueba
    test_inventory = FileInventory()
    scanner = NetworkScanner(test_inventory)
    
    # Red de prueba
    test_network = "10.0.2.0/24"
    test_interface = "enp0s3"
    
    print(f"\nEscaneando red de prueba: {test_network} en {test_interface}")
    devices = scanner.scan_network(test_network, test_interface)
    
    if devices:
        print("\nDispositivos encontrados:")
        for i, device in enumerate(devices, 1):
            print(f"{i}. MAC: {device['mac']} | IP: {device['ip']} | Fabricante: {device['vendor']}")
    else:
        print("No se encontraron dispositivos o hubo un error en el escaneo")