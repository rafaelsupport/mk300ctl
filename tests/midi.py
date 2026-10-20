# midi.py — uso:
#   python midi.py listen          (mostra tudo que a pedaleira envia)
#   python midi.py pc 5            (Program Change para o preset 5)
#   python midi.py cc 20 127       (Control Change 20 = 127)
import asyncio, sys
from bleak import BleakClient

MAC  = "C7:34:55:44:9C:4A"
CHAR = "7772e5db-3868-4112-a1a9-f2669d106bf3"   # característica BLE-MIDI I/O
CH   = 0                                        # canal MIDI 1

def ble(msg):                       # header + timestamp + mensagem MIDI
    return bytes([0x80, 0x80]) + bytes(msg)

async def main():
    async with BleakClient(MAC) as c:
        await c.start_notify(CHAR, lambda _, b: print("RX", b.hex(" ")))
        cmd = sys.argv[1] if len(sys.argv) > 1 else "listen"
        if cmd == "pc":
            await c.write_gatt_char(CHAR, ble([0xC0 | CH, int(sys.argv[2]) & 0x7F]), response=False)
        elif cmd == "cc":
            await c.write_gatt_char(CHAR, ble([0xB0 | CH, int(sys.argv[2]) & 0x7F, int(sys.argv[3]) & 0x7F]), response=False)
        print("ouvindo 30s... mexa na pedaleira (troque preset, liga/desliga efeito, gira knob)")
        await asyncio.sleep(30)

asyncio.run(main())
