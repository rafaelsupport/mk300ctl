#!/usr/bin/env python3
"""
mk300ctl — controle da M-Vave MK-300 via Bluetooth LE (protocolo AE40 do app M-EFCS + BLE-MIDI)

Uso:
  mk300ctl.py info                     mostra o preset em edição
  mk300ctl.py preset 12                troca para o preset 13 (0-based, vai até 159)
  mk300ctl.py pc 5                     Program Change via BLE-MIDI (0-127)
  mk300ctl.py on  DLY                  liga módulo
  mk300ctl.py off FX                   desliga módulo
  mk300ctl.py toggle REV               inverte módulo
  mk300ctl.py vol 70                   Preset Vol            
  mk300ctl.py bpm 120                  BPM 40-240
  mk300ctl.py pan -20                  Pan -100..100
  mk300ctl.py dump preset.bin          salva o preset em edição (448 bytes)
  mk300ctl.py names                    lê do pedal os nomes dos presets, AMPs, CABs e DSs (salva em mk300_names.json)
  mk300ctl.py presets                  lista os 160 presets (usa o cache; rode "names" antes)
  mk300ctl.py params                   mostra tipo e 12 parâmetros de cada módulo
  mk300ctl.py param AMP 0 80           escreve parâmetro 0 do AMP = 80 (int16)
  mk300ctl.py param AMP gain 80        idem, pelo nome (quando o catálogo conhece)

Vários comandos na mesma conexão:  mk300ctl.py preset 3 off DLY on FX info

Opções (antes dos comandos):
  -v, --verbose     mostra cada pacote enviado/recebido (TX/RX em hex)
  --debug           em caso de erro, mostra o traceback completo
  -q, --quiet       mostra só o resultado dos comandos, sem as mensagens de progresso
  --mac XX:..:XX    usa outro endereço Bluetooth
  --timeout N       segundos procurando o pedal (padrão 10)

As mensagens de progresso vão para stderr; o resultado dos comandos vai para stdout.

Módulos: WAH FX GATE DS AMP CAB EQ MOD DLY REV VOL
Alterações vão para o buffer de edição (LED do SAVE pisca); só ficam gravadas se salvar no pedal.
"""
import asyncio, json, os, shutil, subprocess, sys, time
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
from mk300_catalog import type_name, param_names

MAC  = "C7:34:55:44:9C:4A"
WR   = "0000ae41-0000-1000-8000-00805f9b34fb"
NT   = "0000ae42-0000-1000-8000-00805f9b34fb"
MIDI = "7772e5db-3868-4112-a1a9-f2669d106bf3"

MODS = ["WAH", "FX", "GATE", "DS", "AMP", "CAB", "EQ", "MOD", "DLY", "REV", "VOL"]
TYPE      = 0x04
BUF       = 0x10000000      # preset em edição (ao vivo)
SWITCH    = 0xE0000000      # + índice do preset
GLOB      = 0x20000000      # dados globais; byte 1 = preset atual (getGlobPatchIndex no app)
OFF_NAME, OFF_COLOR, OFF_VOL, OFF_BPM, OFF_PAN = 0, 20, 24, 26, 28
OFF_CHAIN, OFF_EN, OFF_UNIT, OFF_PARA = 32, 43, 54, 66
PARAMS_PER_MOD = 12        # 11 módulos x 12 int16 = 264 bytes
PATCH_SIZE = 448            # sizeof(TPatch) no app
# ProductConfig da MK-300 no app (Obj!ProductConfig@923ef1)
PRESET_COUNT, PRESET_NAME_LEN, PRESET_NAMES = 160, 17, 0x70200000
RESOURCES = {"CAB": (100, 0x80000000), "AMP": (120, 0x90000000), "DS": (40, 0xA0000000)}
RES_NAME_LEN, RES_TYPE = 14, 0x05
NAMES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mk300_names.json")
READ_CHUNK = 1000


def frame(cmd, payload=b""):
    n = len(payload)
    cks = (~sum(payload)) & 0xFF
    return bytes([0x00, 0x59, cmd, n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF]) + payload + bytes([cks])


