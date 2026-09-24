import asyncio
from bleak import BleakClient

WATCH = "3A:E3:6A:D3:09:D5"


async def main():
    print("Connecting to Boult Watch SH...")

    async with BleakClient(WATCH) as client:
        print("Connected:", client.is_connected)
        print()

        for service in client.services:
            print(f"SERVICE: {service.uuid}")
            print(f"  {service.description}")

            for char in service.characteristics:
                print(f"  CHARACTERISTIC: {char.uuid}")
                print(f"    Description: {char.description}")
                print(f"    Properties: {char.properties}")

            print()


asyncio.run(main())