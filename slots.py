from config import SCALE_MIN, SCALE_MAX
from persistence import load_from_disk, save_to_disk

_values, _names = load_from_disk()

def clamp(value):
    return max(SCALE_MIN, min(SCALE_MAX, value))

def save_slot(index, value):
    value = clamp(value)
    _values[index] = value
    save_to_disk(_values, _names)
    return value

def load_slot(index):
    return _values[index]

def clear_slot(index):
    _values[index] = None
    save_to_disk(_values, _names)

def slot_is_empty(index):
    return _values[index] is None

def get_slot_name(index):
    return _names[index] if index < len(_names) else ""

def set_slot_name(index, name):
    _names[index] = name
    save_to_disk(_values, _names)