class Log:
    """Mensagens de progresso no stderr, com cor quando é um terminal."""
    verbose = False
    quiet = False
    _t0 = time.monotonic()
    _color = sys.stderr.isatty()

    @classmethod
    def _out(cls, sym, color, msg):
        t = time.monotonic() - cls._t0
        if cls._color:
            sys.stderr.write(f"\033[2m{t:6.1f}s\033[0m \033[{color}m{sym}\033[0m {msg}\n")
        else:
            sys.stderr.write(f"{t:6.1f}s {sym} {msg}\n")
        sys.stderr.flush()

    @classmethod
    def step(cls, msg):
        if not cls.quiet: cls._out("…", "36", msg)

    @classmethod
    def ok(cls, msg):
        if not cls.quiet: cls._out("✓", "32", msg)

    @classmethod
    def warn(cls, msg):
        cls._out("!", "33", msg)

    @classmethod
    def error(cls, msg):
        cls._out("✗", "31", msg)

    @classmethod
    def hint(cls, msg):
        cls._out(" ", "2", msg)

    @classmethod
    def debug(cls, msg):
        if cls.verbose: cls._out("·", "2", msg)


class PedalError(Exception):
    """Erro com mensagem amigável e dicas para o usuário."""
    def __init__(self, msg, hints=(), code=1):
        super().__init__(msg)
        self.hints, self.code = hints, code


