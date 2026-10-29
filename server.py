# WAR CHAT — cloud build. Same API as sandbox version, plus /health endpoint for uptime monitors.
# Storage: JSON files on the platform's persistent disk (Railway volume / Render disk).
import json, os, base64, threading, time, re, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get('DATA_DIR', os.path.join(ROOT, 'data'))
MEDIA = os.path.join(DATA, 'media'); STORE = os.path.join(DATA, 'messages.json')
CODE = os.environ.get('WARCHAT_CODE')
if not CODE:
    try:
        CODE = json.load(open(os.path.join(ROOT, 'config.json')))['passcode']
    except Exception:
        CODE = 'war2526'
PORT = int(os.environ.get('PORT', 8801))
_lock = threading.Lock()
os.makedirs(MEDIA, exist_ok=True)

def load_msgs():
    try: return json.load(open(STORE))
    except Exception: return []
def save_msgs(m):
    tmp = STORE + '.tmp'
    with open(tmp,'w') as f: json.dump(m,f)
    os.replace(tmp, STORE)
def auth(h): return h.get('X-Token','') == CODE
def ext_of(name, mime):
    m = {'image/png':'png','image/jpeg':'jpg','image/webp':'webp','image/gif':'gif',
         'audio/webm':'webm','audio/ogg':'ogg','audio/mpeg':'mp3','audio/mp4':'m4a',
         'application/pdf':'pdf','text/plain':'txt'}
    return (m.get(mime) or (name.rsplit('.',1)[-1].lower() if '.' in name else 'bin'))[:8] or 'bin'

class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def _hdr(self, code, ctype='application/json'):
        self.send_response(code); self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control','no-store'); self.end_headers()
    def _json(self, obj, code=200):
        self._hdr(code); self.wfile.write(json.dumps(obj).encode())
    def do_GET(self):
        u = urlparse(self.path)
        if u.path == '/health':
            return self._json({'ok': True, 'uptime': int(time.time()) - STARTED})
        if u.path in ('/','/index.html'):
            body = open(os.path.join(ROOT,'index.html'),'rb').read()
            self._hdr(200,'text/html; charset=utf-8'); self.wfile.write(body); return
        if u.path == '/api/poll':
            if not auth(self.headers): return self._json({'err':'unauth'},401)
            since = int(parse_qs(u.query).get('since',['0'])[0])
            with _lock: msgs = load_msgs()
            return self._json({'messages': [m for m in msgs if m['id'] > since][-200:]})
        if u.path.startswith('/media/'):
            if not auth(self.headers): return self._json({'err':'unauth'},401)
            fn = os.path.basename(u.path); p = os.path.join(MEDIA, fn)
            if not os.path.isfile(p): return self._json({'err':'nofile'},404)
            e = fn.rsplit('.',1)[-1]
            mime = {'png':'image/png','jpg':'image/jpeg','webp':'image/webp','gif':'image/gif',
                    'webm':'audio/webm','ogg':'audio/ogg','mp3':'audio/mpeg','m4a':'audio/mp4',
                    'pdf':'application/pdf','txt':'text/plain'}.get(e,'application/octet-stream')
            self._hdr(200, mime)
            with open(p,'rb') as f: self.wfile.write(f.read()); return
        self._json({'err':'nope'},404)
    def do_POST(self):
        u = urlparse(self.path)
        if not auth(self.headers): return self._json({'err':'unauth'},401)
        n = int(self.headers.get('Content-Length','0'))
        if n > 14_000_000: return self._json({'err':'too big'},413)
        try: req = json.loads(self.rfile.read(n) or b'{}')
        except Exception: return self._json({'err':'bad json'},400)
        if u.path == '/api/send':
            who = req.get('who','')
            if who not in ('tatharaj','adhithiya'): return self._json({'err':'who?'},400)
            kind = req.get('kind','text')
            m = {'id':0,'from':who,'kind':kind,'text':(req.get('text') or '')[:4000],
                 'ts':int(time.time()),'seen':False,'media':None,'name':None,'size':None}
            if kind in ('image','audio','file'):
                d = req.get('data','')
                if ',' in d: d = d.split(',',1)[1]
                raw = base64.b64decode(d)
                if len(raw) > 10_000_000: return self._json({'err':'too big'},413)
                fn = f"{int(time.time()*1000)}_{uuid.uuid4().hex[:6]}.{ext_of(req.get('name','f'), req.get('mime',''))}"
                open(os.path.join(MEDIA,fn),'wb').write(raw)
                m.update(media=fn, name=(req.get('name') or fn)[:120], size=len(raw))
            with _lock:
                msgs = load_msgs(); m['id'] = (msgs[-1]['id']+1) if msgs else 1
                msgs.append(m); save_msgs(msgs)
            return self._json({'ok':True,'message':m})
        if u.path == '/api/seen':
            with _lock:
                msgs = load_msgs(); ch = False
                for x in msgs:
                    if x['from']==req.get('mark_from','') and not x['seen']: x['seen']=True; ch=True
                if ch: save_msgs(msgs)
            return self._json({'ok':True})
        self._json({'err':'nope'},404)

STARTED = int(time.time())
if __name__ == '__main__':
    print(f'WAR CHAT cloud up on :{PORT}')
    ThreadingHTTPServer(('0.0.0.0', PORT), H).serve_forever()
