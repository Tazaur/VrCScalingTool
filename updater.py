import sys
import os
import json
import subprocess
import tempfile
import threading
import urllib.request

import config as _cfg


def version_newer(a, b):
    try:
        return tuple(int(x) for x in a.split(".")) > tuple(int(x) for x in b.split("."))
    except Exception:
        return False


def check_update(repo, current_version, on_found, on_up_to_date=None, on_error=None, on_ahead=None):
    """Fetch the latest GitHub release in a background thread.

    Callbacks are invoked from that thread — callers must marshal to the main
    thread themselves (e.g. window.after) if they touch tkinter widgets.

    on_found(tag, html_url, asset_url)
    on_up_to_date()
    on_ahead(tag)
    on_error()
    """
    def _fetch():
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/releases/latest",
                headers={"User-Agent": "TazaursVrCScalingTool"},
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
            tag       = data.get("tag_name", "").lstrip("v")
            html_url  = data.get("html_url", "")
            asset_url = next(
                (a["browser_download_url"] for a in data.get("assets", [])
                 if a.get("name", "").endswith(".exe")),
                None,
            )
            if version_newer(tag, current_version):
                on_found(tag, html_url, asset_url)
            elif version_newer(current_version, tag):
                if on_ahead:
                    on_ahead(tag)
            elif on_up_to_date:
                on_up_to_date()
        except Exception:
            if on_error:
                on_error()

    threading.Thread(target=_fetch, daemon=True).start()


def download_update(asset_url, dest_path, on_done, on_error):
    """Download asset_url to dest_path in a background thread.

    on_done(dest_path)
    on_error(exc)
    """
    def _fetch():
        try:
            urllib.request.urlretrieve(asset_url, dest_path)
            on_done(dest_path)
        except Exception as e:
            on_error(e)

    threading.Thread(target=_fetch, daemon=True).start()


def launch_updater(tmp_exe, quit_fn, on_error):
    """Launch a hidden PowerShell script that swaps the EXE and cleans up,
    then quit the app. No relaunch — user reopens manually.

    quit_fn()     — called to close the app after the script is launched
    on_error(msg) — called if anything goes wrong (stays on main thread)
    """
    try:
        exe_path = sys.executable
        ps1_path = os.path.join(tempfile.gettempdir(), "tvst_update.ps1")
        script = (
            "Start-Sleep -Seconds 2\r\n"
            f'Move-Item -Force -LiteralPath "{exe_path}" -Destination "{exe_path}.old"\r\n'
            f'Move-Item -Force -LiteralPath "{tmp_exe}" -Destination "{exe_path}"\r\n'
            "Start-Sleep -Seconds 2\r\n"
            f'Remove-Item -LiteralPath "{exe_path}.old" -ErrorAction SilentlyContinue\r\n'
            "Remove-Item -LiteralPath $PSCommandPath -ErrorAction SilentlyContinue\r\n"
        )
        with open(ps1_path, "w") as f:
            f.write(script)
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-File", ps1_path],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        quit_fn()
    except Exception as e:
        on_error(str(e))
