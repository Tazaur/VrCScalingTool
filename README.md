# Tazaur's VrC Scaling Tool

A lightweight Windows desktop app for controlling your VRChat avatar's eye height via OSC, with a wider range than VRChat's default menu allows.

## Features

- Set eye height from **0.01m to 20m** via OSC
- **5 save slots** (configurable 1–10) with custom names
- **Slot 1** can be triggered in-game via an avatar Bool parameter (`ScaleOverride`)
- **Nudge** buttons (±0.01m per press)
- **Tiny** and **Normal** quick-apply buttons
- **1-level undo**
- **Global hotkeys** — `Ctrl+Shift+1–9` loads slots from anywhere
- **System tray** — minimizes to tray instead of closing
- **Always-on-top** pin
- **Auto update checker** on launch with manual check button

## Download

Grab the latest `.exe` from [Releases](https://github.com/Tazaur/VrCScalingTool/releases).

No install needed — just run the EXE.

## Building from source

**Requirements:**
```
pip install pyinstaller pythonosc pillow pystray keyboard
```

**Build:**
```
pyinstaller TazaursVrCScalingTool.spec --noconfirm
```

Output: `dist/TazaursVrCScalingTool.exe`

## In-game trigger (optional)

To trigger Slot 1 from inside VRChat:

1. Add a **Bool parameter** named `ScaleOverride` to your avatar's VRC Expression Parameters asset
2. Add a **Button Toggle** in your Expression Menu that controls it
3. Enable OSC in VRChat: `Action Menu → Options → OSC → Enabled`

Toggling it ON will load and apply Slot 1 automatically.

## Notes

- OSC must be enabled in VRChat for the tool to communicate with your avatar
- Save data and settings are stored in `Documents\TazaursVrCScalingTool\data.json`
- Please don't abuse extreme scales in public lobbies

## License

Free to use. If you paid for it, you were scammed.
