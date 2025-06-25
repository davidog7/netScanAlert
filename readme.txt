Instrucciones de uso

0.- Clona el repositorio (si lo tienes en uno)
    git clone https://github.com/davidog7/netScanAlert
    cd netScanAlert

1.- Instalar dependencias:
    sudo apt install python3
    pip install -r requirements.txt
    # Instala arp-scan (requiere permisos sudo)
    sudo apt install arp-scan  # Para Ubuntu/Debian o
    sudo yum install arp-scan  # Para CentOS/RHEL

2.- Configurar:
    Configurar Telegram (opcional pero recomendado):
    python cli.py set-telegram-token
    python cli.py set-telegram-chat
       #o
    Editar config/telegram.conf con tu bot token y chat ID
    
    Editar config/networks.txt con tus subredes

3.- Ejecutar:
    Modo monitoreo:
        python3 netScanAlert.py

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
