import os
import sys
import json
import subprocess
import winreg

_APP_KEY  = "tazaur.vrcscalingtool"
_APP_NAME = "Tazaur's VrC Scaling Tool"
_APP_DESC = "VRChat avatar scale controller via OSC"


def _data_dir():
    return os.path.join(os.path.expanduser("~"), "Documents", "TazaursVrCScalingTool")


def _manifest_path():
    return os.path.join(_data_dir(), "TazaursVrCScalingTool.vrmanifest")


def _find_vrpathreg():
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for subkey in (
            r"SOFTWARE\WOW6432Node\Valve\Steam",
            r"SOFTWARE\Valve\Steam",
        ):
            try:
                with winreg.OpenKey(hive, subkey) as k:
                    steam_path, _ = winreg.QueryValueEx(k, "InstallPath")
                    candidate = os.path.join(
                        steam_path, "steamapps", "common",
                        "SteamVR", "bin", "win64", "vrpathreg.exe"
                    )
                    if os.path.isfile(candidate):
                        return candidate
            except Exception:
                pass
    return None


def _write_manifest(exe_path):
    manifest = {
        "source": "builtin",
        "applications": [{
            "app_key": _APP_KEY,
            "launch_type": "binary",
            "binary_path_windows": exe_path,
            "is_dashboard_overlay": False,
            "strings": {
                "en_us": {
                    "name": _APP_NAME,
                    "description": _APP_DESC,
                }
            }
        }]
    }
    os.makedirs(_data_dir(), exist_ok=True)
    with open(_manifest_path(), "w") as f:
        json.dump(manifest, f, indent=2)


def is_registered():
    return os.path.isfile(_manifest_path())


def register(exe_path):
    """Write manifest to Documents folder and register with SteamVR.
    Returns (True, None) on success or (False, error_str) on failure.
    """
    vrpathreg = _find_vrpathreg()
    if not vrpathreg:
        return False, "SteamVR not found — is SteamVR installed?"
    try:
        _write_manifest(exe_path)
        result = subprocess.run(
            [vrpathreg, "addapp", _manifest_path()],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode != 0:
            return False, (result.stderr.strip() or result.stdout.strip() or "vrpathreg failed")
        return True, None
    except Exception as e:
        return False, str(e)


def unregister():
    """Remove SteamVR registration and delete the manifest file.
    Always succeeds from the user's perspective.
    """
    vrpathreg = _find_vrpathreg()
    if vrpathreg:
        try:
            subprocess.run(
                [vrpathreg, "removeapp", _APP_KEY],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception:
            pass
    try:
        os.remove(_manifest_path())
    except Exception:
        pass
    return True, None


def ensure_path_current():
    """If registered and running as a frozen EXE, silently update the manifest
    with the current exe path so SteamVR always points to the right location.
    """
    if not getattr(sys, "frozen", False):
        return
    if not is_registered():
        return
    try:
        _write_manifest(sys.executable)
    except Exception:
        pass
