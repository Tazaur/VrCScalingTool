import sys
import os
import json
import ctypes
import threading
import webbrowser
import urllib.request
import tkinter as tk
import config as _cfg
from PIL import Image as PILImage, ImageTk
from persistence import SLOT_COUNT, load_settings, save_settings
from slots import save_slot, load_slot, clear_slot, clamp, slot_is_empty, get_slot_name, set_slot_name
from osc_client import apply_scale, probe_param, init_client
from osc_server import register_handler, start_server

try:
    import pystray
    _tray_available = True
except ImportError:
    _tray_available = False

try:
    import keyboard
    _hotkeys_available = True
except ImportError:
    _hotkeys_available = False

_settings = load_settings()

SCALE_DEFAULT        = _settings.get("scale_default",        _cfg.SCALE_DEFAULT)
SCALE_TINY           = _settings.get("scale_tiny",           _cfg.SCALE_TINY)
NUDGE_STEP           = _settings.get("nudge_step",           _cfg.NUDGE_STEP)
SCALE_OVERRIDE_PARAM = _settings.get("scale_override_param", _cfg.SCALE_OVERRIDE_PARAM)
HOTKEY_PREFIX        = _settings.get("hotkey_prefix",        _cfg.HOTKEY_PREFIX)
SEND_PORT            = _settings.get("send_port",            _cfg.SEND_PORT)
RECEIVE_PORT         = _settings.get("receive_port",         _cfg.RECEIVE_PORT)

init_client(_cfg.HOST, SEND_PORT)

################################################################################
# --- OSC callbacks ---

_avatar_seen = False

def handle_scale_override(_address, *args):
    global _avatar_seen
    first_contact = not _avatar_seen
    _avatar_seen = True
    if args[0]:
        if slot_is_empty(0):
            window.after(0, lambda: set_status(f"{SCALE_OVERRIDE_PARAM} triggered — slot 1 is empty!", "orange"))
        else:
            window.after(0, lambda: _load_and_refresh(0))
    elif first_contact:
        window.after(0, _revert_status)

def handle_avatar_change(_address, *_):
    global _avatar_seen
    _avatar_seen = False
    window.after(0, _revert_status)
    window.after(1000, lambda: probe_param(SCALE_OVERRIDE_PARAM))

register_handler(f"/avatar/parameters/{SCALE_OVERRIDE_PARAM}", handle_scale_override)
register_handler("/avatar/change", handle_avatar_change)
start_server(RECEIVE_PORT)

################################################################################
# --- Scale tracking for undo ---

_prev_applied = None
_cur_applied  = None

def _do_apply(value):
    global _prev_applied, _cur_applied
    result = apply_scale(value)
    _prev_applied = _cur_applied
    _cur_applied  = result
    undo_btn.config(state="normal" if _prev_applied is not None else "disabled")
    return result
################################################################################
# --- Slot label helper ---

def _slot_label(index, value=None):
    name    = get_slot_name(index)
    v       = load_slot(index) if value is None else value
    val_str = f"{v}m" if v is not None else "empty"
    if name:
        return f"{name}: {val_str}"
    if index == 0:
        return f"Slot 1 [{SCALE_OVERRIDE_PARAM}]: {val_str}"
    return f"Slot {index + 1}: {val_str}"

################################################################################
# --- UI actions ---

def _load_and_refresh(index):
    value = load_slot(index)
    if value is None:
        if _settings.get("empty_slot_applies_default", False):
            _quick_apply(SCALE_DEFAULT, f"Slot {index + 1} empty — applied default", "#aaa")
        else:
            set_status(f"Slot {index + 1} is empty", "orange")
        return
    result = _do_apply(value)
    scale_entry.delete(0, tk.END)
    scale_entry.insert(0, str(result))
    name = get_slot_name(index) or f"Slot {index + 1}"
    set_status(f"{name} loaded — {result}m", "green")

def _save_and_refresh(index):
    try:
        value = clamp(float(scale_entry.get()))
    except ValueError:
        set_status("Invalid input — enter a number to save", "red")
        return
    result = save_slot(index, value)
    slot_buttons[index].config(text=_slot_label(index, result))
    clear_buttons[index].config(state="normal")
    name = get_slot_name(index) or f"Slot {index + 1}"
    set_status(f"Saved {result}m to {name}", "cyan")

