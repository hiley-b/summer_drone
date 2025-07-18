#!/usr/bin/env sage -python
import socket, json
import basicident
from basicident import H1, encrypt
from sage.all import EllipticCurve, GF
import config

print("PLEASE START PLEASE up")   # 🔥 first check

def send_request(port, req):
    print(f" connecting to port {port}…")
    try:
        s = socket.socket()
        s.connect((config.HOST, port))
        s.sendall(json.dumps(req).encode())
        data = b''
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        s.close()
        return json.loads(data.decode())
    except Exception as e:
        print(f"send_request error ({port}):", e)
        return None

def fetch_params():
    return send_request(config.KGA_PORT, {'type':'params'})

def request_entry(identity, mission_id):
    print(f"…request_entry → id={identity}, mid={mission_id}")
    p      = fetch_params()
    if not p:
        print("aborting: no params")
        return
    order  = p['order']
    E      = EllipticCurve(GF(10177), [0,1])
    P_pub  = E(p['P_pub']['x'], p['P_pub']['y'])
    Q_sam  = H1(config.SAM_ID, order, E(p['P']['x'], p['P']['y']))
    C1, C2 = encrypt(str(mission_id), P_pub, order,
                     E(p['P']['x'], p['P']['y']), Q_sam)

    req = {
        'type': 'request_entry',
        'id': identity,
        'encrypted_mission_id': {
            'C1': {'x': int(C1[0]), 'y': int(C1[1])},
            'C2': C2
        }
    }
    resp = send_request(config.SAM_PORT, req)
    print("→ entry response:", resp)

def exit_log(identity, mission_id, completed='success'):
    print(f"…exit_log → id={identity}, mid={mission_id}, completed={completed}")
    req = {
        'type': 'exit_log',
        'id': identity,
        'mission_id': mission_id,
        'completed': completed
    }
    resp = send_request(config.SAM_PORT, req)
    print("→ exit response:", resp)

if __name__ == '__main__':
    ID  = 'lime@notredame'
    MID = 123456
    request_entry(ID, MID)
    exit_log(ID, MID)
