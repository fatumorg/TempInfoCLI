# TempInfoCLI

A live temperature dashboard for your terminal. A CLI port of the Windows TempInfo hardware monitor.

```
$ tempinfocli
myhost  ·  up 0d 1h 16m
╭─ CPU ───────────────────╮
│ Tctl             55 °C  │
╰─────────────────────────╯
...
```

Read-only: it reads sensors and draws them. It never changes anything on your system.

## What it does

- Full-screen dashboard that refreshes in place (default 1s); Ctrl-C exits.
- Panels for CPU, GPU, Motherboard, Storage, and Fans / Other, colored green → yellow → red by thermal headroom (drives run hotter-limited than CPUs).
- Shows "no sensors readable" instead of inventing numbers when nothing can be read.

## Platform support

| Platform | Coverage |
|----------|----------|
| Linux / NixOS | Complete: hwmon via psutil (CPU, motherboard, NVMe/SSD, AMD/Intel GPU, fans), NVIDIA via `nvidia-smi` |
| macOS | Best effort: `powermetrics`, which needs root. Run `sudo tempinfocli`; otherwise you get "no sensors readable" |
| Windows | Best effort: ACPI thermal zones via WMI/PowerShell, which usually needs an Administrator terminal. Many machines expose few or none |

## Install

### Build from source (any OS)

```bash
git clone https://github.com/fatumorg/TempInfoCLI
cd TempInfoCLI
pip install -e .
tempinfocli
```

### NixOS / Nix

`nix-shell` builds the package from `default.nix` and puts `tempinfocli` on your PATH:

```bash
nix-shell
tempinfocli
```

Or build it standalone with `nix-build && ./result/bin/tempinfocli`.

## Usage

| Command | What it does |
|---------|--------------|
| `tempinfocli` | live dashboard |
| `tempinfocli --once` | print one snapshot and exit |
| `tempinfocli --json` | print sensors as JSON and exit |
| `tempinfocli --interval 2` | refresh every 2s (minimum 0.2) |
| `tempinfocli --no-color` | plain output |

When the output is piped or redirected, `tempinfocli` prints one snapshot instead of the live view.

## Desktop icon / shortcut

Install `tempinfocli` first, then:

- Linux: `./packaging/linux/install-desktop-entry.sh` adds an application-menu entry that opens a terminal running `tempinfocli`.
- Windows: double-click `packaging\windows\install-shortcut.bat` (or run the `.ps1`) to add Desktop and Start Menu shortcuts that open a console running `tempinfocli`.

## Tests

```bash
pip install pytest && pytest
```

## License

MIT, see [LICENSE](LICENSE).