def _clear_and_refresh(index):
    clear_slot(index)
    slot_buttons[index].config(text=_slot_label(index))
    clear_buttons[index].config(state="disabled")
    name = get_slot_name(index) or f"Slot {index + 1}"
    set_status(f"{name} cleared", "#888")

def _rename_slot(index):
    dialog = tk.Toplevel(window)
    dialog.title(f"Rename Slot {index + 1}")
    dialog.configure(bg="#1e1e1e")
    dialog.resizable(False, False)
    dialog.transient(window)
    dialog.attributes("-toolwindow", True)
    dialog.grab_set()
    tk.Label(dialog, text=f"Name for Slot {index + 1}:", fg="white", bg="#1e1e1e").pack(pady=(10, 4))
    entry = tk.Entry(dialog, width=24)
    entry.insert(0, get_slot_name(index))
    entry.select_range(0, tk.END)
    entry.pack()
    entry.focus()
    def _confirm(_=None):
        set_slot_name(index, entry.get().strip())
        slot_buttons[index].config(text=_slot_label(index))
        dialog.destroy()
    entry.bind("<Return>", _confirm)
    tk.Button(dialog, text="OK", command=_confirm, bg="#5865f2", fg="white", width=8).pack(pady=6)
    dialog.update_idletasks()
    dw = dialog.winfo_reqwidth()
    dh = dialog.winfo_reqheight()
    x  = window.winfo_x() + (window.winfo_width()  - dw) // 2
    y  = window.winfo_y() + (window.winfo_height() - dh) // 2
    dialog.geometry(f"{dw}x{dh}+{x}+{y}")

def _show_slot_menu(event, index):
    menu = tk.Menu(window, tearoff=0, bg="#2a2a3a", fg="white",
                   activebackground="#5865f2", activeforeground="white")
    menu.add_command(label="Load",               command=lambda: _load_and_refresh(index))
    menu.add_command(label="Save current value", command=lambda: _save_and_refresh(index))
    menu.add_command(label="Rename...",          command=lambda: _rename_slot(index))
    if not slot_is_empty(index):
        menu.add_separator()
        menu.add_command(label="Clear", command=lambda: _clear_and_refresh(index))
    menu.tk_popup(event.x_root, event.y_root)

def apply_from_input():
    try:
        value = float(scale_entry.get())
        result = _do_apply(value)
        set_status(f"Scale set to {result}m", "green")
    except ValueError:
        set_status("Invalid input — enter a number", "red")

def nudge(delta):
    try:
        current = float(scale_entry.get())
    except ValueError:
        current = SCALE_DEFAULT
    new_val = clamp(round(current + delta, 3))
    scale_entry.delete(0, tk.END)
    scale_entry.insert(0, str(new_val))
    result = _do_apply(new_val)
    set_status(f"Scale nudged to {result}m", "green")

def _quick_apply(value, label, color="green"):
    result = _do_apply(value)
    scale_entry.delete(0, tk.END)
    scale_entry.insert(0, str(result))
    set_status(f"{label} — {result}m", color)

def undo_scale():
    global _prev_applied, _cur_applied
    if _prev_applied is not None:
        result = apply_scale(_prev_applied)
        scale_entry.delete(0, tk.END)
        scale_entry.insert(0, str(result))
        set_status(f"Undo — {result}m", "#aaa")
        _cur_applied, _prev_applied = _prev_applied, None
        undo_btn.config(state="disabled")

################################################################################
# --- Status helpers ---

_status_timer = None

def _idle_text():
    if _avatar_seen:
        return f"Avatar connected  •  \"{SCALE_OVERRIDE_PARAM}\" found"
    return f"Listening on port {RECEIVE_PORT} for \"{SCALE_OVERRIDE_PARAM}\""

def _idle_color():
    return "#4a9" if _avatar_seen else "#666"

def _revert_status():
    global _status_timer
    _status_timer = None
    status_label.config(text=_idle_text(), fg=_idle_color())

def set_status(text, fg="white", temporary=True):
    global _status_timer
    if _status_timer:
        window.after_cancel(_status_timer)
        _status_timer = None
    status_label.config(text=text, fg=fg)
    if temporary:
        _status_timer = window.after(3000, _revert_status)
    if not _avatar_seen:
        probe_param(SCALE_OVERRIDE_PARAM)

