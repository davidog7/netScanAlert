import subprocess
import re
from inventory import FileInventory

class NetworkScanner:
    def __init__(self, inventory):
        self.inventory = inventory
    
    def arp_scan(self):
        """Ejecuta arp-scan y procesa resultados"""
        try:
            result = subprocess.run(['arp-scan', '-l'], 
                                  capture_output=True, 
                                  text=True)
            return self._parse_arp_output(result.stdout)
        except Exception as e:
            print(f"Error en arp-scan: {e}")
            return []
    
    def _parse_arp_output(self, output):
        devices = []
        # Expresión regular para líneas con MAC e IP
        pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:]{17})\s+(.+)')
        
        for line in output.split('\n'):
            match = pattern.search(line)
            if match:
                ip, mac, vendor = match.groups()
                devices.append({
                    'ip': ip,
                    'mac': mac,
                    'vendor': vendor.strip()
                })
        return devices
    
    def scan_and_update(self):
        devices = self.arp_scan()
        for device in devices:
            if not self.inventory.device_exists(device['mac']):
                self.inventory.add_device(
                    mac=device['mac'],
                    ip=device['ip'],
                    vendor=device['vendor']
                )
                return device  # Retorna el nuevo dispositivo detectado
        return None
    