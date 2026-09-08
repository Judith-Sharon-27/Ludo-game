# Ludo Game — Python + Pygame

A local 4-player Ludo game for Windows.

## Features
- Red, Green, Yellow and Blue players
- Four tokens per player
- Roll 6 to leave the yard
- Exact roll required to reach the center
- Capturing opponent tokens
- Safe starting squares
- Extra turn on 6 or a capture
- Win detection
- Restart with `R`

## Run locally

Install Python 3.12+.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Build a Windows EXE

```bash
pip install pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --name LudoGame main.py
```

The executable will be:

`dist/LudoGame.exe`

Or double-click `build_exe.bat`.

## GitHub releases

The included GitHub Actions workflow automatically builds the EXE and creates a Release whenever you push a version tag such as:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The EXE will appear in the GitHub Release assets.

## Controls

- Mouse: roll dice / select token
- `R`: restart
- `Esc`: quit

## Important

This is a complete playable local Ludo implementation intended as a solid starting point. Ludo rules differ by region, so you can customize safe squares, capture rules, block rules, animations, AI, online multiplayer, sounds, and graphics as desired.