################################################################################
# --- Tooltip ---

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text   = text
        self._tip   = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _=None):
        if self._tip:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.attributes("-topmost", True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=self.text, bg="#2a2a3a", fg="white",
                 font=("Arial", 8), padx=8, pady=4, relief="flat").pack()

    def _hide(self, _=None):
        if self._tip:
            self._tip.destroy()
            self._tip = None

################################################################################
# --- Always-on-top ---

_always_on_top = _settings.get("always_on_top", False)

def toggle_always_on_top():
    global _always_on_top
    _always_on_top = not _always_on_top
    window.attributes("-topmost", _always_on_top)
    pin_btn.config(fg="#7aadff" if _always_on_top else "#666")
    _settings["always_on_top"] = _always_on_top
    save_settings(_settings)

################################################################################
# --- About dialog ---

def _open_about():
    dialog = tk.Toplevel(window)
    dialog.title("About")
    dialog.configure(bg="#1e1e1e")
    dialog.resizable(False, False)
    dialog.transient(window)
    dialog.attributes("-toolwindow", True)
    dialog.grab_set()

    try:
        _about_img = ImageTk.PhotoImage(PILImage.open(_ico_path).resize((64, 64), PILImage.LANCZOS))
        _img_label = tk.Label(dialog, image=_about_img, bg="#1e1e1e")
        _img_label.image = _about_img
        _img_label.pack(pady=(18, 6))
    except Exception:
        tk.Frame(dialog, height=18, bg="#1e1e1e").pack()

    tk.Label(dialog, text="Tazaur's VrC Scaling Tool",
             fg="white", bg="#1e1e1e", font=("Arial", 13, "bold")).pack(pady=(0, 2))
    tk.Label(dialog, text=f"Version {_cfg.VERSION}  •  Updated {_cfg.UPDATED}",
             fg="#888", bg="#1e1e1e", font=("Arial", 9)).pack()

    tk.Frame(dialog, bg="#333", height=1).pack(fill="x", padx=20, pady=12)

    tk.Label(dialog,
             text="Designed to make avatar scaling convenient,\nallowing for a wider range than VRChat's\ndefault menu allows. Please do not abuse\nthis in public lobbies.",
             fg="#aaa", bg="#1e1e1e", font=("Arial", 9), justify="left").pack(padx=24, anchor="w")

    tk.Frame(dialog, bg="#333", height=1).pack(fill="x", padx=20, pady=12)

    for line, color in [
        ("Made by Tazaur", "white"),
        ("This tool is free and open to use.", "#aaa"),
        ("If you paid for it, you were scammed.", "#f97"),
    ]:
        tk.Label(dialog, text=line, fg=color, bg="#1e1e1e",
                 font=("Arial", 9)).pack(padx=24, anchor="w")

    tk.Button(dialog, text="OK", command=dialog.destroy,
              bg="#333", fg="white", width=10).pack(pady=(14, 16))

    dialog.update_idletasks()
    dw = dialog.winfo_reqwidth()
    dh = dialog.winfo_reqheight()
    x  = window.winfo_x() + (window.winfo_width()  - dw) // 2
    y  = window.winfo_y() + (window.winfo_height() - dh) // 2
    dialog.geometry(f"{dw}x{dh}+{x}+{y}")

################################################################################
# --- Settings dialog ---

