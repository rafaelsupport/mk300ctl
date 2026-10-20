# diag.py — uso: python diag.py            (lista tudo)
#                python diag.py MK300      (conecta e lista serviços)
import asyncio, sys
from bleak import BleakScanner, BleakClient

async def main():
    found = await BleakScanner.discover(timeout=8, return_adv=True)
    for addr, (d, adv) in sorted(found.items(), key=lambda x: -x[1][1].rssi):
        print(f"{addr}  rssi={adv.rssi:4}  nome={adv.local_name or d.name!s:20}  uuids={adv.service_uuids}")
    if len(sys.argv) < 2: return
    alvo = sys.argv[1].lower()
    dev = next((d for a,(d,adv) in found.items()
                if alvo in a.lower() or alvo in (adv.local_name or d.name or "").lower().replace("-","")), None)
    if not dev: return print("alvo não encontrado")
    async with BleakClient(dev) as c:
        for s in c.services:
            print("SERVIÇO", s.uuid, s.description)
            for ch in s.characteristics:
                print("   ", ch.uuid, ch.properties)

asyncio.run(main())
