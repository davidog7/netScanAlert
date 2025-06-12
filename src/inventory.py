import csv
from pathlib import Path
from datetime import datetime

class FileInventory:
    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.devices_file = self.data_dir / 'devices.csv'
        self.whitelist_file = self.data_dir / 'whitelist.txt'
        self.blacklist_file = self.data_dir / 'blacklist.txt'
        self.history_file = self.data_dir / 'history.log'
        
        # Crear archivos si no existen
        self._initialize_files()
    
    def _initialize_files(self):
        self.data_dir.mkdir(exist_ok=True)
        
        if not self.devices_file.exists():
            with open(self.devices_file, 'w') as f:
                writer = csv.writer(f)
                writer.writerow(['mac', 'ip', 'name', 'os', 'vendor', 'status', 'first_seen', 'last_seen'])
        
        for f in [self.whitelist_file, self.blacklist_file, self.history_file]:
            f.touch(exist_ok=True)
    
    def device_exists(self, mac):
        with open(self.devices_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['mac'].lower() == mac.lower():
                    return True
        return False
    
    def add_device(self, mac, ip, vendor, os_info='unknown', name=''):
        status = self._determine_status(mac)
        now = datetime.now().isoformat()
        
        with open(self.devices_file, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([mac, ip, name, os_info, vendor, status, now, now])
        
        self._log_connection(mac, ip, 'connected')
    
    def update_device(self, mac, ip):
        # Implementación para actualizar última conexión
        pass
    
    def _determine_status(self, mac):
        with open(self.whitelist_file, 'r') as f:
            if mac.lower() in [line.strip().lower() for line in f]:
                return 'authorized'
        
        with open(self.blacklist_file, 'r') as f:
            if mac.lower() in [line.strip().lower() for line in f]:
                return 'blocked'
        
        return 'unknown'
    
    def _log_connection(self, mac, ip, event):
        with open(self.history_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()},{mac},{ip},{event}\n")
    
    def whitelist_device(self, mac):
        self._update_list(mac, self.whitelist_file)
    
    def blacklist_device(self, mac):
        self._update_list(mac, self.blacklist_file)
    
    def _update_list(self, mac, list_file):
        mac = mac.strip().lower()
        with open(list_file, 'r+') as f:
            macs = [line.strip().lower() for line in f]
            if mac not in macs:
                f.write(f"{mac}\n")