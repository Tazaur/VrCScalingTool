import os
import sys
import json

_APP_KEY  = "tazaur.vrcscalingtool"
_APP_NAME = "Tazaur's VrC Scaling Tool"
_APP_DESC = "VRChat avatar scale controller via OSC"


def _data_dir():
    return os.path.join(os.path.expanduser("~"), "Documents", "TazaurApplications", "TazaursVrCScalingTool")


def _manifest_path():
    return os.path.join(_data_dir(), "TazaursVrCScalingTool.vrmanifest")


def _write_manifest(exe_path):
    manifest = {
        "source": "builtin",
        "applications": [{
            "app_key": _APP_KEY,
            "launch_type": "binary",
            "binary_path_windows": exe_path,
            "is_dashboard_overlay": True,
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


def get_registered_path():
    try:
        with open(_manifest_path()) as f:
            data = json.load(f)
        return data["applications"][0]["binary_path_windows"]
    except Exception:
        return None


def register(exe_path):
    """Write the manifest to Documents folder.
    Returns (True, None) on success or (False, error_str) on failure.
    """
    try:
        _write_manifest(exe_path)
        return True, None
    except Exception as e:
        return False, str(e)


def unregister():
    """Delete the manifest file. Always succeeds."""
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
