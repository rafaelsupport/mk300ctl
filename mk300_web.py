#!/usr/bin/env python3
"""
mk300_web.py — Servidor Web local para a interface de navegador do mk300ctl.

Como usar:
  ./mk300_web.py              abre em http://localhost:8080
  ./mk300_web.py --port 8000  usa outra porta
  ./mk300_web.py --mac XX:..  usa outro endereço MAC

No navegador você pode conectar de duas formas:
  1. Direto pelo navegador (Web Bluetooth API no Chrome/Brave/Edge)
  2. Pela Ponte Local (Bleak) — funciona em qualquer navegador (incluindo Firefox)
     e libera automaticamente a conexão do BlueZ no Linux.
"""
import asyncio, base64, json, mimetypes, os, sys, urllib.parse
from mk300ctl import MAC, TYPE, MK300, PedalError, Log, check_adapter, release_bluez, connect

ROOT = os.path.dirname(os.path.abspath(__file__))


class BridgeState:
    def __init__(self, mac):
        self.mac = mac
        self.client = None
        self.mk = None
        self.model = None
        self.lock = asyncio.Lock()

    async def ensure_connected(self):
        async with self.lock:
            if self.client and self.client.is_connected and self.mk:
                return self.model
            check_adapter()
            release_bluez(self.mac)
            self.client = await connect(self.mac, 10.0)
            self.mk = MK300(self.client)
            self.model = await self.mk.start()
            return self.model

    async def disconnect(self):
        async with self.lock:
            if self.client and self.client.is_connected:
                await self.client.disconnect()
            self.client = None
            self.mk = None
            self.model = None


async def handle_http(reader, writer, state: BridgeState):
    try:
        req_line = await asyncio.wait_for(reader.readline(), timeout=5)
        if not req_line:
            writer.close()
            return
        method, raw_path, _ = req_line.decode("latin-1").strip().split(" ", 2)
        headers = {}
        while True:
            line = await reader.readline()
            if line in (b"\r\n", b"\n", b""):
                break
            if b":" in line:
                k, v = line.decode("latin-1").split(":", 1)
                headers[k.strip().lower()] = v.strip()

        content_len = int(headers.get("content-length", "0"))
        body = await reader.readexactly(content_len) if content_len > 0 else b""
        parsed = urllib.parse.urlparse(raw_path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        def send_json(status, payload):
            raw = json.dumps(payload).encode("utf-8")
            hdr = (
                f"HTTP/1.1 {status}\r\n"
                f"Content-Type: application/json; charset=utf-8\r\n"
                f"Content-Length: {len(raw)}\r\n"
                f"Cache-Control: no-store\r\n"
                f"Connection: close\r\n\r\n"
            ).encode("latin-1")
            writer.write(hdr + raw)

        if path == "/api/ping":
            send_json("200 OK", {"ok": True, "mac": state.mac})
        elif path == "/api/connect" and method == "POST":
            try:
                model = await state.ensure_connected()
                send_json("200 OK", {"ok": True, "model": model})
            except PedalError as e:
                send_json("500 Internal Server Error", {"error": str(e), "hints": list(e.hints)})
            except Exception as e:
                send_json("500 Internal Server Error", {"error": f"{type(e).__name__}: {e}"})
        elif path == "/api/disconnect" and method == "POST":
            await state.disconnect()
            send_json("200 OK", {"ok": True})
        elif path == "/api/read" and method == "GET":
            try:
                await state.ensure_connected()
                addr = int(qs["addr"][0], 0)
                size = int(qs["size"][0], 0)
                typ = int(qs.get("typ", [str(TYPE)])[0], 0)
                async with state.lock:
                    data = await state.mk.read(addr, size, typ)
                send_json("200 OK", {"data": base64.b64encode(data).decode("ascii")})
            except Exception as e:
                send_json("500 Internal Server Error", {"error": str(e)})
        elif path == "/api/write" and method == "POST":
            try:
                await state.ensure_connected()
                payload = json.loads(body.decode("utf-8"))
                addr = int(payload["addr"])
                data = base64.b64decode(payload["data"])
                async with state.lock:
                    await state.mk.write(addr, data)
                send_json("200 OK", {"ok": True})
            except Exception as e:
                send_json("500 Internal Server Error", {"error": str(e)})
        else:
            rel = "index.html" if path in ("/", "/index.html") else path.lstrip("/")
            full = os.path.realpath(os.path.join(ROOT, rel))
            if not full.startswith(ROOT) or not os.path.isfile(full):
                send_json("404 Not Found", {"error": "Not found"})
            else:
                with open(full, "rb") as f:
                    data = f.read()
                ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
                hdr = (
                    f"HTTP/1.1 200 OK\r\n"
                    f"Content-Type: {ctype}\r\n"
                    f"Content-Length: {len(data)}\r\n"
                    f"Cache-Control: no-cache\r\n"
                    f"Connection: close\r\n\r\n"
                ).encode("latin-1")
                writer.write(hdr + data)

        await writer.drain()
    except Exception:
        pass
    finally:
        writer.close()


async def serve(host, port, mac):
    state = BridgeState(mac)
    server = await asyncio.start_server(lambda r, w: handle_http(r, w, state), host, port)
    Log.ok(f"Interface Web rodando em: http://{host}:{port}")
    Log.step(f"MAC configurado para a Ponte Local: {mac} (use --mac para alterar)")
    Log.step("Pressione Ctrl+C para encerrar.")
    try:
        async with server:
            await server.serve_forever()
    finally:
        await state.disconnect()


def main(argv):
    host, port, mac = "127.0.0.1", 8080, MAC
    it = iter(argv)
    for a in it:
        if a == "--port": port = int(next(it, "8080"))
        elif a == "--host": host = next(it, "127.0.0.1")
        elif a == "--mac": mac = next(it, MAC)
        elif a in ("-v", "--verbose"): Log.verbose = True
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
    try:
        asyncio.run(serve(host, port, mac))
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
