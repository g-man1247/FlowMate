import asyncio
from bleak import BleakClient

WATCH = "41:42:8C:18:3F:28"
BATTERY = "00002a19-0000-1000-8000-00805f9b34fb"


def handler(sender, data):
    print("Battery notification:", list(data))


async def main():
    async with BleakClient(WATCH) as client:
        print("Connected:", client.is_connected)

        await client.start_notify(BATTERY, handler)

        print("Listening for battery notifications...")
        print("Leave the watch connected for 30 seconds.")

        await asyncio.sleep(30)

        await client.stop_notify(BATTERY)


asyncio.run(main())