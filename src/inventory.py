import csv
from pathlib import Path
from datetime import datetime
import ipaddress

class FileInventory:
    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.devices_file = self.data_dir / 'devices.csv'
        self.whitelist_file = self.data_dir / 'whitelist.txt'
        self.ip_whitelist_file = self.data_dir / 'ip_whitelist.txt'
        self.blacklist_file = self.data_dir / 'blacklist.txt'
        self.history_file = self.data_dir / 'history.log'
        
        # Crear archivos y directorios si no existen
        self._initialize_files()
    
    def _initialize_files(self):
        """Inicializa todos los archivos necesarios con sus estructuras básicas"""
        self.data_dir.mkdir(exist_ok=True)
        
        # Archivo CSV de dispositivos
        if not self.devices_file.exists():
            with open(self.devices_file, 'w') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'mac', 'ip', 'name', 'os', 'vendor', 
                    'status', 'first_seen', 'last_seen'
                ])
        
        # Archivos de listas (whitelist/blacklist)
        for f in [
            self.whitelist_file, 
            self.ip_whitelist_file,
            self.blacklist_file, 
            self.history_file
        ]:
            f.touch(exist_ok=True)
    
    def device_exists(self, mac):
        """Verifica si un dispositivo ya existe en el inventario por su MAC"""
        with open(self.devices_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['mac'].lower() == mac.lower():
                    return True
        return False
    
    def add_device(self, mac, ip, vendor, os_info='unknown', name=''):
        """
        Añade un nuevo dispositivo al inventario
        
        Args:
            mac (str): Dirección MAC del dispositivo
            ip (str): Dirección IP del dispositivo
            vendor (str): Fabricante del dispositivo
            os_info (str): Sistema operativo detectado
            name (str): Nombre descriptivo del dispositivo
        """
        status = self._determine_status(mac, ip)
        now = datetime.now().isoformat()
        
        with open(self.devices_file, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([
                mac, ip, name, os_info, vendor, 
                status, now, now
            ])
        
        self._log_connection(mac, ip, 'connected')
    
    def update_device(self, mac, ip):
        """Actualiza la última vez que se vio un dispositivo"""
        updated = False
        rows = []
        
        # Leer todos los dispositivos
        with open(self.devices_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Actualizar el dispositivo específico
        for row in rows:
            if row['mac'].lower() == mac.lower():
                row['ip'] = ip
                row['last_seen'] = datetime.now().isoformat()
                updated = True
                break
        
        # Reescribir el archivo si hubo cambios
        if updated:
            with open(self.devices_file, 'w') as f:
                writer = csv.writer(f)
                # Escribir encabezados
                writer.writerow([
                    'mac', 'ip', 'name', 'os', 'vendor', 
                    'status', 'first_seen', 'last_seen'
                ])
                # Escribir datos actualizados
                for row in rows:
                    writer.writerow([
                        row['mac'], row['ip'], row['name'], 
                        row['os'], row['vendor'], row['status'],
                        row['first_seen'], row['last_seen']
                    ])
    
    def _determine_status(self, mac, ip):
        """
        Determina el estado de un dispositivo basado en las listas blancas/negras
        
        Args:
            mac (str): Dirección MAC del dispositivo
            ip (str): Dirección IP del dispositivo
            
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
        
        # Verificar listas negras
        with open(self.blacklist_file, 'r') as f:
            if mac.lower() in [line.strip().lower() for line in f if line.strip()]:
                return 'blocked'
        
        return 'unknown'
    
    def _log_connection(self, mac, ip, event):
        """Registra un evento de conexión en el historial"""
        with open(self.history_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()},{mac},{ip},{event}\n")
    
    def whitelist_device(self, mac):
        """Añade una MAC a la lista blanca"""
        self._update_list(mac, self.whitelist_file)
    
    def blacklist_device(self, mac):
        """Añade una MAC a la lista negra"""
        self._update_list(mac, self.blacklist_file)
    
    def _update_list(self, identifier, list_file):
        """
        Actualiza una lista (whitelist/blacklist) con un nuevo identificador
        
        Args:
            identifier (str): MAC o IP a añadir
            list_file (Path): Archivo de lista a actualizar
        """
        identifier = identifier.strip().lower() if ':' in identifier else identifier.strip()
        
        # Leer identificadores existentes
        with open(list_file, 'r') as f:
            existing_ids = [line.strip().lower() if ':' in line else line.strip() 
                           for line in f if line.strip()]
        
        # Añadir si no existe
        if identifier not in existing_ids:
            with open(list_file, 'a') as f:
                f.write(f"{identifier}\n")
    
    def get_whitelisted_ips(self):
        """Devuelve todas las IPs en la lista blanca"""
        with open(self.ip_whitelist_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    
    def get_whitelisted_macs(self):
        """Devuelve todas las MACs en la lista blanca"""
        with open(self.whitelist_file, 'r') as f:
            return [line.strip().lower() for line in f if line.strip()]
    
    def is_authorized(self, mac=None, ip=None):
        """
        Verifica si un dispositivo está autorizado
        
        Args:
            mac (str): Dirección MAC a verificar
            ip (str): Dirección IP a verificar
            
        Returns:
            bool: True si está autorizado, False en caso contrario
        """
        if mac:
            mac = mac.lower()
            if mac in self.get_whitelisted_macs():
                return True
        
        if ip:
            if ip in self.get_whitelisted_ips():
                return True
        
        return False
    
    def validate_ip(self, ip_address):
        """
        Valida que una dirección IP tenga formato correcto
        
        Args:
            ip_address (str): Dirección IP a validar
            
        Returns:
            bool: True si es válida, False en caso contrario
        """
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False