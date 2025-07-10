#!/usr/bin/env python3
import click
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import ipaddress
from dotenv import load_dotenv, set_key

# Cargar variables de entorno
load_dotenv()

@click.group()
def cli():
    """Sistema de Monitoreo de Red - Interfaz de Administración"""
    pass

def verify_config() -> bool:
    """Verifica la configuración esencial"""
    required_files = [
        'config/.env',
        'config/networks.txt',
        'data/devices.csv'
    ]
    
    missing = [f for f in required_files if not Path(f).exists()]
    if missing:
        click.echo("\n⚠️ Archivos esenciales faltantes:", err=True)
        for f in missing:
            click.echo(f"- {f}", err=True)
        click.echo("\nEjecuta 'python cli.py init' para inicializar", err=True)
        return False
    return True

@cli.command()
def init():
    """Inicializa la estructura del proyecto"""
    # Directorios
    Path('config').mkdir(exist_ok=True)
    Path('data').mkdir(exist_ok=True)
    
    # Archivo config/.env
    if not Path('config/.env').exists():
        with open('config/.env', 'w') as f:
            f.write("# Configuración de Telegram\n")
            f.write("TELEGRAM_BOT_TOKEN=\n")
            f.write("TELEGRAM_CHAT_ID=\n")
            f.write("\n# Configuración de la aplicación\n")
            f.write("LOG_LEVEL=warning\n")
            f.write('ALERT_MESSAGE="⚠️ ALERTA: Nuevo dispositivo detectado - MAC: {mac} IP: {ip} Vendor: {vendor}"\n')
    
    # networks.txt
    if not Path('config/networks.txt').exists():
        with open('config/networks.txt', 'w') as f:
            f.write("# Redes a monitorear (una por línea)\n")
            f.write("# Ejemplo:\n")
            f.write("# 192.168.1.0/24\n")
            f.write("# 10.0.0.0/8\n")
    
    # devices.csv
    if not Path('data/devices.csv').exists():
        with open('data/devices.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'mac', 'ip', 'name', 'os', 'vendor',
                'status', 'first_seen', 'last_seen'
            ])
    
    click.echo("✅ Estructura del proyecto inicializada")
    click.echo("ℹ️ Completa los valores en config/.env y config/networks.txt")

@cli.command()
def show_config():
    """Muestra la configuración actual"""
    if not verify_config():
        return
    
    # Mostrar configuración de Telegram
    click.echo("\n🔧 Configuración de Telegram:")
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    click.echo(f"BOT_TOKEN: {'✅' if token else '❌ No configurado'}")
    if token:
        click.echo(f"  (últimos 4 chars: {token[-4:]})")
    click.echo(f"CHAT_ID: {'✅' if chat_id else '❌ No configurado'}")
    
    # Mostrar redes a monitorear
    click.echo("\n🌐 Redes a monitorear:")
    try:
        with open('config/networks.txt') as f:
            networks = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            valid_networks = []
            invalid_networks = []
            
            for net in networks:
                try:
                    network = ipaddress.ip_network(net, strict=False)
                    valid_networks.append(str(network))
                except ValueError:
                    invalid_networks.append(net)
            
            if valid_networks:
                click.echo("Redes válidas:")
                for net in valid_networks:
                    click.echo(f"- {net}")
            
            if invalid_networks:
                click.echo("\n❌ Redes inválidas (serán ignoradas):")
                for net in invalid_networks:
                    click.echo(f"- {net}")
            
            if not valid_networks and not invalid_networks:
                click.echo("No hay redes configuradas")
    except FileNotFoundError:
        click.echo("❌ No se encontró config/networks.txt")

@cli.command()
@click.argument('identifier')
def whitelist(identifier):
    """Añade un dispositivo (MAC o IP) a la lista blanca"""
    if not verify_config():
        return
    
    from inventory import FileInventory
    inv = FileInventory()
    
    # Determinar si es MAC o IP
    if ':' in identifier or '-' in identifier:  # MAC
        normalized_mac = inv.normalize_mac(identifier)
        if not normalized_mac:
            click.echo(f"❌ Formato MAC inválido: {identifier}", err=True)
            click.echo("Formato esperado: 00:11:22:33:44:55", err=True)
            return
        
        inv.whitelist_device(normalized_mac)
        click.echo(f"✅ MAC {normalized_mac} añadida a la lista blanca")
    else:  # IP
        if not inv.validate_ip(identifier):
            click.echo(f"❌ IP inválida: {identifier}", err=True)
            return
        
        inv.whitelist_device(identifier)
        click.echo(f"✅ IP {identifier} añadida a la lista blanca")

