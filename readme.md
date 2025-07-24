# NetScanAlert Usage Instructions / Instrucciones de uso de netScanAlert
NetScanAlert is a continuous network scanning and monitoring system designed to automatically detect unauthorized devices and report them via instant messaging platforms.
NetScanAlert es un sistema de escaneo y monitoreo continuo de redes con el fin de detectar de forma automatizada equipos no autorizados y con capacidad de reportarlos a través de sistemas de mensajería instantánea.
## 1.- Install Dependencies / Instalar dependencias:
```bash
    # Install required packages / Instalar paquetes necesarios 
    sudo apt update
    sudo apt install git python3 python3-pip python3-venv arp-scan nmap  
    # Configure sudo permissions for nmap and arp-scan / Configurar permisos sudo para nmap y arp-scan
    # Add to /etc/sudoers.d/netScanAlert (sudo visudo):  
    usuario ALL=(ALL) NOPASSWD: /usr/bin/nmap, /usr/bin/arp-scan
    # Create a virtual environment / Crear entorno virtual  
    mkdir -p ~/venvs
    python3 -m venv ~/venvs/netScanAlert
    # Activate the environment / Activar el entorno
    source ~/venvs/netScanAlert/bin/activate
    # Clone the repository / Clonar el repositorio 
    git clone https://github.com/davidog7/netScanAlert
    cd netScanAlert
    pip install -r requirements.txt
```
## 2.- Configure / Configurar:
```bash
    # Initialize the tool (creates directories and config files) / Inicializar la herramienta para crear directorios y archivos de trabajo
    python cli.py init
    # Add networks to scan in ./config/networks.txt / Añadir redes a escanear  
    nano ./config/networks.txt
    # Optional: Set up Telegram (recommended) / Configurar Telegram (opcional pero recomendado)
    python cli.py set-telegram-token
    python cli.py set-telegram-chat
    # View current configuration / Ver configuración actual
    python cli.py show-config
```
## 3.- Run / Ejecutar:
```bash
   # Run in monitoring mode / Ejecutar en modo monitoreo  
    cd ./src
    python3 netScanAlert.py 
    # Or run in background / O ejecutar en segundo plano  
    nohup python3 netScanAlert.py > /dev/null 2>&1 &
    # Monitor logs / Monitorear logs
    tail -f netScanAlert.log
```

## 4.- CLI Commands / Comandos CLI:
```bash
$ python cli.py --help
Usage: cli.py [OPTIONS] COMMAND [ARGS]...

  Sistema de Monitoreo de Red - Interfaz de Administración

Options:
  --help  Show this message and exit.

Commands:
  blacklist         Add a MAC to the blacklist (not implemented) / Añade una MAC a la lista negra (no implementado)
  cleanup           Normalize and clean inventory data (not implemented) / Normaliza y limpia todos los datos del inventario (no implementado, borrar directorio data)
  init              Initialize project structure / Inicializa la estructura del proyecto
  list-devices      List all known devices (not implemented) / Lista todos los dispositivos conocidos (no implementado)
  network-devices   List devices in a specific network (not implemented) / Lista dispositivos en una red específica (no implementado)
  set-alert-message Configure custom alert message (not implemented) / Configura el mensaje de alerta personalizado (no implementado)
  set-log-level     Set logging level (not implemented) / Configura el nivel de logging (no implementado)
  set-telegram-chat Set Telegram Chat ID / Set Telegram Chat ID / Configura el Chat ID de Telegram
  set-telegram-token Set Telegram Bot Token / Configura el Bot Token de Telegram
  show-config       Show current configuration / Muestra la configuración actual
  validate          Validate an IP or network range (not implemented) / Valida una dirección IP o rango de red (no implementado)
  whitelist         Add a device (MAC/IP) to the whitelist (not implemented) / Añade un dispositivo (MAC o IP) a la lista blanca (no implementado)
  ```
