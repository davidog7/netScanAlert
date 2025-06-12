import click
from inventory import FileInventory

@click.group()
def cli():
    """Sistema de monitoreo de red"""
    pass

@cli.command()
@click.argument('mac')
def whitelist(mac):
    """Añadir dispositivo a la lista blanca"""
    inventory = FileInventory()
    inventory.whitelist_device(mac)
    click.echo(f"Dispositivo {mac} añadido a la lista blanca")

@cli.command()
def list_devices():
    """Listar todos los dispositivos conocidos"""
    inventory = FileInventory()
    
    with open(inventory.devices_file, 'r') as f:
        reader = csv.DictReader(f)
        for device in reader:
            click.echo(f"{device['mac']} ({device['ip']}) - {device['vendor']} [{device['status']}]")

if __name__ == "__main__":
    cli()