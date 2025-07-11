#!/usr/bin/env python3
import click
import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key

# Configurar la ruta del archivo .env (subir un nivel y entrar a config/)
BASE_DIR = Path(__file__).parent.parent
ENV_PATH = BASE_DIR / "config" / ".env"

# Cargar variables de entorno
load_dotenv(dotenv_path=ENV_PATH)

def verify_env_file():
    """Verifica que el archivo .env exista y sea legible"""
    if not ENV_PATH.exists():
        click.echo(f"❌ Error: No se encontró el archivo .env en {ENV_PATH}", err=True)
        click.echo("Ejecute primero: python cli.py init", err=True)
        return False
    
    try:
        ENV_PATH.read_text(encoding='utf-8')
        return True
    except Exception as e:
        click.echo(f"❌ Error leyendo .env: {str(e)}", err=True)
        return False

@click.group()
def cli():
    """Sistema de Monitoreo de Red - Interfaz de Administración"""
    pass

@cli.command()
def init():
    """Inicializa la estructura del proyecto"""
    # Crear directorios necesarios
    (BASE_DIR / "config").mkdir(exist_ok=True)
    (BASE_DIR / "data").mkdir(exist_ok=True)
    
    # Crear archivo .env si no existe
    if not ENV_PATH.exists():
        ENV_PATH.write_text(
            "# Configuración de Telegram\n"
            "TELEGRAM_BOT_TOKEN=\n"
            "TELEGRAM_CHAT_ID=\n\n"
            "# Configuración de la aplicación\n"
            "LOG_LEVEL=info\n"
            "SCAN_INTERVAL=300\n"
        )
        click.echo(f"✅ Archivo .env creado en {ENV_PATH}")
    else:
        click.echo("ℹ️ El archivo .env ya existe")

    click.echo("\nEstructura inicial creada. Ahora configure:")
    click.echo("1. python cli.py set-telegram-token")
    click.echo("2. python cli.py set-telegram-chat")

@cli.command()
def show_config():
    """Muestra la configuración actual"""
    if not verify_env_file():
        sys.exit(1)
    
    # Recargar variables para asegurar los últimos cambios
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    click.echo("\n🔧 Configuración actual:")
    click.echo(f"📁 Ubicación .env: {ENV_PATH.absolute()}")
    
    # Mostrar configuración de Telegram
    if token:
        click.echo(f"✅ TELEGRAM_BOT_TOKEN: {'*'*12}{token[-4:]}")
    else:
        click.echo("❌ TELEGRAM_BOT_TOKEN: No configurado")
    
    if chat_id:
        click.echo(f"✅ TELEGRAM_CHAT_ID: {chat_id}")
    else:
        click.echo("❌ TELEGRAM_CHAT_ID: No configurado")
    
    # Mostrar otras configuraciones
    click.echo("\n⚙️ Otras configuraciones:")
    click.echo(f"LOG_LEVEL: {os.getenv('LOG_LEVEL', 'No configurado')}")
    click.echo(f"SCAN_INTERVAL: {os.getenv('SCAN_INTERVAL', 'No configurado')}")

@cli.command()
@click.option('--token', prompt='Bot Token de Telegram', hide_input=True)
def set_telegram_token(token):
    """Configura el Bot Token de Telegram"""
    if not verify_env_file():
        sys.exit(1)
    
    # Validación básica del token
    if len(token) < 30 or ':' not in token:
        click.echo("❌ El token parece inválido. Debe tener el formato '123456789:ABCdefGHIjkl...'", err=True)
        if not click.confirm("¿Desea guardarlo de todos modos?"):
            return
    
    set_key(str(ENV_PATH), 'TELEGRAM_BOT_TOKEN', token)
    click.echo(f"✅ Token guardado en {ENV_PATH}")
    
    # Verificar que se guardó correctamente
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    if os.getenv('TELEGRAM_BOT_TOKEN') == token:
        click.echo("✓ Verificación: Token guardado correctamente")
    else:
        click.echo("❌ Error: El token no se guardó correctamente", err=True)

@cli.command()
@click.option('--chat', prompt='Chat ID de Telegram')
def set_telegram_chat(chat):
    """Configura el Chat ID de Telegram"""
    if not verify_env_file():
        sys.exit(1)
    
    set_key(str(ENV_PATH), 'TELEGRAM_CHAT_ID', chat)
    click.echo(f"✅ Chat ID guardado en {ENV_PATH}")

@cli.command()
def verify():
    """Verifica profundamente la configuración"""
    if not verify_env_file():
        sys.exit(1)
    
    # Mostrar contenido crudo del archivo
    click.echo("\n📄 Contenido de .env:")
    click.echo(ENV_PATH.read_text(encoding='utf-8'))
    
    # Verificar conexión con Telegram
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if token and chat_id:
        click.echo("\n🔍 Probando conexión con Telegram...")
        try:
            import requests
            response = requests.get(
                f"https://api.telegram.org/bot{token}/getMe",
                timeout=10
            )
            if response.status_code == 200:
                click.echo("✅ Conexión exitosa!")
                click.echo(f"Bot: @{response.json()['result']['username']}")
            else:
                click.echo(f"❌ Error de API: {response.text}")
        except Exception as e:
            click.echo(f"❌ Error de conexión: {str(e)}")
    else:
        click.echo("\n⚠️ Configuración incompleta para probar Telegram")

if __name__ == "__main__":
    cli()
    