def _open_settings():
    dialog = tk.Toplevel(window)
    dialog.title("Settings")
    dialog.configure(bg="#1e1e1e")
    dialog.resizable(False, False)
    dialog.transient(window)
    dialog.attributes("-toolwindow", True)
    dialog.grab_set()

    fields = {}

    def _section(text):
        tk.Label(dialog, text=text, fg="#888", bg="#1e1e1e",
                 font=("Arial", 8)).pack(anchor="w", padx=16, pady=(10, 1))
        tk.Frame(dialog, bg="#444", height=1).pack(fill="x", padx=12, pady=(0, 4))

    def _row(label, key, value):
        f = tk.Frame(dialog, bg="#1e1e1e")
        f.pack(fill="x", padx=16, pady=2)
        tk.Label(f, text=label, fg="white", bg="#1e1e1e",
                 width=22, anchor="w").pack(side="left")
        e = tk.Entry(f, width=14)
        e.insert(0, str(value) if value is not None else "")
        e.pack(side="left")
        fields[key] = e

    _section("Scale")
    _row("Default height (m):", "scale_default", _settings.get("scale_default", _cfg.SCALE_DEFAULT))
    _row("Tiny height (m):",    "scale_tiny",    _settings.get("scale_tiny",    _cfg.SCALE_TINY))
    _row("Nudge step (m):",     "nudge_step",    _settings.get("nudge_step",    _cfg.NUDGE_STEP))

    _section("Slots")
    _row("Slot count (1–10):", "slot_count", _settings.get("slot_count", _cfg.SLOT_COUNT))
    _empty_default_var = tk.BooleanVar(value=_settings.get("empty_slot_applies_default", False))
    ed_frame = tk.Frame(dialog, bg="#1e1e1e")
    ed_frame.pack(fill="x", padx=16, pady=2)
    tk.Label(ed_frame, text="Empty slot behaviour:", fg="white", bg="#1e1e1e",
             width=22, anchor="w").pack(side="left")
    tk.Checkbutton(ed_frame, text="Apply default height", variable=_empty_default_var,
                   fg="white", bg="#1e1e1e", selectcolor="#333",
                   activebackground="#1e1e1e", activeforeground="white").pack(side="left")

    _section("Avatar")
    _row("OSC parameter:", "scale_override_param", _settings.get("scale_override_param", _cfg.SCALE_OVERRIDE_PARAM))

    _section("Hotkeys")
    hk_label_frame = tk.Frame(dialog, bg="#1e1e1e")
    hk_label_frame.pack(fill="x", padx=16, pady=(2, 0))
    tk.Label(hk_label_frame, text="Modifier keys:", fg="white", bg="#1e1e1e",
             width=22, anchor="w").pack(side="left")
    _current_prefix = (_settings.get("hotkey_prefix", _cfg.HOTKEY_PREFIX) or "").lower()
    _hk_vars = {}
    hk_check_frame = tk.Frame(dialog, bg="#1e1e1e")
    hk_check_frame.pack(fill="x", padx=16, pady=(0, 2))
    for mod in ("ctrl", "shift", "alt", "win"):
        v = tk.BooleanVar(value=(mod in _current_prefix))
        _hk_vars[mod] = v
        tk.Checkbutton(hk_check_frame, text=mod, variable=v, fg="white", bg="#1e1e1e",
                       selectcolor="#333", activebackground="#1e1e1e",
                       activeforeground="white").pack(side="left", padx=(0, 6))
    tk.Label(hk_check_frame, text="+ slot number", fg="#888", bg="#1e1e1e",
             font=("Arial", 8)).pack(side="left")

    _section("Advanced")
    _row("Send port:",    "send_port",    _settings.get("send_port",    _cfg.SEND_PORT))
    _row("Receive port:", "receive_port", _settings.get("receive_port", _cfg.RECEIVE_PORT))

    tk.Label(dialog, text="⚠  Restart required for changes to take effect.",
             fg="#e74c3c", bg="#1e1e1e", font=("Arial", 8)).pack(pady=(10, 2))

    btn_frame = tk.Frame(dialog, bg="#1e1e1e")
    btn_frame.pack(pady=(2, 12))

    def _save():
        try:
            new = dict(_settings)
            new["scale_default"]             = float(fields["scale_default"].get())
            new["scale_tiny"]                = float(fields["scale_tiny"].get())
            new["nudge_step"]                = float(fields["nudge_step"].get())
            new["slot_count"]                = max(1, min(10, int(fields["slot_count"].get())))
            new["scale_override_param"]      = fields["scale_override_param"].get().strip()
            checked = [mod for mod in ("ctrl", "shift", "alt", "win") if _hk_vars[mod].get()]
            new["hotkey_prefix"]             = "+".join(checked) or None
            new["send_port"]                 = int(fields["send_port"].get())
            new["receive_port"]              = int(fields["receive_port"].get())
            new["always_on_top"]             = _always_on_top
            new["tray_enabled"]              = _tray_enabled
            new["empty_slot_applies_default"] = _empty_default_var.get()
        except ValueError as e:
            set_status(f"Invalid value — {e}", "red")
            return
        save_settings(new)
        _settings.update(new)
        dialog.destroy()
        set_status("Settings saved — restart to apply", "#aaa")

    def _restore_defaults():
        for key, val in {
            "scale_default":        _cfg.SCALE_DEFAULT,
            "scale_tiny":           _cfg.SCALE_TINY,
            "nudge_step":           _cfg.NUDGE_STEP,
            "slot_count":           _cfg.SLOT_COUNT,
            "scale_override_param": _cfg.SCALE_OVERRIDE_PARAM,
            "send_port":            _cfg.SEND_PORT,
            "receive_port":         _cfg.RECEIVE_PORT,
        }.items():
            fields[key].delete(0, tk.END)
            fields[key].insert(0, str(val) if val is not None else "")
        default_prefix = (_cfg.HOTKEY_PREFIX or "").lower()
        for mod, var in _hk_vars.items():
            var.set(mod in default_prefix)

    tk.Button(btn_frame, text="Save",             command=_save,             bg="#5865f2", fg="white", width=10).pack(side="left", padx=6)
    tk.Button(btn_frame, text="Restore Defaults", command=_restore_defaults, bg="#555",    fg="white", width=14).pack(side="left", padx=6)
    tk.Button(btn_frame, text="Cancel",           command=dialog.destroy,    bg="#333",    fg="white", width=10).pack(side="left", padx=6)

    dialog.update_idletasks()
    dw = dialog.winfo_reqwidth()
    dh = dialog.winfo_reqheight()
    x  = window.winfo_x() + (window.winfo_width()  - dw) // 2
    y  = window.winfo_y() + (window.winfo_height() - dh) // 2
    dialog.geometry(f"{dw}x{dh}+{x}+{y}")

