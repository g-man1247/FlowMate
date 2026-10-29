import asyncio
from bleak import BleakClient, BleakScanner


# ============================================================
# FLOWMATE - BOULT WATCH DEEP BLE INSPECTION
# ============================================================

WATCH_NAME = "Boult Watch SH"


# ============================================================
# STEP 1: SCAN FOR THE WATCH
# ============================================================

async def find_watch():
    """Scan nearby Bluetooth devices and find the Boult watch."""

    print("=" * 70)
    print("FLOWMATE - BOULT WATCH INSPECTION")
    print("=" * 70)
    print()
    print("Scanning for Boult Watch SH...")
    print("Keep the watch awake and close to the laptop.")
    print()

    try:
        devices = await BleakScanner.discover(timeout=10)
    except Exception as e:
        print(f"❌ Bluetooth scan failed: {e}")
        return None

    for device in devices:
        name = device.name or ""

        if WATCH_NAME.lower() in name.lower():
            print("✅ Watch found!")
            print(f"Name: {name}")
            print(f"Address: {device.address}")
            return device

    print("❌ Boult Watch SH was not found.")
    return None


# ============================================================
# STEP 2: READ A CHARACTERISTIC
# ============================================================

async def read_characteristic(client, uuid, name):
    """Read and display a BLE characteristic."""

    print()
    print(f"--- {name} ---")
    print(f"UUID: {uuid}")

    try:
        value = await client.read_gatt_char(uuid)

        print(f"Raw bytes: {value.hex(' ')}")

        # Try to decode the value as text.
        try:
            text = value.decode("utf-8", errors="replace")

            if text.strip():
                print(f"Text: {text}")

        except Exception:
            pass

    except Exception as e:
        print("Could not read characteristic.")
        print(f"Reason: {e}")


# ============================================================
# STEP 3: INSPECT THE WATCH
# ============================================================

async def inspect_watch(device):
    """Connect to the watch and inspect its BLE services."""

    print()
    print("Connecting to Boult Watch SH...")

    try:
        async with BleakClient(device) as client:

            if not client.is_connected:
                print("❌ Could not connect.")
                return

            print("✅ Connected successfully.")
            print()

            # ------------------------------------------------
            # Read standard Bluetooth information
            # ------------------------------------------------

            print("=" * 70)
            print("STANDARD BLE INFORMATION")
            print("=" * 70)

            standard_characteristics = [
                (
                    "00002a00-0000-1000-8000-00805f9b34fb",
                    "Device Name",
                ),
                (
                    "00002a25-0000-1000-8000-00805f9b34fb",
                    "Serial Number",
                ),
                (
                    "00002a26-0000-1000-8000-00805f9b34fb",
                    "Firmware Revision",
                ),
                (
                    "00002a28-0000-1000-8000-00805f9b34fb",
                    "Software Revision",
                ),
                (
                    "00002a29-0000-1000-8000-00805f9b34fb",
                    "Manufacturer",
                ),
                (
                    "00002a38-0000-1000-8000-00805f9b34fb",
                    "Body Sensor Location",
                ),
                (
                    "00002a19-0000-1000-8000-00805f9b34fb",
                    "Battery Level",
                ),
            ]

            for uuid, name in standard_characteristics:
                await read_characteristic(
                    client,
                    uuid,
                    name,
                )

            # ------------------------------------------------
            # Inspect every GATT service
            # ------------------------------------------------

            print()
            print("=" * 70)
            print("ALL GATT SERVICES")
            print("=" * 70)

            for service in client.services:

                print()
                print("SERVICE")
                print("-" * 70)
                print(f"UUID: {service.uuid}")
                print(f"Description: {service.description}")

                # Inspect all characteristics in this service.
                for characteristic in service.characteristics:

                    print()
                    print("  CHARACTERISTIC")
                    print("  " + "-" * 60)

                    print(f"  UUID: {characteristic.uuid}")
                    print(
                        f"  Description: "
                        f"{characteristic.description}"
                    )
                    print(
                        f"  Properties: "
                        f"{characteristic.properties}"
                    )

                    # Inspect characteristic descriptors.
                    for descriptor in characteristic.descriptors:

                        print()
                        print("    DESCRIPTOR")
                        print(
                            f"    UUID: "
                            f"{descriptor.uuid}"
                        )

                        try:
                            value = await client.read_gatt_descriptor(
                                descriptor.handle
                            )

                            print(
                                f"    Value: "
                                f"{value.hex(' ')}"
                            )

                        except Exception as e:
                            print(
                                f"    Could not read: "
                                f"{e}"
                            )

            # ------------------------------------------------
            # Inspection finished
            # ------------------------------------------------

            print()
            print("=" * 70)
            print("INSPECTION COMPLETE")
            print("=" * 70)

    except Exception as e:

        print()
        print("=" * 70)
        print("❌ CONNECTION ERROR")
        print("=" * 70)
        print(str(e))


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

async def main():
    """Start the watch inspection."""

    device = await find_watch()

    if device is None:
        return

    await inspect_watch(device)


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print()
        print("Inspection stopped by user.")