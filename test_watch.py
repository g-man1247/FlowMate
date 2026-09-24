import asyncio
from bleak import BleakScanner


async def detection_callback(device, advertisement_data):
    name = device.name or advertisement_data.local_name

    if name:
        print(
            f"Name: {name:<30} "
            f"Address: {device.address}"
        )


async def main():
    print("Scanning continuously for 60 seconds...")
    print("Keep the EVO Vista close to the laptop.")
    print("If possible, wake the watch screen.")
    print()

    scanner = BleakScanner(detection_callback)

    await scanner.start()

    try:
        await asyncio.sleep(60)
    finally:
        await scanner.stop()

    print("\nScan finished.")


asyncio.run(main())