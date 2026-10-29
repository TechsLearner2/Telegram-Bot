# Telegram bridge — cloud build. ENV: TG_TOKEN, DATA_DIR. Same logic as sandbox bridge.
import json, os, time, threading, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get('DATA_DIR', os.path.join(ROOT, 'data'))
MEDIA = os.path.join(DATA, 'media'); STORE = os.path.join(DATA, 'messages.json')
TOKEN = os.environ.get('TG_TOKEN')
if not TOKEN:
    TG = json.load(open(os.path.join(ROOT, 'telegram_config.json')))
    TOKEN = TG['token']
LOCK_FILE = os.path.join(DATA, 'tg_chat_id.txt')
os.makedirs(MEDIA, exist_ok=True)
_offset = {'v': 0}; _lock = threading.Lock()

def api(method, **params):
    url = f'https://api.telegram.org/bot{TOKEN}/{method}'
    try:
        with urllib.request.urlopen(url, data=urllib.parse.urlencode(params).encode(), timeout=35) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[tg] {method}: {e}'); return None

def load_msgs():
    try: return json.load(open(STORE))
    except Exception: return []
def save_msgs(m):
    tmp = STORE + '.tmp'
    with open(tmp,'w') as f: json.dump(m,f)
    os.replace(tmp, STORE)
def add_msg(who, kind, text, media=None, name=None, size=None):
    with _lock:
        msgs = load_msgs()
        m = {'id': (msgs[-1]['id']+1) if msgs else 1, 'from': who, 'kind': kind,
             'text': (text or '')[:4000], 'ts': int(time.time()), 'seen': False,
             'media': media, 'name': name, 'size': size}
        msgs.append(m); save_msgs(msgs)
    return m
def get_chat_id():
    try: return open(LOCK_FILE).read().strip()
    except Exception: return None
def dl(file_id):
    r = api('getFile', file_id=file_id)
    if not r or not r.get('ok'): return None, None
    path = r['result']['file_path']
    with urllib.request.urlopen(f'https://api.telegram.org/file/bot{TOKEN}/{path}', timeout=30) as resp:
        raw = resp.read()
    ext = path.rsplit('.',1)[-1][:5] or 'bin'
    fn = f"{int(time.time()*1000)}_{os.urandom(3).hex()}.{ext}"
    open(os.path.join(MEDIA, fn),'wb').write(raw)
    return fn, len(raw)

def poll_tg():
    while True:
        r = api('getUpdates', offset=_offset['v'], timeout=30)
        if not r or not r.get('ok'): time.sleep(3); continue
        for u in r['result']:
            _offset['v'] = u['update_id'] + 1
            msg = u.get('message')
            if not msg: continue
            chat_id = str(msg['chat']['id']); locked = get_chat_id()
            if not locked:
                open(LOCK_FILE,'w').write(chat_id); locked = chat_id
                api('sendMessage', chat_id=chat_id, text='⚔️ WAR CHAT cloud bridge LOCKED to this chat.')
            if chat_id != locked: continue
            text = msg.get('text') or msg.get('caption') or ''
            if text.startswith('/start'): continue
            if 'photo' in msg:
                fn, sz = dl(msg['photo'][-1]['file_id']); add_msg('tatharaj','image',text,fn,'telegram-photo.jpg',sz)
            elif 'voice' in msg or 'audio' in msg:
                fid = msg.get('voice',{}).get('file_id') or msg.get('audio',{}).get('file_id')
                fn, sz = dl(fid); add_msg('tatharaj','audio',text,fn,'telegram-voice.ogg',sz)
            elif 'document' in msg:
                d = msg['document']; fn, sz = dl(d['file_id']); add_msg('tatharaj','file',text,fn,d.get('file_name','file'),sz)
            elif text:
                add_msg('tatharaj','text',text)

def poll_chat():
    last = 0
    while True:
        cid = get_chat_id()
        if cid:
            try:
                for m in load_msgs():
                    if m['id'] <= last: continue
                    if m['from'] != 'adhithiya': last = m['id']; continue
                    body = m['text'] or ''
                    if m['kind']=='image': body = f"🖼️ [photo] {body}"
                    elif m['kind']=='audio': body = f"🎙️ [voice] {body}"
                    elif m['kind']=='file': body = f"📄 [{m.get('name','file')}] {body}"
                    api('sendMessage', chat_id=cid, text=(f"<b>Adhithiya ⚔️</b>\n{body}" if body else "<b>Adhithiya ⚔️</b> (media)"), parse_mode='HTML')
                    last = m['id']
            except Exception as e: print(f'[chat->tg] {e}')
        time.sleep(2)

if __name__ == '__main__':
    print('TG bridge cloud up')
    threading.Thread(target=poll_tg, daemon=True).start()
    poll_chat()
