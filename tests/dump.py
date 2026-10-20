# dump.py — python dump.py 0x10000000 2048 antes.bin
import asyncio, sys
from bleak import BleakClient

MAC = "C7:34:55:44:9C:4A"
WR  = "0000ae41-0000-1000-8000-00805f9b34fb"
NT  = "0000ae42-0000-1000-8000-00805f9b34fb"
CHUNK = 1000                                   # app usa no máximo 1015

def frame(cmd, payload=b""):
    n = len(payload); cks = (~sum(payload)) & 0xFF
    return bytes([0, 0x59, cmd, n & 0xFF, n >> 8 & 0xFF, n >> 16 & 0xFF]) + payload + bytes([cks])

def read(addr, size):
    return frame(0x23, bytes([4]) + addr.to_bytes(4, "little") + size.to_bytes(3, "little"))

async def main():
    base, total, out = int(sys.argv[1], 0), int(sys.argv[2]), sys.argv[3]
    buf, q = bytearray(), asyncio.Queue()
    async with BleakClient(MAC, timeout=25) as c:
        await c.start_notify(NT, lambda _, b: q.put_nowait(bytes(b)))
        for off in range(0, total, CHUNK):
            size = min(CHUNK, total - off)
            await c.write_gatt_char(WR, read(base + off, size), response=False)
            resp = b""
            while len(resp) < 14 + size + 1:           # resposta pode vir em vários pacotes BLE
                resp += await asyncio.wait_for(q.get(), 5)
            if resp[2] != 0x23: raise SystemExit(f"erro em {base+off:#x}: {resp.hex(' ')}")
            buf += resp[14:14 + size]
            print(f"{base+off:#010x} ok ({size} bytes)")
    open(out, "wb").write(buf)
    print("salvo em", out)

asyncio.run(main())