def load_cache():
    try:
        with open(NAMES_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


CACHE = load_cache()


class MK300:
    def __init__(self, client):
        self.c = client
        self.q = asyncio.Queue()

    async def start(self):
        await self.c.start_notify(NT, lambda _, b: self.q.put_nowait(bytes(b)))
        r = await self._xfer(frame(0x11), 7)
        return r[6:6 + int.from_bytes(r[3:6], "little")].split(b"\0")[0].decode(errors="replace")

    async def _xfer(self, pkt, minlen):
        while not self.q.empty():
            self.q.get_nowait()
        Log.debug(f"TX {pkt.hex(' ')}")
        await self.c.write_gatt_char(WR, pkt, response=False)
        resp = b""
        try:
            while len(resp) < minlen or len(resp) < 7 + int.from_bytes(resp[3:6], "little"):
                resp += await asyncio.wait_for(self.q.get(), 5)
        except asyncio.TimeoutError:
            raise PedalError("o pedal não respondeu ao comando (timeout de 5s)",
                             ["a conexão pode ter caído; rode o comando de novo",
                              "use -v para ver os pacotes trocados"]) from None
        Log.debug(f"RX {resp.hex(' ') if len(resp) <= 48 else resp[:48].hex(' ') + f' … ({len(resp)} bytes)'}")
        return resp

    async def read(self, addr, size, typ=TYPE):
        if size > READ_CHUNK:
            out = bytearray()
            for off in range(0, size, READ_CHUNK):
                Log.debug(f"lendo {addr + off:#010x} ({min(READ_CHUNK, size - off)} bytes)")
                out += await self.read(addr + off, min(READ_CHUNK, size - off), typ)
            return bytes(out)
        pkt = frame(0x23, bytes([typ]) + addr.to_bytes(4, "little") + size.to_bytes(3, "little"))
        r = await self._xfer(pkt, 15)
        if r[2] != 0x23:
            raise PedalError(f"o pedal recusou a leitura em {addr:#x}",
                             [f"resposta: {r[:16].hex(' ')}"])
        return r[14:14 + size]

    async def write(self, addr, data):
        data = bytes(data)
        pkt = frame(0x22, bytes([TYPE]) + addr.to_bytes(4, "little") + len(data).to_bytes(3, "little") + data)
        r = await self._xfer(pkt, 8)
        if not (r[2] == 0 and r[6] == 0):
            raise PedalError(f"o pedal recusou a escrita em {addr:#x}",
                             [f"resposta: {r[:16].hex(' ')}"])

    async def midi(self, msg):
        await self.c.write_gatt_char(MIDI, bytes([0x80, 0x80]) + bytes(msg), response=False)

    # ---- comandos de alto nível ----
    async def info(self):
        idx = (await self.read(GLOB, 2))[1]
        d = await self.read(BUF, 64)
        u16 = lambda o: int.from_bytes(d[o:o + 2], "little")
        name = d[OFF_NAME:OFF_NAME + 20].split(b"\0")[0].decode(errors="replace")
        print(f"Preset: [{idx + 1:03}]  (índice {idx}; use \"preset {idx}\")")
        saved = (CACHE.get("presets") or [])
        if idx < len(saved) and saved[idx] and saved[idx] != name:
            Log.debug(f"nome salvo no slot {idx + 1}: {saved[idx]!r} (o preset em edição pode ter sido renomeado)")
        print("Nome  :", name)
        print("Cor   : #%06X" % int.from_bytes(d[OFF_COLOR:OFF_COLOR + 4], "little"))
        print("Vol   :", u16(OFF_VOL), "  BPM:", u16(OFF_BPM),
              "  Pan:", int.from_bytes(d[OFF_PAN:OFF_PAN + 2], "little", signed=True))
        chain = [MODS[i] if d[OFF_EN + i] else MODS[i].lower() for i in d[OFF_CHAIN:OFF_CHAIN + 11]]
        print("Chain :", " → ".join(chain))

    async def preset(self, n):
        if not 0 <= n <= 159:
            raise PedalError("preset deve ser 0-159")
        await self.write(SWITCH + n, [1])
        await asyncio.sleep(0.8)          # tempo para o pedal carregar o preset

    async def module(self, name, mode):
        mid = MODS.index(name.upper())
        cur = (await self.read(BUF + OFF_EN + mid, 1))[0]
        new = {"on": 1, "off": 0, "toggle": 0 if cur else 1}[mode]
        if new != cur:
            await self.write(BUF + OFF_EN + mid, [new])
        print(f"{MODS[mid]}: {'ON' if new else 'off'}")

    async def names(self):
        def split(buf, n):
            return [buf[i:i + n].split(b"\0")[0].decode("latin-1").strip() for i in range(0, len(buf), n)]
        data = {}
        Log.step("lendo nomes dos presets...")
        data["presets"] = split(await self.read(PRESET_NAMES, PRESET_COUNT * PRESET_NAME_LEN), PRESET_NAME_LEN)
        for mod, (count, addr) in RESOURCES.items():
            Log.step(f"lendo nomes de {mod}...")
            data[mod] = split(await self.read(addr, count * RES_NAME_LEN, RES_TYPE), RES_NAME_LEN)
        with open(NAMES_FILE, "w") as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        Log.ok(f"salvo em {NAMES_FILE}: {len(data['presets'])} presets, "
              + ", ".join(f"{len(data[m])} {m}" for m in RESOURCES))

    async def params(self):
        d = await self.read(BUF, PATCH_SIZE)
        for k, m in enumerate(MODS):
            o = OFF_PARA + k * PARAMS_PER_MOD * 2
            vals = [int.from_bytes(d[o + 2*i:o + 2*i + 2], "little", signed=True) for i in range(PARAMS_PER_MOD)]
            t = d[OFF_UNIT + k]
            tname = (CACHE.get(m) or [None] * 256)[t] if m in CACHE and t < len(CACHE[m]) else None
            tname = tname or type_name(m, t)
            names = param_names(m, t)
            if names:
                shown = "  ".join(f"{n}={vals[i]}" for i, n in enumerate(names))
            else:
                while len(vals) > 1 and vals[-1] == 0:
                    vals.pop()
                shown = str(vals)
            label = f"{t:3} {tname}" if tname else f"{t:3}"
            print(f"{m:5} {'ON ' if d[OFF_EN + k] else 'off'} {label:22} {shown}")

    async def param(self, name, idx, val):
        mid = MODS.index(name.upper())
        if isinstance(idx, str):
            t = (await self.read(BUF + OFF_UNIT + mid, 1))[0]
            names = [n.lower() for n in (param_names(MODS[mid], t) or [])]
            idx = int(idx) if idx.isdigit() else names.index(idx.lower())
        if not 0 <= idx < PARAMS_PER_MOD:
            raise ValueError("índice do parâmetro deve ser 0-11")
        addr = BUF + OFF_PARA + mid * PARAMS_PER_MOD * 2 + idx * 2
        await self.write(addr, val.to_bytes(2, "little", signed=True))
        print(f"{MODS[mid]}[{idx}] = {val}")

    async def u16(self, off, val, lo, hi, signed=False):
        if not lo <= val <= hi:
            raise PedalError(f"valor fora da faixa {lo}..{hi}")
        await self.write(BUF + off, val.to_bytes(2, "little", signed=signed))


def list_presets():
    names = CACHE.get("presets")
    if not names:
        raise PedalError("ainda não há nomes de presets em cache",
                         ['rode "mk300ctl.py names" uma vez com o pedal ligado'])
    for i, n in enumerate(names):
        print(f"{i:3}  [{i + 1:03}] {n}")


# ---------------------------------------------------------------- comandos
def _int(v, what):
    try:
        return int(v, 0)
    except ValueError:
        raise PedalError(f"{what} deve ser um número (recebi {v!r})") from None


def _mod(v):
    if v.upper() not in MODS:
        raise PedalError(f"módulo desconhecido: {v}", ["módulos: " + " ".join(MODS)])
    return v.upper()


# nome -> (nº de argumentos, conversor dos argumentos, descrição para o log)
COMMANDS = {
    "info":   (0, lambda a: (), lambda a: "lendo o preset atual"),
    "params": (0, lambda a: (), lambda a: "lendo parâmetros dos módulos"),
    "names":  (0, lambda a: (), lambda a: "lendo nomes do pedal"),
    "preset": (1, lambda a: (_int(a[0], "preset"),), lambda a: f"trocando para o preset {a[0]} ([{a[0] + 1:03}])"),
    "pc":     (1, lambda a: (_int(a[0], "program"),), lambda a: f"enviando Program Change {a[0]}"),
    "on":     (1, lambda a: (_mod(a[0]),), lambda a: f"ligando {a[0]}"),
    "off":    (1, lambda a: (_mod(a[0]),), lambda a: f"desligando {a[0]}"),
    "toggle": (1, lambda a: (_mod(a[0]),), lambda a: f"invertendo {a[0]}"),
    "vol":    (1, lambda a: (_int(a[0], "volume"),), lambda a: f"Preset Vol = {a[0]}"),
    "bpm":    (1, lambda a: (_int(a[0], "BPM"),), lambda a: f"BPM = {a[0]}"),
    "pan":    (1, lambda a: (_int(a[0], "pan"),), lambda a: f"Pan = {a[0]}"),
    "dump":   (1, lambda a: (a[0],), lambda a: f"salvando o preset em {a[0]}"),
    "param":  (3, lambda a: (_mod(a[0]), a[1], _int(a[2], "valor")), lambda a: f"{a[0]}[{a[1]}] = {a[2]}"),
}


def parse(args):
    """Valida tudo antes de conectar, para não abrir conexão à toa."""
    out, i = [], 0
    while i < len(args):
        name = args[i].lower()
        if name not in COMMANDS:
            raise PedalError(f"comando desconhecido: {args[i]}", ["rode sem argumentos para ver a ajuda"])
        n, conv, _ = COMMANDS[name]
        if len(args) - i - 1 < n:
            raise PedalError(f'"{name}" precisa de {n} argumento(s)')
        out.append((name, conv(args[i + 1:i + 1 + n])))
        i += 1 + n
    return out


async def execute(mk, name, a):
    if name == "info":     await mk.info()
    elif name == "params": await mk.params()
    elif name == "names":  await mk.names()
    elif name == "preset": await mk.preset(*a)
    elif name == "pc":
        await mk.midi([0xC0, a[0] & 0x7F]); await asyncio.sleep(0.8)
    elif name in ("on", "off", "toggle"): await mk.module(a[0], name)
    elif name == "vol":    await mk.u16(OFF_VOL, a[0], 0, 100)
    elif name == "bpm":    await mk.u16(OFF_BPM, a[0], 40, 240)
    elif name == "pan":    await mk.u16(OFF_PAN, a[0], -100, 100, signed=True)
    elif name == "param":  await mk.param(*a)
    elif name == "dump":
        data = await mk.read(BUF, PATCH_SIZE)
        with open(a[0], "wb") as f:
            f.write(data)
        Log.ok(f"{len(data)} bytes salvos em {a[0]}")


# ---------------------------------------------------------------- conexão
def check_adapter():
    if not shutil.which("bluetoothctl"):
        Log.warn("bluetoothctl não encontrado; pulando checagem do adaptador")
        return
    show = subprocess.run(["bluetoothctl", "show"], capture_output=True, text=True).stdout
    if not show.strip():
        raise PedalError("nenhum adaptador Bluetooth encontrado no PC",
                         ["confira com: bluetoothctl list", "o serviço está rodando? systemctl status bluetooth"])
    if "Powered: yes" not in show:
        raise PedalError("o Bluetooth do PC está desligado", ["ligue com: bluetoothctl power on"])
    Log.debug("adaptador Bluetooth ligado")


def bluez_connected(mac):
    if not shutil.which("bluetoothctl"):
        return False
    info = subprocess.run(["bluetoothctl", "info", mac], capture_output=True, text=True).stdout
    return "Connected: yes" in info


def release_bluez(mac, quiet_if_free=False):
    """O BlueZ reconecta sozinho (porta ALSA MIDI); soltamos para o pedal voltar a anunciar."""
    if bluez_connected(mac):
        Log.step("o BlueZ está conectado ao pedal; liberando a conexão...")
        subprocess.run(["bluetoothctl", "disconnect", mac], capture_output=True)
        time.sleep(1)
        return True
    if not quiet_if_free:
        Log.debug("pedal não está conectado ao BlueZ")
    return False


async def connect(mac, scan_timeout, tries=3):
    dev = None
    for rnd in range(2):
        Log.step(f"procurando a MK-300 ({mac}) por até {scan_timeout:.0f}s...")
        try:
            dev = await BleakScanner.find_device_by_address(mac, timeout=scan_timeout)
        except (BleakError, OSError) as e:
            raise PedalError("não consegui acessar o Bluetooth do sistema (BlueZ / D-Bus)", [
                f"detalhe: {e}",
                "o serviço está rodando? systemctl status bluetooth",
            ], code=4) from None
        if dev:
            break
        # Com o pedal "trusted", o BlueZ às vezes reconecta durante a busca e o pedal para de anunciar.
        if rnd == 0 and release_bluez(mac, quiet_if_free=True):
            Log.warn("o BlueZ reconectou ao pedal durante a busca; tentando de novo")
            continue
        break
    if dev is None:
        raise PedalError("MK-300 não encontrada", [
            "o Bluetooth do pedal está ligado? (segure o GLOB; LED piscando = ligado e aguardando conexão)",
            "o pedal está conectado no app do celular? Feche o app ou desligue o Bluetooth do celular",
            "aproxime o pedal do PC e tente de novo, ou aumente com --timeout 20",
        ], code=2)
    Log.ok(f"encontrada: {dev.name or '(sem nome)'}")
    last = None
    for n in range(1, tries + 1):
        Log.step(f"conectando (tentativa {n}/{tries})...")
        client = BleakClient(dev, timeout=20)
        try:
            await client.connect()
            return client
        except (BleakError, asyncio.TimeoutError, OSError) as e:
            last = e
            Log.warn(f"falhou: {e or type(e).__name__}")
            await asyncio.sleep(2)
    raise PedalError("não foi possível conectar à MK-300", [
        f"último erro: {last}",
        "desligue e ligue o Bluetooth do pedal (segure o GLOB) e tente de novo",
        "se persistir: bluetoothctl remove " + mac], code=3)


async def run(args, mac, scan_timeout):
    cmds = parse(args)
    if cmds == [("presets", ())] or args == ["presets"]:
        return list_presets()
    check_adapter()
    release_bluez(mac)
    client = await connect(mac, scan_timeout)
    try:
        mk = MK300(client)
        Log.step("handshake...")
        model = await mk.start()
        Log.ok(f"conectado: {model}")
        for name, a in cmds:
            Log.step(COMMANDS[name][2](a))
            await execute(mk, name, a)
        Log.ok("pronto")
    finally:
        if client.is_connected:
            Log.debug("desconectando")
            await client.disconnect()


def main(argv):
    debug, mac, scan_timeout, args = False, MAC, 10.0, []
    it = iter(argv)
    for a in it:
        if a in ("-v", "--verbose"): Log.verbose = True
        elif a in ("-q", "--quiet"): Log.quiet = True
        elif a == "--debug": debug = Log.verbose = True
        elif a == "--mac": mac = next(it, MAC)
        elif a == "--timeout": scan_timeout = float(next(it, "10"))
        elif a in ("-h", "--help"): print(__doc__); return 0
        else: args.append(a)
    if not args:
        print(__doc__); return 0
    COMMANDS["presets"] = (0, lambda a: (), lambda a: "")
    try:
        asyncio.run(run(args, mac, scan_timeout))
        return 0
    except PedalError as e:
        Log.error(str(e))
        for h in e.hints:
            Log.hint(f"→ {h}")
        if debug: raise
        return e.code
    except KeyboardInterrupt:
        Log.warn("interrompido")
        return 130
    except Exception as e:
        Log.error(f"erro inesperado: {type(e).__name__}: {e}")
        Log.hint("→ rode de novo com --debug para ver o traceback completo")
        if debug: raise
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
