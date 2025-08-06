from machine import Pin, PWM
import uasyncio

class Motor:
    def __init__(self, in1_pin: int, in2_pin: int, freq: int = 1000, correction: float = 1.0) -> None:
        self.in1_pwm: PWM = PWM(Pin(in1_pin))
        self.in2_pwm: PWM = PWM(Pin(in2_pin))
        self.in1_pwm.freq(freq)
        self.in2_pwm.freq(freq)
        self._last_in1: int = 0
        self._last_in2: int = 0
        self.correction: float = correction

    def _map_speed(self, speed: int) -> int:
        """
        Map speed from 1-100 to 0-65535 for PWM, applying correction factor.
        """
        speed = max(-100, min(100, speed))
        speed = int(speed * self.correction)
        if speed == 0:
            return 0
        sign = 1 if speed > 0 else -1
        speed = max(1, min(100, abs(speed)))
        return sign * int((speed / 100) * 65535)

    async def _ramp_pwm(self, target_in1: int, target_in2: int, ramp_time: float = 0.1, steps: int = 3) -> None:
        """
        Helper to ramp PWM values for in1 and in2 pins independently.
        """
        current_in1 = self._last_in1
        current_in2 = self._last_in2
        if ramp_time <= 0 or steps <= 1 or (current_in1 == target_in1 and current_in2 == target_in2):
            self.in1_pwm.duty_u16(target_in1)
            self.in2_pwm.duty_u16(target_in2)
            self._last_in1 = target_in1
            self._last_in2 = target_in2
            return
        step_in1 = (target_in1 - current_in1) / steps
        step_in2 = (target_in2 - current_in2) / steps
        delay = ramp_time / steps
        for i in range(1, steps + 1):
            next_in1 = int(current_in1 + step_in1 * i)
            next_in2 = int(current_in2 + step_in2 * i)
            self.in1_pwm.duty_u16(next_in1)
            self.in2_pwm.duty_u16(next_in2)
            self._last_in1 = next_in1
            self._last_in2 = next_in2
            await uasyncio.sleep(delay)

    async def forward(self, speed: int, ramp_time: float = 0.1, steps: int = 3) -> None:
        """
        Set motor to move forward at given speed (1-100), with optional ramping.
        Only use ramping when starting from stop.
        """
        pwm = self._map_speed(speed)
        prev_stopped = self._last_in1 == 0 and self._last_in2 == 0
        if prev_stopped:
            await self._ramp_pwm(pwm, 0, ramp_time, steps)
        else:
            self.in1_pwm.duty_u16(pwm)
            self.in2_pwm.duty_u16(0)
            self._last_in1 = pwm
            self._last_in2 = 0

    async def backward(self, speed: int, ramp_time: float = 0.1, steps: int = 3) -> None:
        """
        Set motor to move backward at given speed (1-100), with optional ramping.
        Only use ramping when starting from stop.
        """
        pwm = self._map_speed(speed)
        prev_stopped = self._last_in1 == 0 and self._last_in2 == 0
        if prev_stopped:
            await self._ramp_pwm(0, pwm, ramp_time, steps)
        else:
            self.in1_pwm.duty_u16(0)
            self.in2_pwm.duty_u16(pwm)
            self._last_in1 = 0
            self._last_in2 = pwm

    async def stop(self, ramp_time: float = 0.1, steps: int = 3) -> None:
        """
        Gradually stop the motor with optional ramping.
        """
        await self._ramp_pwm(0, 0, ramp_time, steps)

    async def throttle(self, value: int, ramp_time: float = 0.1, steps: int = 3) -> None:
        """
        Set motor speed and direction with a single value (-100 to 100).
        Positive values move forward, negative values move backward.
        Deadzone: values between -25 and 25 are treated as zero.
        Use ramping when starting from stop, stopping to zero, or changing direction.
        """
        value = max(-100, min(100, value))
        prev_stopped = self._last_in1 == 0 and self._last_in2 == 0
        target_stopped = -25 < value < 25
        prev_forward = self._last_in1 > 0 and self._last_in2 == 0
        prev_backward = self._last_in2 > 0 and self._last_in1 == 0
        direction_change = (prev_forward and value < -25) or (prev_backward and value > 25)
        if target_stopped:
            # Stopping
            if not prev_stopped:
                await self._ramp_pwm(0, 0, ramp_time, steps)
            else:
                self.in1_pwm.duty_u16(0)
                self.in2_pwm.duty_u16(0)
                self._last_in1 = 0
                self._last_in2 = 0
        elif value > 0:
            pwm = self._map_speed(value)
            if prev_stopped or direction_change:
                await self._ramp_pwm(pwm, 0, ramp_time, steps)
            else:
                self.in1_pwm.duty_u16(pwm)
                self.in2_pwm.duty_u16(0)
                self._last_in1 = pwm
                self._last_in2 = 0
        else:
            pwm = self._map_speed(abs(value))
            if prev_stopped or direction_change:
                await self._ramp_pwm(0, pwm, ramp_time, steps)
            else:
                self.in1_pwm.duty_u16(0)
                self.in2_pwm.duty_u16(pwm)
                self._last_in1 = 0
                self._last_in2 = pwm