################################################################################
# --- Slot 1 info dialog ---

def _show_slot1_info():
    d = tk.Toplevel(window)
    d.title("Slot 1 — In-Game Trigger")
    d.configure(bg="#1e1e1e")
    d.resizable(False, False)
    d.transient(window)
    d.attributes("-toolwindow", True)
    d.grab_set()

    tk.Label(d, text="In-Game Trigger",
             fg="white", bg="#1e1e1e", font=("Arial", 13, "bold")).pack(pady=(18, 2), padx=24)
    tk.Label(d, text="Optional — trigger Slot 1 from inside VRChat",
             fg="#888", bg="#1e1e1e", font=("Arial", 9)).pack()

    tk.Frame(d, bg="#333", height=1).pack(fill="x", padx=20, pady=12)

    for text, color in [
        ("1.  Open your VRC Expression Parameters asset and", "#aaa"),
        ("    add a new Bool parameter named:",               "#aaa"),
    ]:
        tk.Label(d, text=text, fg=color, bg="#1e1e1e",
                 font=("Arial", 9), justify="left").pack(padx=24, anchor="w")
    tk.Label(d, text=f"    {SCALE_OVERRIDE_PARAM}",
             fg="white", bg="#1e1e1e", font=("Arial", 9, "bold")).pack(padx=24, anchor="w", pady=(2, 6))

    for text, color in [
        ("2.  Add a Button Toggle to your Expression Menu", "#aaa"),
        ("    that controls that parameter.",               "#aaa"),
        ("",                                               "#aaa"),
        ("3.  Enable OSC in VRChat:",                      "#aaa"),
        ("    Action Menu → Options → OSC → Enabled",      "#aaa"),
    ]:
        tk.Label(d, text=text, fg=color, bg="#1e1e1e",
                 font=("Arial", 9), justify="left").pack(padx=24, anchor="w")

    tk.Frame(d, bg="#333", height=1).pack(fill="x", padx=20, pady=12)

    tk.Label(d, text="When toggled ON in-game, Slot 1 loads and applies automatically.",
             fg="#aaa", bg="#1e1e1e", font=("Arial", 9), wraplength=280, justify="left").pack(padx=24, anchor="w")
    tk.Label(d, text="The parameter name can be changed in Settings.",
             fg="#5865f2", bg="#1e1e1e", font=("Arial", 8)).pack(padx=24, anchor="w", pady=(4, 0))

    tk.Button(d, text="OK", command=d.destroy,
              bg="#333", fg="white", width=10).pack(pady=(14, 16))

    d.update_idletasks()
    dw = d.winfo_reqwidth()
    dh = d.winfo_reqheight()
    x  = window.winfo_x() + (window.winfo_width()  - dw) // 2
    y  = window.winfo_y() + (window.winfo_height() - dh) // 2
    d.geometry(f"{dw}x{dh}+{x}+{y}")

################################################################################
# --- Update check ---

def _version_newer(a, b):
    try:
        return tuple(int(x) for x in a.split(".")) > tuple(int(x) for x in b.split("."))
    except Exception:
        return False

