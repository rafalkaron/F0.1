import uasyncio as asyncio
from f01.motor import Motor

async def test_motors() -> None:
    left_motor = Motor(17, 18)
    right_motor = Motor(19, 20)

    print("Test motor throttle")
    await asyncio.gather(
        left_motor.throttle(100),
        right_motor.throttle(100)
    )
    await asyncio.sleep(1)
    await asyncio.gather(
        left_motor.throttle(50),
        right_motor.throttle(50)
    )
    await asyncio.sleep(1)
    await asyncio.gather(
        left_motor.throttle(25),
        right_motor.throttle(25)
    )
    await asyncio.sleep(1)
    await asyncio.gather(
        left_motor.throttle(0),
        right_motor.throttle(0)
    )
    await asyncio.sleep(1)
    await asyncio.gather(
        left_motor.throttle(-25),
        right_motor.throttle(-25)
    )
    await asyncio.sleep(1)
    await asyncio.gather(
        left_motor.throttle(-50),
        right_motor.throttle(-50)
    )
    await asyncio.sleep(1)
    await asyncio.gather(
        left_motor.throttle(-100),
        right_motor.throttle(-100)
    )
    await asyncio.sleep(1)
    print("Test motor throttle with ramp_time and steps")
    await asyncio.gather(
        left_motor.throttle(75, ramp_time=0.5, steps=5),
        right_motor.throttle(75, ramp_time=0.5, steps=5)
    )
    await asyncio.sleep(1)
    print("Test motor forward")
    await asyncio.gather(
        left_motor.forward(100),
        right_motor.forward(100)
    )
    await asyncio.sleep(1)
    await asyncio.gather(
        left_motor.forward(50),
        right_motor.forward(50)
    )
    await asyncio.sleep(1)
    print("Test motor forward with ramp_time and steps")
    await asyncio.gather(
        left_motor.forward(80, ramp_time=0.6, steps=8),
        right_motor.forward(80, ramp_time=0.6, steps=8)
    )
    await asyncio.sleep(1)
    print("Test motor backward")
    await asyncio.gather(
        left_motor.backward(100),
        right_motor.backward(100)
    )
    await asyncio.sleep(1)
    await asyncio.gather(
        left_motor.backward(50),
        right_motor.backward(50)
    )
    await asyncio.sleep(1)
    print("Test motor backward with ramp_time and steps")
    await asyncio.gather(
        left_motor.backward(60, ramp_time=0.4, steps=4),
        right_motor.backward(60, ramp_time=0.4, steps=4)
    )
    await asyncio.sleep(1)
    print("Test motor stop")
    await asyncio.gather(
        left_motor.stop(),
        right_motor.stop()
    )
    await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_motors())
