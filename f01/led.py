import uasyncio
from machine import Pin, PWM

class Led:
    def __init__(self, pin_name: str = "LED") -> None:
        self.pin: Pin = Pin(pin_name, Pin.OUT)
        try:
            self.pwm: PWM | None = PWM(self.pin)
            self.pwm.freq(1000)
        except (ValueError, TypeError):
            self.pwm = None

    def _set_pwm(self, bright: float) -> None:
        duty = int(65535 * (bright / 100))
        self.pwm.duty_u16(duty)

    def _get_pwm(self) -> int:
        try:
            return self.pwm.duty_u16()
        except AttributeError:
            return 0

    async def _smooth_transition(self, target_bright: float, duration_ms: int = 1000) -> None:
        if self.pwm is None:
            self.pin.value(1 if target_bright > 0 else 0)
            return
        current = self._get_pwm() / 65535 * 100
        steps = 20
        step_time = duration_ms // steps
        for i in range(1, steps + 1):
            bright = current + (target_bright - current) * i / steps
            self._set_pwm(bright)
            await uasyncio.sleep_ms(step_time)

    async def on(self, bright: float = 100, smooth: float = 0) -> None:
        if smooth == 0:
            if self.pwm is not None:
                self._set_pwm(bright)
            else:
                self.pin.value(1)
        else:
            await self._smooth_transition(bright, duration_ms=int(1000 * (smooth / 100)))

    async def off(self, smooth: float = 0) -> None:
        if smooth == 0:
            if self.pwm is not None:
                self._set_pwm(0)
            else:
                self.pin.value(0)
        else:
            await self._smooth_transition(0, duration_ms=int(1000 * (smooth / 100)))

    async def toggle(self, bright: float = 100, smooth: float = 0) -> None:
        if self.pwm is not None:
            if self._get_pwm() == 0:
                await self.on(bright=bright, smooth=smooth)
            else:
                await self.off(smooth=smooth)
        else:
            self.pin.value(not self.pin.value())

    async def blink(self, interval_ms: int = 500, bright: float = 100, smooth: float = 0) -> None:
        while True:
            await self.toggle(bright=bright, smooth=smooth)
            await uasyncio.sleep_ms(interval_ms)
