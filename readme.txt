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
        python cli.py whitelist 00:11:22:33:44:55  #añadir Mac autorizada
        python cli.py list-devices #listar dispositivos autorizados
        