def _show_update_dialog(version, url):
    d = tk.Toplevel(window)
    d.title("Update Available")
    d.configure(bg="#1e1e1e")
    d.resizable(False, False)
    d.transient(window)
    d.attributes("-toolwindow", True)

    tk.Label(d, text="Update Available",
             fg="white", bg="#1e1e1e", font=("Arial", 13, "bold")).pack(pady=(18, 2), padx=24)
    tk.Label(d, text=f"v{version} is available  •  You have v{_cfg.VERSION}",
             fg="#888", bg="#1e1e1e", font=("Arial", 9)).pack()

    tk.Frame(d, bg="#333", height=1).pack(fill="x", padx=20, pady=12)

    tk.Label(d, text="Would you like to download the latest version?",
             fg="#aaa", bg="#1e1e1e", font=("Arial", 9)).pack(padx=24)

    tk.Frame(d, bg="#333", height=1).pack(fill="x", padx=20, pady=12)

    btn_frame = tk.Frame(d, bg="#1e1e1e")
    btn_frame.pack(pady=(0, 16))

    def _go():
        webbrowser.open(url)
        d.destroy()

    tk.Button(btn_frame, text="Download Update", command=_go,
              bg="#5865f2", fg="white", width=14).pack(side="left", padx=6)
    tk.Button(btn_frame, text="Not Now", command=d.destroy,
              bg="#333", fg="white", width=10).pack(side="left", padx=6)

    d.update_idletasks()
    dw = d.winfo_reqwidth()
    dh = d.winfo_reqheight()
    x  = window.winfo_x() + (window.winfo_width()  - dw) // 2
    y  = window.winfo_y() + (window.winfo_height() - dh) // 2
    d.geometry(f"{dw}x{dh}+{x}+{y}")

def _check_update(silent=True):
    if not _cfg.GITHUB_REPO:
        if not silent:
            set_status("No GitHub repo configured", "#888")
        return
    def _fetch():
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{_cfg.GITHUB_REPO}/releases/latest",
                headers={"User-Agent": "TazaursVrCScalingTool"}
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
            tag     = data.get("tag_name", "").lstrip("v")
            html_url = data.get("html_url", "")
            if _version_newer(tag, _cfg.VERSION):
                window.after(0, lambda: _show_update_dialog(tag, html_url))
            elif not silent:
                window.after(0, lambda: set_status("You're up to date", "#4a9"))
        except Exception:
            if not silent:
                window.after(0, lambda: set_status("Update check failed", "#e74c3c"))
    threading.Thread(target=_fetch, daemon=True).start()

################################################################################
# --- Tray toggle ---

_tray_enabled = _settings.get("tray_enabled", True)

def toggle_tray():
    global _tray_enabled
    _tray_enabled = not _tray_enabled
    tray_btn.config(fg="#7aadff" if _tray_enabled else "#666")
    _settings["tray_enabled"] = _tray_enabled
    save_settings(_settings)

################################################################################
# --- System tray ---

_tray_icon = None

def _hide_to_tray():
    window.withdraw()

def _show_from_tray(*_):
    window.after(0, lambda: (window.deiconify(), window.lift()))

def _save_window_pos():
    _settings["window_x"] = window.winfo_x()
    _settings["window_y"] = window.winfo_y()
    save_settings(_settings)

def _quit_app(*_):
    window.after(0, lambda: (_save_window_pos(), window.destroy()))

def _on_close():
    _save_window_pos()
    if _tray_available and _tray_icon and _tray_enabled:
        _hide_to_tray()
    else:
        window.destroy()

def _setup_tray():
    global _tray_icon
    if not _tray_available:
        return
    try:
        img = PILImage.open(_ico_path).resize((64, 64))
    except Exception:
        img = PILImage.new("RGB", (64, 64), color=(88, 101, 242))

    slot_items = []
    for i in range(SLOT_COUNT):
        name  = get_slot_name(i) or f"Slot {i + 1}"
        val   = load_slot(i)
        label = f"{name}: {val}m" if val is not None else f"{name} (empty)"
        slot_items.append(pystray.MenuItem(
            label,
            lambda *_, i=i: window.after(0, lambda i=i: _load_and_refresh(i)),
            enabled=val is not None
        ))

    menu = pystray.Menu(
        pystray.MenuItem("Show", _show_from_tray, default=True),
        pystray.Menu.SEPARATOR,
        *slot_items,
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", _quit_app),
    )
    _tray_icon = pystray.Icon("TazaursVrCScalingTool", img, "Tazaur's VrC Scaling Tool", menu)
    threading.Thread(target=_tray_icon.run, daemon=True).start()

