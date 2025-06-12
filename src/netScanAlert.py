import time
from scanner import NetworkScanner
from inventory import FileInventory
from notifier import TelegramNotifier

def main():
    # Inicializar componentes
    inventory = FileInventory()
    scanner = NetworkScanner(inventory)
    notifier = TelegramNotifier()
    
    # Bucle principal
    scan_interval = 300  # 5 minutos
    
    print("Iniciando monitoreo de red...")
    while True:
        print(f"Escaneando red... {time.ctime()}")
        new_device = scanner.scan_and_update()
        
        if new_device:
            message = (f"⚠️ <b>Nuevo dispositivo detectado!</b>\n"
                      f"MAC: {new_device['mac']}\n"
                      f"IP: {new_device['ip']}\n"
                      f"Fabricante: {new_device['vendor']}")
            
            print(message)
            notifier.send_alert(message)
        
        time.sleep(scan_interval)

if __name__ == "__main__":
    main()