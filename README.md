# mk300ctl — Controle Open Source para a M-Vave MK-300 no Linux

Alternativa open source inicial ao aplicativo **M-EFCS** da **M-Vave** (que oficialmente só possui versões para Android/iOS, Windows e macOS), permitindo controlar e inspecionar a pedaleira **M-Vave MK-300** diretamente pelo terminal no Linux (ou qualquer sistema com suporte a Bluetooth LE via `bleak`).

---

## Motivação

A M-Vave MK-300 utiliza Bluetooth Low Energy (BLE) para comunicação em tempo real com o app oficial **M-EFCS**. Como não há cliente oficial para Linux, este projeto implementa a engenharia reversa do protocolo proprietário **AE40** (leitura/escrita direta de memória de presets e parâmetros) e do **BLE-MIDI**, oferecendo uma ferramenta de linha de comando rápida e scriptável.

---

## Status do Projeto e Compatibilidade

Desenvolvido e testado atualmente no **Linux (Ubuntu 26.04.1 LTS)** com firmware **v070** da M-Vave MK-300.

### Conexão e Plataforma
- ✅ **Conexão via Bluetooth LE (BLE)** no Linux (testado no Ubuntu 26.04.1 LTS via BlueZ + `bleak`)
- ✅ **Liberação automática da conexão BlueZ** (evita que o ALSA BLE-MIDI trave o anúncio do pedal)
- ⏳ **Conexão via cabo USB** — *em breve*
- ⏳ **Interface gráfica / TUI interativa** — *em breve*

### Funcionalidades
- ✅ **Inspeção do preset atual (`info`)**: nome, número do slot, cor do LED, volume, BPM, Pan e ordem/estado da cadeia de sinal (`Chain`).
- ✅ **Leitura completa de parâmetros (`params`)**: exibe o modelo selecionado (`AMP`, `CAB`, `DS`, `FX`, `DLY`, `REV`, etc.) e os 12 parâmetros de cada um dos 11 módulos.
- ✅ **Troca de presets (`preset`, `pc`)**: via protocolo AE40 (todos os 160 slots: `0` a `159`) ou via BLE-MIDI Program Change (`0` a `127`).
- ✅ **Controle de módulos (`on`, `off`, `toggle`)**: liga, desliga ou inverte qualquer um dos 11 módulos da cadeia (`WAH`, `FX`, `GATE`, `DS`, `AMP`, `CAB`, `EQ`, `MOD`, `DLY`, `REV`, `VOL`).
- ✅ **Edição de parâmetros em tempo real (`param`, `vol`, `bpm`, `pan`)**: altera knobs pelo nome (ex.: `gain`, `mix`, `time`) ou pelo índice numérico (`0` a `11`).
- ✅ **Leitura de nomes da memória do pedal (`names`, `presets`)**: extrai os nomes atuais dos 160 presets, 120 AMPs, 100 CABs e 40 DS diretamente da memória da pedaleira (incluindo IRs/AMPs importados pelo usuário) e salva em cache (`mk300_names.json`).
- ✅ **Backup binário de preset (`dump`)**: salva os 448 bytes brutos do preset em edição em um arquivo `.bin`.
- ✅ **Encadeamento de comandos**: executa várias ações em uma única conexão BLE.
- ⏳ **Troca do modelo/tipo de efeito (`effunit`) de um módulo via CLI** — *em breve*
- ⏳ **Reordenação da cadeia de sinal (`Chain`) e edição de nome/cor do preset** — *em breve*
- ⏳ **Importação/restauração de preset (`.bin`) e gravação permanente no slot (Save)** — *em breve*
- ⏳ **Mapeamento completo dos nomes de knobs de todos os subtipos de `FX`, `DLY` e `REV`** — *em andamento*

> **Nota:** Assim como no app M-EFCS, alterações feitas no buffer de edição ficam ativas imediatamente no som (o botão `SAVE` da pedaleira começa a piscar), mas só são gravadas permanentemente se você salvar no pedal.

---

## Requisitos e Instalação