@cli.command()
@click.argument('mac')
def blacklist(mac):
    """Añade una MAC a la lista negra"""
    if not verify_config():
        return
    
    from inventory import FileInventory
    inv = FileInventory()
    
    normalized_mac = inv.normalize_mac(mac)
    if not normalized_mac:
        click.echo(f"❌ Formato MAC inválido: {mac}", err=True)
        click.echo("Formato esperado: 00:11:22:33:44:55", err=True)
        return
    
    inv.blacklist_device(normalized_mac)
    click.echo(f"✅ MAC {normalized_mac} añadida a la lista negra")

@cli.command()
@click.option('--token', prompt='Bot Token de Telegram', hide_input=True)
def set_telegram_token(token):
    """Configura el Bot Token de Telegram"""
    set_key('config/.env', 'TELEGRAM_BOT_TOKEN', token)
    click.echo("✅ Token de Telegram actualizado")
    click.echo("💡 Asegúrate de que config/.env está en .gitignore")

@cli.command()
@click.option('--chat', prompt='Chat ID de Telegram')
def set_telegram_chat(chat):
    """Configura el Chat ID de Telegram"""
    set_key('config/.env', 'TELEGRAM_CHAT_ID', chat)
    click.echo("✅ Chat ID de Telegram actualizado")

@cli.command()
@click.option('--level', type=click.Choice(['debug', 'info', 'warning', 'error'], case_sensitive=False),
              prompt='Nivel de log (debug/info/warning/error)')
def set_log_level(level):
    """Configura el nivel de logging"""
    set_key('config/.env', 'LOG_LEVEL', level.lower())
    click.echo(f"✅ Nivel de log configurado a {level.lower()}")

@cli.command()
@click.option('--message', prompt='Mensaje de alerta personalizado')
def set_alert_message(message):
    """Configura el mensaje de alerta personalizado"""
    set_key('config/.env', 'ALERT_MESSAGE', message)
    click.echo("✅ Mensaje de alerta actualizado")

@cli.command()
def list_devices():
    """Lista todos los dispositivos conocidos"""
    if not verify_config():
        return
    
    from inventory import FileInventory
    inv = FileInventory()
    
    devices = inv.get_all_devices()
    if not devices:
        click.echo("No hay dispositivos registrados")
        return
    
    click.echo("\n📋 Dispositivos registrados:")
    for device in devices:
        status_icon = {
            'authorized': '✅',
            'blocked': '❌',
            'unknown': '❓'
        }.get(device['status'], ' ')
        
        click.echo(f"{status_icon} {device['mac']} ({device['ip']}) - {device.get('vendor', '')}")

@cli.command()
@click.argument('network')
def network_devices(network):
    """Lista dispositivos en una red específica"""
    if not verify_config():
        return
    
    try:
        ipaddress.ip_network(network, strict=False)
    except ValueError as e:
        click.echo(f"❌ Red inválida: {str(e)}", err=True)
        return
    
    from inventory import FileInventory
    inv = FileInventory()
    
    devices = inv.get_network_devices(network)
    if not devices:
        click.echo(f"No hay dispositivos registrados en {network}")
        return
    
    click.echo(f"\n📋 Dispositivos en {network}:")
    for device in devices:
        click.echo(f"- {device['mac']} ({device['ip']}) - {device.get('vendor', '')}")

@cli.command()
def cleanup():
    """Normaliza y limpia todos los datos del inventario"""
    if not verify_config():
        return
    
    from inventory import FileInventory
    inv = FileInventory()
    
    click.echo("🛠 Normalizando datos...")
    inv.cleanup_data()
    click.echo("✅ Datos normalizados y limpiados")

@cli.command()
@click.argument('ip_or_network')
def validate(ip_or_network):
    """Valida una dirección IP o rango de red"""
    try:
        if '/' in ip_or_network:
            net = ipaddress.ip_network(ip_or_network, strict=False)
            click.echo(f"✅ Red válida: {net}")
            click.echo(f"  - Versión: IPv{net.version}")
            click.echo(f"  - Máscara: {net.netmask}")
            click.echo(f"  - Hosts: {net.num_addresses}")
        else:
            ip = ipaddress.ip_address(ip_or_network)
            click.echo(f"✅ IP válida: {ip}")
            click.echo(f"  - Versión: IPv{ip.version}")
            click.echo(f"  - Público: {ip.is_global}")
            click.echo(f"  - Privado: {ip.is_private}")
    except ValueError as e:
        click.echo(f"❌ Error: {str(e)}", err=True)

if __name__ == "__main__":
    # Verificar estructura básica
    if not Path('config/.env').exists() and 'init' not in sys.argv:
        click.echo("⚠️ Ejecuta primero 'python cli.py init' para inicializar", err=True)
        sys.exit(1)
    
    cli()