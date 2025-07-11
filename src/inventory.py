import csv
from pathlib import Path
from datetime import datetime
import ipaddress
from typing import List, Dict, Optional, Union

class FileInventory:
    def __init__(self, data_dir: str = '../data') -> None:
        """
        Inicializa el sistema de inventario con manejo seguro de direcciones IP.
        
        Args:
            data_dir: Directorio donde se almacenan los archivos de datos
        """
        self.data_dir = Path(data_dir)
        self._initialize_files()

    def _initialize_files(self) -> None:
        """Crea la estructura de archivos necesaria si no existe"""
        self.data_dir.mkdir(exist_ok=True)
        
        # Archivo CSV principal de dispositivos
        self.devices_file = self.data_dir / 'devices.csv'
        if not self.devices_file.exists():
            with open(self.devices_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'mac', 'ip', 'name', 'os', 'vendor',
                    'status', 'first_seen', 'last_seen'
                ])
        
        # Archivos de listas de control
        self.whitelist_file = self.data_dir / 'whitelist.txt'
        self.ip_whitelist_file = self.data_dir / 'ip_whitelist.txt'
        self.blacklist_file = self.data_dir / 'blacklist.txt'
        self.history_file = self.data_dir / 'history.log'
        
        for f in [self.whitelist_file, self.ip_whitelist_file,
                 self.blacklist_file, self.history_file]:
            f.touch(exist_ok=True)

    def validate_ip(self, ip_str: str) -> bool:
        """
        Valida una dirección IP usando el módulo ipaddress.
        
        Args:
            ip_str: Dirección IP a validar
            
        Returns:
            bool: True si es una IP válida, False en caso contrario
        """
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False

    def is_ip_in_any_network(self, ip_str: str, networks: List[str]) -> bool:
        """
        Verifica si una IP pertenece a cualquiera de las redes proporcionadas.
        
        Args:
            ip_str: Dirección IP a verificar
            networks: Lista de redes en formato CIDR
            
        Returns:
            bool: True si la IP está en alguna de las redes
        """
        try:
            ip = ipaddress.ip_address(ip_str)
            for network_str in networks:
                try:
                    network = ipaddress.ip_network(network_str, strict=False)
                    if ip in network:
                        return True
                except ValueError:
                    continue
            return False
        except ValueError:
            return False

    def add_device(self, mac: str, ip: str, vendor: str, 
                  os_info: str = 'unknown', name: str = '') -> None:
        """
        Añade un nuevo dispositivo al inventario con validación de IP.
        
        Args:
            mac: Dirección MAC del dispositivo
            ip: Dirección IP del dispositivo
            vendor: Fabricante del dispositivo
            os_info: Sistema operativo detectado (opcional)
            name: Nombre descriptivo (opcional)
            
        Raises:
            ValueError: Si la IP no es válida
        """
        if not self.validate_ip(ip):
            raise ValueError(f"Dirección IP inválida: {ip}")
        
        status = self._determine_status(mac, ip)
        now = datetime.now().isoformat()
        
        with open(self.devices_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                mac, ip, name, os_info, vendor,
                status, now, now
            ])
        
        self._log_connection(mac, ip, 'connected')

    def device_exists(self, mac: str) -> bool:
        """
        Verifica si un dispositivo existe en el inventario por su MAC.
        
        Args:
            mac: Dirección MAC a buscar
            
        Returns:
            bool: True si el dispositivo existe
        """
        with open(self.devices_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['mac'].lower() == mac.lower():
                    return True
        return False

    def _determine_status(self, mac: str, ip: str) -> str:
        """
        Determina el estado de un dispositivo basado en las listas de control.
        
        Args:
            mac: Dirección MAC del dispositivo
            ip: Dirección IP del dispositivo
            
        Returns:
            str: Estado del dispositivo ('authorized', 'blocked', 'unknown')
        """
        # Verificar MAC en whitelist
        with open(self.whitelist_file, 'r') as f:
            if mac.lower() in [line.strip().lower() for line in f if line.strip()]:
                return 'authorized'
        
        # Verificar IP en whitelist
        with open(self.ip_whitelist_file, 'r') as f:
            if ip in [line.strip() for line in f if line.strip()]:
                return 'authorized'
        
        # Verificar blacklist
        with open(self.blacklist_file, 'r') as f:
            if mac.lower() in [line.strip().lower() for line in f if line.strip()]:
                return 'blocked'
        
        return 'unknown'

    def _log_connection(self, mac: str, ip: str, event: str) -> None:
        """
        Registra un evento de conexión en el historial.
        
        Args:
            mac: Dirección MAC del dispositivo
            ip: Dirección IP del dispositivo
            event: Tipo de evento ('connected', 'disconnected')
        """
        with open(self.history_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()},{mac},{ip},{event}\n")

    def whitelist_device(self, identifier: str) -> None:
        """
        Añade un dispositivo (MAC o IP) a la lista blanca.
        
        Args:
            identifier: Dirección MAC o IP a añadir
            
        Raises:
            ValueError: Si el identificador no es MAC ni IP válida
        """
        if ':' in identifier or '-' in identifier:  # Es MAC
            self._update_list(identifier, self.whitelist_file)
        elif self.validate_ip(identifier):  # Es IP
            self._update_list(identifier, self.ip_whitelist_file)
        else:
            raise ValueError("Identificador debe ser MAC (00:11:22:33:44:55) o IP válida")

    def blacklist_device(self, mac: str) -> None:
        """
        Añade una MAC a la lista negra.
        
        Args:
            mac: Dirección MAC a bloquear
        """
        self._update_list(mac, self.blacklist_file)

    def _update_list(self, identifier: str, list_file: Path) -> None:
        """
        Actualiza un archivo de lista (whitelist/blacklist).
        
        Args:
            identifier: Identificador a añadir (MAC o IP)
            list_file: Archivo de lista a actualizar
        """
        identifier = identifier.strip()
        existing = set()
        
        # Leer existentes
        if list_file.exists():
            with open(list_file, 'r') as f:
                existing = {line.strip() for line in f if line.strip()}
        
        # Añadir si no existe
        if identifier not in existing:
            with open(list_file, 'a') as f:
                f.write(f"{identifier}\n")

    def get_all_devices(self) -> List[Dict[str, str]]:
        """
        Obtiene todos los dispositivos del inventario.
        
        Returns:
            Lista de diccionarios con información de dispositivos
        """
        devices = []
        with open(self.devices_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                devices.append(dict(row))
        return devices

    def get_network_devices(self, network: str) -> List[Dict[str, str]]:
        """
        Obtiene dispositivos que pertenecen a una red específica.
        
        Args:
            network: Red en formato CIDR (ej. '192.168.1.0/24')
            
        Returns:
            Lista de dispositivos en esa red
        """
        try:
            target_net = ipaddress.ip_network(network, strict=False)
        except ValueError:
            return []
            
        devices = []
        with open(self.devices_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ip = ipaddress.ip_address(row['ip'])
                    if ip in target_net:
                        devices.append(dict(row))
                except ValueError:
                    continue
        return devices

    def normalize_mac(self, mac: str) -> str:
        """
        Normaliza una dirección MAC a formato estándar (00:11:22:33:44:55).
        
        Args:
            mac: Dirección MAC en cualquier formato
            
        Returns:
            str: MAC normalizada o cadena vacía si no es válida
        """
        mac = mac.strip().lower()
        # Eliminar separadores no alfanuméricos
        mac = ''.join(c for c in mac if c.isalnum())
        
        if len(mac) != 12:
            return ''
            
        # Formatear con dos puntos cada dos caracteres
        return ':'.join(mac[i:i+2] for i in range(0, 12, 2))

    def cleanup_data(self) -> None:
        """Limpia y normaliza todos los datos en los archivos"""
        # Normalizar MACs en devices.csv
        devices = []
        with open(self.devices_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['mac'] = self.normalize_mac(row['mac']) or row['mac']
                devices.append(row)
        
        # Reescribir archivo
        with open(self.devices_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=devices[0].keys())
            writer.writeheader()
            writer.writerows(devices)
        
        # Normalizar archivos de listas
        for list_file in [self.whitelist_file, self.blacklist_file]:
            items = set()
            if list_file.exists():
                with open(list_file, 'r') as f:
                    items = {self.normalize_mac(line.strip()) or line.strip() 
                            for line in f if line.strip()}
            
            with open(list_file, 'w') as f:
                for item in sorted(items):
                    f.write(f"{item}\n")
        
        # Normalizar ip_whitelist.txt
        ips = set()
        if self.ip_whitelist_file.exists():
            with open(self.ip_whitelist_file, 'r') as f:
                for line in f:
                    ip = line.strip()
                    if self.validate_ip(ip):
                        ips.add(ip)
            
            with open(self.ip_whitelist_file, 'w') as f:
                for ip in sorted(ips, key=lambda x: ipaddress.ip_address(x)):
                    f.write(f"{ip}\n")