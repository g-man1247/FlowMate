import asyncio
from bleak import BleakScanner


async def main():
    print("Scanning for Bluetooth devices...")
    print("Keep the EVO Vista close to your laptop.")
    print()

    devices = await BleakScanner.discover(timeout=10)

    if not devices:
        print("No Bluetooth devices found.")
        return

    print("Devices found:")
    print("-" * 60)

    for device in devices:
        print(f"Name: {device.name}")
        print(f"Address: {device.address}")
        print("-" * 60)


asyncio.run(main())