<p align="center">
  <img src="assets/icon.png" width="96" alt="TempInfoCLI icon">
</p>

<h1 align="center">🌡️ TempInfoCLI <sup>v0.1.0</sup></h1>

<p align="center">
  A live, color-coded temperature dashboard for your terminal.<br>
  A CLI port of the Windows TempInfo hardware monitor.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v0.1.0-00bcd4?style=for-the-badge" alt="version v0.1.0">
  <img src="https://img.shields.io/badge/python-3.8+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="python 3.8+">
  <img src="https://img.shields.io/badge/nix-flake-5277c3?style=for-the-badge&logo=nixos&logoColor=white" alt="nix flake">
  <img src="https://img.shields.io/badge/license-MIT-2ea44f?style=for-the-badge" alt="MIT license">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Linux-complete-2ea44f?logo=linux&logoColor=white" alt="Linux: complete">
  <img src="https://img.shields.io/badge/macOS-best_effort-e3b341?logo=apple&logoColor=white" alt="macOS: best effort">
  <img src="https://img.shields.io/badge/Windows-best_effort-e3b341?logo=windows&logoColor=white" alt="Windows: best effort">
</p>

<p align="center">
  <img src="assets/preview.svg" alt="TempInfoCLI dashboard preview">
</p>

<p align="center"><sub>Real readings from a Ryzen + Radeon desktop, captured with <code>tempinfocli</code> v0.1.0.</sub></p>

## ✨ What it does

- 🔄 **Live dashboard** that refreshes in place (default every second). Ctrl-C exits cleanly.
- 🧩 **Grouped panels**: CPU, GPU, Motherboard, Storage, and Fans / Other.
- 🎨 **Color by thermal headroom**: every reading gets a bar and a color for how close it is to its limit.
- 🚫 **Never makes numbers up**: if nothing can be read, it says "no sensors readable".
- 🔒 **Read-only**: it reads sensors and draws them. It never changes anything on your system.

### 🎨 Color thresholds

Drives get hot sooner than CPUs, so each kind of sensor has its own limits:

| Sensor | Cool | Warm | Hot |
|--------|------|------|-----|
| CPU / GPU | ![cool](https://img.shields.io/badge/below-75%C2%B0C-2ea44f) | ![warm](https://img.shields.io/badge/75--89-%C2%B0C-e3b341) | ![hot](https://img.shields.io/badge/90%C2%B0C-and_up-d73a49) |
| Motherboard / other | ![cool](https://img.shields.io/badge/below-60%C2%B0C-2ea44f) | ![warm](https://img.shields.io/badge/60--79-%C2%B0C-e3b341) | ![hot](https://img.shields.io/badge/80%C2%B0C-and_up-d73a49) |
| Storage (NVMe / SSD) | ![cool](https://img.shields.io/badge/below-50%C2%B0C-2ea44f) | ![warm](https://img.shields.io/badge/50--64-%C2%B0C-e3b341) | ![hot](https://img.shields.io/badge/65%C2%B0C-and_up-d73a49) |
| Fans | ![neutral](https://img.shields.io/badge/RPM-always_cyan-00bcd4) | | |

## 🖥️ Platform support

| Platform | Coverage |
|----------|----------|
| 🐧 Linux / NixOS | **Complete**: hwmon via psutil (CPU, motherboard, NVMe/SSD, AMD/Intel GPU, fans), NVIDIA via `nvidia-smi` |
| 🍎 macOS | **Best effort**: `powermetrics`, which needs root. Run `sudo tempinfocli`; otherwise you get "no sensors readable" |
| 🪟 Windows | **Best effort**: ACPI thermal zones via WMI/PowerShell, which usually needs an Administrator terminal. Many machines expose few or none |

## ❄️ Install with Nix flakes (NixOS)

TempInfoCLI is **not in nixpkgs**. The repo ships its own flake instead, so you add it as a flake input.

### Try it without installing

```bash
nix run github:fatumorg/TempInfoCLI
```

### Add it to your NixOS configuration

**1. Add the input** to your system `flake.nix`:

```nix
{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    tempinfocli = {
      url = "github:fatumorg/TempInfoCLI";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
}
```

`inputs.nixpkgs.follows` makes TempInfoCLI build against your system's nixpkgs instead of pulling a second copy.

**2. Pass `inputs` through to your modules** in the same file:

```nix
{
  outputs = { nixpkgs, ... }@inputs: {
    nixosConfigurations.myhost = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      specialArgs = { inherit inputs; };
      modules = [ ./configuration.nix ];
    };
  };
}
```

**3. Install the package.** System-wide, in `configuration.nix`:

```nix
{ pkgs, inputs, ... }:
{
  environment.systemPackages = [
    inputs.tempinfocli.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}
```

Or for one user with Home Manager, in `home.nix`. This needs `home-manager.extraSpecialArgs = { inherit inputs; };` in your flake:

```nix
{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.tempinfocli.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}
```

**4. Rebuild:**

```bash
sudo nixos-rebuild switch --flake .#myhost
tempinfocli
```

### Updating and pinning

| Goal | How |
|------|-----|
| Update to the latest commit | `nix flake update tempinfocli`, then rebuild |
| Pin to this release | `url = "github:fatumorg/TempInfoCLI/v0.1.0";` |
| Install without NixOS (any Nix) | `nix profile install github:fatumorg/TempInfoCLI` |
| Hack on it | `nix develop` inside a clone |

### Without flakes

From a clone, `nix-shell` builds the package from `default.nix` and puts `tempinfocli` on your PATH. Or build it standalone with `nix-build && ./result/bin/tempinfocli`.

## 📦 Install from source (any OS)

```bash
git clone https://github.com/fatumorg/TempInfoCLI
cd TempInfoCLI
pip install -e .
tempinfocli
```

## 🚀 Usage

| Command | What it does |
|---------|--------------|
| `tempinfocli` | live dashboard |
| `tempinfocli --once` | print one snapshot and exit |
| `tempinfocli --json` | print sensors as JSON and exit |
| `tempinfocli --interval 2` | refresh every 2s (minimum 0.2) |
| `tempinfocli --no-color` | plain output |
| `tempinfocli --version` | print `tempinfocli 0.1.0` |

When the output is piped or redirected, `tempinfocli` prints one snapshot instead of the live view.

`--json` gives one object per sensor, ready for scripts:

```json
[
  {
    "group": "k10temp",
    "label": "Tctl",
    "value": 57.25,
    "unit": "°C",
    "kind": "cpu"
  },
  {
    "group": "amdgpu",
    "label": "edge",
    "value": 47.0,
    "unit": "°C",
    "kind": "gpu"
  }
]
```

## 🖱️ Desktop icon / shortcut

Install `tempinfocli` first, then:

- 🐧 **Linux**: `./packaging/linux/install-desktop-entry.sh` adds an application-menu entry that opens a terminal running `tempinfocli`.
- 🪟 **Windows**: double-click `packaging\windows\install-shortcut.bat` (or run the `.ps1`) to add Desktop and Start Menu shortcuts that open a console running `tempinfocli`.

## 🧪 Tests

```bash
pip install pytest && pytest
```

The Nix build runs the same suite.

## 📄 License

MIT, see [LICENSE](LICENSE).
