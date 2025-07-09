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
        self.arp_timeout = 5  # segundos para timeout de arp-scan
        self.scan_batch_size = 64  # Número de IPs por lote de escaneo

    def _run_arp_scan(self, network: str) -> Optional[str]:
        """
        Ejecuta arp-scan en una red específica.
        
        Args:
            network: Red en formato CIDR (ej. '192.168.1.0/24')
            
        Returns:
            str: Salida del comando arp-scan o None si falla
        """
        try:
            result = subprocess.run(
                ['arp-scan', '--localnet', '--interface=eth0', f'--arpscan-timeout={self.arp_timeout}'],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout if result.returncode == 0 else None
        except subprocess.TimeoutExpired:
            logging.warning(f"Timeout al escanear red {network}")
            return None
        except Exception as e:
            logging.error(f"Error ejecutando arp-scan: {str(e)}")
            return None

    def _parse_arp_output(self, output: str, target_network: str) -> List[Dict]:
        """
        Procesa la salida de arp-scan y filtra por red objetivo.
        
        Args:
            output: Salida de texto de arp-scan
            target_network: Red en formato CIDR para filtrar resultados
            
        Returns:
            List[Dict]: Lista de dispositivos encontrados
        """
        devices = []
        # Expresión regular mejorada para capturar MAC e IP
        arp_pattern = re.compile(
            r'^\s*((?:\d{1,3}\.){3}\d{1,3})\s+'
            r'((?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})\s+'
            r'(.+?)\s*$',
            re.MULTILINE
        )
        
        try:
            target_net = ipaddress.ip_network(target_network, strict=False)
        except ValueError as e:
            logging.error(f"Red objetivo inválida {target_network}: {str(e)}")
            return devices
        
        for match in arp_pattern.finditer(output):
            ip_str, mac, vendor = match.groups()
            
            try:
                ip = ipaddress.ip_address(ip_str)
                if ip in target_net:
                    devices.append({
                        'ip': str(ip),
                        'mac': mac.upper().replace('-', ':'),  # Normaliza MAC
                        'vendor': vendor.strip()
                    })
            except ValueError:
                continue
                
        return devices

    def scan_single_network(self, network: str) -> List[Dict]:
        """
        Escanea una única red y devuelve dispositivos encontrados.
        
        Args:
            network: Red en formato CIDR a escanear
            
        Returns:
            List[Dict]: Dispositivos encontrados con sus datos
        """
        if not self._validate_network(network):
            logging.warning(f"Red inválida omitida: {network}")
            return []
            
        logging.info(f"Escaneando red: {network}")
        arp_output = self._run_arp_scan(network)
        
        if not arp_output:
            return []
            
        return self._parse_arp_output(arp_output, network)

    def scan_network_ranges(self, networks: List[str]) -> List[Dict]:
        """
        Escanea múltiples rangos de red.
        
        Args:
            networks: Lista de redes en formato CIDR
            
        Returns:
            List[Dict]: Todos los dispositivos encontrados
        """
        all_devices = []
        
        for network in networks:
            if not self._validate_network(network):
                continue
                
            try:
                devices = self.scan_single_network(network)
                all_devices.extend(devices)
                logging.debug(f"Encontrados {len(devices)} dispositivos en {network}")
            except Exception as e:
                logging.error(f"Error escaneando {network}: {str(e)}")
                continue
                
        return all_devices

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

    def detect_new_devices(self, networks: List[str]) -> List[Dict]:
        """
        Detecta nuevos dispositivos que no están en el inventario.
        
        Args:
            networks: Lista de redes a escanear
            
        Returns:
            List[Dict]: Nuevos dispositivos encontrados
        """
        current_devices = self.scan_network_ranges(networks)
        new_devices = []
        
        for device in current_devices:
            if not self.inventory.device_exists(device['mac']):
                if not self.inventory.validate_ip(device['ip']):
                    logging.warning(f"IP inválida detectada: {device['ip']}")
                    continue
                    
                new_devices.append(device)
                logging.info(f"Nuevo dispositivo: {device['mac']} ({device['ip']})")
                
        return new_devices


if __name__ == "__main__":
    # Prueba de funcionamiento
    print("=== Prueba de NetworkScanner ===")
    
    # Configuración de prueba
    test_inventory = FileInventory()
    scanner = NetworkScanner(test_inventory)
    
    # Red de prueba (usar una red real para pruebas efectivas)
    test_network = "192.168.1.0/24"
    
    print(f"\nEscaneando red de prueba: {test_network}")
    devices = scanner.scan_single_network(test_network)
    
    if devices:
        print("\nDispositivos encontrados:")
        for i, device in enumerate(devices, 1):
            print(f"{i}. MAC: {device['mac']} | IP: {device['ip']} | Fabricante: {device['vendor']}")
    else:
        print("No se encontraron dispositivos o hubo un error en el escaneo")