- **Python 3.9+**
- **BlueZ** (`bluetoothctl` instalado e serviço `bluetooth` ativo no Linux)
- Biblioteca Python [`bleak`](https://github.com/hbldh/bleak)

```bash
git clone https://github.com/rafaelsupport/mk300ctl.git
cd mk300ctl
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Descobrindo o endereço MAC da sua MK-300

Com o Bluetooth da pedaleira piscando (segure o botão **GLOB** caso esteja desligado), rode o script de diagnóstico:

```bash
python3 tests/diag.py
```

Ele listará os dispositivos BLE próximos. Caso o MAC da sua unidade seja diferente do padrão configurado em `mk300ctl.py`, você pode passá-lo via `--mac XX:XX:XX:XX:XX:XX` ou editar a constante `MAC` no topo do `mk300ctl.py`.

---

## Como Usar

```bash
# Sincronizar nomes de presets, AMPs, CABs e DS da memória do pedal (recomendado rodar 1x)
./mk300ctl.py names

# Listar todos os 160 presets em cache
./mk300ctl.py presets

# Ver resumo do preset atual e cadeia de sinal
./mk300ctl.py info

# Ver todos os módulos, modelos selecionados e valores dos parâmetros (knobs)
./mk300ctl.py params

# Trocar de preset (0 a 159)
./mk300ctl.py preset 12

# Ligar / desligar / inverter módulos
./mk300ctl.py on DLY
./mk300ctl.py off FX
./mk300ctl.py toggle REV

# Alterar parâmetros de um módulo (por nome ou índice 0..11)
./mk300ctl.py param AMP gain 80
./mk300ctl.py param DLY mix 35
./mk300ctl.py param AMP 0 80

# Ajustes globais do preset
./mk300ctl.py vol 75
./mk300ctl.py bpm 120
./mk300ctl.py pan -20

# Executar vários comandos na mesma conexão Bluetooth
./mk300ctl.py preset 3 off DLY on FX param AMP gain 65 info

# Salvar dump binário do preset atual (448 bytes)
./mk300ctl.py dump meu_preset.bin
```

### Opções de Linha de Comando

| Opção | Descrição |
|---|---|
| `-v`, `--verbose` | Mostra o tráfego de pacotes BLE enviados/recebidos (`TX`/`RX` em hexadecimal) |
| `-q`, `--quiet` | Suprime mensagens de progresso no `stderr` e exibe apenas a saída final no `stdout` |
| `--debug` | Exibe o traceback completo em caso de erro |
| `--mac XX:..:XX` | Usa outro endereço MAC Bluetooth |
| `--timeout N` | Tempo máximo (em segundos) procurando o anúncio BLE do pedal (padrão: `10`) |

---

## Como Tudo Funciona (Protocolo AE40)

### 1. Serviços e Características GATT

A MK-300 expõe dois serviços principais via Bluetooth LE:

1. **Serviço Proprietário AE40 (`0000ae40-0000-1000-8000-00805f9b34fb`)**:
   - **Write (`0000ae41-...`)**: envio de comandos para o pedal (Write Without Response).
   - **Notify (`0000ae42-...`)**: respostas e dados lidos da memória do pedal.
2. **Serviço BLE-MIDI Padrão (`03b80e5a-ede8-4b33-a751-6ce34ec4c700`)**:
   - **Característica I/O (`7772e5db-3868-4112-a1a9-f2669d106bf3`)**: recebe e envia mensagens MIDI padrão encapsuladas em BLE-MIDI (`0x80 0x80 <status> <data...>`).

### 2. Estrutura do Pacote AE40

Todos os pacotes enviados e recebidos no serviço AE40 seguem o formato:

```text
+------+------+------+-------------------+----------------+------+
| 0x00 | 0x59 | CMD  | LEN (3 bytes LE)  | PAYLOAD (N B)  | CKS  |
+------+------+------+-------------------+----------------+------+
```

- **Cabeçalho fixo**: `0x00 0x59`
- **`CMD`**:
  - `0x11`: Handshake / identificação do modelo (retorna string `"MK-300"`).
  - `0x22`: Escrita em endereço de memória (`[type:1B] [addr:4B LE] [size:3B LE] [dados...]`).
  - `0x23`: Leitura de endereço de memória (`[type:1B] [addr:4B LE] [size:3B LE]`).
- **`CKS` (Checksum de 1 byte)**: complemento de 1 da soma dos bytes do `PAYLOAD`: `(~sum(payload)) & 0xFF`.
- Leituras grandes são fatiadas em blocos de até `1000` bytes (o app oficial usa no máximo `1015`).

### 3. Mapa de Memória Descoberto

| Endereço Base | `type` | Tamanho / Formato | Descrição |
|---|---|---|---|
| `0x10000000` | `0x04` | `448` bytes (`TPatch`) | Buffer do preset em edição ao vivo |
| `0x20000000` | `0x04` | `2+` bytes | Dados globais (`byte[1]` = índice `0..159` do preset atual) |
| `0xE0000000 + N` | `0x04` | Escrita `[0x01]` | Troca imediatamente para o preset `N` (`0..159`) |
| `0x70200000` | `0x04` | `160 × 17` bytes | Nomes salvos dos 160 presets (strings terminadas em `\0`) |
| `0x80000000` | `0x05` | `100 × 14` bytes | Nomes dos 100 CABs na memória do pedal |
| `0x90000000` | `0x05` | `120 × 14` bytes | Nomes dos 120 AMPs na memória do pedal |
| `0xA0000000` | `0x05` | `40 × 14` bytes | Nomes dos 40 pedais de Drive/DS na memória do pedal |

### 4. Layout da Struct do Preset (`0x10000000`, 448 bytes)

| Offset | Tamanho | Tipo | Descrição |
|---|---|---|---|
| `0` (`0x00`) | 20 B | `char[20]` | Nome do preset (terminado em `\0`) |
| `20` (`0x14`) | 4 B | `uint32 LE` | Cor do LED em RGB (`#RRGGBB`) |
| `24` (`0x18`) | 2 B | `uint16 LE` | Volume do preset (`0..100`) |
| `26` (`0x1A`) | 2 B | `uint16 LE` | BPM (`40..240`) |
| `28` (`0x1C`) | 2 B | `int16 LE` | Pan (`-100..100`) |
| `32` (`0x20`) | 11 B | `uint8[11]` | Ordem dos 11 módulos na cadeia de sinal (`0..10`) |
| `43` (`0x2B`) | 11 B | `uint8[11]` | Estado ON (`1`) / OFF (`0`) de cada módulo |
| `54` (`0x36`) | 11 B | `uint8[11]` | Tipo/modelo selecionado (`effunit`) em cada módulo |
| `66` (`0x42`) | 264 B | `int16 LE[11][12]` | 12 parâmetros (`int16`) para cada um dos 11 módulos |

Os 11 módulos têm índices fixos nos arrays de estado/tipo/parâmetros:
`0: WAH`, `1: FX`, `2: GATE`, `3: DS`, `4: AMP`, `5: CAB`, `6: EQ`, `7: MOD`, `8: DLY`, `9: REV`, `10: VOL`.

### 5. Peculiaridade do BlueZ no Linux

Como a MK-300 também anuncia o serviço **BLE-MIDI**, o daemon `bluetoothd` (BlueZ) do Linux costuma reconectar sozinho à pedaleira para criar uma porta ALSA MIDI, fazendo a pedaleira parar de anunciar pacotes BLE e bloqueando novas conexões GATT. O `mk300ctl.py` detecta isso automaticamente via `bluetoothctl` e libera a conexão ociosa antes de iniciar a comunicação.

---

## Estrutura do Repositório

```text
.
├── mk300ctl.py        # CLI principal de controle da MK-300
├── mk300_catalog.py   # Catálogo de efeitos, modelos de fábrica e nomes de parâmetros
├── mk300_names.json   # Cache dos nomes de presets/AMP/CAB/DS lidos da pedaleira
├── requirements.txt   # Dependências Python (bleak)
└── tests/             # Utilitários isolados para diagnóstico e engenharia reversa
    ├── diag.py        # Scanner BLE e listagem de serviços/características GATT
    ├── ae40.py        # Teste isolado de baixo nível do protocolo AE40 (handshake/read/write)
    ├── dump.py        # Dump bruto de qualquer região de memória via AE40
    ├── bindiff.py     # Compara dois dumps (.bin) byte a byte e int16 LE para mapear novos knobs
    └── midi.py        # Monitor e injetor de mensagens BLE-MIDI (Program Change / Control Change)
```
