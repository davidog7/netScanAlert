#!/usr/bin/env python3
import subprocess
import re
import ipaddress
import logging
import netifaces
import socket
from typing import List, Dict
from pathlib import Path
from inventory import FileInventory

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class NetworkScanner:
    def __init__(self, inventory: FileInventory):
        """Inicializa el escáner de red"""
        self.inventory = inventory
        self.arp_timeout = 2000
        self.nmap_timeout = 5000
        self.local_networks = self._get_local_networks()
        
    def _get_local_networks(self) -> List[str]:
        """Obtiene redes locales de interfaces activas"""
        local_nets = []
        for interface in netifaces.interfaces():
            try:
                if interface == 'lo' or not netifaces.AF_INET in netifaces.ifaddresses(interface):
                    continue
                    
                for addr in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
                    if 'addr' in addr and 'netmask' in addr:
                        network = ipaddress.ip_network(
                            f"{addr['addr']}/{addr['netmask']}", 
                            strict=False
                        )
                        local_nets.append(str(network))
            except Exception as e:
                logging.debug(f"Error obteniendo red para {interface}: {str(e)}")
        return local_nets

    def _is_local_network(self, network: str) -> bool:
        """Determina si una red es local"""
        try:
            target_net = ipaddress.ip_network(network, strict=False)
            for local_net in self.local_networks:
                if target_net.subnet_of(ipaddress.ip_network(local_net)):
                    return True
            return False
        except ValueError as e:
            logging.error(f"Error validando red {network}: {str(e)}")
            return False

    def _scan_local_with_arp(self, network: str, interface: str) -> List[Dict]:
        """Escaneo ARP mejorado"""
        try:
            cmd = [
                'sudo', 'arp-scan',
                '-I', interface,
                '--timeout=1000',  # 1 segundo
                '--retry=2',
                network
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5  # Timeout total de 5 segundos
            )
            
            if result.returncode == 0:
                return self._parse_arp_output(result.stdout)
            
            logging.error(f"ARP-scan falló. Código: {result.returncode}")
            return []
        except subprocess.TimeoutExpired:
            logging.warning("ARP-scan timeout, intentando con método alternativo")
            return self._scan_local_alternative(network, interface)
        except Exception as e:
            logging.error(f"Error en ARP-scan: {str(e)}")
            return []

    def _scan_local_alternative(self, network: str, interface: str) -> List[Dict]:
        """Método alternativo para escaneo local"""
        try:
            cmd = ['sudo', 'arp', '-a', '-i', interface]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            return self._parse_arp_output_alternative(result.stdout)
        except Exception as e:
            logging.error(f"Error en escaneo alternativo: {str(e)}")
            return []

    def _parse_arp_output(self, output: str) -> List[Dict]:
        """Procesa la salida de arp-scan"""
        devices = []
        pattern = re.compile(r'^\s*((?:\d{1,3}\.){3}\d{1,3})\s+((?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})\s+(.+?)\s*$', re.MULTILINE)
        
        for match in pattern.finditer(output):
            ip, mac, vendor = match.groups()
            devices.append({
                'ip': ip,
                'mac': mac.upper().replace('-', ':'),
                'vendor': vendor.strip()
            })
        return devices

    def _parse_arp_output_alternative(self, output: str) -> List[Dict]:
        """Procesa la salida alternativa de arp"""
        devices = []
        pattern = re.compile(r'^\S+\s+\(([\d\.]+)\)\s+at\s+([0-9A-Fa-f:]+)\s+\[ether\]\s+on\s+\S+$')
        
        for line in output.splitlines():
            match = pattern.match(line)
            if match:
                ip, mac = match.groups()
                devices.append({
                    'ip': ip,
                    'mac': mac.upper(),
                    'vendor': 'Desconocido'
                })
        return devices

    def _scan_remote_with_nmap(self, network: str) -> List[Dict]:
        """Escaneo remoto que devuelve dispositivos válidos"""
        try:
            cmd = [
                'sudo', 'nmap',
                '-sn',
                '-PE',
                '-PS21,22,80,443',
                '-n',
                '--max-retries=1',
                '--host-timeout=2s',
                network
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                devices = self._parse_nmap_output(result.stdout)
                # Filtrar IPs inválidas
                return [d for d in devices if self.inventory.validate_ip(d['ip'])]
                
            logging.error(f"Nmap falló. Código: {result.returncode}")
            return []
        except Exception as e:
            logging.error(f"Error en Nmap: {str(e)}")
            return []
    
    def _parse_nmap_output(self, output: str) -> List[Dict]:
        """Procesa la salida de nmap con IP única"""
        devices = []
        ip_pattern = re.compile(r'Nmap scan report for ([\d\.]+)$')
        seen_ips = set()
        
        for line in output.splitlines():
            if ip_match := ip_pattern.match(line):
                ip = ip_match.group(1)
                if ip not in seen_ips:
                    seen_ips.add(ip)
                    devices.append({
                        'ip': ip,
                        'mac': '00:00:00:00:00:00',
                        'vendor': 'Desconocido'
                    })
        return devices
    
    def scan_network(self, network: str, interface: str = 'eth0') -> List[Dict]:
        """Escanea una red con el método apropiado"""
        try:
            if self._is_local_network(network):
                logging.info(f"[LOCAL] Escaneando {network} en {interface}")
                return self._scan_local_with_arp(network, interface)
            else:
                logging.info(f"[REMOTA] Escaneando {network}")
                return self._scan_remote_with_nmap(network)
        except Exception as e:
            logging.error(f"Error escaneando {network}: {str(e)}")
            return []