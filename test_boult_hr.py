import asyncio
from bleak import BleakClient

WATCH = "3A:E3:6A:D3:09:D5"

HEART_RATE = "00002a37-0000-1000-8000-00805f9b34fb"
BATTERY = "00002a19-0000-1000-8000-00805f9b34fb"


def heart_rate_handler(sender, data):
    """
    BLE Heart Rate Measurement format.

    Byte 0 = flags
    Byte 1 or bytes 1-2 = heart rate
    """

    if not data:
        return

    flags = data[0]

    # Bit 0:
    # 0 = heart rate is UINT8
    # 1 = heart rate is UINT16
    if flags & 0x01:
        heart_rate = int.from_bytes(data[1:3], byteorder="little")
    else:
        heart_rate = data[1]

    print(f"❤️ Heart Rate: {heart_rate} BPM")


def battery_handler(sender, data):
    if data:
        print(f"🔋 Battery: {data[0]}%")


async def main():

    print("Connecting to Boult Watch SH...")
    
    async with BleakClient(WATCH) as client:

        print("Connected:", client.is_connected)
        print()

        # Read current battery
        try:
            battery = await client.read_gatt_char(BATTERY)
            print(f"Initial battery: {battery[0]}%")
        except Exception as e:
            print("Battery read failed:", e)

        # Subscribe to heart-rate notifications
        await client.start_notify(
            HEART_RATE,
            heart_rate_handler
        )

        # Subscribe to battery notifications
        try:
            await client.start_notify(
                BATTERY,
                battery_handler
            )
        except Exception as e:
            print("Battery notifications unavailable:", e)

        print()
        print("=" * 60)
        print("LISTENING FOR HEART RATE")
        print("Keep the watch on your wrist.")
        print("Open the heart-rate measurement screen if necessary.")
        print("=" * 60)
        print()

        try:
            await asyncio.sleep(60)

        finally:
            if client.is_connected:

                try:
                    await client.stop_notify(HEART_RATE)
                except Exception:
                    pass

                try:
                    await client.stop_notify(BATTERY)
                except Exception:
                    pass

    print()
    print("Finished.")


asyncio.run(main())