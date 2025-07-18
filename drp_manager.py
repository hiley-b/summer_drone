#!/usr/bin/env python3
import socket
import json
import config

DB_FILE = 'drp.json'

# ─── load/save helpers ────────────────────────────────────────────────────────
def load_drp():
    with open(DB_FILE) as f:
        return json.load(f)

def save_drp(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ─── TCP helpers ─────────────────────────────────────────────────────────────
def recv_msg(conn):
    # single recv: assumes incoming JSON < 4 KiB
    data = conn.recv(4096)
    return json.loads(data.decode())

def send_msg(conn, obj):
    conn.sendall(json.dumps(obj).encode())

# ─── core request dispatcher ──────────────────────────────────────────────────
def handle_request(req):
    typ      = req.get('type')
    identity = req.get('identity')
    drones   = load_drp().get('drones', [])

    if typ == 'get_profile':
        for d in drones:
            if d.get('identity') == identity:
                return d
        return {'error': 'not found'}

    if typ == 'update_profile':
        patch = req.get('patch', {})
        for d in drones:
            if d.get('identity') == identity:
                d.update(patch)
                save_drp({'drones': drones})
                return d
        return {'error': 'not found'}

    return {'error': 'unknown request'}

# ─── server loop ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((config.HOST, config.DRP_MANAGER_PORT))
    sock.listen(1)
    print(f"DRP Manager on {config.HOST}:{config.DRP_MANAGER_PORT}")

    while True:
        conn, _ = sock.accept()
        try:
            req  = recv_msg(conn)
            resp = handle_request(req)
            send_msg(conn, resp)
        except Exception as e:
            send_msg(conn, {'error': str(e)})
        finally:
            conn.close()
