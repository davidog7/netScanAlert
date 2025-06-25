import click
import configparser
from pathlib import Path
from inventory import FileInventory

@click.group()
def cli():
    """Sistema de monitoreo de red - Interfaz de administración"""
    pass

@cli.command()
@click.argument('identifier')  # Puede ser MAC o IP
def whitelist(identifier):
    """Añadir dispositivo (MAC o IP) a la lista blanca"""
    inventory = FileInventory()
    
    # Determinar si es MAC o IP
    if ':' in identifier or '-' in identifier:  # Es una MAC
        inventory.whitelist_device(identifier)
        click.echo(f"✅ MAC {identifier} añadida a la lista blanca")
    else:  # Asumimos que es una IP
        with open(inventory.data_dir / 'ip_whitelist.txt', 'a') as f:
            f.write(f"{identifier}\n")
        click.echo(f"✅ IP {identifier} añadida a la lista blanca")

@cli.command()
@click.option('--token', prompt='Bot Token de Telegram', hide_input=True)
def set_telegram_token(token):
    """Configurar el Bot Token de Telegram"""
    config = configparser.ConfigParser()
    config_file = Path('../config/telegram.conf')
    
    if config_file.exists():
        config.read(config_file)
    
    if 'telegram' not in config:
        config['telegram'] = {}
    
    config['telegram']['bot_token'] = token
    
    with open(config_file, 'w') as f:
        config.write(f)
    
    click.echo("✅ Token de Telegram configurado correctamente")

@cli.command()
@click.option('--chat', prompt='Chat ID de Telegram')
def set_telegram_chat(chat):
    """Configurar el Chat ID de Telegram"""
    config = configparser.ConfigParser()
    config_file = Path('../config/telegram.conf')
    
    if config_file.exists():
        config.read(config_file)
    
    if 'telegram' not in config:
        config['telegram'] = {}
    
    config['telegram']['chat_id'] = chat
    
    with open(config_file, 'w') as f:
        config.write(f)
    
    click.echo("✅ Chat ID de Telegram configurado correctamente")

@cli.command()
@click.option('--level', type=click.Choice(['debug', 'info', 'warning', 'error']), 
              prompt='Nivel de log (debug/info/warning/error)')
def set_log_level(level):
    """Configurar el nivel de logging"""
    config = configparser.ConfigParser()
    config_file = Path('../config/telegram.conf')
    
    if config_file.exists():
        config.read(config_file)
    
    if 'telegram' not in config:
        config['telegram'] = {}
    
    config['telegram']['log_level'] = level
    
    with open(config_file, 'w') as f:
        config.write(f)
    
    click.echo(f"✅ Nivel de log configurado a {level}")

@cli.command()
@click.option('--message', prompt='Mensaje de alerta personalizado')
def set_alert_message(message):
    """Configurar mensaje de alerta personalizado"""
    config = configparser.ConfigParser()
    config_file = Path('../config/telegram.conf')
    
    if config_file.exists():
        config.read(config_file)
    
    if 'telegram' not in config:
        config['telegram'] = {}
    
    config['telegram']['alert_message'] = message
    
    with open(config_file, 'w') as f:
        config.write(f)
    
    click.echo("✅ Mensaje de alerta configurado correctamente")

@cli.command()
def show_config():
    """Mostrar la configuración actual"""
    config = configparser.ConfigParser()
    config_file = Path('../config/telegram.conf')
    
    if not config_file.exists():
        click.echo("⚠️ No existe archivo de configuración")
        return
    
    config.read(config_file)
    
    if 'telegram' not in config:
        click.echo("⚠️ No hay configuración de Telegram")
        return
    
    click.echo("\n🔧 Configuración actual:")
    for key, value in config['telegram'].items():
        if 'token' in key.lower():
            value = value[:4] + '...' + value[-4:]  # Ocultar parte del token
        click.echo(f"{key.upper()}: {value}")

if __name__ == "__main__":
    # Crear directorio config si no existe
    Path('config').mkdir(exist_ok=True)
    cli()