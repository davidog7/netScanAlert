Instrucciones de uso

1.- Instalar dependencias:
    pip install -r requirements.txt

2.- Configurar:
    Editar config/telegram.conf con tu bot token y chat ID
    Editar config/networks.txt con tus subredes

3.- Ejecutar:
    Modo monitoreo:
        python netScanAlert.py

    Gestionar (CLI):
        # Añadir dispositivo a lista blanca (MAC o IP)
        python cli.py whitelist 00:11:22:33:44:55
        python cli.py whitelist 192.168.1.100

        # Configurar Telegram
        python cli.py set-telegram-token
        python cli.py set-telegram-chat

        # Configurar logging y mensajes
        python cli.py set-log-level
        python cli.py set-alert-message

        # Ver configuración actual
        python cli.py show-config
