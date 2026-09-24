import asyncio
from bleak import BleakClient


WATCH_ADDRESS = "41:42:8C:18:3F:28"

CHARACTERISTICS = {
    "Serial Number": "00002a25-0000-1000-8000-00805f9b34fb",
    "Hardware Revision": "00002a27-0000-1000-8000-00805f9b34fb",
    "Firmware Revision": "00002a26-0000-1000-8000-00805f9b34fb",
    "Software Revision": "00002a28-0000-1000-8000-00805f9b34fb",
    "Battery Level": "00002a19-0000-1000-8000-00805f9b34fb",
}


async def main():
    print("Connecting to EVO Vista...")

    async with BleakClient(WATCH_ADDRESS) as client:

        print("Connected:", client.is_connected)
        print()

        for name, uuid in CHARACTERISTICS.items():

            try:
                data = await client.read_gatt_char(uuid)

                # Battery Level is normally a single byte percentage.
                if name == "Battery Level" and data:
                    print(f"{name}: {data[0]}%")
                else:
                    try:
                        value = data.decode("utf-8").rstrip("\x00")
                        print(f"{name}: {value}")
                    except UnicodeDecodeError:
                        print(f"{name}: {data.hex()}")

            except Exception as e:
                print(f"{name}: READ FAILED - {e}")


asyncio.run(main())