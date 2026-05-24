import ctypes
import sys

_mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "TazaursVrCScalingTool_Mutex")
if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    hwnd = ctypes.windll.user32.FindWindowW(None, "Tazaur's VrC Scaling Tool")
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 9)   # SW_RESTORE
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    sys.exit(0)

import ui
