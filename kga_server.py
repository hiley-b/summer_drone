#!/usr/bin/env sage -python
import socket
import json
import basicident
from basicident import gen_global_params, H1
from sage.all import EllipticCurve, GF
import config

# ─── IBE SETUP (in SGX) ────────────────────────────────────────────────────────
ibe   = gen_global_params()
P     = ibe.P
order = int(ibe.order)
P_pub = ibe.gen_P_pub()

# ─── TCP HELPERS ───────────────────────────────────────────────────────────────
def recv_msg(conn):
    # read up to 4 KiB once (assumes your JSON <4 KiB)
    data = conn.recv(4096)
    return json.loads(data.decode())

def send_msg(conn, obj):
    conn.sendall(json.dumps(obj).encode())

# ─── CORE REQUEST HANDLER ─────────────────────────────────────────────────────
def handle_request(req):
    typ = req.get('type')
    if typ == 'params':
        return {
            'P':     {'x': int(P[0]),     'y': int(P[1])},
            'P_pub': {'x': int(P_pub[0]), 'y': int(P_pub[1])},
            'order': order
        }

    if typ == 'public_key':
        identity = req.get('identity')
        Q_ID = H1(identity, order, P)
        return {
            'identity': identity,
            'Q_ID':     {'x': int(Q_ID[0]), 'y': int(Q_ID[1])}
        }

    if typ == 'private_key':
        identity = req.get('identity')
        d_ID = ibe.private_key(identity, order, P)
        return {
            'identity': identity,
            'd_ID':     {'x': int(d_ID[0]), 'y': int(d_ID[1])}
        }

    return {'error': 'unknown request'}

# ─── SERVER LOOP ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((config.HOST, config.KGA_PORT))
    sock.listen(1)
    print(f"KGA listening on {config.HOST}:{config.KGA_PORT}")

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
