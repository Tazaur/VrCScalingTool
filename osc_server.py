import threading
from pythonosc import dispatcher, osc_server
from config import HOST

_handlers = {}

def register_handler(address, fn):
    _handlers[address] = fn

def start_server(port):
    """Start OSC server. Returns actual port bound, or None on failure.
    Pass port=0 to let the OS pick a free port.
    """
    try:
        disp = dispatcher.Dispatcher()
        for address, fn in _handlers.items():
            disp.map(address, fn)
        server = osc_server.ThreadingOSCUDPServer((HOST, port), disp)
        actual_port = server.server_address[1]
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return actual_port
    except OSError:
        return None
