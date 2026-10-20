# ae40.py (v3)
#   python ae40.py                      handshake
#   python ae40.py preset 3             troca de preset via AE40
#   python ae40.py read 0x10000000 64   leitura (testa type 0..4)
import asyncio, sys
from bleak import BleakClient

MAC = "C7:34:55:44:9C:4A"
WR  = "0000ae41-0000-1000-8000-00805f9b34fb"
NT  = "0000ae42-0000-1000-8000-00805f9b34fb"

def frame(cmd, payload=b""):
    n = len(payload); cks = (~sum(payload)) & 0xFF
    return bytes([0x00, 0x59, cmd, n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF]) + payload + bytes([cks])

def write(typ, addr, data):
    return frame(0x22, bytes([typ]) + addr.to_bytes(4, "little") + len(data).to_bytes(3, "little") + bytes(data))

def read(typ, addr, size):
    return frame(0x23, bytes([typ]) + addr.to_bytes(4, "little") + size.to_bytes(3, "little"))

async def main():
    c = BleakClient(MAC, timeout=25)
    for i in range(4):
        try: await c.connect(); break
        except Exception as e: print(f"tentativa {i+1}: {e}"); await asyncio.sleep(2)
    else: raise SystemExit("não conectou")
    await c.start_notify(NT, lambda _, b: print("RX", b.hex(" ")))

    async def tx(pkt, label):
        print(f"TX {label:16} {pkt.hex(' ')}")
        await c.write_gatt_char(WR, pkt, response=False)
        await asyncio.sleep(1.5)

    await tx(frame(0x11), "query")
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "preset":
        for typ in (0x04, 0x02):
            await tx(write(typ, 0xE0000000 + int(sys.argv[2]), [1]), f"preset t={typ:#04x}")
    elif mode == "read":
        addr, size = int(sys.argv[2], 0), int(sys.argv[3])
        for typ in range(5):
            await tx(read(typ, addr, size), f"read t={typ}")
    await asyncio.sleep(3)
    await c.disconnect()

asyncio.run(main())
