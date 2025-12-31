import time
import network
import ntptime
from machine import UART, Pin

SSID, PASSWORD = "YOUR-SSID", "YOUR-PWD"

UART_ID = 0
BAUD = 1_400_000
TX = 8
RX = 9
RTS = 4
CTS = 5

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
            timeout=0, rxbuf=rxbuf
        )
        print(f"UART: {BAUD} baud, rxbuf={rxbuf}, flow=OFF, timeout=0")
        print(f"PINS: tx={TX}, rx={RX}")
    except Exception as e:
        print(f"UART setup error: {e}")
        raise
    return uart

def wifi_connect(max_retries=40, retry_delay_ms=250):
    network.WLAN(network.AP_IF).active(False)
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        print("Connecting WiFi...")
        sta.connect(SSID, PASSWORD)
        for i in range(max_retries):
            if sta.isconnected():
                break
            time.sleep_ms(retry_delay_ms)
            if (i + 1) % 10 == 0:
                print(f"  Still connecting... ({i+1}/{max_retries})")
    if not sta.isconnected():
        sta.active(False)
        raise RuntimeError("WiFi connection failed")
    print("WiFi OK:", sta.ifconfig()[0])
    return sta

def set_time(host='pool.ntp.org'): # default to global ntp servers pool
    ntptime.host = host
    try:
        ntptime.timeout = 10
        ntptime.settime()  # Syncs time with an NTP server.
                           # Important when working with CERT
    except Exception as e:
        print(f'ntptime error: {e}')
        return False
    return True

