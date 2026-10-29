# WAR CHAT — 24/7 Deploy Kit

## ⚠️ 29 Oct 2026: RAILWAY IS NOT AN OPTION RIGHT NOW
Railway had a **security incident on 21 Oct 2026**. Official status (status.railway.com):
**"New signups remain paused"** — no reopen date announced. You cannot sign up; not your fault,
nothing to fix on your side. → **Deploy to Render (Option A below).** Railway files stay in this
kit in case it reopens later.

---

## OPTION A — RENDER (free, no card, ~10 min, YOUR accounts — I never touch them)

### Step 1 — GitHub repo (2 min)
1. Go to **github.com/new** → sign in (or create account — yours, not mine)
2. Repository name: `war-chat`
3. Visibility: **Private** ← important
4. Click **Create repository**
5. On the next screen click the link **"uploading an existing file"**
6. Drag in **ALL 8 files from this folder EXCEPT `telegram_config.json`**
   (that file holds the bot token — the token goes into Render env vars instead, never into a repo)
7. Click **Commit changes**

### Step 2 — Render deploy (5 min)
1. Go to **render.com** → **Sign up with GitHub**
2. Top-right **New +** → **Blueprint**
3. Pick your `war-chat` repo → Render reads `render.yaml` automatically
4. It asks for 2 env values:
   - `WARCHAT_CODE` → `war2526`
   - `TG_TOKEN` → copy from `telegram_config.json` in this folder (the long number-colon-letter string)
5. **Apply** → wait ~2 min for the build → your URL appears, like
   `https://war-chat-xxxx.onrender.com`
6. Open it → login passcode: **war2526**
7. From YOUR Telegram: send `/start` to **@adhithiya_ai_bot** → bridge re-locks to your chat

### Step 3 — Keep it awake (2 min, free)
Render free sleeps after 15 min idle (~1 min to wake). To keep it always-on:
1. **uptimerobot.com** → free account (yours)
2. Add New Monitor → type **HTTP(s)** → URL: `https://your-render-url/health` → 5-min interval

---

## Honest limits (Render free tier — read once)
- **No permanent disk on free.** With UptimeRobot pinging /health the service never sleeps, so
  history survives in practice. But a redeploy or a long platform outage can reset the container
  and wipe chat history back to day one.
- Safety net available on request: **nightly auto-backup** — the bot sends `messages.json` to your
  Telegram every night, so a wipe ever costs <1 day of messages. Ask and I build it.
- Free tier allows ~750 instance-hours/month; one always-on service uses ~730. One service only.

## Migration of existing history
Sandbox copy currently holds ids 1–50. Once your Render URL is live and locked: tell me in main
chat — I hand you the history file and we load it up. Until then the sandbox pair stays the backup.

## OPTION B — RAILWAY (only when signups reopen — check status.railway.com)
Files ready: `railway.json` (always-restart policy), deploy via GitHub connect or CLI
(`railway up` inside this folder), env vars same as above, add a **volume at `/app/data`**.
Railway's advantage: no 15-min sleep, real persistent volume.

## Security notes
- Never upload `telegram_config.json` anywhere. Token lives only in Render/Railway env vars.
- Token can be revoked anytime: Telegram → @BotFather → /mybots → API Token → Revoke.
- Chat is passcode-protected (`war2526`); anyone with the URL but without the passcode sees nothing.
