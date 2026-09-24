import asyncio
from bleak import BleakClient


WATCH_ADDRESS = "41:42:8C:18:3F:28"


async def main():
    print("Connecting to EVO Vista...")
    
    async with BleakClient(WATCH_ADDRESS) as client:
        print("Connected:", client.is_connected)
        print()

        print("=" * 70)
        print("GATT DIAGNOSTIC")
        print("=" * 70)

        for service in client.services:
            print()
            print(f"SERVICE: {service.uuid}")
            print(f"  Description: {service.description}")

            for characteristic in service.characteristics:
                print()
                print(f"  CHARACTERISTIC: {characteristic.uuid}")
                print(f"    Description: {characteristic.description}")
                print(f"    Properties: {characteristic.properties}")

                for descriptor in characteristic.descriptors:
                    print(
                        f"    DESCRIPTOR: {descriptor.uuid} "
                        f"{descriptor.description}"
                    )

                    # Read descriptors when possible.
                    try:
                        data = await client.read_gatt_descriptor(
                            descriptor.handle
                        )
                        print(f"      Value: {data.hex(' ')}")
                    except Exception as e:
                        print(f"      Read failed: {e}")

        print()
        print("=" * 70)
        print("Diagnostic complete")
        print("=" * 70)


asyncio.run(main())