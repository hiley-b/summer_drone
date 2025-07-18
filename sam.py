#!/usr/bin/env sage -python
import socket, json, random
import basicident
from basicident import decrypt
from sage.all import EllipticCurve, GF
import config

# ─── Globals (populated once) ─────────────────────────────────────────────────
order = None
P     = None
dSAM  = None

# ─── Simple JSON‑over‑TCP client ────────────────────────────────────────────────
def send_request(port, req):
    s = socket.socket()
    s.connect((config.HOST, port))
    s.sendall(json.dumps(req).encode())
    data = s.recv(4096)   # single recv
    s.close()
    return json.loads(data.decode())

# ─── Pull in IBE params + private key, but only after we bind (so we print immediately) ─
def init_ibe():
    global order, P, dSAM
    kp = send_request(config.KGA_PORT, {'type':'params'})
    order = kp['order']
    E     = EllipticCurve(GF(10177), [0,1])
    P     = E(kp['P']['x'], kp['P']['y'])
    dj    = send_request(config.KGA_PORT,
                         {'type':'private_key','identity':config.SAM_ID})['d_ID']
    dSAM  = E(dj['x'], dj['y'])

# ─── Weather + decision rule ────────────────────────────────────────────────────
def get_wind():
    return random.choice(['no wind','moderate wind','high wind'])

def decide(rep, env):
    xp = rep.get('wind_xp',0)
    if env == 'no wind':
        return 'approval', {}
    if env == 'moderate wind':
        return ('approval', {}) if xp>=1 else ('conditional approval',{'max_velocity[m/s]':5})
    return 'denial', {'reason':'high winds'}

# ─── Handle one incoming JSON req ────────────────────────────────────────────────
def handle_request(req):
    typ = req.get('type')
    if typ == 'request_entry':
        print(" SAM recieved request_entry")                     # DEBUG
        ID  = req['id']
        enc = req['encrypted_mission_id']
        C1  = P.curve()(enc['C1']['x'], enc['C1']['y'])
        C2  = enc['C2']
        mid = decrypt((C1,C2), dSAM, order)

        rep = send_request(config.DRP_MANAGER_PORT,
                           {'type':'get_profile','identity':ID})
        outcome, cond = decide(rep, get_wind())

        resp = {'id':ID,'mission_id':mid,'outcome':outcome}
        if cond: resp['conditions']=cond
        return resp

    if typ == 'exit_log':
        print("SAM got exit_log")                          # DEBUG
        ID     = req['id']
        mid    = req['mission_id']
        status = req.get('completed')
        rep = send_request(config.DRP_MANAGER_PORT,
                           {'type':'get_profile','identity':ID})
        if status=='success' and get_wind()=='moderate wind':
            newxp = rep.get('wind_xp',0)+1
            send_request(config.DRP_MANAGER_PORT,
                         {'type':'update_profile','identity':ID,
                          'patch':{'wind_xp':newxp}})
        return {'status':'logged'}

    return {'error':'unknown request'}

# ─── Main server loop ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((config.HOST, config.SAM_PORT))
    sock.listen(1)
    print(f"SAM listening on {config.HOST}:{config.SAM_PORT}")

    # Now fetch the IBE parameters (won’t block your banner)
    init_ibe()

    while True:
        conn, _ = sock.accept()
        raw = conn.recv(4096)                     # single read
        try:
            req  = json.loads(raw.decode())
            resp = handle_request(req)
        except Exception as e:
            resp = {'error': str(e)}
        conn.sendall(json.dumps(resp).encode())
        conn.close()
