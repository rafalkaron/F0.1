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
