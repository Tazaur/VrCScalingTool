import threading
from pythonosc import dispatcher, osc_server
from config import HOST

_handlers = {}

def register_handler(address, fn):
    _handlers[address] = fn

def start_server(port):
    disp = dispatcher.Dispatcher()
    for address, fn in _handlers.items():
        disp.map(address, fn)
    server = osc_server.ThreadingOSCUDPServer((HOST, port), disp)
    threading.Thread(target=server.serve_forever, daemon=True).start()
