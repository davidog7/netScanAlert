#!/usr/bin/env python3
import click
import os
from pathlib import Path
import sys
from dotenv import load_dotenv, set_key
from inventory import FileInventory

# Cargar variables de entorno al inicio
load_dotenv()

@click.group()
def cli():
    """Sistema de monitoreo de red - Interfaz de administración"""
    pass

def verify_telegram_config():
    """Verifica la configuración de Telegram"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("⚠️ Configuración de Telegram incompleta en .env", file=sys.stderr)
        print("Usa los comandos set-telegram-token y set-telegram-chat", file=sys.stderr)
        return False
    return True

@cli.command()
def show_config():
    """Mostrar la configuración actual"""
    print("\n🔧 Configuración actual:")
    
    # Mostrar configuración de Telegram
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    print("\nTelegram:")
    print(f"BOT_TOKEN: {token[:4]}...{token[-4:]}" if token else "❌ No configurado")
    print(f"CHAT_ID: {chat_id}" if chat_id else "❌ No configurado")
    
    # Mostrar configuración de red
    networks_file = Path('config/networks.txt')
    if networks_file.exists():
        print("\nRedes a monitorear:")
        print(networks_file.read_text())
    else:
        print("\n❌ networks.txt no encontrado")

@cli.command()
@click.argument('identifier')
def whitelist(identifier):
    """Añadir dispositivo (MAC o IP) a la lista blanca"""
    inventory = FileInventory()
    
    if ':' in identifier or '-' in identifier:  # Es una MAC
        inventory.whitelist_device(identifier)
        print(f"✅ MAC {identifier} añadida a la lista blanca")
    else:  # Asumimos que es una IP
        if not inventory.validate_ip(identifier):
            print(f"❌ Error: {identifier} no es una IP válida")
            return
        
        with open(inventory.data_dir / 'ip_whitelist.txt', 'a') as f:
            f.write(f"{identifier}\n")
        print(f"✅ IP {identifier} añadida a la lista blanca")

@cli.command()
@click.option('--token', prompt='Bot Token de Telegram', hide_input=True)
def set_telegram_token(token):
    """Configurar el Bot Token de Telegram en .env"""
    set_key('.env', 'TELEGRAM_BOT_TOKEN', token)
    print("✅ Token de Telegram guardado en .env")
    print("💡 Asegúrate de que .env está en .gitignore")

@cli.command()
@click.option('--chat', prompt='Chat ID de Telegram')
def set_telegram_chat(chat):
    """Configurar el Chat ID de Telegram en .env"""
    set_key('.env', 'TELEGRAM_CHAT_ID', chat)
    print("✅ Chat ID de Telegram guardado en .env")

@cli.command()
@click.option('--level', type=click.Choice(['debug', 'info', 'warning', 'error']), 
              prompt='Nivel de log (debug/info/warning/error)')
def set_log_level(level):
    """Configurar el nivel de logging"""
    set_key('.env', 'LOG_LEVEL', level)
    print(f"✅ Nivel de log configurado a {level}")

@cli.command()
@click.option('--message', prompt='Mensaje de alerta personalizado')
def set_alert_message(message):
    """Configurar mensaje de alerta personalizado"""
    set_key('.env', 'ALERT_MESSAGE', message)
    print("✅ Mensaje de alerta configurado")

@cli.command()
def init():
    """Inicializar estructura de directorios y archivos"""
    Path('config').mkdir(exist_ok=True)
    Path('data').mkdir(exist_ok=True)
    
    if not Path('.env').exists():
        with open('.env', 'w') as f:
            f.write("# Configuración de Telegram\n")
            f.write("TELEGRAM_BOT_TOKEN=\n")
            f.write("TELEGRAM_CHAT_ID=\n")
            f.write("\n# Configuración de la aplicación\n")
            f.write("LOG_LEVEL=warning\n")
            f.write('ALERT_MESSAGE="⚠️ ALERTA: Nuevo dispositivo detectado en la red"\n')
        
        print("✅ Archivo .env creado")
        print("💡 Completa los valores faltantes y asegúrate de añadir .env a .gitignore")
    
    if not Path('config/networks.txt').exists():
        with open('config/networks.txt', 'w') as f:
            f.write("# Lista de redes a monitorear (una por línea)\n")
            f.write("# Ejemplo:\n")
            f.write("# 192.168.1.0/24\n")
        
        print("✅ Archivo networks.txt creado")
    
    print("\nEstructura inicial creada. Usa los comandos set-telegram-* para configurar.")

if __name__ == "__main__":
    # Verificar estructura inicial
    if not Path('.env').exists():
        print("⚠️ Archivo .env no encontrado. Ejecuta 'python cli.py init' para inicializar")
    
    cli()