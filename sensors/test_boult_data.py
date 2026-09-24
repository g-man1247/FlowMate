import asyncio
from datetime import datetime

from bleak import BleakClient, BleakScanner


WATCH_NAME = "Boult Watch SH"

HEART_RATE_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
BATTERY_UUID = "00002a19-0000-1000-8000-00805f9b34fb"


async def find_watch():
    print("Scanning for Boult Watch SH...")

    devices = await BleakScanner.discover(timeout=10)

    for device in devices:
        if device.name and WATCH_NAME.lower() in device.name.lower():
            print(f"Found: {device.name}")
            print(f"Address: {device.address}")
            return device

    return None


def heart_rate_handler(sender, data):
    if not data:
        return

    # Bluetooth Heart Rate Measurement format
    flags = data[0]

    # Bit 0:
    # 0 = HR is UINT8
    # 1 = HR is UINT16
    if flags & 0x01:
        if len(data) >= 3:
            heart_rate = int.from_bytes(data[1:3], "little")
        else:
            return
    else:
        heart_rate = data[1]

    timestamp = datetime.now().strftime("%H:%M:%S")

    print(f"[{timestamp}] ❤️ Heart Rate: {heart_rate} BPM")


def battery_handler(sender, data):
    if not data:
        return

    battery = data[0]

    timestamp = datetime.now().strftime("%H:%M:%S")

    print(f"[{timestamp}] 🔋 Battery: {battery}%")


async def main():

    print("=" * 60)
    print("FLOWMATE - BOULT DATA TEST")
    print("=" * 60)

    device = await find_watch()

    if device is None:
        print()
        print("❌ Boult Watch SH not found.")
        print("Wake the watch and keep it close to the laptop.")
        return

    print()
    print("Connecting...")

    async with BleakClient(device) as client:

        if not client.is_connected:
            print("❌ Connection failed.")
            return

        print("✅ Connected!")
        print()

        # Read initial battery
        try:
            battery_data = await client.read_gatt_char(BATTERY_UUID)
            battery = battery_data[0]
            print(f"🔋 Initial Battery: {battery}%")
        except Exception as e:
            print(f"Could not read battery: {e}")

        # Subscribe to heart rate
        await client.start_notify(
            HEART_RATE_UUID,
            heart_rate_handler
        )

        print("❤️ Heart-rate notifications enabled.")

        # Subscribe to battery
        try:
            await client.start_notify(
                BATTERY_UUID,
                battery_handler
            )

            print("🔋 Battery notifications enabled.")

        except Exception as e:
            print(f"Battery notifications unavailable: {e}")

        print()
        print("=" * 60)
        print("LISTENING FOR DATA")
        print("=" * 60)
        print("Keep the watch on your wrist.")
        print("Press Ctrl+C to stop.")
        print()

        try:
            while True:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass

        finally:

            try:
                await client.stop_notify(HEART_RATE_UUID)
            except Exception:
                pass

            try:
                await client.stop_notify(BATTERY_UUID)
            except Exception:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print("Stopped.")