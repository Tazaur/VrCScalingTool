from pythonosc import udp_client
from slots import clamp

_client = None

def init_client(host, port):
    global _client
    _client = udp_client.SimpleUDPClient(host, port)

def apply_scale(height):
    height = clamp(height)
    _client.send_message("/avatar/eyeheight", height)
    return height

def probe_param(name):
    _client.send_message(f"/avatar/parameters/{name}", False)
