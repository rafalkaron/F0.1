import time

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


class Station:
    def __init__(self, ssid: str, password: str) -> None:
        self.ssid: str = ssid
        self.password: str = password
        self.sta: network.WLAN | None = None

    def connect(self, timeout: int = 10) -> bool:
        if self.sta is None:
            self.sta = network.WLAN(network.STA_IF)
            self.sta.active(True)
        if self.sta.isconnected():
            print("Already connected.")
            return True
        else:
            print("Connecting to WiFi...")
            self.sta.disconnect()
            self.sta.connect(self.ssid, self.password)
        start: float = time.time()
        while not self.sta.isconnected():
            if time.time() - start > timeout:
                print("Connection timed out")
                return False
            time.sleep(0.5)
        print("Connected, IP address:", self.sta.ifconfig()[0])
        return True