################################################################################
# --- Global hotkeys ---

def _setup_hotkeys():
    if not _hotkeys_available or not HOTKEY_PREFIX:
        return
    try:
        for i in range(min(SLOT_COUNT, 9)):
            keyboard.add_hotkey(
                f"{HOTKEY_PREFIX}+{i + 1}",
                lambda i=i: window.after(0, lambda i=i: _load_and_refresh(i))
            )
    except Exception as e:
        print(f"Hotkeys unavailable: {e}")

################################################################################
# --- Build window ---

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("TazaursVrCScalingTool")
window = tk.Tk()
window.withdraw()
window.title("Tazaur's VrC Scaling Tool")
_base     = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
_ico_path = os.path.join(_base, "TVST.ico")
window.iconbitmap(_ico_path)
_ico_img = ImageTk.PhotoImage(PILImage.open(_ico_path))
window.iconphoto(True, _ico_img)
window.configure(bg="#1e1e1e")
window.resizable(False, False)

# Title bar (icons)
title_frame = tk.Frame(window, bg="#1e1e1e")
title_frame.pack(fill="x", padx=10, pady=(10, 0))

settings_btn = tk.Button(title_frame, text="⚙", fg="#666", bg="#1e1e1e", relief="flat",
                         font=("Arial", 12), command=_open_settings, cursor="hand2", bd=0)
settings_btn.pack(side="right", padx=(0, 4))
Tooltip(settings_btn, "Settings")

update_btn = tk.Button(title_frame, text="↻", fg="#666", bg="#1e1e1e", relief="flat",
                       font=("Arial", 12), command=lambda: _check_update(silent=False),
                       cursor="hand2", bd=0)
update_btn.pack(side="right", padx=(0, 4))
Tooltip(update_btn, "Check for updates")

tray_btn = tk.Button(title_frame, text="⬇", fg="#7aadff" if _tray_available else "#444",
                     bg="#1e1e1e", relief="flat", font=("Arial", 11), bd=0,
                     command=toggle_tray if _tray_available else None, cursor="hand2")
tray_btn.pack(side="right", padx=(0, 4))
Tooltip(tray_btn, "Minimize to system tray on close" if _tray_available else "pystray not installed")

pin_btn = tk.Button(title_frame, text="📌", fg="#666", bg="#1e1e1e", relief="flat",
                    font=("Arial", 11), command=toggle_always_on_top, cursor="hand2", bd=0)
pin_btn.pack(side="right", padx=(0, 2))
Tooltip(pin_btn, "Keep window always on top")

about_btn = tk.Button(title_frame, text="ℹ", fg="#666", bg="#1e1e1e", relief="flat",
                      font=("Arial", 11), command=_open_about, cursor="hand2", bd=0)
about_btn.pack(side="right")
Tooltip(about_btn, "About")

# Title label
tk.Label(window, text="Avatar Scale Control", fg="white", bg="#1e1e1e",
         font=("Arial", 14, "bold")).pack(pady=(6, 2))

if _always_on_top:
    window.attributes("-topmost", True)
    pin_btn.config(fg="#7aadff")
if not _tray_enabled and _tray_available:
    tray_btn.config(fg="#666")

# Input row
input_frame = tk.Frame(window, bg="#1e1e1e")
input_frame.pack(pady=5)
tk.Label(input_frame, text="Eye Height (m):", fg="white", bg="#1e1e1e").grid(row=0, column=0, padx=5)
scale_entry = tk.Entry(input_frame, width=8)
scale_entry.insert(0, str(SCALE_DEFAULT))
scale_entry.grid(row=0, column=1, padx=4)
tk.Button(input_frame, text="Apply", command=apply_from_input,
          bg="#5865f2", fg="white", width=6).grid(row=0, column=2, padx=(0, 2))
tk.Button(input_frame, text="−", command=lambda: nudge(-NUDGE_STEP),
          bg="#333", fg="white", width=2).grid(row=0, column=3, padx=1)
tk.Button(input_frame, text="+", command=lambda: nudge(NUDGE_STEP),
          bg="#333", fg="white", width=2).grid(row=0, column=4, padx=(1, 5))

