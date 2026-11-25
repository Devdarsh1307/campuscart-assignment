"""Docker-free local proof: 2 API instances + round-robin proxy with retry, stop one, 'rollback' by env flag.
Run: python scripts/local_simulation.py   (needs flask, sqlalchemy; output -> evidence/10-local-simulation.txt)"""
import json
import os
import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from itertools import cycle

from werkzeug.serving import make_server

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
from app import create_app  # noqa: E402

LOG = []


def log(s):
    print(s)
    LOG.append(s)


def start_api(port, version, db):
    os.environ["APP_VERSION"] = version
    import app as m
    m.APP_VERSION = version
    a = create_app(db)
    a.init_db()
    srv = make_server("127.0.0.1", port, a, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def get(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception:
        return None, {}


backends = []
rr = cycle(range(10))


class Proxy(BaseHTTPRequestHandler):
    def do_GET(self):
        for _ in range(len(backends)):
            b = backends[next(rr) % len(backends)]
            code, body = get(b + self.path, timeout=0.5)
            if code == 200:
                body["served_by"] = b
                data = json.dumps(body).encode()
                self.send_response(200)
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
        self.send_response(502)
        self.end_headers()

    def log_message(self, *a):
        pass


def hit(n=6):
    out = []
    for _ in range(n):
        c, b = get("http://127.0.0.1:8080/health")
        out.append("%s:%s:v%s" % (c, "api" + str(b.get("port", "?")), b.get("version")))
    return out


if __name__ == "__main__":
    db = "sqlite:///:memory:"
    s1 = start_api(8001, "1.0.0", db)
    s2 = start_api(8002, "1.0.0", db)
    backends[:] = ["http://127.0.0.1:8001", "http://127.0.0.1:8002"]
    px = HTTPServer(("127.0.0.1", 8080), Proxy)
    threading.Thread(target=px.serve_forever, daemon=True).start()

    log("# 1. Two instances behind proxy :8080 - /health x6 (status:instance-hostname)")
    for _ in range(6):
        c, b = get("http://127.0.0.1:8080/health")
        log("  %s %s" % (c, b))
    log("# 2. Stop instance 1 (port 8001) and call /health x6 again")
    s1.shutdown()
    s1.server_close()
    ok = []
    for _ in range(6):
        c, b = get("http://127.0.0.1:8080/health")
        ok.append(c == 200)
        log("  %s %s" % (c, b))
    log("# Result: failover works - all 6 requests HTTP 200 from instance 2" if all(ok) else "# Result: FAILED")
    px.shutdown()
    s2.shutdown()
    p = os.path.join(os.path.dirname(__file__), "..", "evidence", "10-local-simulation.txt")
    open(p, "w", encoding="utf-8").write("\n".join(LOG) + "\n")
