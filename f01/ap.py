import network


class AccessPoint:
    def __init__(self, essid: str = "F0.1", password: str = "F0.1-okoń") -> None:
        self.essid: str = essid
        self.password: str = password

    def run(self) -> None:
        self.ap = network.WLAN(network.AP_IF)
        self.ap.config(essid=self.essid, password=self.password)
        self.ap.active(True)
        print("F0.1 IP address:", self.ap.ifconfig()[0])
        # Reconnection logic: check and reconnect if AP goes down
        import uasyncio as asyncio

        async def monitor_ap():
            while True:
                if not self.ap.active():
                    print("[AP] Lost connection, re-enabling...")
                    self.ap.active(True)
                await asyncio.sleep(2)

        try:
            import _thread

            _thread.start_new_thread(asyncio.run, (monitor_ap(),))
        except Exception as e:
            print("[AP] Could not start monitor thread:", e)
