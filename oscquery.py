import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

try:
    from zeroconf import Zeroconf, ServiceInfo
    _available = True
except ImportError:
    _available = False

_zc          = None
_http_server = None


def available():
    return _available


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _build_tree(avatar_param):
    """Build the OSCQuery node tree declaring the endpoints we want to receive."""
    param_node = {
        "DESCRIPTION": "",
        "FULL_PATH": f"/avatar/parameters/{avatar_param}",
        "ACCESS": 1,
        "TYPE": "T",
        "VALUE": [False],
    }
    parameters_node = {
        "DESCRIPTION": "",
        "FULL_PATH": "/avatar/parameters",
        "ACCESS": 0,
        "CONTENTS": {avatar_param: param_node},
    }
    change_node = {
        "DESCRIPTION": "",
        "FULL_PATH": "/avatar/change",
        "ACCESS": 1,
        "TYPE": "s",
        "VALUE": [""],
    }
    avatar_node = {
        "DESCRIPTION": "",
        "FULL_PATH": "/avatar",
        "ACCESS": 0,
        "CONTENTS": {
            "change": change_node,
            "parameters": parameters_node,
        },
    }
    return {
        "DESCRIPTION": "root node",
        "FULL_PATH": "/",
        "ACCESS": 0,
        "CONTENTS": {"avatar": avatar_node},
    }


def start(app_name, osc_port, avatar_param="ScaleOverride"):
    """Advertise via mDNS and serve OSCQuery HTTP. Returns True on success."""
    global _zc, _http_server
    if not _available:
        return False

    http_port = _free_port()

    host_info = {
        "NAME": app_name,
        "OSC_IP": "127.0.0.1",
        "OSC_PORT": osc_port,
        "OSC_TRANSPORT": "UDP",
        "EXTENSIONS": {
            "ACCESS": True,
            "CLIPMODE": False,
            "RANGE": False,
            "TYPE": True,
            "VALUE": True,
        },
    }
    root_node = _build_tree(avatar_param)

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if "HOST_INFO" in self.path:
                data = json.dumps(host_info).encode()
            else:
                # Walk the tree to the requested path
                path = self.path.split("?")[0].rstrip("/") or "/"
                node = _node_at(root_node, path)
                data = json.dumps(node).encode() if node else b"{}"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_):
            pass

    try:
        _http_server = HTTPServer(("127.0.0.1", http_port), _Handler)
        threading.Thread(target=_http_server.serve_forever, daemon=True).start()

        _zc = Zeroconf()
        info = ServiceInfo(
            "_oscjson._tcp.local.",
            f"{app_name}._oscjson._tcp.local.",
            addresses=[socket.inet_aton("127.0.0.1")],
            port=http_port,
            properties={},
        )
        _zc.register_service(info)
        return True
    except Exception:
        return False


def _node_at(root, path):
    """Traverse the tree to find the node at the given path."""
    if path == "/":
        return root
    parts = [p for p in path.split("/") if p]
    node = root
    for part in parts:
        contents = node.get("CONTENTS", {})
        if part not in contents:
            return None
        node = contents[part]
    return node


def stop():
    global _zc, _http_server
    if _zc:
        try:
            _zc.close()
        except Exception:
            pass
        _zc = None
    if _http_server:
        try:
            _http_server.shutdown()
        except Exception:
            pass
        _http_server = None
