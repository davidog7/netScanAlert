#!/usr/bin/env python3
import click
import configparser
from pathlib import Path
import sys
from inventory import FileInventory

@click.group()
def cli():
    """Sistema de monitoreo de red - Interfaz de administración"""
    pass

def load_telegram_config():
    """Carga la configuración de Telegram con depuración mejorada"""
    config = configparser.ConfigParser()
    config_file = Path('config/telegram.conf')
    
    # Verificar existencia del archivo
    if not config_file.exists():
        print(f"❌ Error: Archivo de configuración no encontrado en {config_file.absolute()}", file=sys.stderr)
        print("Solución: Crea el archivo config/telegram.conf con la estructura adecuada", file=sys.stderr)
        return None
    
    # Leer archivo
    try:
        config.read(config_file)
    except Exception as e:
        print(f"❌ Error leyendo archivo de configuración: {str(e)}", file=sys.stderr)
        return None
    
    # Verificar sección [telegram]
    if 'telegram' not in config:
        print("❌ Error: Sección [telegram] no encontrada en el archivo de configuración", file=sys.stderr)
        print("Secciones encontradas:", config.sections(), file=sys.stderr)
        return None
    
    # Verificar campos obligatorios
    required_fields = ['bot_token', 'chat_id']
    missing_fields = [field for field in required_fields if field not in config['telegram']]
    
    if missing_fields:
        print(f"❌ Error: Campos faltantes en configuración: {', '.join(missing_fields)}", file=sys.stderr)
        return None
    
    return config['telegram']

@cli.command()
def show_config():
    """Mostrar la configuración actual con verificación detallada"""
    telegram_config = load_telegram_config()
    
    if not telegram_config:
        print("\n💡 Ejemplo de archivo config/telegram.conf correcto:")
        print("""
[telegram]
bot_token = 123456789:AAFmBbQdEeFfGgHhIiJjKkLlMmNnOoPpQqRr
chat_id = -1001234567890
log_level = warning
alert_message = ⚠️ ALERTA: Nuevo dispositivo detectado
""")
        return
    
    print("\n🔧 Configuración actual de Telegram:")
    for key, value in telegram_config.items():
        # Ocultar parte del token por seguridad
        displayed_value = (value[:4] + '...' + value[-4:]) if 'token' in key.lower() else value
        print(f"{key.upper():<15}: {displayed_value}")
    
    # Verificación adicional de valores
    if not telegram_config['bot_token'].count(':') == 1:
        print("\n⚠️ Advertencia: El bot_token no parece tener el formato correcto (debería ser '123456789:ABCdefGHIjklMNopQRSTuvwXYZ')")
    
    if not telegram_config['chat_id'].startswith('-100'):
        print("\n⚠️ Advertencia: El chat_id para grupos normalmente comienza con -100")

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
    """Configurar el Bot Token de Telegram"""
    config = configparser.ConfigParser()
    config_file = Path('config/telegram.conf')
    
    if config_file.exists():
        config.read(config_file)
    
    if 'telegram' not in config:
        config['telegram'] = {}
    
    config['telegram']['bot_token'] = token
    
    with open(config_file, 'w') as f:
        config.write(f)
    
    print("✅ Token de Telegram configurado correctamente")

@cli.command()
@click.option('--chat', prompt='Chat ID de Telegram')
def set_telegram_chat(chat):
    """Configurar el Chat ID de Telegram"""
    config = configparser.ConfigParser()
    config_file = Path('config/telegram.conf')
    
    if config_file.exists():
        config.read(config_file)
    
    if 'telegram' not in config:
        config['telegram'] = {}
    
    config['telegram']['chat_id'] = chat
    
    with open(config_file, 'w') as f:
        config.write(f)
    
    print("✅ Chat ID de Telegram configurado correctamente")

@cli.command()
@click.option('--level', type=click.Choice(['debug', 'info', 'warning', 'error']), 
              prompt='Nivel de log (debug/info/warning/error)')
def set_log_level(level):
    """Configurar el nivel de logging"""
    config = configparser.ConfigParser()
    config_file = Path('config/telegram.conf')
    
    if config_file.exists():
        config.read(config_file)
    
    if 'telegram' not in config:
        config['telegram'] = {}
    
    config['telegram']['log_level'] = level
    
    with open(config_file, 'w') as f:
        config.write(f)
    
    print(f"✅ Nivel de log configurado a {level}")

@cli.command()
@click.option('--message', prompt='Mensaje de alerta personalizado')
def set_alert_message(message):
    """Configurar mensaje de alerta personalizado"""
    config = configparser.ConfigParser()
    config_file = Path('config/telegram.conf')
    
    if config_file.exists():
        config.read(config_file)
    
    if 'telegram' not in config:
        config['telegram'] = {}
    
    config['telegram']['alert_message'] = message
    
    with open(config_file, 'w') as f:
        config.write(f)
    
    print("✅ Mensaje de alerta configurado correctamente")

if __name__ == "__main__":
    # Crear directorios necesarios
    Path('config').mkdir(exist_ok=True)
    Path('data').mkdir(exist_ok=True)
    
    # Verificar archivo de configuración
    if not Path('config/telegram.conf').exists():
        print("ℹ️ Archivo config/telegram.conf no encontrado. Usa los comandos set-telegram-* para crearlo")
    
    cli()
    