VERSION = "1.0.2"
UPDATED = "2026-05-30"

# Ports
SEND_PORT = 9000
RECEIVE_PORT = 9001
HOST = "127.0.0.1"

# Scale limits
SCALE_MIN = 0.01
SCALE_MAX = 20.0
SCALE_DEFAULT = 1.7
SCALE_TINY = 0.1

# Number of save slots (1–10, enforced at runtime)
SLOT_COUNT = 5

# VRChat avatar parameter name that triggers Slot 1 via OSC
# Must match the Bool parameter name on your avatar (optional feature)
SCALE_OVERRIDE_PARAM = "ScaleOverride"

# Scale nudge step for the +/- buttons (in metres)
NUDGE_STEP = 0.01

# Global hotkey prefix for loading slots (e.g. "ctrl+shift" → ctrl+shift+1 loads slot 1)
# Set to None to disable global hotkeys entirely
HOTKEY_PREFIX = "ctrl+shift"

# GitHub repo for update checks (e.g. "Tazaur/VrCScalingTool") — leave empty to disable
GITHUB_REPO = "Tazaur/VrCScalingTool"
