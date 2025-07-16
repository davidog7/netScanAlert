# Instrucciones de uso de netScanAlert
NetScanAlert es un sistema de escaneo y monitoreo continuo de redes con el fin de detectar de forma automatizada equipos no autorizados y con capacidad de reportarlos a través de sistemas de mensajería instantánea.
## 1.- Instalar dependencias:
```bash
    sudo apt update
    sudo apt install git python3 python3-pip python3-venv arp-scan #(arp-scan requiere permisos sudo)
    # Crear el entorno virtual en tu home
    mkdir -p ~/venvs
    python3 -m venv ~/venvs/netScanAlert
    # Activar el entorno
    source ~/venvs/netScanAlert/bin/activate
    # Clonar el repositorio
    git clone https://github.com/davidog7/netScanAlert
    cd netScanAlert
    pip install -r requirements.txt
```
## 2.- Configurar:
```bash
    # Inicializar la herramienta para crear directorios y archivos de trabajo
    python cli.py init
    # Añadir las redes a escanear en el archivo ./config/networks.txt
    nano ./config/networks.txt
    # Configurar Telegram, opcional pero recomendado. Se recomienda mejor usar variables de entorno en entornos productivos:
    python cli.py set-telegram-token
    python cli.py set-telegram-chat
    # Ver configuración actual
    python cli.py show-config
```
## 3.- Ejecutar:
```bash
   # Ejecutar el programa en modo monitoreo:
        python3 netScanAlert.py 
    # O en segundo plano:
        nohup python3 netScanAlert.py > /dev/null 2>&1 &
    # monitoreo del log
    tail -f netScanAlert.log
```

## 4.- CLI:
```bash
$ python cli.py --help
Usage: cli.py [OPTIONS] COMMAND [ARGS]...

  Sistema de Monitoreo de Red - Interfaz de Administración

Options:
  --help  Show this message and exit.

Commands:
  blacklist         Añade una MAC a la lista negra (no implementado)
  cleanup           Normaliza y limpia todos los datos del inventario (no implementado, borrar directorio data)
  init              Inicializa la estructura del proyecto
  list-devices      Lista todos los dispositivos conocidos (no implementado)
  network-devices   Lista dispositivos en una red específica (no implementado)
  set-alert-message Configura el mensaje de alerta personalizado (no implementado)
  set-log-level     Configura el nivel de logging (no implementado)
  set-telegram-chat Configura el Chat ID de Telegram
  set-telegram-token Configura el Bot Token de Telegram
  show-config       Muestra la configuración actual
  validate          Valida una dirección IP o rango de red (no implementado)
  whitelist         Añade un dispositivo (MAC o IP) a la lista blanca (no implementado)
  ```
