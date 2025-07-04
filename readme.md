# Instrucciones de uso de NETSCANALERT
NETSCANALERT es un sistema de escaneo y monitoreo continuo de redes con el fin de detectar de forma automatizada equipos no autorizados y con capacidad de reportarlos a través de sistemas de mensajería instantánea.
## 0.- Clonar el repositorio:
```bash
    sudo apt install git
    git clone https://github.com/davidog7/netScanAlert
```
## 1.- Instalar dependencias:
```bash
    sudo apt install python3
    sudo apt install python3-pip
    sudo apt install arp-scan
    cd netScanAlert
    pip install -r requirements.txt
    # Instala arp-scan (requiere permisos sudo)
    sudo apt install arp-scan  # Para Ubuntu/Debian o
    sudo yum install arp-scan  # Para CentOS/RHEL
```
## 2.- Configurar:
```bash
    # Añadir dispositivo a lista blanca (MAC o IP)
    python cli.py whitelist 00:11:22:33:44:55
    python cli.py whitelist 192.168.1.100
    #Configurar Telegram (opcional) pero recomendado).Se recomienda mejor usar variables de entorno en entornos productivos:
    python cli.py set-telegram-token
    python cli.py set-telegram-chat
    # Configurar logging y mensajes
    python cli.py set-log-level
    python cli.py set-alert-message
    # Ver configuración actual
    python cli.py show-config
```
## 3.- Ejecutar:
```bash
   # Ejecutar el programa en modo monitoreo:
        python3 netScanAlert.py 
```

