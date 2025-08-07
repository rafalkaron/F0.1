import gc

import uasyncio as asyncio

from f01.ap import AccessPoint
from f01.led import Led
from f01.motor import Motor
from f01.webserver import WebServer


class F01:
    def __init__(self) -> None:
        self.led_internal: Led = Led()
        self.led_back_left: Led = Led(12)
        self.led_back_right: Led = Led(13)
        self.led_front_right: Led = Led(14)
        self.led_front_left: Led = Led(15)
        self.left_motor: Motor = Motor(17, 18, correction=0.5)
        self.right_motor: Motor = Motor(19, 20)
        self.ap: AccessPoint = AccessPoint()
        self.ap.run()
        self.web_server: WebServer = WebServer()

    async def move(self, left_speed: int = 0, right_speed: int = 0) -> None:
        await asyncio.gather(
            self.left_motor.throttle(left_speed, ramp_time=0.1, steps=3),
            self.right_motor.throttle(right_speed, ramp_time=0.1, steps=3),
        )

    async def control_from_web_server(self) -> None:
        """Controls the motors based on web server input. LEDs are also updated based on motor speed.
        Implements simple debounce to avoid rapid command flooding."""
        try:
            # Debounce: Only update if values changed since last check
            if not hasattr(self, "_last_web_values"):
                self._last_web_values = (None, None)
            left_speed: int = (
                self.web_server.last_left
                if hasattr(self.web_server, "last_left")
                else 0
            )
            right_speed: int = (
                self.web_server.last_right
                if hasattr(self.web_server, "last_right")
                else 0
            )
            if (left_speed, right_speed) == self._last_web_values:
                await asyncio.sleep(0.005)  # Short delay to avoid busy loop
                return
            self._last_web_values = (left_speed, right_speed)

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
        blink_task = asyncio.create_task(
            self.led_internal.blink(interval_ms=500, bright=100, smooth=0)
        )
        while getattr(self.web_server, "_client_count", 0) == 0:
            await asyncio.sleep(0.1)
        blink_task.cancel()
        try:
            await blink_task
        except asyncio.CancelledError:
            pass
        await self.led_internal.on()

    async def monitor_ap(self) -> None:
        while True:
            if not self.ap.ap.active():
                print("[AP] Lost connection, re-enabling...")
                self.ap.ap.active(True)
            await asyncio.sleep(2)

    async def run(self) -> None:
        print("Running F0.1...")
        await asyncio.gather(
            self.led_front_left.on(bright=25, smooth=100),
            self.led_front_right.on(bright=25, smooth=100),
            self.led_back_left.on(bright=25, smooth=100),
            self.led_back_right.on(bright=25, smooth=100),
        )
        gc_counter = 0
        last_motor = (None, None)
        last_leds = (None, None, None, None)
        while True:
            try:
                # Prioritize motor control and change only on value change
                left_speed = self.web_server.last_left
                right_speed = self.web_server.last_right
                if (left_speed, right_speed) != last_motor:
                    await self.move(left_speed=left_speed, right_speed=right_speed)
                    last_motor = (left_speed, right_speed)
                # Only update LEDs if values changed
                led_front_left_bright = left_speed if left_speed > 25 else 25
                led_front_right_bright = right_speed if right_speed > 25 else 25
                led_back_left_bright = abs(left_speed) if left_speed < -25 else 25
                led_back_right_bright = abs(right_speed) if right_speed < -25 else 25
                leds = (
                    led_front_left_bright,
                    led_front_right_bright,
                    led_back_left_bright,
                    led_back_right_bright,
                )
                if leds != last_leds:
                    await asyncio.gather(
                        self.led_front_left.on(bright=led_front_left_bright, smooth=25),
                        self.led_front_right.on(
                            bright=led_front_right_bright, smooth=25
                        ),
                        self.led_back_left.on(bright=led_back_left_bright, smooth=25),
                        self.led_back_right.on(bright=led_back_right_bright, smooth=25),
                    )
                    last_leds = leds
            except Exception as e:
                print(f"[run loop] Error: {e}")
            await asyncio.sleep(0.01)
            gc_counter += 1
            if gc_counter >= 500:
                gc.collect()
                gc_counter = 0


if __name__ == "__main__":
    try:
        f01 = F01()
        loop = asyncio.get_event_loop()
        loop.create_task(f01.web_server.run())
        loop.create_task(f01.run())
        loop.create_task(f01.blink_internal_led_until_connected())
        loop.create_task(f01.monitor_ap())
        loop.run_forever()
    except Exception as e:
        print(f"[main] Error: {e}")
