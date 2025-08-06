import uasyncio as asyncio
from f01.motor import Motor
from f01.led import Led
from f01.ap import AccessPoint
from f01.webserver import WebServer

class F01:
    def __init__(self) -> None:
        # Initialize hardware components
        self.led_internal: Led = Led()
        self.led_back_left: Led = Led(12)
        self.led_back_right: Led = Led(13)
        self.led_front_right: Led = Led(14)
        self.led_front_left: Led = Led(15)
        self.left_motor: Motor = Motor(17, 18, correction=0.5)
        self.right_motor: Motor = Motor(19, 20)

        # Initialize access point
        self.ap: AccessPoint = AccessPoint()
        self.ap.run()
        # Initialize web server
        self.web_server: WebServer = WebServer()

    async def move(self, left_speed: int = 0, right_speed: int = 0) -> None:
        # Use throttle to allow both forward and backward motion
        await asyncio.gather(
            self.left_motor.throttle(left_speed, ramp_time=0.1, steps=3),
            self.right_motor.throttle(right_speed, ramp_time=0.1, steps=3)
        )

    async def stop(self) -> None:
        await asyncio.gather(
            self.left_motor.stop(),
            self.right_motor.stop()
        )

    async def control_from_web_server(self) -> None:
        """ Controls the motors based on web server input. LEDs are also updated based on motor speed. """
        try:
            left_speed: int = self.web_server.last_left if hasattr(self.web_server, "last_left") else 0
            right_speed: int = self.web_server.last_right if hasattr(self.web_server, "last_right") else 0

            led_front_left_bright: int = left_speed if left_speed > 25 else 25
            led_front_right_bright: int = right_speed if right_speed > 25 else 25
            led_back_left_bright: int = abs(left_speed) if left_speed < -25 else 25
            led_back_right_bright: int = abs(right_speed) if right_speed < -25 else 25

            await asyncio.gather(
                self.move(left_speed=left_speed, right_speed=right_speed),
                self.led_front_left.on(bright=led_front_left_bright, smooth=25),
                self.led_front_right.on(bright=led_front_right_bright, smooth=25),
                self.led_back_left.on(bright=led_back_left_bright, smooth=25),
                self.led_back_right.on(bright=led_back_right_bright, smooth=25),
            )
        except Exception as e:
            print(f"[control_from_web_server] Error: {e}")

    async def blink_internal_led_until_connected(self) -> None:
        """Blink internal LED using its blink method until at least one client is connected, then keep it on."""
        blink_task = asyncio.create_task(self.led_internal.blink(interval_ms=500, bright=100, smooth=0))
        while getattr(self.web_server, "_client_count", 0) == 0:
            await asyncio.sleep(0.1)
        blink_task.cancel()
        try:
            await blink_task
        except asyncio.CancelledError:
            pass
        await self.led_internal.on()

    async def run(self) -> None:
        print("Running F0.1...")
        await asyncio.gather(
            self.led_front_left.on(bright=25, smooth=100),
            self.led_front_right.on(bright=25, smooth=100),
            self.led_back_left.on(bright=25, smooth=100),
            self.led_back_right.on(bright=25, smooth=100),
        )
        while True:
            await self.control_from_web_server()
            await asyncio.sleep(0.05)

if __name__ == "__main__":
    try:
        f01 = F01()
        loop = asyncio.get_event_loop()
        loop.create_task(f01.web_server.run())
        loop.create_task(f01.run())
        loop.create_task(f01.blink_internal_led_until_connected())
        loop.run_forever()
    except Exception as e:
        print(f"[main] Error: {e}")
