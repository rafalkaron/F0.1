import uasyncio as asyncio
from f01.led import Led

async def test_leds() -> None:
    led_internal = Led()
    led_back_left = Led(12)
    led_back_right = Led(13)
    led_front_right = Led(14)
    led_front_left = Led(15)

    print("Test LED on (instant)")
    await asyncio.gather(
        led_internal.on(),
        led_front_left.on(),
        led_front_right.on(),
        led_back_left.on(),
        led_back_right.on()
    )

    print("Test LED off (smooth)")
    await asyncio.sleep(1)
    await asyncio.gather(
        led_internal.off(smooth=100),
        led_front_left.off(smooth=50),
        led_front_right.off(smooth=50),
        led_back_left.off(smooth=100),
        led_back_right.off(smooth=100)
    )
    await asyncio.sleep(2)

    print("Test LED on (smooth)")
    await asyncio.gather(
        led_internal.on(bright=100, smooth=100),
        led_front_left.on(bright=1, smooth=100),
        led_front_right.on(bright=100, smooth=100),
        led_back_left.on(bright=1, smooth=100),
        led_back_right.on(bright=100, smooth=100)
    )
    await asyncio.sleep(2)

    print("Test LED off (instant)")
    await asyncio.sleep(1)
    await asyncio.gather(
        led_internal.off(),
        led_front_left.off(),
        led_front_right.off(),
        led_back_left.off(),
        led_back_right.off()
    )
    await asyncio.sleep(2)

    print("Test LED brightness change (smooth)")
    await led_internal.on(bright=20, smooth=100)
    await asyncio.sleep(1)
    await led_internal.on(bright=80, smooth=100)
    await asyncio.sleep(1)
    await led_internal.off(smooth=100)
    await asyncio.sleep(1)

    print("Test LED blinking (smooth)")
    blinking_task = asyncio.create_task(asyncio.gather(
        led_internal.blink(500, bright=100, smooth=100),
        led_front_left.blink(1000, bright=100, smooth=100),
        led_front_right.blink(1000, bright=100, smooth=100),
        led_back_left.blink(500, bright=100, smooth=100),
        led_back_right.blink(500, bright=100, smooth=100),
    ))
    print("Leds are blinking in a non-blocking way (smooth transitions)")
    await asyncio.sleep(10)
    blinking_task.cancel()
    await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_leds())
