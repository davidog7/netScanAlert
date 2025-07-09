# Instrucciones de uso de netScanAlert
NetScanAlert es un sistema de escaneo y monitoreo continuo de redes con el fin de detectar de forma automatizada equipos no autorizados y con capacidad de reportarlos a través de sistemas de mensajería instantánea.
## 1.- Instalar dependencias:
```bash
    sudo apt update
    sudo apt install git python3 python3-pip python3-venv arp-scan #(requiere permisos sudo)
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
  blacklist         Añade una MAC a la lista negra
  cleanup           Normaliza y limpia todos los datos del inventario
  init              Inicializa la estructura del proyecto
  list-devices      Lista todos los dispositivos conocidos
  network-devices   Lista dispositivos en una red específica
  set-alert-message Configura el mensaje de alerta personalizado
  set-log-level     Configura el nivel de logging
  set-telegram-chat Configura el Chat ID de Telegram
  set-telegram-token Configura el Bot Token de Telegram
  show-config       Muestra la configuración actual
  validate          Valida una dirección IP o rango de red
  whitelist         Añade un dispositivo (MAC o IP) a la lista blanca
  ```
