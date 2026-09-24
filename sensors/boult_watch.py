import asyncio
from bleak import BleakClient, BleakScanner


class BoultWatch:

    DEVICE_NAME = "Boult Watch SH"

    HEART_RATE_UUID = (
        "00002a37-0000-1000-8000-00805f9b34fb"
    )

    BATTERY_UUID = (
        "00002a19-0000-1000-8000-00805f9b34fb"
    )

    def __init__(self):
        self.client = None
        self.connected = False
        self.heart_rate = None
        self.battery = None

    # ---------------------------------------------------------
    # HEART RATE
    # ---------------------------------------------------------

    def _heart_rate_callback(self, sender, data):

        if not data:
            return

        try:
            flags = data[0]

            if flags & 0x01:

                if len(data) < 3:
                    return

                self.heart_rate = int.from_bytes(
                    data[1:3],
                    byteorder="little"
                )

            else:

                if len(data) < 2:
                    return

                self.heart_rate = data[1]

            print(
                f"❤️ Heart Rate: {self.heart_rate} BPM"
            )

        except Exception as e:

            print(
                f"Heart-rate parsing error: {e}"
            )

    # ---------------------------------------------------------
    # BATTERY
    # ---------------------------------------------------------

    def _battery_callback(self, sender, data):

        if not data:
            return

        try:

            self.battery = data[0]

            print(
                f"🔋 Battery: {self.battery}%"
            )

        except Exception as e:

            print(
                f"Battery parsing error: {e}"
            )

    # ---------------------------------------------------------
    # FIND WATCH
    # ---------------------------------------------------------

    async def find_watch(self):

        print(
            "Scanning continuously for Boult Watch SH..."
        )

        print(
            "Keep the watch awake and close to the laptop."
        )

        print()

        for attempt in range(6):

            print(
                f"Scan {attempt + 1}/6..."
            )

            try:

                devices = await BleakScanner.discover(
                    timeout=5
                )

            except Exception as e:

                print(
                    f"Scan error: {e}"
                )

                continue

            for device in devices:

                name = device.name or ""

                if (
                    self.DEVICE_NAME.lower()
                    in name.lower()
                ):

                    print()
                    print("✅ Watch found!")

                    print(
                        f"Name: {device.name}"
                    )

                    print(
                        f"Address: {device.address}"
                    )

                    print()

                    return device

            await asyncio.sleep(1)

        return None

    # ---------------------------------------------------------
    # CONNECT
    # ---------------------------------------------------------

    async def connect(self):

        device = await self.find_watch()

        if device is None:

            print()
            print(
                "❌ Boult Watch SH was not found."
            )

            print()
            print(
                "Try waking the watch screen and "
                "run the program again."
            )

            return False

        try:

            print(
                f"Connecting to {device.name}..."
            )

            self.client = BleakClient(device)

            await self.client.connect()

            self.connected = (
                self.client.is_connected
            )

            if not self.connected:

                print(
                    "❌ Connection failed."
                )

                return False

            print(
                "✅ Connected successfully."
            )

            print()

            # -------------------------------------------------
            # BATTERY
            # -------------------------------------------------

            try:

                data = (
                    await self.client.read_gatt_char(
                        self.BATTERY_UUID
                    )
                )

                if data:

                    self.battery = data[0]

                    print(
                        f"🔋 Initial Battery: "
                        f"{self.battery}%"
                    )

            except Exception as e:

                print(
                    f"Battery read failed: {e}"
                )

            # -------------------------------------------------
            # HEART RATE
            # -------------------------------------------------

            try:

                await self.client.start_notify(
                    self.HEART_RATE_UUID,
                    self._heart_rate_callback
                )

                print(
                    "❤️ Heart-rate notifications enabled."
                )

            except Exception as e:

                print(
                    f"❌ Heart-rate notification failed: {e}"
                )

                await self.disconnect()

                return False

            # -------------------------------------------------
            # BATTERY NOTIFICATIONS
            # -------------------------------------------------

            try:

                await self.client.start_notify(
                    self.BATTERY_UUID,
                    self._battery_callback
                )

                print(
                    "🔋 Battery notifications enabled."
                )

            except Exception:

                print(
                    "Battery notifications unavailable."
                )

            print()

            return True

        except Exception as e:

            print(
                f"❌ Connection error: {e}"
            )

            self.connected = False

            return False

    # ---------------------------------------------------------
    # DISCONNECT
    # ---------------------------------------------------------

    async def disconnect(self):

        if self.client is None:
            return

        try:

            if self.client.is_connected:

                try:

                    await self.client.stop_notify(
                        self.HEART_RATE_UUID
                    )

                except Exception:
                    pass

                try:

                    await self.client.stop_notify(
                        self.BATTERY_UUID
                    )

                except Exception:
                    pass

                await self.client.disconnect()

        except Exception as e:

            print(
                f"Disconnect warning: {e}"
            )

        finally:

            self.connected = False
            self.client = None

    # ---------------------------------------------------------
    # DATA ACCESS
    # ---------------------------------------------------------

    def get_heart_rate(self):

        return self.heart_rate

    def get_battery(self):

        return self.battery

    def is_connected(self):

        return (
            self.client is not None
            and self.client.is_connected
        )


# =============================================================
# TEST PROGRAM
# =============================================================

async def test():

    watch = BoultWatch()

    print("=" * 60)
    print("FLOWMATE - BOULT WATCH TEST")
    print("=" * 60)
    print()

    connected = await watch.connect()

    if not connected:

        print()
        print(
            "❌ Could not connect to the watch."
        )

        return

    print("=" * 60)
    print("WATCH CONNECTED")
    print("=" * 60)

    print()

    print(
        f"Battery: {watch.get_battery()}%"
    )

    print()

    print(
        "Listening for heart-rate data..."
    )

    print(
        "Keep the watch on your wrist."
    )

    print(
        "Press Ctrl+C to stop."
    )

    print()

    try:

        while True:

            await asyncio.sleep(1)

    except KeyboardInterrupt:

        print()
        print(
            "Stopping..."
        )

    finally:

        await watch.disconnect()

        print(
            "Watch disconnected."
        )


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":

    asyncio.run(test())