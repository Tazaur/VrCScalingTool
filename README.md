# Tazaur's VrCScalingTool (TVST) — Advanced VRChat Avatar OSC Scaling Tool

[![GitHub release](https://shields.io)](https://github.com/Tazaur/VrCScalingTool/releases)
[![Platform](https://shields.io)]

**Tazaur's VrCScalingTool (TVST)** is a lightweight Windows desktop application designed to bypass the default VRChat radial menu limitations. Using VRChat's native OSC (Open Sound Control) protocol, this tool allows you to safely change your avatar eye height anywhere from **0.01m up to 20m** with precise, sub-centimeter control.

## Features

- Set eye height from **0.01m to 20m** via OSC
- **1-10 save slots** (defaults to 5) with custom names
- **Slot 1** can be triggered in-game via an avatar Bool parameter (`ScaleOverride`)
- **Nudge** buttons (±0.01m per press)
- **Tiny** and **Normal** quick-apply buttons
- **1-level undo**
- **Global hotkeys** - `Ctrl+Shift+1–9` loads slots from anywhere
- **SteamVR integration** - register to auto-launch with SteamVR
- **System tray** - minimizes to tray instead of closing
- **Always-on-top** pin
- **Auto update checker** on launch with manual check button

<img width="689" height="559" alt="TVST_GUI" src="https://github.com/user-attachments/assets/45ad6613-1e77-40d9-870c-1e3af036b5ee" />

## Download

Grab the latest `.exe` from [Releases](https://github.com/Tazaur/VrCScalingTool/releases).

If youre using Edge web browser to download the app, It may be flagged by Microsoft because its unverified. To keep it, you have to click the '...' on the download and choose "Keep" then "Keep Anyway" in the "Delete" Dropdown arrow.

No install needed - just run the EXE.

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

<img width="1685" height="1387" alt="TVSTScaleDisplay" src="https://github.com/user-attachments/assets/fc06317b-fca0-41b3-9ec2-afb3a3e3d830" />

## Frequently Asked Questions (FAQ)

### How do I scale my VRChat avatar past the radial menu limits?
VRChat's built-in expression menu restricts avatar scaling. Tazaur's VrCScalingTool uses the OSC system to send eye-height values directly to the client, allowing scales from 0.01m to 20m.

### Will using an OSC scaling tool get me banned in VRChat?
No. This tool utilizes VRChat's officially supported OSC API and standard avatar parameters (`EyeHeight`). It does not modify game files, inject code, or break the Terms of Service.

### Can I trigger avatar scaling macros using standard hotkeys?
Yes. TVST includes global Windows hotkeys (`Ctrl+Shift+1-9`) so you can load saved height profiles instantly while in-game, without Alt-Tabbing.
