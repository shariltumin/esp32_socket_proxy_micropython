# pico_config.py
from machine import UART, Pin

UART_ID = 0
BAUD = 1_400_000
TX = 0
RX = 1
CTS = 2
RTS = 3

def uart_setup():
    try:
        rxbuf=16384
        uart = UART(
            UART_ID, baudrate=BAUD,
            tx=Pin(TX), rx=Pin(RX),
            rts=Pin(RTS), cts=Pin(CTS),
            timeout=0, rxbuf=rxbuf,
            flow=UART.RTS | UART.CTS,
        )
        print(f"UART: {BAUD} baud, rxbuf={rxbuf}, flow=ON, timeout=0")
        print(f"PINS: tx={TX}, rx={RX}, rts={RTS}, cts={CTS}")
    except TypeError:
        rxbuf=8192
        uart = UART(
            UART_ID, baudrate=BAUD,
            tx=Pin(TX), rx=Pin(RX),
            timeout=0, rxbuf=rxbuf,
        )
        print(f"UART: {BAUD} baud, rxbuf={rxbuf}, flow=OFF, timeout=0")
        print(f"PINS: tx={TX}, rx={RX}")
    except Exception as e:
        print(f"UART setup error: {e}")
        raise
    return uart