tk.Label(window, text=f"(Range: 0.01 – 20.0  •  Nudge: ±{NUDGE_STEP}m)",
         fg="#888", bg="#1e1e1e", font=("Arial", 8)).pack()

tk.Frame(window, bg="#444", height=1).pack(fill="x", padx=20, pady=8)

# Slots
tk.Label(window, text="Save Slots", fg="white", bg="#1e1e1e", font=("Arial", 11, "bold")).pack()
instruction_lines = [
    "• Click a slot to load and apply it",
    "• Right-click a slot for options (save, rename, clear)",
    "• Press ℹ on Slot 1 to set up in-game triggering",
]
if HOTKEY_PREFIX and _hotkeys_available:
    instruction_lines.append(f"• {HOTKEY_PREFIX.upper()}+1–{min(SLOT_COUNT, 9)} loads slots globally")
tk.Label(window, text="\n".join(instruction_lines), fg="#888", bg="#1e1e1e",
         font=("Arial", 8), justify="left").pack(padx=20, anchor="w")

slot_frame = tk.Frame(window, bg="#1e1e1e")
slot_frame.pack(pady=8)

slot_buttons  = []
clear_buttons = []

for i in range(SLOT_COUNT):
    row_frame = tk.Frame(slot_frame, bg="#1e1e1e")
    row_frame.pack(pady=2)

    if i == 0:
        tk.Button(row_frame, text="ℹ", width=2, bg="#2a2a3a", fg="#7aadff",
                  command=_show_slot1_info).pack(side="left", padx=(0, 4))
    else:
        tk.Label(row_frame, text="", width=2, bg="#1e1e1e").pack(side="left", padx=(0, 8))

    btn = tk.Button(row_frame, text=_slot_label(i), width=24,
                    bg="#2a2a3a" if i == 0 else "#333", fg="white", anchor="w",
                    command=lambda i=i: _load_and_refresh(i))
    btn.bind("<Button-3>", lambda e, i=i: _show_slot_menu(e, i))
    btn.pack(side="left")

    clr = tk.Button(row_frame, text="✕", width=2, bg="#555", fg="#e74c3c",
                    state="normal" if not slot_is_empty(i) else "disabled",
                    command=lambda i=i: _clear_and_refresh(i))
    clr.pack(side="left", padx=4)

    slot_buttons.append(btn)
    clear_buttons.append(clr)

tk.Frame(window, bg="#444", height=1).pack(fill="x", padx=20, pady=8)

# Quick buttons + undo
quick_frame = tk.Frame(window, bg="#1e1e1e")
quick_frame.pack()
tk.Button(quick_frame, text=f"Tiny ({SCALE_TINY}m)",
          command=lambda: _quick_apply(SCALE_TINY, "Tiny", "#e74c3c"),
          bg="#e74c3c", fg="white", width=11).grid(row=0, column=0, padx=3)
tk.Button(quick_frame, text=f"Normal ({SCALE_DEFAULT}m)",
          command=lambda: _quick_apply(SCALE_DEFAULT, "Normal", "#aaa"),
          bg="#555", fg="white", width=11).grid(row=0, column=1, padx=3)
undo_btn = tk.Button(quick_frame, text="↩ Undo", command=undo_scale,
                     bg="#333", fg="#aaa", width=8, state="disabled")
undo_btn.grid(row=0, column=2, padx=3)

# Status
status_label = tk.Label(window, text=_idle_text(), fg=_idle_color(),
                        bg="#1e1e1e", font=("Arial", 9))
status_label.pack(pady=8)

# Lock window size and restore position
window.update_idletasks()
_h  = window.winfo_reqheight()
_wx = _settings.get("window_x")
_wy = _settings.get("window_y")
window.geometry(f"340x{_h}+{_wx}+{_wy}" if _wx is not None and _wy is not None else f"340x{_h}")

def _enforce_size(event):
    if event.widget is window and window.state() == "normal" and window.winfo_height() < _h - 5:
        window.geometry(f"340x{_h}")
window.bind("<Configure>", _enforce_size)

_setup_tray()
_setup_hotkeys()
window.protocol("WM_DELETE_WINDOW", _on_close)
probe_param(SCALE_OVERRIDE_PARAM)
_check_update(silent=True)
window.deiconify()
window.mainloop()
