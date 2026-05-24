import json
import os
from config import SLOT_COUNT as _cfg_slot_count

_base     = os.path.join(os.path.expanduser("~"), "Documents", "TazaursVrCScalingTool")
os.makedirs(_base, exist_ok=True)
DATA_FILE = os.path.join(_base, "data.json")

_data = {}

def _load():
    global _data
    try:
        with open(DATA_FILE) as f:
            _data = json.load(f)
    except Exception:
        _data = {}

def _save():
    with open(DATA_FILE, "w") as f:
        json.dump(_data, f)

_load()
SLOT_COUNT = max(1, min(10, _data.get("slot_count", _cfg_slot_count)))

def load_settings():
    return dict(_data)

def save_settings(patch):
    _data.update(patch)
    _save()

def load_from_disk():
    values = list(_data.get("slot_values", []))
    names  = list(_data.get("slot_names",  []))
    if len(values) < SLOT_COUNT:
        values += [None] * (SLOT_COUNT - len(values))
    if len(names) < SLOT_COUNT:
        names  += [""]   * (SLOT_COUNT - len(names))
    return values[:SLOT_COUNT], names[:SLOT_COUNT]

def save_to_disk(values, names):
    _data["slot_values"] = values
    _data["slot_names"]  = names
    _save()
